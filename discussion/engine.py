"""
讨论引擎主模块

实现群聊讨论的核心逻辑，包括轮流发言、共识检测、状态管理等
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
import logging

from .message import Message, MessageType, MessagePriority, MessageStore, DiscussionSummary
from .state import DiscussionState, DiscussionPhase, StateManager, RoundManager
from .round_robin import Role, TurnManager, TurnOrderStrategy, SpeakingQueue
from .consensus import (
    ConsensusChecker, ConsensusStrategy, ConsensusResult,
    HybridConsensusDetector, StagnationDetector
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscussionConfig:
    """讨论配置类"""
    
    def __init__(
        self,
        max_rounds: int = 20,
        consensus_strategy: ConsensusStrategy = ConsensusStrategy.HYBRID,
        consensus_threshold: float = 0.7,
        turn_order_strategy: TurnOrderStrategy = TurnOrderStrategy.ROUND_ROBIN,
        auto_check_consensus: bool = True,
        check_consensus_every_n_rounds: int = 1,
        enable_stagnation_detection: bool = True,
        stagnation_rounds: int = 3,
        boss_intervention_keywords: Optional[List[str]] = None
    ):
        self.max_rounds = max_rounds
        self.consensus_strategy = consensus_strategy
        self.consensus_threshold = consensus_threshold
        self.turn_order_strategy = turn_order_strategy
        self.auto_check_consensus = auto_check_consensus
        self.check_consensus_every_n_rounds = check_consensus_every_n_rounds
        self.enable_stagnation_detection = enable_stagnation_detection
        self.stagnation_rounds = stagnation_rounds
        self.boss_intervention_keywords = boss_intervention_keywords or [
            '我决定', '听我的', '就这样', '执行', '定下来',
            'i decide', 'final decision', 'execute', 'do it'
        ]


class DiscussionEngine:
    """
    讨论引擎主类
    
    管理整个讨论流程，包括：
    - 轮流发言机制（狼人杀式轮询）
    - 达成一致判断（共识检测算法）
    - 轮次限制控制（每阶段最多20轮）
    - 老板介入检测（任意消息触发）
    - 讨论状态管理（进行中/已达成一致/需要老板决策/轮次耗尽）
    - 讨论消息的存储和展示
    """
    
    def __init__(
        self,
        roles: List[Role],
        phase: DiscussionPhase = DiscussionPhase.INITIAL,
        config: Optional[DiscussionConfig] = None,
        boss_role_id: Optional[str] = None
    ):
        """
        初始化讨论引擎
        
        Args:
            roles: 参与讨论的角色列表
            phase: 当前讨论阶段
            config: 讨论配置
            boss_role_id: 老板角色ID（可选）
        """
        self.roles = roles
        self.phase = phase
        self.config = config or DiscussionConfig()
        self.boss_role_id = boss_role_id
        
        # 初始化各个管理器
        self.state_manager = StateManager(DiscussionState.PENDING)
        self.round_manager = RoundManager(self.config.max_rounds)
        self.turn_manager = TurnManager(roles, self.config.turn_order_strategy)
        self.message_store = MessageStore()
        self.speaking_queue = SpeakingQueue()
        self.consensus_checker = ConsensusChecker(self.config.consensus_strategy)
        
        # 停滞检测器
        self.stagnation_detector = StagnationDetector(
            stagnation_rounds=self.config.stagnation_rounds
        )
        
        # 讨论主题
        self.topic: Optional[str] = None
        
        # 事件回调
        self._on_state_change: Optional[Callable[[DiscussionState, DiscussionState], None]] = None
        self._on_consensus: Optional[Callable[[ConsensusResult], None]] = None
        self._on_boss_intervention: Optional[Callable[[Message], None]] = None
        self._on_round_complete: Optional[Callable[[int], None]] = None
        
        # 统计信息
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        logger.info(f"讨论引擎初始化完成，角色数: {len(roles)}, 最大轮次: {self.config.max_rounds}")
    
    # ============ 事件回调设置 ============
    
    def on_state_change(self, callback: Callable[[DiscussionState, DiscussionState], None]) -> None:
        """设置状态变化回调"""
        self._on_state_change = callback
    
    def on_consensus(self, callback: Callable[[ConsensusResult], None]) -> None:
        """设置达成共识回调"""
        self._on_consensus = callback
    
    def on_boss_intervention(self, callback: Callable[[Message], None]) -> None:
        """设置老板介入回调"""
        self._on_boss_intervention = callback
    
    def on_round_complete(self, callback: Callable[[int], None]) -> None:
        """设置轮次完成回调"""
        self._on_round_complete = callback
    
    # ============ 核心方法 ============
    
    async def start_discussion(self, topic: str) -> bool:
        """
        开始讨论
        
        Args:
            topic: 讨论主题
            
        Returns:
            是否成功开始
        """
        if not self.state_manager.can_transition_to(DiscussionState.ONGOING):
            logger.warning(f"无法从 {self.state_manager.current_state} 开始讨论")
            return False
        
        self.topic = topic
        self.start_time = datetime.now()
        
        # 状态转换
        self._transition_state(
            DiscussionState.ONGOING,
            reason=f"开始讨论: {topic}",
            triggered_by="system"
        )
        
        # 开始第一轮
        self.round_manager.start_round()
        self.turn_manager.start_new_round()
        
        logger.info(f"讨论开始: {topic}")
        return True
    
    async def next_turn(self) -> Optional[Message]:
        """
        进行下一轮发言
        
        Returns:
            下一位发言者的消息请求（需要外部填充内容），如果讨论结束则返回None
        """
        # 检查讨论状态
        if not self.state_manager.is_active():
            logger.info(f"讨论已结束，当前状态: {self.state_manager.current_state}")
            return None
        
        # 检查轮次是否耗尽
        if self.round_manager.is_rounds_exhausted():
            self._transition_state(
                DiscussionState.ROUNDS_EXHAUSTED,
                reason=f"达到最大轮次限制 ({self.config.max_rounds})",
                triggered_by="system"
            )
            return None
        
        # 获取下一个发言者
        speaker = self.turn_manager.get_next_speaker()
        
        if speaker is None:
            # 当前轮次完成，开始新一轮
            self._complete_current_round()
            
            # 检查是否需要自动检测共识
            if self.config.auto_check_consensus:
                consensus_result = self.check_consensus()
                if consensus_result.reached:
                    self._handle_consensus_reached(consensus_result)
                    return None
            
            # 开始新一轮
            self.round_manager.start_round()
            self.turn_manager.start_new_round()
            
            # 获取新一轮的第一个发言者
            speaker = self.turn_manager.get_next_speaker()
        
        if speaker is None:
            logger.warning("没有可用的发言者")
            return None
        
        # 创建消息请求（内容为空，待填充）
        message = Message.create_request(
            sender_id=speaker.id,
            sender_name=speaker.name,
            round_number=self.round_manager.current_round,
            message_type=MessageType.SPEECH
        )
        
        return message
    
    def submit_message(self, message: Message) -> bool:
        """
        提交发言消息
        
        Args:
            message: 发言消息
            
        Returns:
            是否成功提交
        """
        if not self.state_manager.is_active():
            return False
        
        # 检查消息内容
        if not message.content or not message.content.strip():
            logger.warning(f"消息内容不能为空: {message.sender_id}")
            return False
        
        # 设置轮次号
        message.round_number = self.round_manager.current_round
        
        # 检查老板介入
        if self.check_boss_intervention(message):
            message.message_type = MessageType.BOSS_INTERVENTION
            message.priority = MessagePriority.URGENT
            self._handle_boss_intervention(message)
        
        # 存储消息
        self.message_store.add(message)
        
        # 记录参与者
        self.round_manager.record_participant(message.sender_id)
        self.turn_manager.mark_spoken(message.sender_id)
        
        # 更新角色发言统计
        role = self.turn_manager.get_role(message.sender_id)
        if role:
            role.record_speech(len(message.content))
        
        # 添加到停滞检测器
        if self.config.enable_stagnation_detection:
            round_messages = [m.content for m in self.message_store.get_by_round(self.round_manager.current_round)]
            self.stagnation_detector.add_round_messages(self.round_manager.current_round, round_messages)
        
        logger.debug(f"消息已提交: {message.sender_name} (轮次: {message.round_number})")
        return True
    
    def check_consensus(self) -> ConsensusResult:
        """
        检查是否达成共识
        
        Returns:
            共识检测结果
        """
        # 收集所有消息
        messages = [m.content for m in self.message_store.get_all()]
        participants = self.turn_manager.get_speaking_order()
        
        # 执行共识检测
        result = self.consensus_checker.check(
            messages=messages,
            participants=participants,
            current_round=self.round_manager.current_round
        )
        
        logger.info(f"共识检测结果: reached={result.reached}, confidence={result.confidence:.2%}")
        return result
    
    def check_boss_intervention(self, message: Message) -> bool:
        """
        检查是否是老板介入消息
        
        Args:
            message: 待检查的消息
            
        Returns:
            是否是老板介入
        """
        # 检查发送者是否是老板
        if message.sender_id == self.boss_role_id:
            return True
        
        role = self.turn_manager.get_role(message.sender_id)
        if role and role.is_boss:
            return True
        
        # 检查关键词
        content_lower = message.content.lower()
        for keyword in self.config.boss_intervention_keywords:
            if keyword.lower() in content_lower:
                return True
        
        return False
    
    # ============ 内部处理方法 ============
    
    def _transition_state(
        self, 
        new_state: DiscussionState, 
        reason: str = "",
        triggered_by: Optional[str] = None
    ) -> bool:
        """状态转换"""
        old_state = self.state_manager.current_state
        success = self.state_manager.transition_to(new_state, reason, triggered_by)
        
        if success:
            logger.info(f"状态转换: {old_state.name} -> {new_state.name}, 原因: {reason}")
            
            # 触发回调
            if self._on_state_change:
                try:
                    self._on_state_change(old_state, new_state)
                except Exception as e:
                    logger.error(f"状态变化回调执行失败: {e}")
            
            # 如果是终止状态，记录结束时间
            if new_state.is_terminal():
                self.end_time = datetime.now()
        
        return success
    
    def _handle_consensus_reached(self, result: ConsensusResult) -> None:
        """处理达成共识"""
        self._transition_state(
            DiscussionState.CONSENSUS_REACHED,
            reason=f"达成共识，置信度: {result.confidence:.2%}",
            triggered_by="consensus_checker"
        )
        
        # 触发回调
        if self._on_consensus:
            try:
                self._on_consensus(result)
            except Exception as e:
                logger.error(f"共识回调执行失败: {e}")
    
    def _handle_boss_intervention(self, message: Message) -> None:
        """处理老板介入"""
        logger.info(f"检测到老板介入: {message.sender_name}")
        
        # 触发回调
        if self._on_boss_intervention:
            try:
                self._on_boss_intervention(message)
            except Exception as e:
                logger.error(f"老板介入回调执行失败: {e}")
        
        # 转换状态为需要老板决策
        self._transition_state(
            DiscussionState.BOSS_NEEDED,
            reason=f"老板 {message.sender_name} 介入讨论",
            triggered_by=message.sender_id
        )
    
    def _complete_current_round(self) -> None:
        """完成当前轮次"""
        self.round_manager.end_round()
        
        logger.info(f"轮次 {self.round_manager.current_round} 完成")
        
        # 触发回调
        if self._on_round_complete:
            try:
                self._on_round_complete(self.round_manager.current_round)
            except Exception as e:
                logger.error(f"轮次完成回调执行失败: {e}")
    
    # ============ 查询方法 ============
    
    def get_current_state(self) -> DiscussionState:
        """获取当前状态"""
        return self.state_manager.current_state
    
    def get_current_round(self) -> int:
        """获取当前轮次"""
        return self.round_manager.current_round
    
    def get_remaining_rounds(self) -> int:
        """获取剩余轮次"""
        return self.round_manager.get_remaining_rounds()
    
    def get_progress(self) -> Dict[str, Any]:
        """获取讨论进度"""
        return {
            'state': self.state_manager.current_state.name,
            'state_desc': str(self.state_manager.current_state),
            'current_round': self.round_manager.current_round,
            'max_rounds': self.config.max_rounds,
            'remaining_rounds': self.round_manager.get_remaining_rounds(),
            'progress_percentage': self.round_manager.get_progress_percentage(),
            'message_count': self.message_store.get_message_count(),
            'participant_count': len(self.turn_manager.get_all_roles()),
            'speaking_participants': len(self.message_store.get_participants())
        }
    
    def get_discussion_history(self) -> List[Dict[str, Any]]:
        """获取讨论历史"""
        return self.message_store.to_dict_list()
    
    def get_summary(self) -> DiscussionSummary:
        """获取讨论总结"""
        summary = DiscussionSummary(
            topic=self.topic or "未设置主题",
            total_rounds=self.round_manager.current_round,
            participants=self.turn_manager.get_speaking_order()
        )
        
        # 收集关键信息
        all_messages = self.message_store.get_all()
        
        # 提取关键观点（简单实现）
        for msg in all_messages:
            if msg.is_proposal():
                summary.key_points.append(msg.content)
            elif msg.is_agreement():
                summary.agreements.append(msg.content)
            elif msg.is_disagreement():
                summary.disagreements.append(msg.content)
        
        # 计算持续时间
        if self.start_time:
            end = self.end_time or datetime.now()
            summary.duration_seconds = (end - self.start_time).total_seconds()
        
        return summary
    
    def get_next_speaker_info(self) -> Optional[Dict[str, Any]]:
        """获取下一位发言者信息"""
        speaker = self.turn_manager.get_current_speaker()
        if speaker:
            return {
                'id': speaker.id,
                'name': speaker.name,
                'description': speaker.description,
                'speech_count': speaker.speech_count
            }
        return None
    
    def get_stagnation_status(self) -> Dict[str, Any]:
        """获取停滞状态"""
        if not self.config.enable_stagnation_detection:
            return {'enabled': False}
        return self.stagnation_detector.detect_stagnation()
    
    # ============ 控制方法 ============
    
    def pause(self) -> bool:
        """暂停讨论"""
        return self._transition_state(
            DiscussionState.PAUSED,
            reason="讨论被暂停",
            triggered_by="user"
        )
    
    def resume(self) -> bool:
        """恢复讨论"""
        return self._transition_state(
            DiscussionState.ONGOING,
            reason="讨论被恢复",
            triggered_by="user"
        )
    
    def terminate(self, reason: str = "") -> bool:
        """终止讨论"""
        return self._transition_state(
            DiscussionState.TERMINATED,
            reason=reason or "讨论被终止",
            triggered_by="user"
        )
    
    def force_consensus(self, conclusion: str) -> None:
        """强制设置共识结论"""
        self._transition_state(
            DiscussionState.CONSENSUS_REACHED,
            reason=f"强制设置共识: {conclusion}",
            triggered_by="user"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'topic': self.topic,
            'phase': self.phase.name,
            'config': {
                'max_rounds': self.config.max_rounds,
                'consensus_strategy': self.config.consensus_strategy.name,
                'turn_order_strategy': self.config.turn_order_strategy.name
            },
            'state': self.state_manager.to_dict(),
            'round': self.round_manager.to_dict(),
            'turn': self.turn_manager.to_dict(),
            'progress': self.get_progress(),
            'summary': self.get_summary().to_dict()
        }


class AsyncDiscussionRunner:
    """
    异步讨论运行器
    
    用于异步运行完整讨论流程
    """
    
    def __init__(self, engine: DiscussionEngine):
        self.engine = engine
        self._message_generator: Optional[Callable[[Role, str], str]] = None
    
    def set_message_generator(self, generator: Callable[[Role, str], str]) -> None:
        """设置消息生成器（用于模拟发言）"""
        self._message_generator = generator
    
    async def run(
        self, 
        topic: str,
        max_messages: Optional[int] = None
    ) -> AsyncGenerator[Message, None]:
        """
        运行完整讨论流程
        
        Args:
            topic: 讨论主题
            max_messages: 最大消息数限制
            
        Yields:
            每条发言消息
        """
        # 开始讨论
        await self.engine.start_discussion(topic)
        
        message_count = 0
        
        while self.engine.get_current_state() == DiscussionState.ONGOING:
            # 获取下一位发言者
            message_request = await self.engine.next_turn()
            
            if message_request is None:
                break
            
            # 如果有消息生成器，生成消息内容
            if self._message_generator:
                role = self.engine.turn_manager.get_role(message_request.sender_id)
                if role:
                    message_request.content = self._message_generator(role, topic)
            
            # 提交消息
            self.engine.submit_message(message_request)
            
            # 产出消息
            yield message_request
            
            message_count += 1
            
            # 检查消息数限制
            if max_messages and message_count >= max_messages:
                logger.info(f"达到最大消息数限制 ({max_messages})")
                break
            
            # 短暂延迟，避免过快
            await asyncio.sleep(0.1)
        
        logger.info(f"讨论结束，共 {message_count} 条消息")
