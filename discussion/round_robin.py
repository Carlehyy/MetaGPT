"""
轮流发言管理模块

实现狼人杀式轮询机制，管理角色的轮流发言顺序
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Iterator
from enum import Enum, auto
import random


class TurnOrderStrategy(Enum):
    """发言顺序策略"""
    FIXED = auto()           # 固定顺序
    RANDOM = auto()          # 随机顺序
    PRIORITY = auto()        # 优先级顺序
    ROUND_ROBIN = auto()     # 轮询（循环）
    REVERSE = auto()         # 反向顺序


@dataclass
class Role:
    """
    讨论角色类
    
    表示参与讨论的一个角色
    """
    id: str
    name: str
    description: str = ""
    priority: int = 0              # 发言优先级（数字越小优先级越高）
    can_skip: bool = False         # 是否可以跳过发言
    is_boss: bool = False          # 是否是老板
    
    # 发言统计
    speech_count: int = 0
    total_speech_length: int = 0
    
    def record_speech(self, content_length: int) -> None:
        """记录发言"""
        self.speech_count += 1
        self.total_speech_length += content_length
    
    def get_average_speech_length(self) -> float:
        """获取平均发言长度"""
        return self.total_speech_length / self.speech_count if self.speech_count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'can_skip': self.can_skip,
            'is_boss': self.is_boss,
            'speech_count': self.speech_count,
            'total_speech_length': self.total_speech_length,
            'average_speech_length': self.get_average_speech_length()
        }


class TurnManager:
    """
    轮流发言管理器
    
    管理讨论中的轮流发言机制，支持多种发言顺序策略
    """
    
    def __init__(
        self, 
        roles: List[Role], 
        strategy: TurnOrderStrategy = TurnOrderStrategy.ROUND_ROBIN
    ):
        self.roles = {role.id: role for role in roles}
        self.role_order = list(roles)
        self.strategy = strategy
        self._current_index = 0
        self._round_count = 0
        self._completed_roles: Set[str] = set()  # 当前轮次已完成发言的角色
        
        # 应用策略初始化顺序
        self._apply_strategy()
    
    def _apply_strategy(self) -> None:
        """应用发言顺序策略"""
        if self.strategy == TurnOrderStrategy.FIXED:
            # 保持原有顺序
            pass
        elif self.strategy == TurnOrderStrategy.RANDOM:
            # 随机顺序
            random.shuffle(self.role_order)
        elif self.strategy == TurnOrderStrategy.PRIORITY:
            # 按优先级排序（数字小的先发言）
            self.role_order.sort(key=lambda r: r.priority)
        elif self.strategy == TurnOrderStrategy.REVERSE:
            # 反向顺序
            self.role_order.reverse()
        # ROUND_ROBIN 保持原有顺序
    
    def get_next_speaker(self) -> Optional[Role]:
        """
        获取下一个发言角色
        
        Returns:
            下一个发言的角色，如果当前轮次所有角色都已发言则返回None
        """
        # 查找下一个未发言的角色
        start_index = self._current_index
        checked = 0
        
        while checked < len(self.role_order):
            role = self.role_order[self._current_index]
            
            # 如果角色可以跳过且本轮未发言过，则跳过
            if role.can_skip and role.id not in self._completed_roles:
                self._completed_roles.add(role.id)
            
            # 如果角色本轮未发言，则返回该角色
            if role.id not in self._completed_roles:
                return role
            
            # 移动到下一个角色
            self._current_index = (self._current_index + 1) % len(self.role_order)
            checked += 1
            
            # 如果回到起点，说明本轮结束
            if self._current_index == start_index:
                break
        
        return None
    
    def mark_spoken(self, role_id: str) -> None:
        """
        标记角色已发言
        
        Args:
            role_id: 角色ID
        """
        if role_id in self.roles:
            self._completed_roles.add(role_id)
            self.roles[role_id].record_speech(0)  # 长度在外部更新
            self._current_index = (self._current_index + 1) % len(self.role_order)
    
    def start_new_round(self) -> int:
        """
        开始新一轮发言
        
        Returns:
            新轮次号
        """
        self._round_count += 1
        self._completed_roles.clear()
        self._current_index = 0
        return self._round_count
    
    def is_round_complete(self) -> bool:
        """检查当前轮次是否完成"""
        return len(self._completed_roles) >= len(self.role_order)
    
    def get_remaining_roles(self) -> List[Role]:
        """获取当前轮次尚未发言的角色"""
        return [role for role in self.role_order if role.id not in self._completed_roles]
    
    def get_current_speaker(self) -> Optional[Role]:
        """获取当前应该发言的角色"""
        if self._current_index < len(self.role_order):
            role = self.role_order[self._current_index]
            if role.id not in self._completed_roles:
                return role
        return None
    
    def get_speaking_order(self) -> List[str]:
        """获取完整的发言顺序（角色ID列表）"""
        return [role.id for role in self.role_order]
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """获取指定角色"""
        return self.roles.get(role_id)
    
    def get_all_roles(self) -> List[Role]:
        """获取所有角色"""
        return list(self.role_order)
    
    def get_boss_role(self) -> Optional[Role]:
        """获取老板角色"""
        for role in self.role_order:
            if role.is_boss:
                return role
        return None
    
    def has_boss(self) -> bool:
        """检查是否有老板角色"""
        return any(role.is_boss for role in self.role_order)
    
    def get_round_progress(self) -> Dict[str, Any]:
        """获取当前轮次进度"""
        total = len(self.role_order)
        completed = len(self._completed_roles)
        return {
            'round': self._round_count,
            'total_roles': total,
            'completed': completed,
            'remaining': total - completed,
            'progress_percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'strategy': self.strategy.name,
            'current_round': self._round_count,
            'current_index': self._current_index,
            'role_order': [role.id for role in self.role_order],
            'completed_roles': list(self._completed_roles),
            'round_progress': self.get_round_progress(),
            'roles': {role_id: role.to_dict() for role_id, role in self.roles.items()}
        }


class SpeakingQueue:
    """
    发言队列
    
    管理发言请求的队列，支持插队等高级功能
    """
    
    def __init__(self):
        self._queue: List[str] = []  # 角色ID队列
        self._urgent_queue: List[str] = []  # 紧急队列（插队）
        self._speaking_history: List[str] = []  # 发言历史
    
    def enqueue(self, role_id: str, urgent: bool = False) -> None:
        """
        将角色加入队列
        
        Args:
            role_id: 角色ID
            urgent: 是否紧急（插队）
        """
        if urgent:
            if role_id not in self._urgent_queue:
                self._urgent_queue.append(role_id)
        else:
            if role_id not in self._queue:
                self._queue.append(role_id)
    
    def dequeue(self) -> Optional[str]:
        """
        从队列中取出一个角色
        
        Returns:
            角色ID，如果队列为空则返回None
        """
        # 优先处理紧急队列
        if self._urgent_queue:
            return self._urgent_queue.pop(0)
        
        if self._queue:
            role_id = self._queue.pop(0)
            self._speaking_history.append(role_id)
            return role_id
        
        return None
    
    def peek(self) -> Optional[str]:
        """查看队列中的下一个角色（不移除）"""
        if self._urgent_queue:
            return self._urgent_queue[0]
        if self._queue:
            return self._queue[0]
        return None
    
    def remove(self, role_id: str) -> bool:
        """从队列中移除指定角色"""
        if role_id in self._urgent_queue:
            self._urgent_queue.remove(role_id)
            return True
        if role_id in self._queue:
            self._queue.remove(role_id)
            return True
        return False
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self._queue) == 0 and len(self._urgent_queue) == 0
    
    def size(self) -> int:
        """获取队列大小"""
        return len(self._queue) + len(self._urgent_queue)
    
    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()
        self._urgent_queue.clear()
    
    def get_history(self) -> List[str]:
        """获取发言历史"""
        return self._speaking_history.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'normal_queue': self._queue.copy(),
            'urgent_queue': self._urgent_queue.copy(),
            'history': self._speaking_history.copy(),
            'total_size': self.size()
        }


class RoundRobinIterator:
    """
    轮询迭代器
    
    用于循环遍历角色列表
    """
    
    def __init__(self, roles: List[Role], start_index: int = 0):
        self.roles = roles
        self.index = start_index % len(roles) if roles else 0
    
    def __iter__(self) -> Iterator[Role]:
        return self
    
    def __next__(self) -> Role:
        if not self.roles:
            raise StopIteration
        
        role = self.roles[self.index]
        self.index = (self.index + 1) % len(self.roles)
        return role
    
    def peek(self) -> Optional[Role]:
        """查看当前位置的角色（不移除）"""
        if not self.roles:
            return None
        return self.roles[self.index]
    
    def reset(self) -> None:
        """重置迭代器"""
        self.index = 0
    
    def skip(self, n: int = 1) -> None:
        """跳过n个角色"""
        if self.roles:
            self.index = (self.index + n) % len(self.roles)
