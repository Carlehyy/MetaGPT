"""
MetaGPT群聊讨论系统 - 飞书机器人集成模块
======================================
定义飞书机器人相关类
"""

from typing import List, Set, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hmac
import hashlib
import base64

from architecture.message import Message, DiscussionMessage, SystemMessage
from architecture.base import FeishuAPIException


class FeishuMessageType(Enum):
    """飞书消息类型"""
    TEXT = "text"
    POST = "post"
    IMAGE = "image"
    INTERACTIVE = "interactive"
    SHARE_CHAT = "share_chat"


@dataclass
class FeishuMessage:
    """飞书消息"""
    msg_type: FeishuMessageType
    content: Dict[str, Any]
    receive_id: Optional[str] = None
    mentions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "msg_type": self.msg_type.value,
            "content": json.dumps(self.content),
            "receive_id": self.receive_id
        }


@dataclass
class FeishuEvent:
    """飞书事件"""
    event_type: str
    event_data: Dict[str, Any]
    timestamp: str
    token: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeishuEvent':
        """从字典创建事件"""
        return cls(
            event_type=data.get("event_type", ""),
            event_data=data.get("event", {}),
            timestamp=data.get("timestamp", ""),
            token=data.get("token", "")
        )


class FeishuBot:
    """
    飞书机器人类
    
    处理飞书消息的收发和事件处理
    """
    
    def __init__(self, app_id: str, app_secret: str, 
                 webhook_url: Optional[str] = None,
                 encrypt_key: Optional[str] = None,
                 verification_token: Optional[str] = None):
        """
        初始化飞书机器人
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            webhook_url: Webhook地址
            encrypt_key: 加密密钥
            verification_token: 验证Token
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.webhook_url = webhook_url
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token
        
        self._access_token: Optional[str] = None
        self._token_expire_time: Optional[datetime] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._command_handlers: Dict[str, Callable] = {}
        
        # 注册默认命令处理器
        self._register_default_commands()
    
    def _register_default_commands(self) -> None:
        """注册默认命令处理器"""
        self.register_command("/start", self._handle_start_command)
        self.register_command("/status", self._handle_status_command)
        self.register_command("/help", self._handle_help_command)
    
    def _handle_start_command(self, params: str, user_id: str) -> str:
        """处理/start命令"""
        return "开始新的讨论。请提供项目需求。"
    
    def _handle_status_command(self, params: str, user_id: str) -> str:
        """处理/status命令"""
        return "当前状态：等待开始"
    
    def _handle_help_command(self, params: str, user_id: str) -> str:
        """处理/help命令"""
        help_text = """
