"""
MetaGPT群聊讨论系统 - 消息模块
=============================
定义消息相关的类和消息池
"""

from typing import List, Set, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class MessageType(Enum):
    """消息类型"""
    DISCUSSION = "discussion"    # 讨论消息
    SYSTEM = "system"            # 系统消息
    NOTIFICATION = "notification"  # 通知消息
    COMMAND = "command"          # 命令消息
    DECISION = "decision"        # 决策消息


@dataclass
class Message:
    """
    基础消息类
    
    Attributes:
        content: 消息内容
        sender: 发送者角色ID
        msg_type: 消息类型
        timestamp: 发送时间
        metadata: 附加元数据
    """
    content: str
    sender: str
    msg_type: MessageType = MessageType.DISCUSSION
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "sender": self.sender,
            "msg_type": self.msg_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class DiscussionMessage(Message):
    """
    讨论消息类
    
    Attributes:
        phase: 当前阶段ID
        round_num: 当前轮数
        action: 角色动作
        mentions: @的角色列表
        reply_to: 回复的消息ID
    """
    phase: str = ""
    round_num: int = 0
    action: str = "speak"  # speak/pass/agree/disagree
    mentions: List[str] = field(default_factory=list)
    reply_to: Optional[str] = None
    
    def __post_init__(self):
        self.msg_type = MessageType.DISCUSSION
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base.update({
            "phase": self.phase,
            "round_num": self.round_num,
            "action": self.action,
            "mentions": self.mentions,
            "reply_to": self.reply_to
        })
        return base


@dataclass
class SystemMessage(Message):
    """系统消息"""
    event_type: str = ""  # phase_start, phase_end, consensus_reached, etc.
    
    def __post_init__(self):
        self.msg_type = MessageType.SYSTEM


@dataclass
class DecisionMessage(Message):
    """决策消息"""
    decision_type: str = ""  # consensus, boss_decision, timeout
    decision_result: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.msg_type = MessageType.DECISION


class MessagePool:
    """
    消息池类
    
    管理所有消息的存储、检索和订阅
    """
    
    def __init__(self):
        self._messages: List[Message] = []
        self._subscribers: Dict[str, List[Callable]] = {}
        self._phase_messages: Dict[str, List[Message]] = {}
    
    def publish(self, message: Message) -> None:
        """
        发布消息到消息池
        
        Args:
            message: 要发布的消息
        """
        self._messages.append(message)
        
        # 按阶段分类存储
        if isinstance(message, DiscussionMessage):
            phase = message.phase
            if phase not in self._phase_messages:
                self._phase_messages[phase] = []
            self._phase_messages[phase].append(message)
        
        # 通知订阅者
        self._notify_subscribers(message)
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        订阅特定类型的事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def _notify_subscribers(self, message: Message) -> None:
        """通知订阅者"""
        event_type = message.msg_type.value
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error notifying subscriber: {e}")
    
    def get_all_messages(self) -> List[Message]:
        """获取所有消息"""
        return self._messages.copy()
    
    def get_messages_by_phase(self, phase: str) -> List[Message]:
        """获取指定阶段的消息"""
        return self._phase_messages.get(phase, []).copy()
    
    def get_messages_by_sender(self, sender: str) -> List[Message]:
        """获取指定发送者的消息"""
        return [m for m in self._messages if m.sender == sender]
    
    def get_messages_by_round(self, phase: str, round_num: int) -> List[Message]:
        """获取指定轮次的消息"""
        return [
            m for m in self._messages 
            if isinstance(m, DiscussionMessage) 
            and m.phase == phase 
            and m.round_num == round_num
        ]
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """获取最近N条消息"""
        return self._messages[-count:] if self._messages else []
    
    def get_context_for_role(self, role_id: str, phase: str, 
                              round_num: int, max_history: int = 5) -> str:
        """
        获取角色的上下文信息
        
        Args:
            role_id: 角色ID
            phase: 当前阶段
            round_num: 当前轮数
            max_history: 最大历史消息数
            
        Returns:
            格式化的上下文字符串
        """
        # 获取当前阶段的历史消息
        phase_msgs = self.get_messages_by_phase(phase)
        
        # 过滤当前轮次之前的消息
        context_msgs = [
            m for m in phase_msgs 
            if isinstance(m, DiscussionMessage) 
            and m.round_num <= round_num
        ][-max_history:]
        
        # 格式化上下文
        context_parts = []
        for msg in context_msgs:
            context_parts.append(f"[{msg.sender}]: {msg.content}")
        
        return "\n".join(context_parts)
    
    def clear(self) -> None:
        """清空消息池"""
        self._messages.clear()
        self._phase_messages.clear()
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "messages": [m.to_dict() for m in self._messages],
            "total_count": len(self._messages)
        }
