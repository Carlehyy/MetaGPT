"""
消息存储模块 - 管理消息历史和阶段信息
"""
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json


class PhaseType(str, Enum):
    """阶段类型"""
    REQUIREMENT = "requirement"  # 需求分析
    DESIGN = "design"            # 系统设计
    CODING = "coding"            # 代码编写
    TESTING = "testing"          # 测试验证
    DEPLOYMENT = "deployment"    # 部署发布
    COMPLETED = "completed"      # 已完成


@dataclass
class Message:
    """消息数据类"""
    id: str
    role: str                    # 角色名称 (如: PM, Architect, Developer, Tester, Boss)
    content: str                 # 消息内容
    phase: PhaseType            # 所属阶段
    timestamp: datetime
    message_type: str = "text"   # 消息类型: text, code, image, file
    metadata: Dict = field(default_factory=dict)  # 额外元数据
    is_mention_boss: bool = False  # 是否@老板
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "phase": self.phase.value,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type,
            "metadata": self.metadata,
            "is_mention_boss": self.is_mention_boss
        }


@dataclass
class Phase:
    """阶段数据类"""
    id: PhaseType
    name: str
    description: str
    status: str = "pending"  # pending, active, completed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id.value,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class MessageStorage:
    """消息存储管理器"""
    
    def __init__(self):
        self._messages: List[Message] = []
        self._phases: Dict[PhaseType, Phase] = {}
        self._current_phase: PhaseType = PhaseType.REQUIREMENT
        self._initialize_phases()
    
    def _initialize_phases(self):
        """初始化阶段信息"""
        self._phases = {
            PhaseType.REQUIREMENT: Phase(
                id=PhaseType.REQUIREMENT,
                name="需求分析",
                description="分析用户需求，明确项目目标和功能范围"
            ),
            PhaseType.DESIGN: Phase(
                id=PhaseType.DESIGN,
                name="系统设计",
                description="设计系统架构、数据库结构和API接口"
            ),
            PhaseType.CODING: Phase(
                id=PhaseType.CODING,
                name="代码编写",
                description="根据设计文档编写代码实现"
            ),
            PhaseType.TESTING: Phase(
                id=PhaseType.TESTING,
                name="测试验证",
                description="进行单元测试、集成测试和系统测试"
            ),
            PhaseType.DEPLOYMENT: Phase(
                id=PhaseType.DEPLOYMENT,
                name="部署发布",
                description="部署应用到生产环境"
            ),
            PhaseType.COMPLETED: Phase(
                id=PhaseType.COMPLETED,
                name="已完成",
                description="项目开发完成"
            )
        }
    
    def add_message(self, message: Message) -> Message:
        """添加消息"""
        self._messages.append(message)
        return message
    
    def get_messages(
        self, 
        phase: Optional[PhaseType] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        获取消息列表
        
        Args:
            phase: 按阶段筛选
            role: 按角色筛选
            limit: 返回数量限制
            offset: 偏移量
        """
        messages = self._messages
        
        if phase:
            messages = [m for m in messages if m.phase == phase]
        
        if role:
            messages = [m for m in messages if m.role == role]
        
        # 按时间倒序排列，最新的在前面
        messages = sorted(messages, key=lambda m: m.timestamp, reverse=True)
        
        # 分页
        total = len(messages)
        messages = messages[offset:offset + limit]
        
        # 返回正序排列（旧的在前面）
        return list(reversed(messages))
    
    def get_message_count(
        self, 
        phase: Optional[PhaseType] = None,
        role: Optional[str] = None
    ) -> int:
        """获取消息数量"""
        messages = self._messages
        
        if phase:
            messages = [m for m in messages if m.phase == phase]
        
        if role:
            messages = [m for m in messages if m.role == role]
        
        return len(messages)
    
    def get_all_phases(self) -> List[Phase]:
        """获取所有阶段"""
        return list(self._phases.values())
    
    def get_current_phase(self) -> Phase:
        """获取当前阶段"""
        return self._phases[self._current_phase]
    
    def set_current_phase(self, phase: PhaseType) -> Phase:
        """设置当前阶段"""
        # 完成当前阶段
        if self._current_phase in self._phases:
            current = self._phases[self._current_phase]
            current.status = "completed"
            current.end_time = datetime.now()
        
        # 设置新阶段
        self._current_phase = phase
        new_phase = self._phases[phase]
        new_phase.status = "active"
        new_phase.start_time = datetime.now()
        
        return new_phase
    
    def get_phase(self, phase: PhaseType) -> Optional[Phase]:
        """获取指定阶段"""
        return self._phases.get(phase)
    
    def get_messages_by_phase(self, phase: PhaseType) -> List[Message]:
        """获取指定阶段的所有消息"""
        return [m for m in self._messages if m.phase == phase]
    
    def get_latest_messages(self, count: int = 10) -> List[Message]:
        """获取最新的N条消息"""
        return self._messages[-count:] if len(self._messages) >= count else self._messages
    
    def clear_messages(self):
        """清空所有消息"""
        self._messages = []
        self._initialize_phases()
        self._current_phase = PhaseType.REQUIREMENT
    
    def search_messages(self, keyword: str) -> List[Message]:
        """搜索消息内容"""
        return [m for m in self._messages if keyword.lower() in m.content.lower()]
    
    def get_boss_mentions(self) -> List[Message]:
        """获取所有@老板的消息"""
        return [m for m in self._messages if m.is_mention_boss]
    
    def get_last_boss_reply(self) -> Optional[Message]:
        """获取老板最后一条回复"""
        boss_messages = [m for m in self._messages if m.role == "Boss"]
        return boss_messages[-1] if boss_messages else None
    
    def get_unanswered_mentions(self, since: datetime) -> List[Message]:
        """
        获取自指定时间以来未回复的@老板消息
        
        Args:
            since: 起始时间
        """
        last_boss_reply = self.get_last_boss_reply()
        last_boss_time = last_boss_reply.timestamp if last_boss_reply else since
        
        mentions = self.get_boss_mentions()
        return [m for m in mentions if m.timestamp > last_boss_time]


# 全局存储实例
storage = MessageStorage()
