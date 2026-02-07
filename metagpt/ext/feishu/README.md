# 飞书机器人集成模块

基于 Python + FastAPI 实现的飞书机器人集成模块，提供完整的消息接收、发送、群聊管理和提醒机制功能。

## 功能特性

- ✅ **消息接收**: Webhook 模式接收飞书消息和事件
- ✅ **消息发送**: 支持文本、富文本、交互式卡片等多种消息类型
- ✅ **@提醒功能**: 支持@指定用户、@所有人、多次@提醒
- ✅ **群聊管理**: 创建群聊、管理成员、获取群信息
- ✅ **富文本卡片**: 支持多种卡片模板，包含角色头像、发言内容、当前轮数
- ✅ **定时提醒**: 5分钟间隔提醒、多次提醒、自动停止机制

## 安装依赖

```bash
pip install fastapi httpx uvicorn
```

## 快速开始

### 1. 基础配置

```python
from feishu import FeishuBot, FeishuConfig

# 配置飞书应用
config = FeishuConfig(
    app_id="cli_a90f6f9494f81bcd",
    app_secret="frW8P3XZQxoP5lG8QMqDvdLHYG3OhzEY",
    verification_token="your_verification_token",  # 可选
    encrypt_key="your_encrypt_key"  # 可选，用于签名验证
)

# 创建机器人实例
bot = FeishuBot(config)
```

### 2. 创建 Webhook 服务

```python
from fastapi import FastAPI
import uvicorn

# 创建 FastAPI 应用
app = bot.create_app()

# 运行服务
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. 处理消息事件

```python
from feishu.message import Message

@bot.on_message("text")
async def handle_text_message(event_data):
    """处理文本消息"""
    message = Message.from_event(event_data)
    text = message.get_text_content()
    
    print(f"收到消息: {text} from {message.sender.name}")
    
    # 回复消息
    await bot.send_text_message(
        receive_id=message.chat_id,
        text=f"收到你的消息: {text}",
        receive_id_type="chat_id"
    )

@bot.on_event("im.message.receive_v1")
async def handle_all_messages(event_data):
    """处理所有消息类型"""
    print(f"收到事件: {event_data}")
```

## 消息发送

### 发送文本消息

```python
# 发送给指定用户
await bot.send_text_message(
    receive_id="user_open_id",
    text="你好，这是测试消息",
    receive_id_type="open_id"
)

# 发送到群聊
await bot.send_text_message(
    receive_id="chat_id",
    text="大家好！",
    receive_id_type="chat_id"
)
```

### 发送富文本消息

```python
from feishu.message import MessageBuilder

# 构建富文本内容
content = MessageBuilder.build_rich_text_content(
    title="会议通知",
    paragraphs=[
        [MessageBuilder.build_text_element("会议时间: 14:00")],
        [MessageBuilder.build_text_element("会议地点: 会议室A")],
        [MessageBuilder.build_at_element("user_open_id", "张三")]
    ]
)

await bot.send_message(
    receive_id="chat_id",
    content=content,
    msg_type="post",
    receive_id_type="chat_id"
)
```

### 发送交互式卡片

```python
from feishu.card import CardBuilder, CardTemplate

# 创建卡片
builder = CardBuilder()
card = builder.set_header(
    title="任务提醒",
    subtitle="请尽快处理",
    template=CardTemplate.WARNING
).add_markdown(
    "**任务:** 审核文档\n**截止:** 今天18:00"
).add_actions([
    builder.create_button("立即处理", action_type="primary", value={"action": "process"}),
    builder.create_button("稍后提醒", action_type="default", value={"action": "remind_later"})
]).build()

# 发送卡片
await bot.send_interactive_card(
    receive_id="user_open_id",
    card=card,
    receive_id_type="open_id"
)
```

## @提醒功能

### 在消息中@用户

```python
from feishu.message import MessageBuilder

# 构建带@的消息
content = MessageBuilder.build_text_message(
    text="请查看以上信息",
    at_users=["user_open_id_1", "user_open_id_2"]
)

await bot.send_message(
    receive_id="chat_id",
    content=content,
    msg_type="text",
    receive_id_type="chat_id"
)

# @所有人
content = MessageBuilder.build_text_message(
    text="重要通知！",
    at_all=True
)
```

### 使用富文本@用户

```python
paragraphs = [
    [
        MessageBuilder.build_at_element("user_open_id", "老板"),
        MessageBuilder.build_text_element(" 请审批")
    ]
]

content = MessageBuilder.build_rich_text_content("审批提醒", paragraphs)
```

## 群聊管理

### 创建群聊

```python
from feishu import GroupManager, ChatType, ChatMode

