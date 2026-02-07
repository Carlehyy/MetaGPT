"""
飞书机器人使用示例
演示如何使用飞书机器人模块的各种功能
"""

import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
import uvicorn

from feishu import (
    FeishuBot, FeishuConfig,
    GroupManager, ReminderManager, ReminderConfig,
    CardBuilder, CardTemplate
)
from feishu.message import Message, MessageHandler, MessageBuilder


# ============ 配置 ============
APP_ID = "cli_a90f6f9494f81bcd"
APP_SECRET = "frW8P3XZQxoP5lG8QMqDvdLHYG3OhzEY"

# 示例用户ID（请替换为实际的用户open_id）
BOSS_ID = "ou_xxxxxxxxxxxxxxxx"  # 老板ID
USER_ID = "ou_xxxxxxxxxxxxxxxx"  # 普通用户ID
CHAT_ID = "oc_xxxxxxxxxxxxxxxx"  # 群聊ID


async def demo_basic_message(bot: FeishuBot):
    """演示基础消息发送"""
    print("\n=== 基础消息发送 ===")
    
    # 1. 发送文本消息
    result = await bot.send_text_message(
        receive_id=USER_ID,
        text="你好！这是测试消息",
        receive_id_type="open_id"
    )
    print(f"文本消息发送结果: {result}")
    
    # 2. 发送带@的消息
    content = MessageBuilder.build_text_message(
        text="请查看以上信息",
        at_users=[BOSS_ID]
    )
    result = await bot.send_message(
        receive_id=CHAT_ID,
        content=content,
        msg_type="text",
        receive_id_type="chat_id"
    )
    print(f"@消息发送结果: {result}")
    
    # 3. 发送富文本消息
    paragraphs = [
        [MessageBuilder.build_text_element("会议时间: ", style=["bold"]), 
         MessageBuilder.build_text_element("14:00")],
        [MessageBuilder.build_text_element("会议地点: ", style=["bold"]), 
         MessageBuilder.build_text_element("会议室A")],
        [MessageBuilder.build_at_element(BOSS_ID, "老板")]
    ]
    
    content = MessageBuilder.build_rich_text_content("会议通知", paragraphs)
    result = await bot.send_message(
        receive_id=CHAT_ID,
        content=content,
        msg_type="post",
        receive_id_type="chat_id"
    )
    print(f"富文本消息发送结果: {result}")