可用命令：
/start - 开始新讨论
/status - 查看当前状态
/next - 进入下一阶段（老板专用）
/reset - 重置当前阶段（老板专用）
/boss - 请求老板介入
/help - 显示帮助
        """
        return help_text
    
    def register_event_handler(self, event_type: str, 
                                handler: Callable) -> None:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def register_command(self, command: str, 
                         handler: Callable[[str, str], str]) -> None:
        """
        注册命令处理器
        
        Args:
            command: 命令名称
            handler: 处理函数，接收参数和用户ID，返回响应文本
        """
        self._command_handlers[command] = handler
    
    def _get_access_token(self) -> str:
        """
        获取访问令牌
        
        Returns:
            访问令牌
        """
        # 检查令牌是否过期
        if self._access_token and self._token_expire_time:
            if datetime.now() < self._token_expire_time:
                return self._access_token
        
        # 实际实现中应调用飞书API获取令牌
        # 这里返回模拟值
        self._access_token = "mock_access_token"
        self._token_expire_time = datetime.now()
        return self._access_token
    
    def send_text_message(self, text: str, receive_id: Optional[str] = None,
                          mentions: Optional[List[str]] = None) -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息文本
            receive_id: 接收者ID
            mentions: @的用户列表
            
        Returns:
            是否发送成功
        """
        content = {"text": text}
        
        # 添加@信息
        if mentions:
            at_list = []
            for mention in mentions:
                at_list.append({"tag": "at", "user_id": mention})
            content["text"] = " ".join([f"@{m}" for m in mentions]) + " " + text
        
        message = FeishuMessage(
            msg_type=FeishuMessageType.TEXT,
            content=content,
            receive_id=receive_id,
            mentions=mentions or []
        )
        
        return self._send_message(message)
    
    def send_interactive_message(self, card: Dict[str, Any],
                                  receive_id: Optional[str] = None) -> bool:
        """
        发送交互式卡片消息
        
        Args:
            card: 卡片内容
            receive_id: 接收者ID
            
        Returns:
            是否发送成功
        """
        message = FeishuMessage(
            msg_type=FeishuMessageType.INTERACTIVE,
            content=card,
            receive_id=receive_id
        )
        
        return self._send_message(message)
    
    def send_discussion_message(self, message: DiscussionMessage,
                                 receive_id: Optional[str] = None) -> bool:
        """
        发送讨论消息
        
        Args:
            message: 讨论消息
            receive_id: 接收者ID
            
        Returns:
            是否发送成功
        """
        # 构建卡片消息
        card = self._build_discussion_card(message)
        return self.send_interactive_message(card, receive_id)
    
    def _build_discussion_card(self, message: DiscussionMessage) -> Dict[str, Any]:
        """
        构建讨论消息卡片
        
        Args:
            message: 讨论消息
            
        Returns:
            卡片内容
        """
        header = {
            "title": {
                "tag": "plain_text",
                "content": f"阶段 {message.phase} - 第{message.round_num}轮"
            },
            "template": "blue"
        }
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{message.sender}**: {message.content}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"动作: {message.action}"
                }
            }
        ]
        
        return {
            "config": {"wide_screen_mode": True},
            "header": header,
            "elements": elements
        }
    
    def _send_message(self, message: FeishuMessage) -> bool:
        """
        发送消息到飞书
        
        Args:
            message: 飞书消息
            
        Returns:
            是否发送成功
        """
        # 实际实现中应调用飞书API
        # 这里模拟发送成功
        print(f"[FeishuBot] Sending message: {message.to_dict()}")
        return True
    
    def receive_message(self, event_data: Dict[str, Any]) -> Optional[Message]:
        """
        接收消息
        
        Args:
            event_data: 事件数据
            
        Returns:
            解析后的消息
        """
        event = FeishuEvent.from_dict(event_data)
        
        # 处理URL验证
        if event.event_type == "url_verification":
            return None
        
        # 处理消息事件
        if event.event_type == "im.message.receive_v1":
            message_data = event.event_data.get("message", {})
            content = json.loads(message_data.get("content", "{}"))
            
            # 检查是否是命令
            text = content.get("text", "")
            if text.startswith("/"):
                return self._handle_command(text, event)
            
            # 转换为内部消息格式
            return DiscussionMessage(
                content=text,
                sender=message_data.get("sender", {}).get("sender_id", {}).get("open_id", ""),
                phase="",  # 需要外部设置
                round_num=0  # 需要外部设置
            )
        
        return None
    
    def _handle_command(self, text: str, event: FeishuEvent) -> Optional[Message]:
        """
        处理命令
        
        Args:
            text: 命令文本
            event: 飞书事件
            
        Returns:
            响应消息
        """
        parts = text.split(maxsplit=1)
        command = parts[0]
        params = parts[1] if len(parts) > 1 else ""
        
        user_id = event.event_data.get("sender", {}).get("sender_id", {}).get("open_id", "")
        
        if command in self._command_handlers:
            response = self._command_handlers[command](params, user_id)
            return SystemMessage(
                content=response,
                sender="system",
                event_type="command_response"
            )
        
        return SystemMessage(
            content=f"未知命令: {command}，输入 /help 查看可用命令",
            sender="system",
            event_type="command_response"
        )
    
    def verify_signature(self, timestamp: str, nonce: str, 
                         signature: str, body: str) -> bool:
        """
        验证请求签名
        
        Args:
            timestamp: 时间戳
            nonce: 随机数
            signature: 签名
            body: 请求体
            
        Returns:
            签名是否有效
        """
        if not self.encrypt_key:
            return True
        
        # 构建签名字符串
        sign_str = f"{timestamp}{nonce}{self.encrypt_key}{body}"
        
        # 计算签名
        computed_signature = base64.b64encode(
            hmac.new(
                self.encrypt_key.encode(),
                sign_str.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return computed_signature == signature
    
    def decrypt_message(self, encrypt_data: str) -> Dict[str, Any]:
        """
        解密消息
        
        Args:
            encrypt_data: 加密数据
            
        Returns:
            解密后的数据
        """
        # 实际实现中应使用飞书提供的解密算法
        # 这里返回模拟数据
        return json.loads(encrypt_data)


class FeishuBotAdapter:
    """
    飞书机器人适配器
    
    将飞书消息与内部消息格式进行转换
    """
    
    def __init__(self, bot: FeishuBot):
        self.bot = bot
        self._role_mapping: Dict[str, str] = {}  # feishu_user_id -> role_id
    
    def register_role_mapping(self, feishu_user_id: str, role_id: str) -> None:
        """
        注册用户到角色的映射
        
        Args:
            feishu_user_id: 飞书用户ID
            role_id: 角色ID
        """
        self._role_mapping[feishu_user_id] = role_id
    
    def convert_to_internal_message(self, feishu_msg: Dict[str, Any]) -> Optional[Message]:
        """
        将飞书消息转换为内部消息
        
        Args:
            feishu_msg: 飞书消息
            
        Returns:
            内部消息
        """
        sender_id = feishu_msg.get("sender", "")
        role_id = self._role_mapping.get(sender_id, sender_id)
        
        content = feishu_msg.get("content", {})
        text = content.get("text", "")
        
        return DiscussionMessage(
            content=text,
            sender=role_id
        )
    
    def convert_to_feishu_message(self, message: Message) -> FeishuMessage:
        """
        将内部消息转换为飞书消息
        
        Args:
            message: 内部消息
            
        Returns:
            飞书消息
        """
        if isinstance(message, DiscussionMessage):
            card = self._build_discussion_card(message)
            return FeishuMessage(
                msg_type=FeishuMessageType.INTERACTIVE,
                content=card
            )
        
        return FeishuMessage(
            msg_type=FeishuMessageType.TEXT,
            content={"text": message.content}
        )
    
    def _build_discussion_card(self, message: DiscussionMessage) -> Dict[str, Any]:
        """构建讨论卡片"""
        # 根据动作类型设置颜色
        template_color = "blue"
        if message.action == "agree":
            template_color = "green"
        elif message.action == "disagree":
            template_color = "red"
        elif message.action == "pass":
            template_color = "grey"
        
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{message.sender} - {message.action}"
                },
                "template": template_color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message.content
                    }
                }
            ]
        }