# 创建群聊管理器
group_manager = GroupManager(bot)

# 创建群聊
chat = await group_manager.create_chat(
    name="项目讨论群",
    description="用于项目讨论",
    user_id_list=["user_open_id_1", "user_open_id_2"],
    chat_type=ChatType.PRIVATE,
    chat_mode=ChatMode.NORMAL
)

print(f"群聊创建成功: {chat.chat_id}")
```

### 管理群成员

```python
# 添加成员
await group_manager.add_chat_members(
    chat_id="chat_id",
    user_id_list=["user_open_id_3", "user_open_id_4"]
)

# 移除成员
await group_manager.remove_chat_members(
    chat_id="chat_id",
    user_id_list=["user_open_id_3"]
)

# 获取成员列表
members = await group_manager.get_chat_members(chat_id="chat_id")
```

### 获取群聊信息

```python
# 获取群聊信息
chat_info = await group_manager.get_chat_info(chat_id="chat_id")
print(f"群名称: {chat_info.name}")
print(f"成员数: {chat_info.member_count}")

# 获取群聊列表
chats = await group_manager.get_chat_list()
```

## 提醒机制

### 基础配置

```python
from feishu import ReminderManager, ReminderConfig

# 配置提醒
config = ReminderConfig(
    interval_minutes=5,      # 5分钟间隔
    max_reminders=3,         # 最多提醒3次
    at_boss=True,            # @老板
    boss_ids=["boss_open_id"],  # 老板ID列表
    auto_stop_on_response=True  # 收到回复自动停止
)

# 创建提醒管理器
reminder = ReminderManager(bot, config)
await reminder.start()
```

### 创建间隔提醒

```python
# 创建5分钟间隔的提醒，最多3次
task_id = await reminder.create_interval_reminder(
    target_id="chat_id",
    content="请尽快处理待办事项",
    interval_minutes=5,
    max_count=3,
    at_users=["user_open_id"],
    at_all=False
)
```

### 老板提醒（多次@）

```python
# 创建老板提醒任务（每5分钟@一次老板，共3次）
task_id = await reminder.create_boss_reminder(
    target_id="chat_id",
    content="有紧急事项需要处理",
    boss_ids=["boss_open_id"],
    interval_minutes=5,
    max_count=3
)
```

### 会议提醒

```python
from datetime import datetime, timedelta

# 创建会议提醒
meeting_time = datetime.now() + timedelta(hours=1)

task_ids = await reminder.create_meeting_reminder(
    chat_id="chat_id",
    meeting_title="周会",
    start_time=meeting_time,
    participants=["user1", "user2", "user3"],
    reminder_minutes_before=[15, 5]  # 提前15分钟和5分钟提醒
)
```

### 管理提醒任务

```python
# 取消提醒
await reminder.cancel_reminder(task_id)

# 暂停提醒
await reminder.pause_reminder(task_id)

# 恢复提醒
await reminder.resume_reminder(task_id)

# 获取任务信息
task = reminder.get_task(task_id)
print(f"当前提醒次数: {task.current_count}/{task.max_count}")

# 停止所有提醒
await reminder.stop_all_reminders()
```

## 富文本卡片模板

### 会议摘要卡片

```python
from feishu.card import CardBuilder

# 创建会议摘要卡片
speakers = [
    {
        "avatar": "avatar_image_key_1",
        "name": "张三",
        "content": "我认为这个方案可行",
        "timestamp": "14:30"
    },
    {
        "avatar": "avatar_image_key_2",
        "name": "李四",
        "content": "同意，可以开始实施",
        "timestamp": "14:32"
    }
]

card = CardBuilder.create_meeting_summary_card(
    title="项目讨论会议",
    speakers=speakers,
    current_round=2,
    total_rounds=5
)

await bot.send_interactive_card(
    receive_id="chat_id",
    card=card,
    receive_id_type="chat_id"
)
```

### 进度卡片

```python
from feishu.card import CardBuilder

card = CardBuilder.create_progress_card(
    title="任务进度",
    progress=75,
    status_text="正在进行中",
    details=[
        "已完成: 需求分析",
        "已完成: 技术设计",
        "进行中: 开发实现"
    ]
)
```

### 提醒卡片

```python
from feishu.card import CardBuilder

card = CardBuilder.create_reminder_card(
    title="待办提醒",
    message="请尽快完成代码审查",
    mentioned_users=["user_open_id"],
    urgency="high"
)
```

## 完整示例

```python
import asyncio
from fastapi import FastAPI
import uvicorn

