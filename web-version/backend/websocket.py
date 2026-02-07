"""
WebSocket管理模块 - 处理客户端连接和消息广播
"""
import json
import asyncio
from typing import List, Dict, Callable, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import logging

from .storage import storage, Message, PhaseType

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str  # message, typing, system, phase_change, boss_message, ping, pong
    data: Dict
    timestamp: str = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self._connections: List[WebSocket] = []
        self._boss_connection: Optional[WebSocket] = None  # 老板的特殊连接
        self._message_handlers: List[Callable] = []
        self._boss_message_handlers: List[Callable] = []
        self._typing_handlers: List[Callable] = []
    
    @property
    def connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._connections)
    
    @property
    def has_boss_connection(self) -> bool:
        """检查是否有老板连接"""
        return self._boss_connection is not None
    
    async def connect(self, websocket: WebSocket, is_boss: bool = False):
        """
        接受新的WebSocket连接
        
        Args:
            websocket: WebSocket连接
            is_boss: 是否是老板连接
        """
        await websocket.accept()
        self._connections.append(websocket)
        
        if is_boss:
            self._boss_connection = websocket
            logger.info("老板已连接")
        
        logger.info(f"新客户端连接，当前连接数: {self.connection_count}")
        
        # 发送欢迎消息
        await self.send_to_client(websocket, WebSocketMessage(
            type="system",
            data={
                "message": "连接成功",
                "is_boss": is_boss,
                "connection_id": id(websocket)
            }
        ))
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self._connections:
            self._connections.remove(websocket)
        
        if websocket == self._boss_connection:
            self._boss_connection = None
            logger.info("老板已断开连接")
        
        logger.info(f"客户端断开连接，当前连接数: {self.connection_count}")
    
    async def broadcast(self, message: WebSocketMessage):
        """广播消息给所有客户端"""
        disconnected = []
        for conn in self._connections:
            try:
                await conn.send_json(message.model_dump())
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(conn)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to_client(self, websocket: WebSocket, message: WebSocketMessage):
        """发送消息给指定客户端"""
        try:
            await websocket.send_json(message.model_dump())
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.disconnect(websocket)
    
    async def send_to_boss(self, message: WebSocketMessage):
        """发送消息给老板"""
        if self._boss_connection:
            await self.send_to_client(self._boss_connection, message)
    
    async def broadcast_message(self, role: str, content: str, phase: PhaseType, 
                               message_type: str = "text", metadata: Dict = None,
                               is_mention_boss: bool = False):
        """
        广播聊天消息
        
        Args:
            role: 发送者角色
            content: 消息内容
            phase: 当前阶段
            message_type: 消息类型
            metadata: 额外元数据
            is_mention_boss: 是否@老板
        """
        # 创建消息对象
        message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            role=role,
            content=content,
            phase=phase,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=metadata or {},
            is_mention_boss=is_mention_boss
        )
        
        # 存储消息
        storage.add_message(message)
        
        # 广播消息
        await self.broadcast(WebSocketMessage(
            type="message",
            data=message.to_dict()
        ))
        
        return message
    
    async def broadcast_typing(self, role: str, is_typing: bool = True):
        """广播正在输入状态"""
        await self.broadcast(WebSocketMessage(
            type="typing",
            data={
                "role": role,
                "is_typing": is_typing
            }
        ))
    
    async def broadcast_phase_change(self, phase: PhaseType, phase_info: Dict):
        """广播阶段变更"""
        await self.broadcast(WebSocketMessage(
            type="phase_change",
            data={
                "phase": phase.value,
                "phase_info": phase_info
            }
        ))
    
    async def send_system_message(self, message: str, data: Dict = None):
        """发送系统消息"""
        await self.broadcast(WebSocketMessage(
            type="system",
            data={
                "message": message,
                **(data or {})
            }
        ))
    
    def register_message_handler(self, handler: Callable):
        """注册消息处理器"""
        self._message_handlers.append(handler)
    
    def register_boss_message_handler(self, handler: Callable):
        """注册老板消息处理器"""
        self._boss_message_handlers.append(handler)
    
    def register_typing_handler(self, handler: Callable):
        """注册输入状态处理器"""
        self._typing_handlers.append(handler)
    
    async def handle_client_message(self, websocket: WebSocket, message_data: Dict):
        """
        处理客户端发来的消息
        
        Args:
            websocket: 发送者连接
            message_data: 消息数据
        """
        msg_type = message_data.get("type", "")
        
        if msg_type == "boss_message":
            # 处理老板消息
            await self._handle_boss_message(websocket, message_data)
        
        elif msg_type == "ping":
            # 心跳响应
            await self.send_to_client(websocket, WebSocketMessage(
                type="pong",
                data={"time": datetime.now().isoformat()}
            ))
        
        elif msg_type == "typing":
            # 输入状态
            for handler in self._typing_handlers:
                await handler(message_data)
        
        else:
            # 其他消息类型
            for handler in self._message_handlers:
                await handler(message_data)
    
    async def _handle_boss_message(self, websocket: WebSocket, message_data: Dict):
        """处理老板发送的消息"""
        content = message_data.get("data", {}).get("content", "")
        
        if not content:
            return
        
        # 创建消息
        message = Message(
            id=f"boss_{datetime.now().timestamp()}",
            role="Boss",
            content=content,
            phase=storage.get_current_phase().id,
            timestamp=datetime.now(),
            message_type="text",
            metadata={"source": "boss"}
        )
        
        # 存储消息
        storage.add_message(message)
        
        # 广播给所有客户端
        await self.broadcast(WebSocketMessage(
            type="boss_message",
            data=message.to_dict()
        ))
        
        # 调用注册的处理器
        for handler in self._boss_message_handlers:
            await handler(message)
    
    async def send_reminder_to_boss(self, reminder_message: str, original_message: Dict = None):
        """
        发送提醒给老板
        
        Args:
            reminder_message: 提醒消息内容
            original_message: 原始消息（可选）
        """
        await self.send_to_boss(WebSocketMessage(
            type="reminder",
            data={
                "message": reminder_message,
                "original_message": original_message,
                "timestamp": datetime.now().isoformat()
            }
        ))
        
        # 同时广播给所有客户端显示提醒状态
        await self.broadcast(WebSocketMessage(
            type="system",
            data={
                "message": "等待老板回复",
                "reminder_sent": True
            }
        ))


# 全局连接管理器实例
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, is_boss: bool = False):
    """
    WebSocket端点处理函数
    
    Args:
        websocket: WebSocket连接
        is_boss: 是否是老板连接
    """
    await manager.connect(websocket, is_boss)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 处理消息
            await manager.handle_client_message(websocket, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)
