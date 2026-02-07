#!/usr/bin/env python3
"""
飞书机器人主类 - 提供消息收发、群聊管理功能
"""
import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, Optional, Callable, Any
import httpx

logger = logging.getLogger(__name__)


class FeishuConfig:
    """飞书配置"""
    def __init__(self, app_id: str, app_secret: str, verification_token: Optional[str] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.verification_token = verification_token
        self.base_url = "https://open.feishu.cn/open-apis"
        self._access_token = None
        self._token_expire_time = 0


class FeishuBot:
    """飞书机器人主类"""
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self.message_handler = None
        self.event_callbacks: Dict[str, Callable] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_access_token(self) -> str:
        """获取tenant_access_token"""
        if self.config._access_token and time.time() < self.config._token_expire_time:
            return self.config._access_token
            
        url = f"{self.config.base_url}/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.config.app_id,
            "app_secret": self.config.app_secret
        }
        
        try:
            response = await self.client.post(url, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.config._access_token = result["tenant_access_token"]
                expires_in = result.get("expire", 7200)
                self.config._token_expire_time = time.time() + expires_in - 300
                return self.config._access_token
            else:
                logger.error(f"获取access_token失败: {result}")
                raise Exception(f"获取access_token失败: {result}")
        except Exception as e:
            logger.error(f"获取access_token异常: {e}")
            raise
    
    async def send_text_message(self, receive_id: str, content: str, msg_type: str = "text") -> Dict:
        """发送文本消息"""
        token = await self.get_access_token()
        url = f"{self.config.base_url}/im/v1/messages"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "receive_id": receive_id,
            "receive_id_type": "chat_id",
            "msg_type": msg_type,
            "content": json.dumps({"text": content}) if msg_type == "text" else content
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"消息发送成功")
                return result
            else:
                logger.error(f"消息发送失败: {result}")
                return result
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return {"code": -1, "msg": str(e)}
    
    async def send_card_message(self, receive_id: str, card_content: Dict) -> Dict:
        """发送卡片消息"""
        token = await self.get_access_token()
        url = f"{self.config.base_url}/im/v1/messages"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "receive_id": receive_id,
            "receive_id_type": "chat_id",
            "msg_type": "interactive",
            "content": json.dumps(card_content)
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=data)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"发送卡片消息异常: {e}")
            return {"code": -1, "msg": str(e)}
    
    async def create_chat(self, name: str, description: str = "") -> Dict:
        """创建群聊"""
        token = await self.get_access_token()
        url = f"{self.config.base_url}/im/v1/chats"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": name,
            "description": description,
            "chat_mode": "group",
            "chat_type": "public"
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=data)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"创建群聊异常: {e}")
            return {"code": -1, "msg": str(e)}
    
    async def add_chat_members(self, chat_id: str, user_ids: list) -> Dict:
        """添加群成员"""
        token = await self.get_access_token()
        url = f"{self.config.base_url}/im/v1/chats/{chat_id}/members"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "member_list": [{"id": uid, "type": "user"} for uid in user_ids]
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=data)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"添加群成员异常: {e}")
            return {"code": -1, "msg": str(e)}
    
    async def get_chat_info(self, chat_id: str) -> Dict:
        """获取群聊信息"""
        token = await self.get_access_token()
        url = f"{self.config.base_url}/im/v1/chats/{chat_id}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = await self.client.get(url, headers=headers)
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"获取群聊信息异常: {e}")
            return {"code": -1, "msg": str(e)}
    
    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """验证飞书请求签名"""
        if not self.config.verification_token:
            return True
            
        bytes_to_hash = f"{timestamp}{nonce}{self.config.verification_token}{body}".encode('utf-8')
        hashed = hashlib.sha256(bytes_to_hash).hexdigest()
        return hashed == signature
    
    async def handle_webhook(self, data: Dict) -> Dict:
        """处理飞书Webhook事件"""
        event_type = data.get("header", {}).get("event_type")
        
        if event_type == "url_verification":
            challenge = data.get("challenge")
            return {"challenge": challenge}
        
        # 处理消息事件
        if event_type == "im.message.receive_v1":
            event_data = data.get("event", {})
            message = event_data.get("message", {})
            sender = event_data.get("sender", {})
            
            msg_info = {
                "message_id": message.get("message_id"),
                "chat_id": message.get("chat_id"),
                "sender_id": sender.get("sender_id", {}).get("user_id"),
                "msg_type": message.get("msg_type"),
                "content": json.loads(message.get("content", "{}")),
                "mentions": message.get("mentions", [])
            }
            
            if self.message_handler:
                await self.message_handler(msg_info)
        
        return {"code": 0}
    
    def register_message_handler(self, handler: Callable):
        """注册消息处理器"""
        self.message_handler = handler
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
