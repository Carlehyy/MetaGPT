#!/usr/bin/env python3
"""
Agent Company - 公司主类
整合所有组件，提供统一的对外接口
"""
import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from discussion.engine import DiscussionEngine, DiscussionConfig
from discussion.round_robin import Role
from discussion.state import DiscussionState
from feishu.bot import FeishuBot, FeishuConfig
from feishu.card import CardBuilder
from feishu.reminder import ReminderManager as ReminderService

logger = logging.getLogger(__name__)


@dataclass
class CompanyConfig:
    """公司配置"""
    llm_api_key: str = ""
    llm_model: str = "glm-4"
    llm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    max_rounds_per_phase: int = 20
    consensus_threshold: float = 0.8
    demo_mode: bool = False


class AgentCompany:
    """AI软件公司主类"""
    
    # 9个阶段定义
    PHASES = [
        {"id": "P1", "name": "需求分析", "leader": "产品经理"},
        {"id": "P2", "name": "技术方案设计", "leader": "架构师"},
        {"id": "P3", "name": "UI/UX设计", "leader": "产品设计师"},
        {"id": "P4", "name": "任务拆解", "leader": "项目经理"},
        {"id": "P5", "name": "编码实现", "leader": "开发工程师"},
        {"id": "P6", "name": "UI验收", "leader": "产品设计师"},
        {"id": "P7", "name": "功能测试", "leader": "测试工程师"},
        {"id": "P8", "name": "部署上线", "leader": "项目经理"},
        {"id": "P9", "name": "运维监控", "leader": "运维工程师"}
    ]
    
    # 8个角色定义
    ROLES = [
        {"name": "老板", "role": "boss", "user_id": "boss_001"},
        {"name": "产品经理", "role": "product_manager", "user_id": "pm_001"},
        {"name": "架构师", "role": "architect", "user_id": "arch_001"},
        {"name": "产品设计师", "role": "product_designer", "user_id": "designer_001"},
        {"name": "项目经理", "role": "project_manager", "user_id": "pm_002"},
        {"name": "开发工程师", "role": "engineer", "user_id": "dev_001"},
        {"name": "测试工程师", "role": "qa_engineer", "user_id": "qa_001"},
        {"name": "运维工程师", "role": "devops", "user_id": "ops_001"}
    ]
    
    def __init__(self, config: CompanyConfig):
        self.config = config
        self.current_phase_idx = 0
        self.current_discussion: Optional[DiscussionEngine] = None
        self.project_idea: str = ""
        self.phase_results: Dict[str, Dict] = {}
        
        # 初始化飞书机器人
        feishu_config = FeishuConfig(
            app_id=config.feishu_app_id,
            app_secret=config.feishu_app_secret
        )
        self.feishu_bot = FeishuBot(feishu_config)
        self.reminder_service = ReminderService(self.feishu_bot)
        
        logger.info("AgentCompany初始化完成")
    
    async def start_project(self, idea: str, chat_id: str):
        """启动新项目"""
        self.project_idea = idea
        self.current_phase_idx = 0
        
        logger.info(f"启动新项目: {idea}")
        
        # 演示模式下跳过飞书消息发送
        if not self.config.demo_mode:
            # 发送欢迎卡片
            welcome_card = CardBuilder().build()
            await self.feishu_bot.send_message(chat_id, "欢迎使用AI Team！")
        else:
            logger.info("[演示模式] 跳过发送飞书消息")
        
        # 开始第一个阶段
        await self.start_phase(self.current_phase_idx, chat_id)
    
    async def start_phase(self, phase_idx: int, chat_id: str):
        """开始指定阶段"""
        if phase_idx >= len(self.PHASES):
            logger.info("所有阶段已完成")
            if not self.config.demo_mode:
                await self.feishu_bot.send_text_message(chat_id, "🎉 项目已完成！")
            return
        
        phase = self.PHASES[phase_idx]
        self.current_phase_idx = phase_idx
        
        logger.info(f"开始阶段: {phase['name']}")
        
        # 发送阶段开始通知（非演示模式）
        if not self.config.demo_mode:
            await self.feishu_bot.send_text_message(
                chat_id,
                f"📋 开始阶段 {phase['id']}: {phase['name']}\n负责人: {phase['leader']}"
            )
        else:
            logger.info(f"[演示模式] 阶段 {phase['id']}: {phase['name']}")
        
        # 创建讨论引擎
        discussion_config = DiscussionConfig(
            max_rounds=self.config.max_rounds_per_phase,
            consensus_threshold=self.config.consensus_threshold
        )
        
        # 将字典转换为Role对象
        roles = [
            Role(
                id=r["user_id"],
                name=r["name"],
                description=r["role"],
                is_boss=(r["role"] == "boss")
            )
            for r in self.ROLES
        ]

        self.current_discussion = DiscussionEngine(
            roles=roles,
            phase=phase["name"],
            config=discussion_config
        )
        
        # 注册回调（使用DiscussionEngine支持的方法）
        self.current_discussion.on_state_change(
            lambda old, new: self._on_state_change(new, chat_id)
        )
        
        # 开始讨论
        await self.current_discussion.start_discussion(self.project_idea)
        
        # 发送第一轮通知（演示模式下跳过）
        first_speaker = await self.current_discussion.next_turn()
        if first_speaker and not self.config.demo_mode:
            await self.feishu_bot.send_text_message(
                chat_id,
                f"🎯 第1轮讨论开始\n👤 请 @{first_speaker.sender_name} 发言"
            )
        elif first_speaker:
            logger.info(f"[演示模式] 第1轮，请 @{first_speaker.sender_name} 发言")
    
    async def handle_message(self, sender: str, content: str, chat_id: str):
        """处理用户消息"""
        # 检查是否是老板介入
        if sender == "老板":
            if any(kw in content for kw in ["我决定", "就这样", "听我的"]):
                if self.current_discussion:
                    await self.current_discussion.boss_intervene(content)
                    await self.feishu_bot.send_text_message(
                        chat_id,
                        f"👔 老板已做出决策: {content}"
                    )
                    await self._complete_phase(chat_id)
                    return
        
        # 添加到讨论
        if self.current_discussion and self.current_discussion.state_manager.current_state == DiscussionState.ONGOING:
            # 创建消息对象并提交
            from discussion.message import Message, MessageType
            message = Message(
                content=content,
                sender_id=sender.lower().replace(" ", "_"),
                sender_name=sender,
                message_type=MessageType.SPEECH
            )
            self.current_discussion.submit_message(message)
            
            # 获取下一个发言者
            next_speaker = await self.current_discussion.next_turn()
            if next_speaker:
                if not self.config.demo_mode:
                    await self.feishu_bot.send_text_message(
                        chat_id,
                        f"👤 请 @{next_speaker.sender_name} 发言 (第{next_speaker.round_number}轮)"
                    )
                else:
                    logger.info(f"[演示模式] 请 @{next_speaker.sender_name} 发言 (第{next_speaker.round_number}轮)")
    
    async def _on_message(self, message, chat_id: str):
        """消息回调"""
        # 构建讨论卡片
        participants_status = []
        for p in self.ROLES:
            has_spoken = any(m.sender == p["name"] for m in self.current_discussion.messages)
            participants_status.append({
                "name": p["name"],
                "has_spoken": has_spoken
            })
        
        card = CardBuilder.build_discussion_card(
            phase=self.current_discussion.phase,
            round_num=message.round_num,
            speaker=message.sender,
            speaker_avatar="",
            content=message.content,
            participants=participants_status,
            consensus_status="讨论中"
        )
        
        await self.feishu_bot.send_card_message(chat_id, card)
    
    async def _on_state_change(self, status, chat_id: str):
        """状态变更回调"""
        if status.state == DiscussionState.CONSENSUS_REACHED:
            await self.feishu_bot.send_text_message(
                chat_id,
                f"✅ 已达成共识！\n原因: {status.metadata.get('consensus_reason', '')}"
            )
            await self._complete_phase(chat_id)
        
        elif status.state == DiscussionState.ROUNDS_EXHAUSTED:
            await self.feishu_bot.send_text_message(
                chat_id,
                "⏰ 已达到最大轮数，需要老板决策"
            )
            # 启动老板提醒
            boss = next((r for r in self.ROLES if r["role"] == "boss"), None)
            if boss:
                await self.reminder_service.start_boss_reminder(
                    chat_id=chat_id,
                    boss_user_id=boss["user_id"],
                    reminder_count=3,
                    message="请老板做出最终决策"
                )
    
    async def _complete_phase(self, chat_id: str):
        """完成当前阶段"""
        if not self.current_discussion:
            return
        
        # 保存阶段结果
        phase = self.PHASES[self.current_phase_idx]
        self.phase_results[phase["id"]] = self.current_discussion.get_discussion_summary()
        
        # 发送阶段总结
        summary = self.current_discussion.get_discussion_summary()
        next_phase_name = self.PHASES[self.current_phase_idx + 1]["name"] if self.current_phase_idx + 1 < len(self.PHASES) else "项目完成"
        
        card = CardBuilder.build_phase_summary_card(
            phase=phase["name"],
            summary=f"讨论了 {summary['message_count']} 条消息，共 {summary['rounds']} 轮",
            next_phase=next_phase_name
        )
        await self.feishu_bot.send_card_message(chat_id, card)
        
        # 进入下一阶段
        await asyncio.sleep(2)
        await self.start_phase(self.current_phase_idx + 1, chat_id)
    
    async def close(self):
        """关闭资源"""
        pass  # feishu_bot.close() not available
