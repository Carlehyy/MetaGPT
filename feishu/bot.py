"""
飞书机器人主类
实现飞书机器人的核心功能，包括认证、消息接收和发送
"""

import json
import time
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from functools import wraps

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse


@dataclass
class FeishuConfig:
    """飞书配置类"""
    app_id: str
    app_secret: str
    verification_token: Optional[str] = None
    encrypt_key: Optional[str] = None
    webhook_url: Optional[str] = None
    
    # API 基础URL
    base_url: str = "https://open.feishu.cn/open-apis"
    
    # Token 缓存时间（秒）
    token_expire_buffer: int = 300


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class TokenManager:
    """Token管理器，处理access_token的获取和缓存"""
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self._tenant_access_token: Optional[str] = None
        self._token_expire_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def get_tenant_access_token(self) -> str:
        """获取租户访问令牌（带缓存）"""
        async with self._lock:
            # 检查token是否有效
            if (self._tenant_access_token and 
                self._token_expire_time and 
                datetime.now() < self._token_expire_time - timedelta(seconds=self.config.token_expire_buffer)):
                return self._tenant_access_token
            
            # 重新获取token
            url = f"{self.config.base_url}/auth/v3/tenant_access_token/internal"
            payload = {
                "app_id": self.config.app_id,
                "app_secret": self.config.app_secret
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"获取token失败: {data.get('msg')}")
                
                self._tenant_access_token = data["tenant_access_token"]
                expire_in = data.get("expire", 7200)
                self._token_expire_time = datetime.now() + timedelta(seconds=expire_in)
                
                return self._tenant_access_token
    
    def clear_token(self):
        """清除token缓存"""
        self._tenant_access_token = None
        self._token_expire_time = None


class FeishuBot:
    """飞书机器人类"""
    
    def __init__(self, config: FeishuConfig):
        self.config = config
        self.token_manager = TokenManager(config)
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._app: Optional[FastAPI] = None
    
    def create_app(self) -> FastAPI:
        """创建FastAPI应用用于接收Webhook"""
        self._app = FastAPI(title="Feishu Bot Webhook")
        
        @self._app.post("/webhook/feishu")
        async def webhook_handler(request: Request):
            """处理飞书Webhook回调"""
            body = await request.body()
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            
            # 处理URL验证挑战
            if "challenge" in data:
                return JSONResponse(content={"challenge": data["challenge"]})
            
            # 验证签名（如果配置了encrypt_key）
            if self.config.encrypt_key:
                signature = request.headers.get("X-Lark-Signature", "")
                if not self._verify_signature(body, signature):
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # 处理事件
            event_type = data.get("header", {}).get("event_type", "")
            event_data = data.get("event", {})
            
            # 异步处理事件
            asyncio.create_task(self._handle_event(event_type, event_data))
            
            return JSONResponse(content={"code": 0, "msg": "success"})
        
        @self._app.get("/health")
        async def health_check():
            """健康检查接口"""
            return JSONResponse(content={"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        return self._app
    
    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """验证飞书请求签名"""
        if not self.config.encrypt_key:
            return True
        
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.config.encrypt_key}\n{body.decode()}\n"
        expected_signature = base64.b64encode(
            hmac.new(
                self.config.encrypt_key.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def _handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """处理飞书事件"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                print(f"事件处理错误: {e}")
    
    def on_event(self, event_type: str):
        """事件装饰器"""
        def decorator(func: Callable):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator
    
    def on_message(self, msg_type: Optional[str] = None):
        """消息事件装饰器"""
        def decorator(func: Callable):
            event_type = "im.message.receive_v1"
            
            async def wrapper(event_data: Dict[str, Any]):
                message = event_data.get("message", {})
                current_msg_type = message.get("message_type", "")
                
                if msg_type is None or current_msg_type == msg_type:
                    await func(event_data)
            
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(wrapper)
            return func
        return decorator
    
    @retry_on_error(max_retries=3)
    async def send_message(
        self, 
        receive_id: str, 
        content: Dict[str, Any], 
        msg_type: str = "text",
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        发送消息
        
        Args:
            receive_id: 接收者ID
            content: 消息内容
            msg_type: 消息类型 (text, post, image, file, interactive, etc.)
            receive_id_type: 接收者ID类型 (open_id, user_id, union_id, email, chat_id)
        """
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/im/v1/messages"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {"receive_id_type": receive_id_type}
        
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content) if isinstance(content, dict) else content
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                params=params,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"发送消息失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def send_text_message(
        self, 
        receive_id: str, 
        text: str,
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """发送文本消息"""
        content = {"text": text}
        return await self.send_message(
            receive_id=receive_id,
            content=content,
            msg_type="text",
            receive_id_type=receive_id_type
        )
    
    async def send_rich_text(
        self, 
        receive_id: str, 
        title: str,
        content: List[List[Dict[str, Any]]],
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        发送富文本消息
        
        Args:
            receive_id: 接收者ID
            title: 消息标题
            content: 富文本内容，格式为 [[{"tag": "text", "text": "内容"}]]
            receive_id_type: 接收者ID类型
        """
        post_content = {
            "zh_cn": {
                "title": title,
                "content": content
            }
        }
        
        return await self.send_message(
            receive_id=receive_id,
            content=post_content,
            msg_type="post",
            receive_id_type=receive_id_type
        )
    
    async def send_interactive_card(
        self, 
        receive_id: str, 
        card: Dict[str, Any],
        receive_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """发送交互式卡片消息"""
        return await self.send_message(
            receive_id=receive_id,
            content=card,
            msg_type="interactive",
            receive_id_type=receive_id_type
        )
    
    async def reply_message(
        self, 
        message_id: str, 
        content: Dict[str, Any], 
        msg_type: str = "text"
    ) -> Dict[str, Any]:
        """回复消息"""
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/im/v1/messages/{message_id}/reply"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": json.dumps(content) if isinstance(content, dict) else content,
            "msg_type": msg_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"回复消息失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def edit_message(
        self, 
        message_id: str, 
        content: Dict[str, Any], 
        msg_type: str = "text"
    ) -> Dict[str, Any]:
        """编辑消息"""
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/im/v1/messages/{message_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": json.dumps(content) if isinstance(content, dict) else content,
            "msg_type": msg_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url, 
                headers=headers, 
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"编辑消息失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def delete_message(self, message_id: str) -> bool:
        """删除消息"""
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/im/v1/messages/{message_id}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url, 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("code") == 0
    
    async def get_message_info(self, message_id: str) -> Dict[str, Any]:
        """获取消息信息"""
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/im/v1/messages/{message_id}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取消息信息失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def get_user_info(self, user_id: str, user_id_type: str = "open_id") -> Dict[str, Any]:
        """获取用户信息"""
        token = await self.token_manager.get_tenant_access_token()
        
        url = f"{self.config.base_url}/contact/v3/users/{user_id}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        params = {"user_id_type": user_id_type}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取用户信息失败: {result.get('msg')}")
            
            return result.get("data", {})
