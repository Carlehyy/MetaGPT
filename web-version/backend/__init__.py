"""
AI虚拟软件公司 - 后端模块

包含:
- storage: 消息存储管理
- websocket: WebSocket连接管理
- api: RESTful API路由
- reminder: 提醒服务
- main: FastAPI主应用
"""

from .storage import storage, Message, PhaseType, Phase, MessageStorage
from .websocket import manager, ConnectionManager, WebSocketMessage
from .reminder import reminder_service, ReminderService, ReminderConfig

__all__ = [
    'storage',
    'Message',
    'PhaseType',
    'Phase',
    'MessageStorage',
    'manager',
    'ConnectionManager',
    'WebSocketMessage',
    'reminder_service',
    'ReminderService',
    'ReminderConfig',
]

__version__ = '1.0.0'
