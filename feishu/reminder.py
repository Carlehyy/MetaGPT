"""
提醒机制模块
实现定时提醒、重复提醒、@提醒等功能
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor


class ReminderType(Enum):
    """提醒类型"""
    ONCE = "once"           # 一次性提醒
    INTERVAL = "interval"   # 间隔提醒
    CRON = "cron"          # Cron表达式提醒
    REPEAT = "repeat"      # 重复提醒


class ReminderPriority(Enum):
    """提醒优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ReminderConfig:
    """提醒配置"""
    # 基本配置
    interval_minutes: int = 5  # 默认间隔5分钟
    max_reminders: int = 3     # 最大提醒次数
    
    # @提醒配置
    at_boss: bool = True       # 是否@老板
    at_all: bool = False       # 是否@所有人
    boss_ids: List[str] = field(default_factory=list)  # 老板ID列表
    
    # 消息配置
    message_template: str = "⏰ 提醒: {content}"  # 消息模板
    include_timestamp: bool = True  # 是否包含时间戳
    
    # 行为配置
    auto_stop_on_response: bool = True  # 收到回复后自动停止
    escalate_on_no_response: bool = True  # 无响应时升级


@dataclass
class ReminderTask:
    """提醒任务"""
    task_id: str
    reminder_type: ReminderType
    target_id: str           # 目标ID（用户或群聊）
    target_type: str         # 目标类型 (user, chat)
    content: str             # 提醒内容
    
    # 时间配置
    start_time: datetime
    interval_seconds: int = 300  # 默认5分钟
    max_count: int = 3
    
    # 提醒配置
    priority: ReminderPriority = ReminderPriority.NORMAL
    at_users: List[str] = field(default_factory=list)
    at_all: bool = False
    
    # 状态
    current_count: int = 0
    last_reminder_time: Optional[datetime] = None
    is_active: bool = True
    is_paused: bool = False
    
    # 回调
    on_remind: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_cancel: Optional[Callable] = None


