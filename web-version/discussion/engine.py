"""
讨论引擎模块 - 管理角色间的讨论流程

功能：
- 管理角色轮流发言
- 检测共识
- 处理@老板逻辑
- 支持WebSocket广播
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from roles.base_role import BaseRole, Message, DiscussionContext
from roles.role_matrix import (
    Role, Phase, ParticipationType,
    get_participation_type, get_roles_by_phase, should_notify_boss,
    get_responsible_roles
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscussionStatus(Enum):
    """讨论状态"""
    PENDING = "pending"           # 等待开始
    IN_PROGRESS = "in_progress"   # 进行中
    CONSENSUS = "consensus"       # 达成共识
    NEED_DECISION = "need_decision"  # 需要决策
    COMPLETED = "completed"       # 已完成
    TIMEOUT = "timeout"           # 超时


@dataclass
class DiscussionResult:
    """讨论结果"""
    status: DiscussionStatus
    messages: List[Message]
    consensus_content: Optional[str] = None
    decision_required: bool = False
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpeakingTurn:
    """发言轮次"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    require_boss_attention: bool = False
    is_decision: bool = False


class DiscussionEngine:
    """
    讨论引擎
    
    管理多角色讨论流程，包括：
    - 角色轮流发言
    - 共识检测
    - @老板处理
    - 讨论总结
    """
    
    def __init__(
        self,
        max_rounds: int = 10,
        consensus_threshold: int = 3,
        auto_invite_boss: bool = True
    ):
        """
        初始化讨论引擎
        
        Args:
            max_rounds: 最大讨论轮数
            consensus_threshold: 共识检测阈值（连续几轮无新观点）
            auto_invite_boss: 是否自动邀请老板参与
        """
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.auto_invite_boss = auto_invite_boss
        
        # 角色注册
        self.roles: Dict[str, BaseRole] = {}
        
        # 消息回调
        self.message_callbacks: List[Callable[[Message], None]] = []
        
        # 当前讨论
        self.current_discussion: Optional[DiscussionContext] = None
        self.discussion_history: List[DiscussionContext] = []
        
        logger.info(f"讨论引擎初始化完成 (max_rounds={max_rounds})")
    
    def register_role(self, role: BaseRole):
        """注册角色"""
        self.roles[role.role_type] = role
        logger.info(f"注册角色: {role.role_type}")
    
    def register_roles(self, roles: List[BaseRole]):
        """批量注册角色"""
        for role in roles:
            self.register_role(role)
    
    def add_message_callback(self, callback: Callable[[Message], None]):
        """添加消息回调"""
        self.message_callbacks.append(callback)
    
    def _notify_message(self, message: Message):
        """通知消息回调"""
        for callback in self.message_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"消息回调失败: {e}")
    
    async def start_discussion(
        self,
        phase: Phase,
        topic: str,
        initial_message: Optional[str] = None,
        required_roles: Optional[List[str]] = None
    ) -> DiscussionResult:
        """
        开始讨论
        
        Args:
            phase: 当前阶段
            topic: 讨论主题
            initial_message: 初始消息
            required_roles: 必需参与的角色列表
            
        Returns:
            讨论结果
        """
        # 创建讨论上下文
        context = DiscussionContext(
            phase=phase.value,
            topic=topic,
            participants=[]
        )
        
        self.current_discussion = context
        
        # 确定参与角色
        if required_roles is None:
            phase_roles = get_roles_by_phase(phase)
            required_roles = [r.value for r in phase_roles]
        
        context.participants = required_roles
        
        # 添加初始消息
        if initial_message:
            init_msg = Message(
                role="user",
                content=initial_message,
                sender="系统"
            )
            context.add_message(init_msg)
            self._notify_message(init_msg)
        
        logger.info(f"开始讨论: {topic} (阶段: {phase.value})")
        logger.info(f"参与角色: {required_roles}")
        
        # 执行讨论
        result = await self._run_discussion(context, phase)
        
        # 保存讨论历史
        self.discussion_history.append(context)
        
        return result
    
    async def _run_discussion(
        self,
        context: DiscussionContext,
        phase: Phase
    ) -> DiscussionResult:
        """
        执行讨论流程
        
        Args:
            context: 讨论上下文
            phase: 当前阶段
            
        Returns:
            讨论结果
        """
        round_num = 0
        no_new_idea_count = 0
        last_speaking_contents: List[str] = []
        
        # 获取负责角色（优先发言）
        responsible_roles = get_responsible_roles(phase)
        responsible_role_names = [r.value for r in responsible_roles]
        
        # 排序：负责角色优先
        ordered_roles = sorted(
            context.participants,
            key=lambda r: 0 if r in responsible_role_names else 1
        )
        
        while round_num < self.max_rounds:
            round_num += 1
            logger.info(f"讨论轮次: {round_num}/{self.max_rounds}")
            
            round_has_new_idea = False
            
            for role_name in ordered_roles:
                # 跳过未注册的角色
                if role_name not in self.roles:
                    logger.warning(f"角色未注册: {role_name}")
                    continue
                
                role = self.roles[role_name]
                
                # 检查角色在该阶段的参与类型
                try:
                    role_enum = Role(role_name)
                    participation = get_participation_type(phase, role_enum)
                    
                    # 不参与的角色跳过
                    if participation == ParticipationType.NONE:
                        continue
                except ValueError:
                    pass
                
                # 角色发言
                try:
                    response = await role.participate(
                        context=context,
                        topic=context.topic,
                        previous_messages=context.messages
                    )
                    
                    # 创建消息
                    message = Message(
                        role="assistant",
                        content=response,
                        sender=role_name
                    )
                    context.add_message(message)
                    self._notify_message(message)
                    
                    # 检查是否需要@老板
                    if self._check_mention_boss(response, role_name, phase):
                        logger.info(f"检测到@老板请求: {role_name}")
                        
                        if self.auto_invite_boss and Role.BOSS.value in self.roles:
                            # 邀请老板发言
                            boss_response = await self._invite_boss(context, phase, response)
                            
                            if boss_response:
                                boss_message = Message(
                                    role="assistant",
                                    content=boss_response,
                                    sender=Role.BOSS.value
                                )
                                context.add_message(boss_message)
                                self._notify_message(boss_message)
                                
                                # 检查老板是否做出决策
                                if self._check_boss_decision(boss_response):
                                    context.require_boss_decision = True
                                    return DiscussionResult(
                                        status=DiscussionStatus.NEED_DECISION,
                                        messages=context.messages,
                                        decision_required=True,
                                        summary=self._generate_summary(context)
                                    )
                    
                    # 检查是否有新观点
                    if not self._is_similar_content(response, last_speaking_contents):
                        round_has_new_idea = True
                        last_speaking_contents.append(response)
                        # 保持最近5条内容
                        if len(last_speaking_contents) > 5:
                            last_speaking_contents.pop(0)
                    
                except Exception as e:
                    logger.error(f"角色 {role_name} 发言失败: {e}")
                    continue
            
            # 检查共识
            if not round_has_new_idea:
                no_new_idea_count += 1
                logger.info(f"无新观点计数: {no_new_idea_count}/{self.consensus_threshold}")
                
                if no_new_idea_count >= self.consensus_threshold:
                    logger.info("检测到共识，讨论结束")
                    context.consensus_reached = True
                    return DiscussionResult(
                        status=DiscussionStatus.CONSENSUS,
                        messages=context.messages,
                        consensus_content=self._extract_consensus(context),
                        summary=self._generate_summary(context)
                    )
            else:
                no_new_idea_count = 0
        
        # 达到最大轮数
        logger.info("达到最大讨论轮数，讨论结束")
        return DiscussionResult(
            status=DiscussionStatus.TIMEOUT,
            messages=context.messages,
            summary=self._generate_summary(context)
        )
    
    def _check_mention_boss(self, content: str, role_name: str, phase: Phase) -> bool:
        """
        检查是否需要@老板
        
        Args:
            content: 消息内容
            role_name: 角色名称
            phase: 当前阶段
            
        Returns:
            是否需要@老板
        """
        # 检查显式的@老板
        mention_keywords = ["@老板", "@Boss", "@BOSS", "请老板决策", "需要老板决定"]
        if any(keyword in content for keyword in mention_keywords):
            return True
        
        # 检查职责矩阵
        try:
            role_enum = Role(role_name)
            return should_notify_boss(phase, role_enum)
        except ValueError:
            return False
    
    async def _invite_boss(
        self,
        context: DiscussionContext,
        phase: Phase,
        reason: str
    ) -> Optional[str]:
        """
        邀请老板参与
        
        Args:
            context: 讨论上下文
            phase: 当前阶段
            reason: 邀请原因
            
        Returns:
            老板的回复
        """
        if Role.BOSS.value not in self.roles:
            return None
        
        boss = self.roles[Role.BOSS.value]
        
        # 构建邀请提示
        invite_prompt = f"""团队成员请求您参与决策。

讨论主题: {context.topic}
当前阶段: {phase.value}

请求原因:
{reason}

请查看讨论历史并给出您的意见或决策。
"""
        
        try:
            response = await boss.chat(invite_prompt, context)
            return response
        except Exception as e:
            logger.error(f"邀请老板失败: {e}")
            return None
    
    def _check_boss_decision(self, boss_response: str) -> bool:
        """
        检查老板是否做出了明确决策
        
        Args:
            boss_response: 老板的回复
            
        Returns:
            是否做出了决策
        """
        decision_keywords = [
            "决定", "决策", "批准", "同意", "否决", "驳回",
            "通过", "不通过", "确认", "确定", "最终"
        ]
        return any(keyword in boss_response for keyword in decision_keywords)
    
    def _is_similar_content(self, content: str, previous_contents: List[str]) -> bool:
        """
        检查内容是否与之前的内容相似
        
        Args:
            content: 当前内容
            previous_contents: 之前的内容列表
            
        Returns:
            是否相似
        """
        # 简单的相似度检查：提取关键词比较
        content_keywords = set(self._extract_keywords(content))
        
        for prev in previous_contents:
            prev_keywords = set(self._extract_keywords(prev))
            
            # 计算Jaccard相似度
            if content_keywords and prev_keywords:
                intersection = content_keywords & prev_keywords
                union = content_keywords | prev_keywords
                similarity = len(intersection) / len(union)
                
                if similarity > 0.7:  # 相似度阈值
                    return True
        
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取：过滤停用词，保留名词性词汇
        stop_words = {"的", "了", "是", "在", "和", "与", "或", "有", "我", "你", "他", "她", "它", "我们", "你们", "他们", "这个", "那个", "这些", "那些"}
        
        words = text.split()
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        
        return keywords
    
    def _extract_consensus(self, context: DiscussionContext) -> Optional[str]:
        """提取共识内容"""
        # 从最后几条消息中提取共同观点
        recent_messages = context.messages[-5:] if len(context.messages) >= 5 else context.messages
        
        # 简单处理：返回最后一条负责角色的消息
        for msg in reversed(recent_messages):
            if msg.sender in context.participants:
                return msg.content
        
        return None
    
    def _generate_summary(self, context: DiscussionContext) -> str:
        """生成讨论总结"""
        summary_parts = []
        
        summary_parts.append(f"讨论主题: {context.topic}")
        summary_parts.append(f"阶段: {context.phase}")
        summary_parts.append(f"参与角色: {', '.join(context.participants)}")
        summary_parts.append(f"消息数量: {len(context.messages)}")
        
        if context.consensus_reached:
            summary_parts.append("状态: 已达成共识")
        elif context.require_boss_decision:
            summary_parts.append("状态: 需要老板决策")
        else:
            summary_parts.append("状态: 讨论结束")
        
        return "\n".join(summary_parts)
    
    async def make_decision(
        self,
        context: DiscussionContext,
        decision_topic: str,
        options: List[str]
    ) -> Dict[str, Any]:
        """
        请求老板做出决策
        
        Args:
            context: 讨论上下文
            decision_topic: 决策主题
            options: 可选方案
            
        Returns:
            决策结果
        """
        if Role.BOSS.value not in self.roles:
            return {"error": "老板角色未注册"}
        
        boss = self.roles[Role.BOSS.value]
        
        # 构建决策提示
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        decision_prompt = f"""需要您做出最终决策。

决策主题: {decision_topic}

可选方案:
{options_text}

请查看讨论历史，然后做出决策。
请以JSON格式输出决策结果：
{{
    "decision": "决策内容",
    "selected_option": "选择的方案",
    "reasoning": "决策理由",
    "next_actions": ["后续行动1", "后续行动2"]
}}
"""
        
        try:
            response = await boss.chat(decision_prompt, context)
            
            # 记录决策
            decision_msg = Message(
                role="assistant",
                content=f"【决策】{response}",
                sender=Role.BOSS.value
            )
            context.add_message(decision_msg)
            self._notify_message(decision_msg)
            
            return {
                "topic": decision_topic,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"决策失败: {e}")
            return {"error": str(e)}
    
    def get_discussion_history(self) -> List[DiscussionContext]:
        """获取讨论历史"""
        return self.discussion_history.copy()
    
    def get_current_discussion(self) -> Optional[DiscussionContext]:
        """获取当前讨论"""
        return self.current_discussion
    
    def clear_history(self):
        """清除讨论历史"""
        self.discussion_history.clear()


