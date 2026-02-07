"""
工作流管理模块
=============
管理9个阶段的执行流程和状态转换
"""

import asyncio
import json
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

# 导入架构模块
from architecture.base import PhaseStatus, DiscussionConfig, PhaseConfig
from architecture.phase import Phase, PhaseManager, PhaseOutput
from architecture.role import Role, BossRole, create_all_roles
from architecture.message import Message, DiscussionMessage, SystemMessage, MessagePool
from architecture.discussion_engine import DiscussionEngine, DiscussionState

logger = logging.getLogger(__name__)


class PhaseResultStatus(Enum):
    """阶段结果状态"""
    SUCCESS = "success"          # 成功完成
    CONSENSUS_REACHED = "consensus_reached"  # 达成一致
    TIMEOUT = "timeout"          # 超时
    BOSS_INTERVENTION = "boss_intervention"  # 老板介入
    FAILED = "failed"            # 失败
    SKIPPED = "skipped"          # 跳过


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase_id: str
    phase_name: str
    status: PhaseResultStatus
    output: Any = None
    rounds: int = 0
    duration_seconds: float = 0.0
    messages: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "status": self.status.value,
            "output": self.output,
            "rounds": self.rounds,
            "duration_seconds": self.duration_seconds,
            "messages_count": len(self.messages),
            "error": self.error
        }


