"""讨论引擎模块"""
from .engine import DiscussionEngine, DiscussionConfig
from .consensus import ConsensusDetector
from .state import DiscussionState
from .message import DiscussionMessage

__all__ = ['DiscussionEngine', 'DiscussionConfig', 'ConsensusDetector', 'DiscussionState', 'DiscussionMessage']