class ReminderManager:
    """提醒管理器"""
    
    def __init__(self, bot, config: Optional[ReminderConfig] = None):
        self.bot = bot
        self.config = config or ReminderConfig()
        
        # 任务存储
        self._tasks: Dict[str, ReminderTask] = {}
        self._task_futures: Dict[str, asyncio.Task] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 运行状态
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return f"reminder_{uuid.uuid4().hex[:16]}"
    
    async def start(self):
        """启动提醒管理器"""
        self._running = True
        print("[ReminderManager] 提醒管理器已启动")
    
    async def stop(self):
        """停止提醒管理器"""
        self._running = False
        
        # 取消所有任务
        async with self._lock:
            for task_id, future in self._task_futures.items():
                if not future.done():
                    future.cancel()
            
            self._tasks.clear()
            self._task_futures.clear()
        
        self._executor.shutdown(wait=True)
        print("[ReminderManager] 提醒管理器已停止")
    
    async def create_interval_reminder(
        self,
        target_id: str,
        content: str,
        interval_minutes: Optional[int] = None,
        max_count: Optional[int] = None,
        at_users: Optional[List[str]] = None,
        at_all: bool = False,
        priority: ReminderPriority = ReminderPriority.NORMAL,
        target_type: str = "chat",
        start_delay_seconds: int = 0
    ) -> str:
        """
        创建间隔提醒任务
        
        Args:
            target_id: 目标ID（群聊ID或用户ID）
            content: 提醒内容
            interval_minutes: 间隔分钟数（默认使用配置）
            max_count: 最大提醒次数（默认使用配置）
            at_users: 要@的用户列表
            at_all: 是否@所有人
            priority: 优先级
            target_type: 目标类型
            start_delay_seconds: 开始延迟秒数
        
        Returns:
            任务ID
        """
        task_id = self._generate_task_id()
        
        interval = (interval_minutes or self.config.interval_minutes) * 60
        max_reminders = max_count or self.config.max_reminders
        
        # 合并@用户
        final_at_users = list(at_users or [])
        if self.config.at_boss and self.config.boss_ids:
            final_at_users.extend(self.config.boss_ids)
        
        task = ReminderTask(
            task_id=task_id,
            reminder_type=ReminderType.INTERVAL,
            target_id=target_id,
            target_type=target_type,
            content=content,
            start_time=datetime.now() + timedelta(seconds=start_delay_seconds),
            interval_seconds=interval,
            max_count=max_reminders,
            priority=priority,
            at_users=list(set(final_at_users)),  # 去重
            at_all=at_all or self.config.at_all
        )
        
        async with self._lock:
            self._tasks[task_id] = task
        
        # 启动任务
        future = asyncio.create_task(self._run_interval_reminder(task))
        
        async with self._lock:
            self._task_futures[task_id] = future
        
        print(f"[ReminderManager] 创建间隔提醒任务: {task_id}, 间隔: {interval//60}分钟, 最大次数: {max_reminders}")
        
        return task_id
    
    async def create_one_time_reminder(
        self,
        target_id: str,
        content: str,
        delay_minutes: float = 0,
        at_users: Optional[List[str]] = None,
        at_all: bool = False,
        target_type: str = "chat"
    ) -> str:
        """
        创建一次性提醒任务
        
        Args:
            target_id: 目标ID
            content: 提醒内容
            delay_minutes: 延迟分钟数
            at_users: 要@的用户列表
            at_all: 是否@所有人
            target_type: 目标类型
        
        Returns:
            任务ID
        """
        task_id = self._generate_task_id()
        
        task = ReminderTask(
            task_id=task_id,
            reminder_type=ReminderType.ONCE,
            target_id=target_id,
            target_type=target_type,
            content=content,
            start_time=datetime.now() + timedelta(minutes=delay_minutes),
            interval_seconds=0,
            max_count=1,
            at_users=at_users or [],
            at_all=at_all
        )
        
        async with self._lock:
            self._tasks[task_id] = task
        
        # 启动任务
        future = asyncio.create_task(self._run_one_time_reminder(task))
        
        async with self._lock:
            self._task_futures[task_id] = future
        
        print(f"[ReminderManager] 创建一次性提醒任务: {task_id}, 延迟: {delay_minutes}分钟")
        
        return task_id
    
    async def _run_interval_reminder(self, task: ReminderTask):
        """运行间隔提醒任务"""
        try:
            # 等待到开始时间
            now = datetime.now()
            if task.start_time > now:
                wait_seconds = (task.start_time - now).total_seconds()
                await asyncio.sleep(wait_seconds)
            
            while task.is_active and task.current_count < task.max_count:
                if task.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # 发送提醒
                await self._send_reminder(task)
                
                task.current_count += 1
                task.last_reminder_time = datetime.now()
                
                # 检查是否完成
                if task.current_count >= task.max_count:
                    break
                
                # 等待下一次提醒
                await asyncio.sleep(task.interval_seconds)
            
            # 任务完成
            task.is_active = False
            if task.on_complete:
                if asyncio.iscoroutinefunction(task.on_complete):
                    await task.on_complete(task)
                else:
                    task.on_complete(task)
            
            print(f"[ReminderManager] 提醒任务完成: {task.task_id}")
            
        except asyncio.CancelledError:
            print(f"[ReminderManager] 提醒任务取消: {task.task_id}")
            raise
        except Exception as e:
            print(f"[ReminderManager] 提醒任务异常: {task.task_id}, 错误: {e}")
            task.is_active = False
    
    async def _run_one_time_reminder(self, task: ReminderTask):
        """运行一次性提醒任务"""
        try:
            # 等待到开始时间
            now = datetime.now()
            if task.start_time > now:
                wait_seconds = (task.start_time - now).total_seconds()
                await asyncio.sleep(wait_seconds)
            
            if task.is_active:
                await self._send_reminder(task)
                task.current_count = 1
                task.last_reminder_time = datetime.now()
            
            task.is_active = False
            
            if task.on_complete:
                if asyncio.iscoroutinefunction(task.on_complete):
                    await task.on_complete(task)
                else:
                    task.on_complete(task)
            
            print(f"[ReminderManager] 一次性提醒完成: {task.task_id}")
            
        except asyncio.CancelledError:
            print(f"[ReminderManager] 一次性提醒取消: {task.task_id}")
            raise
        except Exception as e:
            print(f"[ReminderManager] 一次性提醒异常: {task.task_id}, 错误: {e}")
            task.is_active = False
    
    async def _send_reminder(self, task: ReminderTask):
        """发送提醒消息"""
        try:
            # 构建消息内容
            message = task.content
            
            if self.config.include_timestamp:
                timestamp = datetime.now().strftime("%H:%M:%S")
                message = f"[{timestamp}] {message}"
            
            # 添加提醒次数信息
            if task.max_count > 1:
                message = f"【{task.current_count + 1}/{task.max_count}】{message}"
            
            # 添加优先级标记
            priority_markers = {
                ReminderPriority.LOW: "",
                ReminderPriority.NORMAL: "",
                ReminderPriority.HIGH: "⚠️ ",
                ReminderPriority.URGENT: "🚨 "
            }
            message = f"{priority_markers.get(task.priority, '')}{message}"
            
            # 构建@文本
            at_text = ""
            if task.at_all:
                at_text = "<at user_id=\"all\">所有人</at> "
            elif task.at_users:
                at_parts = [f'<at user_id="{uid}"></at>' for uid in task.at_users]
                at_text = " ".join(at_parts) + " "
            
            full_message = f"{at_text}{message}"
            
            # 发送消息
            content = {"text": full_message}
            
            receive_id_type = "chat_id" if task.target_type == "chat" else "open_id"
            
            await self.bot.send_message(
                receive_id=task.target_id,
                content=content,
                msg_type="text",
                receive_id_type=receive_id_type
            )
            
            # 触发回调
            if task.on_remind:
                if asyncio.iscoroutinefunction(task.on_remind):
                    await task.on_remind(task)
                else:
                    task.on_remind(task)
            
            print(f"[ReminderManager] 发送提醒: {task.task_id}, 第{task.current_count + 1}次")
            
        except Exception as e:
            print(f"[ReminderManager] 发送提醒失败: {task.task_id}, 错误: {e}")
    
    async def cancel_reminder(self, task_id: str) -> bool:
        """
        取消提醒任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功取消
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.is_active = False
            
            future = self._task_futures.get(task_id)
            if future and not future.done():
                future.cancel()
            
            if task.on_cancel:
                if asyncio.iscoroutinefunction(task.on_cancel):
                    await task.on_cancel(task)
                else:
                    task.on_cancel(task)
            
            del self._tasks[task_id]
            del self._task_futures[task_id]
        
        print(f"[ReminderManager] 取消提醒任务: {task_id}")
        return True
    
    async def pause_reminder(self, task_id: str) -> bool:
        """暂停提醒任务"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.is_paused = True
                print(f"[ReminderManager] 暂停提醒任务: {task_id}")
                return True
        return False
    
    async def resume_reminder(self, task_id: str) -> bool:
        """恢复提醒任务"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.is_paused = False
                print(f"[ReminderManager] 恢复提醒任务: {task_id}")
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ReminderTask]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ReminderTask]:
        """获取所有任务"""
        return list(self._tasks.values())
    
    def get_active_tasks(self) -> List[ReminderTask]:
        """获取活跃任务"""
        return [task for task in self._tasks.values() if task.is_active]
    
    async def create_boss_reminder(
        self,
        target_id: str,
        content: str,
        boss_ids: Optional[List[str]] = None,
        interval_minutes: int = 5,
        max_count: int = 3,
        target_type: str = "chat"
    ) -> str:
        """
        创建老板提醒任务（多次@老板）
        
        Args:
            target_id: 目标ID
            content: 提醒内容
            boss_ids: 老板ID列表（默认使用配置）
            interval_minutes: 间隔分钟数
            max_count: 最大提醒次数
            target_type: 目标类型
        
        Returns:
            任务ID
        """
        final_boss_ids = boss_ids or self.config.boss_ids
        
        if not final_boss_ids:
            raise ValueError("未配置老板ID")
        
        return await self.create_interval_reminder(
            target_id=target_id,
            content=content,
            interval_minutes=interval_minutes,
            max_count=max_count,
            at_users=final_boss_ids,
            at_all=False,
            priority=ReminderPriority.HIGH,
            target_type=target_type
        )
    
    async def create_meeting_reminder(
        self,
        chat_id: str,
        meeting_title: str,
        start_time: datetime,
        participants: List[str],
        reminder_minutes_before: List[int] = [15, 5]
    ) -> List[str]:
        """
        创建会议提醒
        
        Args:
            chat_id: 群聊ID
            meeting_title: 会议标题
            start_time: 会议开始时间
            participants: 参与者ID列表
            reminder_minutes_before: 提前提醒时间（分钟）
        
        Returns:
            任务ID列表
        """
        task_ids = []
        
        for minutes in reminder_minutes_before:
            delay = (start_time - datetime.now()).total_seconds() / 60 - minutes
            
            if delay > 0:
                content = f"📅 会议提醒: {meeting_title} 将在{minutes}分钟后开始"
                
                task_id = await self.create_one_time_reminder(
                    target_id=chat_id,
                    content=content,
                    delay_minutes=delay,
                    at_users=participants,
                    target_type="chat"
                )
                
                task_ids.append(task_id)
        
        return task_ids
    
    async def stop_all_reminders(self):
        """停止所有提醒任务"""
        async with self._lock:
            task_ids = list(self._tasks.keys())
        
        for task_id in task_ids:
            await self.cancel_reminder(task_id)
        
        print(f"[ReminderManager] 已停止所有提醒任务，共 {len(task_ids)} 个")
    
    async def handle_message_response(self, chat_id: str, user_id: str, message_text: str):
        """
        处理消息响应（用于自动停止提醒）
        
        Args:
            chat_id: 群聊ID
            user_id: 用户ID
            message_text: 消息文本
        """
        if not self.config.auto_stop_on_response:
            return
        
        # 查找该群聊的活跃提醒任务
        active_tasks = self.get_active_tasks()
        
        for task in active_tasks:
            if task.target_id == chat_id and task.is_active:
                # 检查是否是@了相关人员
                if task.at_users and user_id in task.at_users:
                    # 停止提醒
                    await self.cancel_reminder(task.task_id)
                    print(f"[ReminderManager] 收到响应，自动停止提醒: {task.task_id}")
