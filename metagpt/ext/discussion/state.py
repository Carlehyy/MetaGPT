"""
讨论状态管理模块

管理讨论的各种状态：进行中、已达成一致、需要老板决策、轮次耗尽
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


class DiscussionState(Enum):
    """
    讨论状态枚举
    
    定义讨论可能处于的所有状态
    """
    PENDING = auto()           # 等待开始
    ONGOING = auto()           # 进行中
    CONSENSUS_REACHED = auto() # 已达成一致
    BOSS_NEEDED = auto()       # 需要老板决策
    ROUNDS_EXHAUSTED = auto()  # 轮次耗尽
    PAUSED = auto()            # 暂停
    TERMINATED = auto()        # 已终止
    
    def __str__(self) -> str:
        """返回状态的中文描述"""
        descriptions = {
            DiscussionState.PENDING: "等待开始",
            DiscussionState.ONGOING: "进行中",
            DiscussionState.CONSENSUS_REACHED: "已达成一致",
            DiscussionState.BOSS_NEEDED: "需要老板决策",
            DiscussionState.ROUNDS_EXHAUSTED: "轮次耗尽",
            DiscussionState.PAUSED: "暂停",
            DiscussionState.TERMINATED: "已终止"
        }
        return descriptions.get(self, "未知状态")
    
    def is_active(self) -> bool:
        """检查状态是否是活跃状态（可以继续讨论）"""
        return self in [DiscussionState.PENDING, DiscussionState.ONGOING, DiscussionState.PAUSED]
    
    def is_terminal(self) -> bool:
        """检查状态是否是终止状态"""
        return self in [
            DiscussionState.CONSENSUS_REACHED,
            DiscussionState.BOSS_NEEDED,
            DiscussionState.ROUNDS_EXHAUSTED,
            DiscussionState.TERMINATED
        ]


class DiscussionPhase(Enum):
    """
    讨论阶段枚举
    
    定义讨论可能处于的各个阶段
    """
    INITIAL = auto()           # 初始阶段
    INFORMATION_GATHERING = auto()  # 信息收集
    BRAINSTORMING = auto()     # 头脑风暴
    EVALUATION = auto()        # 方案评估
    DECISION_MAKING = auto()   # 决策阶段
    CONSENSUS_BUILDING = auto()  # 共识构建
    FINALIZATION = auto()      # 最终确认
    
    def __str__(self) -> str:
        """返回阶段的中文描述"""
        descriptions = {
            DiscussionPhase.INITIAL: "初始阶段",
            DiscussionPhase.INFORMATION_GATHERING: "信息收集",
            DiscussionPhase.BRAINSTORMING: "头脑风暴",
            DiscussionPhase.EVALUATION: "方案评估",
            DiscussionPhase.DECISION_MAKING: "决策阶段",
            DiscussionPhase.CONSENSUS_BUILDING: "共识构建",
            DiscussionPhase.FINALIZATION: "最终确认"
        }
        return descriptions.get(self, "未知阶段")


@dataclass
class StateTransition:
    """状态转换记录"""
    from_state: DiscussionState
    to_state: DiscussionState
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    triggered_by: Optional[str] = None  # 触发转换的角色/系统


class StateManager:
    """
    讨论状态管理器
    
    负责管理讨论的状态流转和状态历史
    """
    
    # 定义允许的状态转换
    ALLOWED_TRANSITIONS = {
        DiscussionState.PENDING: [DiscussionState.ONGOING, DiscussionState.TERMINATED],
        DiscussionState.ONGOING: [
            DiscussionState.CONSENSUS_REACHED,
            DiscussionState.BOSS_NEEDED,
            DiscussionState.ROUNDS_EXHAUSTED,
            DiscussionState.PAUSED,
            DiscussionState.TERMINATED
        ],
        DiscussionState.PAUSED: [DiscussionState.ONGOING, DiscussionState.TERMINATED],
        DiscussionState.CONSENSUS_REACHED: [],  # 终止状态
        DiscussionState.BOSS_NEEDED: [],        # 终止状态
        DiscussionState.ROUNDS_EXHAUSTED: [],   # 终止状态
        DiscussionState.TERMINATED: []          # 终止状态
    }
    
    def __init__(self, initial_state: DiscussionState = DiscussionState.PENDING):
        self._current_state = initial_state
        self._transitions: List[StateTransition] = []
        self._state_start_time: datetime = datetime.now()
        self._metadata: Dict[str, Any] = {}
    
    @property
    def current_state(self) -> DiscussionState:
        """获取当前状态"""
        return self._current_state
    
    @property
    def state_start_time(self) -> datetime:
        """获取当前状态开始时间"""
        return self._state_start_time
    
    def can_transition_to(self, new_state: DiscussionState) -> bool:
        """检查是否可以转换到指定状态"""
        allowed = self.ALLOWED_TRANSITIONS.get(self._current_state, [])
        return new_state in allowed
    
    def transition_to(
        self, 
        new_state: DiscussionState, 
        reason: str = "",
        triggered_by: Optional[str] = None
    ) -> bool:
        """
        转换到指定状态
        
        Args:
            new_state: 目标状态
            reason: 转换原因
            triggered_by: 触发者
            
        Returns:
            是否成功转换
        """
        if not self.can_transition_to(new_state):
            return False
        
        # 记录转换
        transition = StateTransition(
            from_state=self._current_state,
            to_state=new_state,
            reason=reason,
            triggered_by=triggered_by
        )
        self._transitions.append(transition)
        
        # 更新状态
        self._current_state = new_state
        self._state_start_time = datetime.now()
        
        return True
    
    def get_state_duration(self) -> float:
        """获取当前状态持续时间（秒）"""
        return (datetime.now() - self._state_start_time).total_seconds()
    
    def get_transitions(self) -> List[StateTransition]:
        """获取所有状态转换记录"""
        return self._transitions.copy()
    
    def is_active(self) -> bool:
        """检查讨论是否处于活跃状态"""
        return self._current_state.is_active()
    
    def is_terminal(self) -> bool:
        """检查讨论是否已终止"""
        return self._current_state.is_terminal()
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置状态元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取状态元数据"""
        return self._metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'current_state': self._current_state.name,
            'current_state_desc': str(self._current_state),
            'state_start_time': self._state_start_time.isoformat(),
            'state_duration_seconds': self.get_state_duration(),
            'is_active': self.is_active(),
            'is_terminal': self.is_terminal(),
            'transitions': [
                {
                    'from': t.from_state.name,
                    'to': t.to_state.name,
                    'timestamp': t.timestamp.isoformat(),
                    'reason': t.reason,
                    'triggered_by': t.triggered_by
                }
                for t in self._transitions
            ],
            'metadata': self._metadata
        }