# WebSocket广播支持
class WebSocketBroadcaster:
    """WebSocket广播器"""
    
    def __init__(self):
        self.connections: List[Any] = []
    
    def add_connection(self, connection: Any):
        """添加连接"""
        self.connections.append(connection)
    
    def remove_connection(self, connection: Any):
        """移除连接"""
        if connection in self.connections:
            self.connections.remove(connection)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息"""
        disconnected = []
        
        for conn in self.connections:
            try:
                if hasattr(conn, 'send_json'):
                    await conn.send_json(message)
                elif hasattr(conn, 'send'):
                    await conn.send(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播失败: {e}")
                disconnected.append(conn)
        
        # 清理断开连接
        for conn in disconnected:
            self.remove_connection(conn)


# 便捷函数
async def run_phase_discussion(
    engine: DiscussionEngine,
    phase: Phase,
    topic: str,
    initial_message: str,
    roles: List[BaseRole]
) -> DiscussionResult:
    """
    运行阶段讨论
    
    Args:
        engine: 讨论引擎
        phase: 阶段
        topic: 主题
        initial_message: 初始消息
        roles: 参与角色
        
    Returns:
        讨论结果
    """
    # 注册角色
    engine.register_roles(roles)
    
    # 开始讨论
    result = await engine.start_discussion(
        phase=phase,
        topic=topic,
        initial_message=initial_message
    )
    
    return result


if __name__ == "__main__":
    import asyncio
    
    async def test_engine():
        engine = DiscussionEngine()
        print(f"讨论引擎: {engine}")
        print(f"最大轮数: {engine.max_rounds}")
        print(f"共识阈值: {engine.consensus_threshold}")
    
    asyncio.run(test_engine())
