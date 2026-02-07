"""
讨论消息定义模块

定义讨论过程中使用的消息类型和数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Dict, Any, List
import uuid


class MessageType(Enum):
    """消息类型枚举"""
    SPEECH = auto()           # 普通发言
    PROPOSAL = auto()         # 提案/建议
    AGREEMENT = auto()        # 同意
    DISAGREEMENT = auto()     # 反对
    QUESTION = auto()         # 提问
    CLARIFICATION = auto()    # 澄清说明
    SUMMARY = auto()          # 总结
    BOSS_INTERVENTION = auto()  # 老板介入
    SYSTEM = auto()           # 系统消息


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """
    讨论消息类
    
    用于存储和管理讨论过程中的所有消息
    """
    content: str                          # 消息内容
    sender_id: str                        # 发送者ID
    sender_name: str                      # 发送者名称
    message_type: MessageType = MessageType.SPEECH
    priority: MessagePriority = MessagePriority.NORMAL
    
    # 自动生成的字段
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0                 # 所属轮次
    
    # 可选字段
    reply_to: Optional[str] = None        # 回复的消息ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后的处理"""
        if not self.sender_id:
            raise ValueError("发送者ID不能为空")
    
    @classmethod
    def create_request(
        cls,
        sender_id: str,
        sender_name: str,
        round_number: int = 0,
        message_type: MessageType = MessageType.SPEECH
    ) -> 'Message':
        """
        创建一个消息请求对象（内容为空，待填充）
        
        Args:
            sender_id: 发送者ID
            sender_name: 发送者名称
            round_number: 轮次号
            message_type: 消息类型
            
        Returns:
            消息请求对象
        """
        return cls(
            content="",  # 空内容，需要后续填充
            sender_id=sender_id,
            sender_name=sender_name,
            round_number=round_number,
            message_type=message_type
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'message_type': self.message_type.name,
            'priority': self.priority.name,
            'timestamp': self.timestamp.isoformat(),
            'round_number': self.round_number,
            'reply_to': self.reply_to,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息对象"""
        return cls(
            content=data['content'],
            sender_id=data['sender_id'],
            sender_name=data['sender_name'],
            message_type=MessageType[data.get('message_type', 'SPEECH')],
            priority=MessagePriority[data.get('priority', 'NORMAL')],
            id=data.get('id', str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            round_number=data.get('round_number', 0),
            reply_to=data.get('reply_to'),
            metadata=data.get('metadata', {})
        )
    
    def is_boss_intervention(self) -> bool:
        """检查是否是老板介入消息"""
        return self.message_type == MessageType.BOSS_INTERVENTION
    
    def is_proposal(self) -> bool:
        """检查是否是提案消息"""
        return self.message_type == MessageType.PROPOSAL
    
    def is_agreement(self) -> bool:
        """检查是否是同意消息"""
        return self.message_type == MessageType.AGREEMENT
    
    def is_disagreement(self) -> bool:
        """检查是否是反对消息"""
        return self.message_type == MessageType.DISAGREEMENT
    
    def __str__(self) -> str:
        return f"[{self.round_number}] {self.sender_name}: {self.content[:50]}..."


@dataclass
class DiscussionSummary:
    """
    讨论总结类
    
    用于存储讨论结束后的总结信息
    """
    topic: str                            # 讨论主题
    conclusion: Optional[str] = None      # 最终结论
    key_points: List[str] = field(default_factory=list)
    agreements: List[str] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    total_rounds: int = 0
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'topic': self.topic,
            'conclusion': self.conclusion,
            'key_points': self.key_points,
            'agreements': self.agreements,
            'disagreements': self.disagreements,
            'participants': self.participants,
            'total_rounds': self.total_rounds,
            'duration_seconds': self.duration_seconds
        }


class MessageStore:
    """
    消息存储管理器
    
    用于高效存储和检索讨论消息
    """
    
    def __init__(self):
        self._messages: List[Message] = []
        self._by_round: Dict[int, List[Message]] = {}
        self._by_sender: Dict[str, List[Message]] = {}
        self._by_type: Dict[MessageType, List[Message]] = {}
    
    def add(self, message: Message) -> None:
        """添加消息"""
        self._messages.append(message)
        
        # 按轮次索引
        if message.round_number not in self._by_round:
            self._by_round[message.round_number] = []
        self._by_round[message.round_number].append(message)
        
        # 按发送者索引
        if message.sender_id not in self._by_sender:
            self._by_sender[message.sender_id] = []
        self._by_sender[message.sender_id].append(message)
        
        # 按类型索引
        if message.message_type not in self._by_type:
            self._by_type[message.message_type] = []
        self._by_type[message.message_type].append(message)
    
    def get_all(self) -> List[Message]:
        """获取所有消息"""
        return self._messages.copy()
    
    def get_by_round(self, round_number: int) -> List[Message]:
        """获取指定轮次的消息"""
        return self._by_round.get(round_number, []).copy()
    
    def get_by_sender(self, sender_id: str) -> List[Message]:
        """获取指定发送者的消息"""
        return self._by_sender.get(sender_id, []).copy()
    
    def get_by_type(self, message_type: MessageType) -> List[Message]:
        """获取指定类型的消息"""
        return self._by_type.get(message_type, []).copy()
    
    def get_recent(self, n: int = 5) -> List[Message]:
        """获取最近N条消息"""
        return self._messages[-n:] if n <= len(self._messages) else self._messages.copy()
    
    def get_last_message(self) -> Optional[Message]:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None
    
    def get_round_count(self) -> int:
        """获取已完成的轮次数"""
        return len(self._by_round)
    
    def get_message_count(self) -> int:
        """获取消息总数"""
        return len(self._messages)
    
    def get_participants(self) -> List[str]:
        """获取所有参与者ID"""
        return list(self._by_sender.keys())
    
    def has_spoken(self, sender_id: str) -> bool:
        """检查某参与者是否已发言"""
        return sender_id in self._by_sender and len(self._by_sender[sender_id]) > 0
    
    def clear(self) -> None:
        """清空所有消息"""
        self._messages.clear()
        self._by_round.clear()
        self._by_sender.clear()
        self._by_type.clear()
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [msg.to_dict() for msg in self._messages]