class RoundManager:
    """
    轮次管理器
    
    负责管理讨论的轮次限制和轮次统计
    """
    
    def __init__(self, max_rounds: int = 20):
        self.max_rounds = max(1, max_rounds)
        self._current_round = 0
        self._round_start_times: Dict[int, datetime] = {}
        self._round_end_times: Dict[int, datetime] = {}
        self._round_participants: Dict[int, List[str]] = {}
    
    @property
    def current_round(self) -> int:
        """获取当前轮次"""
        return self._current_round
    
    def start_round(self) -> int:
        """开始新一轮，返回轮次号"""
        self._current_round += 1
        self._round_start_times[self._current_round] = datetime.now()
        self._round_participants[self._current_round] = []
        return self._current_round
    
    def end_round(self) -> None:
        """结束当前轮次"""
        if self._current_round > 0:
            self._round_end_times[self._current_round] = datetime.now()
    
    def record_participant(self, participant_id: str, round_number: Optional[int] = None) -> None:
        """记录参与者发言"""
        round_num = round_number or self._current_round
        if round_num not in self._round_participants:
            self._round_participants[round_num] = []
        if participant_id not in self._round_participants[round_num]:
            self._round_participants[round_num].append(participant_id)
    
    def get_round_participants(self, round_number: Optional[int] = None) -> List[str]:
        """获取指定轮次的参与者"""
        round_num = round_number or self._current_round
        return self._round_participants.get(round_num, []).copy()
    
    def get_round_duration(self, round_number: Optional[int] = None) -> float:
        """获取指定轮次的持续时间（秒）"""
        round_num = round_number or self._current_round
        start = self._round_start_times.get(round_num)
        end = self._round_end_times.get(round_num)
        
        if start and end:
            return (end - start).total_seconds()
        elif start:
            return (datetime.now() - start).total_seconds()
        return 0.0
    
    def is_rounds_exhausted(self) -> bool:
        """检查轮次是否已耗尽"""
        return self._current_round >= self.max_rounds
    
    def get_remaining_rounds(self) -> int:
        """获取剩余轮次"""
        return max(0, self.max_rounds - self._current_round)
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        return (self._current_round / self.max_rounds) * 100 if self.max_rounds > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'max_rounds': self.max_rounds,
            'current_round': self._current_round,
            'remaining_rounds': self.get_remaining_rounds(),
            'is_exhausted': self.is_rounds_exhausted(),
            'progress_percentage': self.get_progress_percentage(),
            'round_history': [
                {
                    'round': r,
                    'participants': self._round_participants.get(r, []),
                    'duration_seconds': self.get_round_duration(r)
                }
                for r in range(1, self._current_round + 1)
            ]
        }
