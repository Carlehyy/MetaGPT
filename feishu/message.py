"""
消息处理模块
处理飞书消息的发送、接收、解析和格式化
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    POST = "post"  # 富文本
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    MEDIA = "media"
    STICKER = "sticker"
    INTERACTIVE = "interactive"  # 交互式卡片
    SHARE_CHAT = "share_chat"
    SHARE_USER = "share_user"


class MentionType(Enum):
    """@类型枚举"""
    ALL = "all"  # @所有人
    USER = "user"  # @指定用户


@dataclass
class UserInfo:
    """用户信息"""
    open_id: str
    user_id: Optional[str] = None
    union_id: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        """从字典创建用户对象"""
        return cls(
            open_id=data.get("open_id", ""),
            user_id=data.get("user_id"),
            union_id=data.get("union_id"),
            name=data.get("name"),
            avatar=data.get("avatar", {}).get("avatar_origin", ""),
        )


@dataclass
class Mention:
    """@提及信息"""
    type: MentionType
    user: Optional[UserInfo] = None
    name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mention":
        """从字典创建@提及对象"""
        mention_type = MentionType.ALL if data.get("type") == "all" else MentionType.USER
        user_info = None
        
        if mention_type == MentionType.USER:
            user_info = UserInfo.from_dict(data)
        
        return cls(
            type=mention_type,
            user=user_info,
            name=data.get("name", "")
        )


@dataclass
class Message:
    """消息对象"""
    message_id: str
    message_type: MessageType
    content: Dict[str, Any]
    sender: UserInfo
    chat_id: str
    chat_type: str
    create_time: datetime
    mentions: List[Mention] = field(default_factory=list)
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    
    @classmethod
    def from_event(cls, event_data: Dict[str, Any]) -> "Message":
        """从事件数据创建消息对象"""
        message = event_data.get("message", {})
        sender = event_data.get("sender", {})
        
        # 解析消息类型
        msg_type_str = message.get("message_type", "text")
        msg_type = MessageType(msg_type_str) if msg_type_str in [t.value for t in MessageType] else MessageType.TEXT
        
        # 解析内容
        content_str = message.get("content", "{}")
        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except json.JSONDecodeError:
            content = {"text": content_str}
        
        # 解析@提及
        mentions = []
        mentions_data = message.get("mentions", [])
        for mention_data in mentions_data:
            mentions.append(Mention.from_dict(mention_data))
        
        # 解析时间戳
        create_time_ms = int(message.get("create_time", "0"))
        create_time = datetime.fromtimestamp(create_time_ms / 1000) if create_time_ms else datetime.now()
        
        return cls(
            message_id=message.get("message_id", ""),
            message_type=msg_type,
            content=content,
            sender=UserInfo.from_dict(sender.get("sender_id", {})),
            chat_id=message.get("chat_id", ""),
            chat_type=message.get("chat_type", ""),
            create_time=create_time,
            mentions=mentions,
            parent_id=message.get("parent_id"),
            root_id=message.get("root_id")
        )
    
    def get_text_content(self) -> str:
        """获取文本内容"""
        if self.message_type == MessageType.TEXT:
            return self.content.get("text", "")
        elif self.message_type == MessageType.POST:
            # 从富文本中提取纯文本
            post_content = self.content.get("zh_cn", {})
            text_parts = []
            for line in post_content.get("content", []):
                for item in line:
                    if item.get("tag") == "text":
                        text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        return ""
    
    def is_mentioned(self, user_open_id: Optional[str] = None) -> bool:
        """检查是否被@"""
        for mention in self.mentions:
            if mention.type == MentionType.ALL:
                return True
            if user_open_id and mention.user and mention.user.open_id == user_open_id:
                return True
        return False
    
    def is_at_all(self) -> bool:
        """检查是否@所有人"""
        return any(m.type == MentionType.ALL for m in self.mentions)


class MessageBuilder:
    """消息构建器"""
    
    @staticmethod
    def build_text_message(text: str, at_users: Optional[List[str]] = None, at_all: bool = False) -> Dict[str, Any]:
        """
        构建文本消息内容
        
        Args:
            text: 文本内容
            at_users: 要@的用户open_id列表
            at_all: 是否@所有人
        """
        content = {"text": text}
        
        if at_all:
            content["text"] = f"<at user_id=\"all\">所有人</at> {text}"
        elif at_users:
            at_texts = [f'<at user_id="{uid}"></at>' for uid in at_users]
            content["text"] = f"{' '.join(at_texts)} {text}"
        
        return content
    
    @staticmethod
    def build_rich_text_content(
        title: str,
        paragraphs: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        构建富文本消息内容
        
        Args:
            title: 标题
            paragraphs: 段落列表，每个段落是一个元素列表
        """
        return {
            "zh_cn": {
                "title": title,
                "content": paragraphs
            }
        }
    
    @staticmethod
    def build_text_element(text: str, style: Optional[List[str]] = None) -> Dict[str, Any]:
        """构建文本元素"""
        element = {"tag": "text", "text": text}
        if style:
            element["style"] = style
        return element
    
    @staticmethod
    def build_at_element(user_id: str, name: str = "") -> Dict[str, Any]:
        """构建@元素"""
        return {"tag": "at", "user_id": user_id, "user_name": name}
    
    @staticmethod
    def build_link_element(href: str, text: str) -> Dict[str, Any]:
        """构建链接元素"""
        return {"tag": "a", "href": href, "text": text}
    
    @staticmethod
    def build_image_element(image_key: str, width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
        """构建图片元素"""
        element = {"tag": "img", "image_key": image_key}
        if width:
            element["width"] = width
        if height:
            element["height"] = height
        return element
    
    @staticmethod
    def build_markdown_content(markdown: str) -> Dict[str, Any]:
        """构建Markdown消息内容（通过富文本模拟）"""
        # 简单的markdown解析
        lines = markdown.split('\n')
        content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理标题
            if line.startswith('# '):
                content.append([MessageBuilder.build_text_element(line[2:], style=["bold"])])
            elif line.startswith('## '):
                content.append([MessageBuilder.build_text_element(line[3:], style=["bold"])])
            elif line.startswith('### '):
                content.append([MessageBuilder.build_text_element(line[4:], style=["bold"])])
            # 处理列表
            elif line.startswith('- ') or line.startswith('* '):
                content.append([MessageBuilder.build_text_element(f"• {line[2:]}")])
            # 处理引用
            elif line.startswith('> '):
                content.append([MessageBuilder.build_text_element(f"┃ {line[2:]}", style=["italic"])])
            # 普通文本
            else:
                # 处理粗体 **text**
                parts = re.split(r'\*\*(.*?)\*\*', line)
                line_content = []
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # 粗体部分
                        line_content.append(MessageBuilder.build_text_element(part, style=["bold"]))
                    else:
                        line_content.append(MessageBuilder.build_text_element(part))
                content.append(line_content)
        
        return MessageBuilder.build_rich_text_content("", content)


class MessageHandler:
    """消息处理器"""
    
    def __init__(self, bot):
        self.bot = bot
        self.command_handlers: Dict[str, Any] = {}
        self.keyword_handlers: List[tuple] = []
    
    def register_command(self, command: str, handler, description: str = ""):
        """注册命令处理器"""
        self.command_handlers[command] = {
            "handler": handler,
            "description": description
        }
    
    def register_keyword(self, keyword: str, handler, match_type: str = "contains"):
        """
        注册关键词处理器
        
        Args:
            keyword: 关键词
            handler: 处理函数
            match_type: 匹配类型 (contains, equals, regex)
        """
        self.keyword_handlers.append((keyword, handler, match_type))
    
    async def handle_message(self, message: Message) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = message.get_text_content().strip()
        
        # 处理命令
        if text.startswith('/') or text.startswith('!'):
            parts = text[1:].split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command in self.command_handlers:
                handler = self.command_handlers[command]["handler"]
                if asyncio.iscoroutinefunction(handler):
                    return await handler(message, args)
                else:
                    return handler(message, args)
        
        # 处理关键词
        for keyword, handler, match_type in self.keyword_handlers:
            matched = False
            if match_type == "contains" and keyword in text:
                matched = True
            elif match_type == "equals" and keyword == text:
                matched = True
            elif match_type == "regex" and re.search(keyword, text):
                matched = True
            
            if matched:
                if asyncio.iscoroutinefunction(handler):
                    return await handler(message)
                else:
                    return handler(message)
        
        return None
    
    async def send_text_reply(
        self, 
        message: Message, 
        text: str, 
        at_users: Optional[List[str]] = None,
        at_all: bool = False
    ) -> Dict[str, Any]:
        """发送文本回复"""
        content = MessageBuilder.build_text_message(text, at_users, at_all)
        
        if message.chat_type == "p2p":
            # 私聊直接发送
            return await self.bot.send_message(
                receive_id=message.sender.open_id,
                content=content,
                msg_type="text",
                receive_id_type="open_id"
            )
        else:
            # 群聊回复原消息
            return await self.bot.reply_message(
                message_id=message.message_id,
                content=content,
                msg_type="text"
            )
    
    async def send_card_reply(self, message: Message, card: Dict[str, Any]) -> Dict[str, Any]:
        """发送卡片回复"""
        if message.chat_type == "p2p":
            return await self.bot.send_interactive_card(
                receive_id=message.sender.open_id,
                card=card,
                receive_id_type="open_id"
            )
        else:
            return await self.bot.reply_message(
                message_id=message.message_id,
                content=card,
                msg_type="interactive"
            )


import asyncio