async def demo_interactive_card(bot: FeishuBot):
    """演示交互式卡片"""
    print("\n=== 交互式卡片 ===")
    
    # 1. 基础卡片
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
    
    result = await bot.send_interactive_card(
        receive_id=USER_ID,
        card=card,
        receive_id_type="open_id"
    )
    print(f"基础卡片发送结果: {result}")
    
    # 2. 会议摘要卡片
    speakers = [
        {
            "avatar": "img_v2_123456",
            "name": "张三",
            "content": "我认为这个方案可行",
            "timestamp": "14:30"
        },
        {
            "avatar": "img_v2_789012",
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
    
    result = await bot.send_interactive_card(
        receive_id=CHAT_ID,
        card=card,
        receive_id_type="chat_id"
    )
    print(f"会议摘要卡片发送结果: {result}")
    
    # 3. 进度卡片
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
    
    result = await bot.send_interactive_card(
        receive_id=CHAT_ID,
        card=card,
        receive_id_type="chat_id"
    )
    print(f"进度卡片发送结果: {result}")


async def demo_group_management(bot: FeishuBot):
    """演示群聊管理"""
    print("\n=== 群聊管理 ===")
    
    group_manager = GroupManager(bot)
    
    # 1. 创建群聊
    from feishu.group import ChatType, ChatMode
    
    try:
        chat = await group_manager.create_chat(
            name="测试群聊",
            description="用于测试的群聊",
            user_id_list=[USER_ID],
            chat_type=ChatType.PRIVATE,
            chat_mode=ChatMode.NORMAL
        )
        print(f"群聊创建成功: {chat.chat_id}")
        new_chat_id = chat.chat_id
    except Exception as e:
        print(f"创建群聊失败: {e}")
        new_chat_id = CHAT_ID
    
    # 2. 获取群聊信息
    try:
        chat_info = await group_manager.get_chat_info(new_chat_id)
        print(f"群名称: {chat_info.name}")
        print(f"成员数: {chat_info.member_count}")
    except Exception as e:
        print(f"获取群聊信息失败: {e}")
    
    # 3. 添加成员
    try:
        result = await group_manager.add_chat_members(
            chat_id=new_chat_id,
            user_id_list=[BOSS_ID]
        )
        print(f"添加成员结果: {result}")
    except Exception as e:
        print(f"添加成员失败: {e}")
    
    # 4. 获取成员列表
    try:
        members = await group_manager.get_chat_members(new_chat_id)
        print(f"成员数量: {len(members.get('items', []))}")
    except Exception as e:
        print(f"获取成员列表失败: {e}")


async def demo_reminder(bot: FeishuBot):
    """演示提醒机制"""
    print("\n=== 提醒机制 ===")
    
    # 配置提醒
    config = ReminderConfig(
        interval_minutes=1,  # 1分钟间隔（演示用）
        max_reminders=2,     # 最多2次
        at_boss=True,
        boss_ids=[BOSS_ID],
        auto_stop_on_response=True
    )
    
    reminder = ReminderManager(bot, config)
    await reminder.start()
    
    # 1. 创建间隔提醒
    task_id1 = await reminder.create_interval_reminder(
        target_id=CHAT_ID,
        content="请尽快处理待办事项",
        interval_minutes=1,
        max_count=2,
        at_users=[USER_ID],
        at_all=False
    )
    print(f"间隔提醒任务创建: {task_id1}")
    
    # 2. 创建老板提醒
    task_id2 = await reminder.create_boss_reminder(
        target_id=CHAT_ID,
        content="有紧急事项需要处理",
        interval_minutes=1,
        max_count=2
    )
    print(f"老板提醒任务创建: {task_id2}")
    
    # 3. 创建一次性提醒
    task_id3 = await reminder.create_one_time_reminder(
        target_id=USER_ID,
        content="这是一条一次性提醒",
        delay_minutes=0.5,  # 30秒后
        at_users=[]
    )
    print(f"一次性提醒任务创建: {task_id3}")
    
    # 等待演示完成
    print("等待提醒任务执行...")
    await asyncio.sleep(150)  # 等待2.5分钟
    
    # 停止提醒管理器
    await reminder.stop()
    print("提醒管理器已停止")


async def demo_webhook_server():
    """演示Webhook服务器"""
    print("\n=== Webhook服务器 ===")
    
    # 配置
    config = FeishuConfig(
        app_id=APP_ID,
        app_secret=APP_SECRET
    )
    
    # 创建机器人
    bot = FeishuBot(config)
    
    # 注册消息处理器
    @bot.on_message("text")
    async def handle_text_message(event_data):
        message = Message.from_event(event_data)
        text = message.get_text_content()
        
        print(f"收到消息: {text} from {message.sender.open_id}")
        
        # 处理命令
        if text.startswith("/help"):
            reply_text = """可用命令:
/help - 显示帮助
/status - 查看状态
/remind - 创建提醒
/card - 发送卡片
"""
            await bot.send_text_message(
                receive_id=message.chat_id,
                text=reply_text,
                receive_id_type="chat_id"
            )
        
        elif text.startswith("/status"):
            await bot.send_text_message(
                receive_id=message.chat_id,
                text="系统运行正常 ✅",
                receive_id_type="chat_id"
            )
    
    @bot.on_event("im.chat.member.user.added_v1")
    async def handle_member_added(event_data):
        print(f"新成员加入: {event_data}")
    
    @bot.on_event("im.chat.member.user.deleted_v1")
    async def handle_member_removed(event_data):
        print(f"成员离开: {event_data}")
    
    # 创建FastAPI应用
    app = bot.create_app()
    
    print("Webhook服务器启动在 http://0.0.0.0:8000")
    print("Webhook地址: http://your-domain.com/webhook/feishu")
    
    # 运行服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)


async def demo_complete_workflow():
    """演示完整工作流"""
    print("\n=== 完整工作流演示 ===")
    
    # 配置
    config = FeishuConfig(
        app_id=APP_ID,
        app_secret=APP_SECRET
    )
    
    # 创建机器人
    bot = FeishuBot(config)
    
    # 创建组件
    group_manager = GroupManager(bot)
    
    reminder_config = ReminderConfig(
        interval_minutes=5,
        max_reminders=3,
        at_boss=True,
        boss_ids=[BOSS_ID],
        auto_stop_on_response=True
    )
    reminder = ReminderManager(bot, reminder_config)
    await reminder.start()
    
    message_handler = MessageHandler(bot)
    
    # 1. 创建项目群聊
    print("1. 创建项目群聊...")
    try:
        chat = await group_manager.create_chat(
            name="项目讨论群",
            description="用于项目讨论和进度同步",
            user_id_list=[USER_ID, BOSS_ID],
            chat_type=ChatType.PRIVATE,
            chat_mode=ChatMode.NORMAL
        )
        project_chat_id = chat.chat_id
        print(f"群聊创建成功: {project_chat_id}")
    except Exception as e:
        print(f"使用默认群聊: {e}")
        project_chat_id = CHAT_ID
    
    # 2. 发送欢迎卡片
    print("2. 发送欢迎卡片...")
    welcome_card = CardBuilder().set_header(
        title="🎉 欢迎加入项目讨论群",
        template=CardTemplate.SUCCESS
    ).add_markdown(
        "**群用途:** 项目讨论和进度同步\n"
        "**群规则:**\n"
        "1. 保持讨论与项目相关\n"
        "2. 及时回复重要消息\n"
        "3. 使用 /help 查看可用命令"
    ).add_actions([
        CardBuilder().create_button("查看项目文档", url="https://example.com/docs"),
        CardBuilder().create_button("提交问题", action_type="primary", value={"action": "submit_issue"})
    ]).build()
    
    await bot.send_interactive_card(
        receive_id=project_chat_id,
        card=welcome_card,
        receive_id_type="chat_id"
    )
    
    # 3. 创建定期提醒
    print("3. 创建每日站会提醒...")
    standup_task = await reminder.create_interval_reminder(
        target_id=project_chat_id,
        content="📅 每日站会时间到了，请大家更新进度",
        interval_minutes=5,  # 演示用，实际应该是1440分钟（24小时）
        max_count=1,
        at_users=[USER_ID, BOSS_ID],
        at_all=False
    )
    print(f"站会提醒任务: {standup_task}")
    
    # 4. 发送项目进度卡片
    print("4. 发送项目进度...")
    progress_card = CardBuilder.create_progress_card(
        title="项目整体进度",
        progress=65,
        status_text="按计划进行中",
        details=[
            "✅ 需求分析完成",
            "✅ 技术设计完成",
            "🔄 开发实现进行中 (65%)",
            "⏳ 测试阶段待开始",
            "⏳ 上线部署待开始"
        ]
    )
    
    await bot.send_interactive_card(
        receive_id=project_chat_id,
        card=progress_card,
        receive_id_type="chat_id"
    )
    
    # 5. 创建紧急提醒（@老板）
    print("5. 创建紧急提醒...")
    urgent_task = await reminder.create_boss_reminder(
        target_id=project_chat_id,
        content="⚠️ 项目遇到技术难题，需要您的决策",
        interval_minutes=5,
        max_count=2
    )
    print(f"紧急提醒任务: {urgent_task}")
    
    print("\n完整工作流演示完成！")
    
    # 清理
    await reminder.stop()


async def main():
    """主函数"""
    print("=" * 50)
    print("飞书机器人模块使用示例")
    print("=" * 50)
    
    # 配置
    config = FeishuConfig(
        app_id=APP_ID,
        app_secret=APP_SECRET
    )
    
    # 创建机器人
    bot = FeishuBot(config)
    
    # 选择演示模式
    print("\n请选择演示模式:")
    print("1. 基础消息发送")
    print("2. 交互式卡片")
    print("3. 群聊管理")
    print("4. 提醒机制")
    print("5. 完整工作流")
    print("6. 启动Webhook服务器")
    print("0. 退出")
    
    # 这里使用固定值演示，实际使用时可以通过输入选择
    demo_mode = 5  # 默认运行完整工作流
    
    try:
        if demo_mode == 1:
            await demo_basic_message(bot)
        elif demo_mode == 2:
            await demo_interactive_card(bot)
        elif demo_mode == 3:
            await demo_group_management(bot)
        elif demo_mode == 4:
            await demo_reminder(bot)
        elif demo_mode == 5:
            await demo_complete_workflow()
        elif demo_mode == 6:
            await demo_webhook_server()
        else:
            print("退出")
    except Exception as e:
        print(f"演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