from feishu import (
    FeishuBot, FeishuConfig, 
    GroupManager, ReminderManager, ReminderConfig,
    CardBuilder, CardTemplate
)
from feishu.message import Message, MessageHandler, MessageBuilder

async def main():
    # 配置
    config = FeishuConfig(
        app_id="cli_a90f6f9494f81bcd",
        app_secret="frW8P3XZQxoP5lG8QMqDvdLHYG3OhzEY"
    )
    
    # 创建机器人
    bot = FeishuBot(config)
    
    # 创建组件
    group_manager = GroupManager(bot)
    
    reminder_config = ReminderConfig(
        interval_minutes=5,
        max_reminders=3,
        at_boss=True,
        boss_ids=["boss_open_id"]
    )
    reminder = ReminderManager(bot, reminder_config)
    await reminder.start()
    
    # 消息处理器
    message_handler = MessageHandler(bot)
    
    @bot.on_message("text")
    async def handle_text(event_data):
        message = Message.from_event(event_data)
        text = message.get_text_content()
        
        # 处理命令
        if text.startswith("/提醒"):
            # 创建提醒
            task_id = await reminder.create_boss_reminder(
                target_id=message.chat_id,
                content="有紧急事项需要处理",
                interval_minutes=5,
                max_count=3
            )
            await message_handler.send_text_reply(
                message, 
                f"已创建提醒任务: {task_id}"
            )
        
        elif text.startswith("/卡片"):
            # 发送卡片
            card = CardBuilder().set_header(
                title="测试卡片",
                template=CardTemplate.INFO
            ).add_markdown("这是一条测试消息").build()
            
            await message_handler.send_card_reply(message, card)
        
        elif text.startswith("/创建群"):
            # 创建群聊
            chat = await group_manager.create_chat(
                name="新项目群",
                description="项目讨论",
                user_id_list=[message.sender.open_id]
            )
            await message_handler.send_text_reply(
                message,
                f"群聊创建成功: {chat.chat_id}"
            )
    
    # 创建应用
    app = bot.create_app()
    
    # 运行
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
```

## Webhook 配置

在飞书开放平台配置 Webhook URL:

1. 进入飞书开放平台: https://open.feishu.cn/
2. 选择你的应用
3. 进入「事件订阅」页面
4. 配置请求地址: `https://your-domain.com/webhook/feishu`
5. 添加需要订阅的事件:
   - `im.message.receive_v1` - 接收消息
   - `im.chat.member.user.added_v1` - 群成员增加
   - `im.chat.member.user.deleted_v1` - 群成员减少

## 环境变量配置

```bash
# .env 文件
FEISHU_APP_ID=cli_a90f6f9494f81bcd
FEISHU_APP_SECRET=frW8P3XZQxoP5lG8QMqDvdLHYG3OhzEY
FEISHU_VERIFICATION_TOKEN=your_token
FEISHU_ENCRYPT_KEY=your_encrypt_key
```

## API 参考

### FeishuBot 方法

| 方法 | 说明 |
|------|------|
| `create_app()` | 创建 FastAPI 应用 |
| `send_message()` | 发送消息 |
| `send_text_message()` | 发送文本消息 |
| `send_rich_text()` | 发送富文本消息 |
| `send_interactive_card()` | 发送交互式卡片 |
| `reply_message()` | 回复消息 |
| `edit_message()` | 编辑消息 |
| `delete_message()` | 删除消息 |
| `on_message()` | 注册消息处理器 |
| `on_event()` | 注册事件处理器 |

### GroupManager 方法

| 方法 | 说明 |
|------|------|
| `create_chat()` | 创建群聊 |
| `get_chat_info()` | 获取群聊信息 |
| `update_chat()` | 更新群聊信息 |
| `delete_chat()` | 解散群聊 |
| `get_chat_members()` | 获取群成员列表 |
| `add_chat_members()` | 添加群成员 |
| `remove_chat_members()` | 移除群成员 |
| `get_chat_list()` | 获取群聊列表 |

### ReminderManager 方法

| 方法 | 说明 |
|------|------|
| `create_interval_reminder()` | 创建间隔提醒 |
| `create_one_time_reminder()` | 创建一次性提醒 |
| `create_boss_reminder()` | 创建老板提醒 |
| `create_meeting_reminder()` | 创建会议提醒 |
| `cancel_reminder()` | 取消提醒 |
| `pause_reminder()` | 暂停提醒 |
| `resume_reminder()` | 恢复提醒 |
| `stop_all_reminders()` | 停止所有提醒 |

## 许可证

MIT License
