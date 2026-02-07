"""
飞书机器人集成模块

提供飞书机器人的完整功能实现，包括：
- 消息接收（Webhook/WebSocket）
- 消息发送（文本、富文本卡片）
- @提醒功能
- 群聊管理
- 定时提醒机制
"""

from .bot import FeishuBot, FeishuConfig
from .message import MessageHandler, MessageType
from .card import CardBuilder, CardTemplate
from .group import GroupManager
from .reminder import ReminderManager, ReminderConfig

__version__ = "1.0.0"
__all__ = [
    "FeishuBot",
    "FeishuConfig",
    "MessageHandler",
    "MessageType",
    "CardBuilder",
    "CardTemplate",
    "GroupManager",
    "ReminderManager",
    "ReminderConfig",
]