class PhaseExecutor:
    """
    阶段执行器
    
    负责执行单个阶段的讨论流程
    """
    
    def __init__(
        self,
        phase: Phase,
        roles: List[Role],
        discussion_engine: DiscussionEngine,
        on_message: Optional[Callable[[DiscussionMessage], None]] = None
    ):
        self.phase = phase
        self.roles = {r.role_id: r for r in roles}
        self.discussion_engine = discussion_engine
        self.on_message = on_message
        self.messages: List[DiscussionMessage] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def get_participating_roles(self) -> List[Role]:
        """获取参与当前阶段的角色"""
        participating = []
        
        # 必需角色
        for role_id in self.phase.config.required_roles:
            if role_id in self.roles:
                participating.append(self.roles[role_id])
        
        # 可选角色
        for role_id in self.phase.config.optional_roles:
            if role_id in self.roles and role_id not in self.phase.config.required_roles:
                participating.append(self.roles[role_id])
        
        # 确保老板在列表中
        for role in self.roles.values():
            if isinstance(role, BossRole) and role not in participating:
                participating.append(role)
                break
        
        return participating
    
    async def execute(self, context: str = "") -> PhaseResult:
        """
        执行阶段讨论
        
        Args:
            context: 阶段上下文（前一阶段的输出）
            
        Returns:
            阶段执行结果
        """
        self.start_time = datetime.now()
        self.messages = []
        
        logger.info(f"开始执行阶段: {self.phase.name} ({self.phase.phase_id})")
        
        # 开始阶段
        self.phase.start()
        
        # 构建讨论主题
        topic = f"【{self.phase.name}】{self.phase.config.description}"
        if context:
            topic += f"\n\n上下文:\n{context}"
        
        # 获取参与角色
        participating_roles = self.get_participating_roles()
        logger.info(f"参与角色: {[r.name for r in participating_roles]}")
        
        # 开始讨论
        await self.discussion_engine.start_discussion(topic)
        
        # 运行讨论直到结束
        while self.discussion_engine.state.is_running:
            # 获取下一位发言者
            message_request = await self.discussion_engine.next_turn()
            
            if message_request is None:
                break
            
            # 获取角色
            role = self.roles.get(message_request.sender_id)
            if role:
                # 获取上下文
                context_str = self._build_context()
                
                # 角色发言
                message = role.speak(context_str, self.phase.phase_id, self.phase.current_round)
                
                # 提交消息
                self.discussion_engine.submit_message(message)
                
                # 记录消息
                if isinstance(message, DiscussionMessage):
                    self.messages.append(message)
                    
                    # 回调通知
                    if self.on_message:
                        await self._notify_message(message)
                
                # 记录参与
                self.phase.record_participation(role.role_id)
            
            # 短暂延迟
            await asyncio.sleep(0.5)
        
        # 阶段结束
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # 确定结果状态
        status = self._determine_result_status()
        
        # 保存阶段输出
        output = self._build_output()
        
        result = PhaseResult(
            phase_id=self.phase.phase_id,
            phase_name=self.phase.name,
            status=status,
            output=output,
            rounds=self.phase.current_round,
            duration_seconds=duration,
            messages=[m.to_dict() for m in self.messages]
        )
        
        logger.info(f"阶段 {self.phase.name} 完成，状态: {status.value}, 轮次: {self.phase.current_round}")
        
        return result
    
    def _build_context(self) -> str:
        """构建讨论上下文"""
        if not self.messages:
            return ""
        
        # 获取最近5条消息
        recent = self.messages[-5:]
        context_parts = []
        for msg in recent:
            sender_name = self.roles.get(msg.sender, msg.sender)
            if hasattr(sender_name, 'name'):
                sender_name = sender_name.name
            context_parts.append(f"[{sender_name}]: {msg.content}")
        
        return "\n".join(context_parts)
    
    async def _notify_message(self, message: DiscussionMessage):
        """通知消息回调"""
        if self.on_message:
            try:
                if asyncio.iscoroutinefunction(self.on_message):
                    await self.on_message(message)
                else:
                    self.on_message(message)
            except Exception as e:
                logger.error(f"消息回调执行失败: {e}")
    
    def _determine_result_status(self) -> PhaseResultStatus:
        """确定结果状态"""
        if self.phase.status == PhaseStatus.CONSENSUS_REACHED:
            return PhaseResultStatus.CONSENSUS_REACHED
        elif self.phase.status == PhaseStatus.TIMEOUT:
            return PhaseResultStatus.TIMEOUT
        elif self.phase.status == PhaseStatus.BOSS_INTERVENTION:
            return PhaseResultStatus.BOSS_INTERVENTION
        elif self.phase.status == PhaseStatus.COMPLETED:
            return PhaseResultStatus.SUCCESS
        else:
            return PhaseResultStatus.FAILED
    
    def _build_output(self) -> Dict[str, Any]:
        """构建阶段输出"""
        return {
            "phase_id": self.phase.phase_id,
            "phase_name": self.phase.name,
            "deliverable_type": self.phase.config.deliverable_type,
            "rounds": self.phase.current_round,
            "messages": [m.to_dict() for m in self.messages],
            "participation": {
                r.role_id: self.phase._participation_count.get(r.role_id, 0)
                for r in self.get_participating_roles()
            },
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """生成阶段总结"""
        if not self.messages:
            return "无讨论内容"
        
        # 简单总结：提取关键观点
        key_points = []
        for msg in self.messages:
            if len(msg.content) > 20:  # 过滤短消息
                key_points.append(msg.content[:100] + "..." if len(msg.content) > 100 else msg.content)
        
        return "\n".join(key_points[:5])  # 最多5条


class WorkflowManager:
    """
    工作流管理器
    
    管理9个阶段的完整流程，包括：
    - 阶段切换
    - 状态持久化
    - 结果收集
    """
    
    def __init__(
        self,
        phase_manager: PhaseManager,
        roles: List[Role],
        discussion_engine: DiscussionEngine,
        on_phase_start: Optional[Callable[[str, str], None]] = None,
        on_phase_end: Optional[Callable[[str, PhaseResult], None]] = None,
        on_message: Optional[Callable[[DiscussionMessage], None]] = None
    ):
        self.phase_manager = phase_manager
        self.roles = roles
        self.discussion_engine = discussion_engine
        self.on_phase_start = on_phase_start
        self.on_phase_end = on_phase_end
        self.on_message = on_message
        
        self.results: Dict[str, PhaseResult] = {}
        self.current_executor: Optional[PhaseExecutor] = None
        self.is_running = False
        
    async def run_full_workflow(self, idea: str) -> Dict[str, PhaseResult]:
        """
        运行完整工作流
        
        Args:
            idea: 项目需求/想法
            
        Returns:
            所有阶段的结果
        """
        self.is_running = True
        self.results = {}
        
        logger.info(f"开始完整工作流，项目需求: {idea[:100]}...")
        
        # 开始第一个阶段
        await self._start_phase("P1", idea)
        
        # 依次执行所有阶段
        while self.is_running and self.phase_manager.current_phase:
            phase = self.phase_manager.current_phase
            
            # 执行当前阶段
            result = await self._execute_current_phase()
            self.results[phase.phase_id] = result
            
            # 检查是否应该继续
            if not self.is_running:
                break
            
            # 进入下一阶段
            if not self.phase_manager.is_last_phase():
                next_phase = self.phase_manager.next_phase()
                if next_phase:
                    # 构建上下文
                    context = self._build_phase_context(result)
                    await self._start_phase(next_phase.phase_id, context)
                else:
                    break
            else:
                logger.info("所有阶段已完成")
                break
        
        self.is_running = False
        return self.results
    
    async def run_single_phase(self, phase_id: str, context: str = "") -> PhaseResult:
        """
        运行单个阶段
        
        Args:
            phase_id: 阶段ID
            context: 上下文
            
        Returns:
            阶段执行结果
        """
        phase = self.phase_manager.get_phase(phase_id)
        if not phase:
            raise ValueError(f"未知阶段: {phase_id}")
        
        await self._start_phase(phase_id, context)
        return await self._execute_current_phase()
    
    async def _start_phase(self, phase_id: str, context: str):
        """开始阶段"""
        phase = self.phase_manager.get_phase(phase_id)
        if not phase:
            return
        
        logger.info(f"开始阶段: {phase.name}")
        
        # 通知回调
        if self.on_phase_start:
            try:
                if asyncio.iscoroutinefunction(self.on_phase_start):
                    await self.on_phase_start(phase_id, phase.name)
                else:
                    self.on_phase_start(phase_id, phase.name)
            except Exception as e:
                logger.error(f"阶段开始回调执行失败: {e}")
    
    async def _execute_current_phase(self) -> PhaseResult:
        """执行当前阶段"""
        phase = self.phase_manager.current_phase
        if not phase:
            raise RuntimeError("没有当前阶段")
        
        # 创建执行器
        executor = PhaseExecutor(
            phase=phase,
            roles=self.roles,
            discussion_engine=self.discussion_engine,
            on_message=self.on_message
        )
        self.current_executor = executor
        
        # 执行阶段
        result = await executor.execute()
        
        # 通知回调
        if self.on_phase_end:
            try:
                if asyncio.iscoroutinefunction(self.on_phase_end):
                    await self.on_phase_end(phase.phase_id, result)
                else:
                    self.on_phase_end(phase.phase_id, result)
            except Exception as e:
                logger.error(f"阶段结束回调执行失败: {e}")
        
        return result
    
    def _build_phase_context(self, result: PhaseResult) -> str:
        """构建阶段上下文"""
        context = f"【{result.phase_name}】阶段已完成\n"
        context += f"状态: {result.status.value}\n"
        context += f"轮次: {result.rounds}\n"
        
        if result.output and "summary" in result.output:
            context += f"\n总结:\n{result.output['summary']}\n"
        
        return context
    
    def skip_to_phase(self, phase_id: str) -> bool:
        """跳转到指定阶段"""
        try:
            self.phase_manager.jump_to_phase(phase_id)
            return True
        except Exception as e:
            logger.error(f"跳转到阶段 {phase_id} 失败: {e}")
            return False
    
    def stop(self):
        """停止工作流"""
        self.is_running = False
        logger.info("工作流已停止")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
        phase_progress = self.phase_manager.get_phase_progress()
        
        return {
            "total_phases": phase_progress["total_phases"],
            "current_phase": phase_progress["current_phase"],
            "completed_phases": phase_progress["completed_phases"],
            "progress_percentage": phase_progress["progress_percentage"],
            "current_phase_name": phase_progress["current_phase_name"],
            "completed_results": {
                k: v.to_dict() for k, v in self.results.items()
            }
        }
    
    def export_results(self) -> Dict[str, Any]:
        """导出所有结果"""
        return {
            "export_time": datetime.now().isoformat(),
            "phases": {
                k: v.to_dict() for k, v in self.results.items()
            },
            "progress": self.get_progress()
        }
    
    def save_results(self, filepath: str):
        """保存结果到文件"""
        data = self.export_results()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"结果已保存到: {filepath}")
