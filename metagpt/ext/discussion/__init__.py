"""
群聊讨论引擎模块

提供完整的群聊讨论管理功能，包括：
- 轮流发言机制（狼人杀式轮询）
- 达成一致判断（共识检测算法）
- 轮次限制控制（每阶段最多20轮）
- 老板介入检测（任意消息触发）
- 讨论状态管理（进行中/已达成一致/需要老板决策/轮次耗尽）
- 讨论消息存储和展示

使用示例:
    from discussion import DiscussionEngine, Role, DiscussionConfig
    
    # 创建角色
    roles = [
        Role(id="role1", name="产品经理", description="负责产品规划"),
        Role(id="role2", name="技术负责人", description="负责技术方案"),
        Role(id="boss", name="老板", description="最终决策者", is_boss=True)
    ]
    
    # 创建引擎
    engine = DiscussionEngine(roles=roles)
    
    # 开始讨论
    await engine.start_discussion("产品功能优先级")
    
    # 进行讨论
    while engine.get_current_state() == DiscussionState.ONGOING:
        message = await engine.next_turn()
        if message:
            # 填充消息内容
            message.content = "我认为..."
            engine.submit_message(message)
    
    # 获取结果
    summary = engine.get_summary()
"""

# 消息相关
from .message import (
    Message,
    MessageType,
    MessagePriority,
    MessageStore,
    DiscussionSummary
)

# 状态相关
from .state import (
    DiscussionState,
    DiscussionPhase,
    StateManager,
    StateTransition,
    RoundManager
)

# 轮流发言相关
from .round_robin import (
    Role,
    TurnManager,
    TurnOrderStrategy,
    SpeakingQueue,
    RoundRobinIterator
)

# 共识检测相关
from .consensus import (
    ConsensusChecker,
    ConsensusStrategy,
    ConsensusResult,
    KeywordConsensusDetector,
    SimilarityConsensusDetector,
    VotingConsensusDetector,
    HybridConsensusDetector,
    StagnationDetector
)

# 引擎相关
from .engine import (
    DiscussionEngine,
    DiscussionConfig,
    AsyncDiscussionRunner
)

__version__ = "1.0.0"
__author__ = "Multi-Agent Team"

__all__ = [
    # 消息
    'Message',
    'MessageType',
    'MessagePriority',
    'MessageStore',
    'DiscussionSummary',
    
    # 状态
    'DiscussionState',
    'DiscussionPhase',
    'StateManager',
    'StateTransition',
    'RoundManager',
    
    # 轮流发言
    'Role',
    'TurnManager',
    'TurnOrderStrategy',
    'SpeakingQueue',
    'RoundRobinIterator',
    
    # 共识检测
    'ConsensusChecker',
    'ConsensusStrategy',
    'ConsensusResult',
    'KeywordConsensusDetector',
    'SimilarityConsensusDetector',
    'VotingConsensusDetector',
    'HybridConsensusDetector',
    'StagnationDetector',
    
    # 引擎
    'DiscussionEngine',
    'DiscussionConfig',
    'AsyncDiscussionRunner',
]
