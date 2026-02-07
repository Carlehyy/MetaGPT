"""
提醒服务模块 - 处理@老板提醒功能
"""
import asyncio
import re
from typing import Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .storage import storage, Message, PhaseType
from .websocket import manager, WebSocketMessage

logger = logging.getLogger(__name__)


@dataclass
class ReminderConfig:
    """提醒配置"""
    first_reminder_delay: int = 30       # 首次提醒延迟（秒）
    reminder_interval: int = 60          # 提醒间隔（秒）
    max_reminder_count: int = 3          # 最大提醒次数
    boss_keywords: list = None           # 触发提醒的关键词
    
    def __post_init__(self):
        if self.boss_keywords is None:
            self.boss_keywords = [
                "@老板", "@boss", "@Boss", "@BOSS",
                "老板，", "老板:", "老板：",
                "请问老板", "需要老板", "请老板"
            ]


class ReminderService:
    """提醒服务"""
    
    def __init__(self, config: ReminderConfig = None):
        self.config = config or ReminderConfig()
        self._running = False
        self._reminder_tasks: dict = {}  # message_id -> task
        self._check_task: Optional[asyncio.Task] = None
        self._mention_handlers: list = []
    
    def start(self):
        """启动提醒服务"""
        if not self._running:
            self._running = True
            self._check_task = asyncio.create_task(self._check_loop())
            logger.info("提醒服务已启动")
    
    def stop(self):
        """停止提醒服务"""
        self._running = False
        
        # 取消所有提醒任务
        for task in self._reminder_tasks.values():
            task.cancel()
        self._reminder_tasks.clear()
        
        # 取消检查循环
        if self._check_task:
            self._check_task.cancel()
        
        logger.info("提醒服务已停止")
    
    def register_mention_handler(self, handler: Callable):
        """注册@老板处理器"""
        self._mention_handlers.append(handler)
    
    def is_mention_boss(self, content: str) -> bool:
        """
        检查消息是否@老板
        
        Args:
            content: 消息内容
            
        Returns:
            是否包含@老板关键词
        """
        if not content:
            return False
        
        for keyword in self.config.boss_keywords:
            if keyword in content:
                return True
        
        # 正则匹配 @老板 的各种变体
        patterns = [
            r'@\s*老板',
            r'@\s*boss',
            r'\b老板\b.*\?',
            r'\b老板\b.*请',
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    async def handle_new_message(self, message: Message):
        """
        处理新消息，检查是否需要提醒
        
        Args:
            message: 新消息
        """
        # 检查是否是老板消息
        if message.role == "Boss":
            # 老板回复了，取消所有相关提醒
            self._cancel_reminders_for_boss_reply()
            return
        
        # 检查是否@老板
        if self.is_mention_boss(message.content):
            logger.info(f"检测到@老板消息: {message.id}")
            
            # 标记消息
            message.is_mention_boss = True
            
            # 调用处理器
            for handler in self._mention_handlers:
                await handler(message)
            
            # 启动提醒任务
            await self._start_reminder_task(message)
    
    async def _start_reminder_task(self, message: Message):
        """
        启动提醒任务
        
        Args:
            message: 触发提醒的消息
        """
        message_id = message.id
        
        # 如果已有任务，先取消
        if message_id in self._reminder_tasks:
            self._reminder_tasks[message_id].cancel()
        
        # 创建新任务
        task = asyncio.create_task(
            self._reminder_loop(message),
            name=f"reminder_{message_id}"
        )
        self._reminder_tasks[message_id] = task
    
    async def _reminder_loop(self, message: Message):
        """
        提醒循环
        
        Args:
            message: 触发提醒的消息
        """
        message_id = message.id
        reminder_count = 0
        
        # 等待首次提醒延迟
        await asyncio.sleep(self.config.first_reminder_delay)
        
        while self._running and reminder_count < self.config.max_reminder_count:
            # 检查老板是否已经回复
            if self._is_boss_replied_after(message.timestamp):
                logger.info(f"老板已回复，取消提醒任务: {message_id}")
                break
            
            # 检查是否还有老板连接
            if not manager.has_boss_connection:
                logger.info(f"老板未连接，跳过提醒: {message_id}")
                await asyncio.sleep(self.config.reminder_interval)
                continue
            
            # 发送提醒
            reminder_count += 1
            await self._send_reminder(message, reminder_count)
            
            # 等待下次提醒
            if reminder_count < self.config.max_reminder_count:
                await asyncio.sleep(self.config.reminder_interval)
        
        # 清理任务
        if message_id in self._reminder_tasks:
            del self._reminder_tasks[message_id]
    
    async def _send_reminder(self, message: Message, reminder_count: int):
        """
        发送提醒
        
        Args:
            message: 原始消息
            reminder_count: 当前提醒次数
        """
        role = message.role
        content_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
        
        reminder_text = f"【提醒-{reminder_count}/{self.config.max_reminder_count}】"
        
        if reminder_count == 1:
            reminder_message = f"{reminder_text} {role} 正在等待您的回复: \"{content_preview}\""
        elif reminder_count == self.config.max_reminder_count:
            reminder_message = f"{reminder_text} {role} 仍在等待您的回复（最后提醒）: \"{content_preview}\""
        else:
            reminder_message = f"{reminder_text} {role} 还在等待您的回复: \"{content_preview}\""
        
        logger.info(f"发送提醒: {reminder_message}")
        
        # 发送提醒给老板
        await manager.send_reminder_to_boss(
            reminder_message,
            message.to_dict()
        )
    
    def _is_boss_replied_after(self, timestamp: datetime) -> bool:
        """
        检查老板是否在指定时间后回复过
        
        Args:
            timestamp: 检查时间点
            
        Returns:
            是否已回复
        """
        last_boss_reply = storage.get_last_boss_reply()
        if not last_boss_reply:
            return False
        
        return last_boss_reply.timestamp > timestamp
    
    def _cancel_reminders_for_boss_reply(self):
        """老板回复后取消所有提醒任务"""
        for task in self._reminder_tasks.values():
            task.cancel()
        self._reminder_tasks.clear()
        logger.info("老板已回复，取消所有提醒任务")
    
    async def _check_loop(self):
        """检查循环 - 定期检查未回复的@老板消息"""
        while self._running:
            try:
                # 检查是否有未回复的@老板消息
                since = datetime.now() - timedelta(minutes=5)
                unanswered = storage.get_unanswered_mentions(since)
                
                for message in unanswered:
                    if message.id not in self._reminder_tasks:
                        await self._start_reminder_task(message)
                
                # 每分钟检查一次
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"提醒检查循环错误: {e}")
                await asyncio.sleep(60)
    
    def get_reminder_status(self) -> dict:
        """获取提醒服务状态"""
        return {
            "running": self._running,
            "active_reminders": len(self._reminder_tasks),
            "config": {
                "first_reminder_delay": self.config.first_reminder_delay,
                "reminder_interval": self.config.reminder_interval,
                "max_reminder_count": self.config.max_reminder_count
            }
        }
    
    async def send_immediate_reminder(self, message: str):
        """
        发送即时提醒
        
        Args:
            message: 提醒消息
        """
        if manager.has_boss_connection:
            await manager.send_reminder_to_boss(message)
            logger.info(f"发送即时提醒: {message}")
        else:
            logger.warning("老板未连接，无法发送即时提醒")


# 全局提醒服务实例
reminder_service = ReminderService()


async def check_and_remind(message: Message):
    """
    检查消息并触发提醒（便捷函数）
    
    Args:
        message: 新消息
    """
    await reminder_service.handle_new_message(message)
