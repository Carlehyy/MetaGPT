"""
讨论引擎模块 - 管理角色间的讨论流程

包含：
- DiscussionEngine: 讨论引擎
- DiscussionStatus: 讨论状态枚举
- DiscussionResult: 讨论结果
- WebSocketBroadcaster: WebSocket广播器
"""

from .engine import (
    DiscussionEngine,
    DiscussionStatus,
    DiscussionResult,
    SpeakingTurn,
    WebSocketBroadcaster,
    run_phase_discussion
)

__all__ = [
    "DiscussionEngine",
    "DiscussionStatus",
    "DiscussionResult",
    "SpeakingTurn",
    "WebSocketBroadcaster",
    "run_phase_discussion",
]
