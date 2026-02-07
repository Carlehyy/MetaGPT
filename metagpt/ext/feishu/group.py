"""
群聊管理模块
提供群聊的创建、管理、成员操作等功能
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx


class ChatType(Enum):
    """群聊类型"""
    PRIVATE = "private"  # 私有群
    PUBLIC = "public"    # 公开群


class ChatMode(Enum):
    """群聊模式"""
    NORMAL = "normal"    # 普通群
    THREAD = "thread"    # 话题群


@dataclass
class ChatInfo:
    """群聊信息"""
    chat_id: str
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    owner_id: Optional[str] = None
    chat_type: Optional[str] = None
    chat_mode: Optional[str] = None
    member_count: int = 0
    create_time: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatInfo":
        """从字典创建群聊信息对象"""
        return cls(
            chat_id=data.get("chat_id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            avatar=data.get("avatar"),
            owner_id=data.get("owner_id"),
            chat_type=data.get("chat_type"),
            chat_mode=data.get("chat_mode"),
            member_count=data.get("member_count", 0),
            create_time=data.get("create_time")
        )


@dataclass
class MemberInfo:
    """成员信息"""
    member_id: str
    member_id_type: str
    name: Optional[str] = None
    tenant_key: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemberInfo":
        """从字典创建成员信息对象"""
        return cls(
            member_id=data.get("member_id", ""),
            member_id_type=data.get("member_id_type", "open_id"),
            name=data.get("name"),
            tenant_key=data.get("tenant_key")
        )


class GroupManager:
    """群聊管理器"""
    
    def __init__(self, bot):
        self.bot = bot
        self.base_url = bot.config.base_url
    
    async def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        token = await self.bot.token_manager.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def create_chat(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        user_id_list: Optional[List[str]] = None,
        bot_id_list: Optional[List[str]] = None,
        chat_type: ChatType = ChatType.PRIVATE,
        chat_mode: ChatMode = ChatMode.NORMAL,
        avatar: Optional[str] = None,
        i18n_names: Optional[Dict[str, str]] = None
    ) -> ChatInfo:
        """
        创建群聊
        
        Args:
            name: 群名称
            description: 群描述
            owner_id: 群主ID
            user_id_list: 初始成员用户ID列表
            bot_id_list: 初始机器人ID列表
            chat_type: 群类型
            chat_mode: 群模式
            avatar: 群头像key
            i18n_names: 多语言名称
        
        Returns:
            创建的群聊信息
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats"
        
        payload: Dict[str, Any] = {
            "name": name,
            "chat_type": chat_type.value,
            "chat_mode": chat_mode.value
        }
        
        if description:
            payload["description"] = description
        if owner_id:
            payload["owner_id"] = owner_id
        if user_id_list:
            payload["user_id_list"] = user_id_list
        if bot_id_list:
            payload["bot_id_list"] = bot_id_list
        if avatar:
            payload["avatar"] = avatar
        if i18n_names:
            payload["i18n_names"] = i18n_names
        
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
                raise Exception(f"创建群聊失败: {result.get('msg')}")
            
            return ChatInfo.from_dict(result.get("data", {}))
    
    async def get_chat_info(self, chat_id: str) -> ChatInfo:
        """
        获取群聊信息
        
        Args:
            chat_id: 群聊ID
        
        Returns:
            群聊信息
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取群聊信息失败: {result.get('msg')}")
            
            return ChatInfo.from_dict(result.get("data", {}))
    
    async def update_chat(
        self,
        chat_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        avatar: Optional[str] = None,
        add_user_permission: Optional[str] = None,
        share_permission: Optional[str] = None,
        at_all_permission: Optional[str] = None,
        edit_permission: Optional[str] = None
    ) -> ChatInfo:
        """
        更新群聊信息
        
        Args:
            chat_id: 群聊ID
            name: 新名称
            description: 新描述
            owner_id: 新群主ID
            avatar: 新头像
            add_user_permission: 添加成员权限
            share_permission: 分享权限
            at_all_permission: @所有人权限
            edit_permission: 编辑权限
        
        Returns:
            更新后的群聊信息
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}"
        
        payload: Dict[str, Any] = {}
        
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if owner_id:
            payload["owner_id"] = owner_id
        if avatar:
            payload["avatar"] = avatar
        if add_user_permission:
            payload["add_user_permission"] = add_user_permission
        if share_permission:
            payload["share_permission"] = share_permission
        if at_all_permission:
            payload["at_all_permission"] = at_all_permission
        if edit_permission:
            payload["edit_permission"] = edit_permission
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"更新群聊失败: {result.get('msg')}")
            
            return ChatInfo.from_dict(result.get("data", {}))
    
    async def delete_chat(self, chat_id: str) -> bool:
        """
        解散群聊
        
        Args:
            chat_id: 群聊ID
        
        Returns:
            是否成功
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("code") == 0
    
    async def get_chat_members(
        self,
        chat_id: str,
        member_id_type: str = "open_id",
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取群成员列表
        
        Args:
            chat_id: 群聊ID
            member_id_type: 成员ID类型
            page_size: 每页数量
            page_token: 分页token
        
        Returns:
            成员列表和分页信息
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"
        
        params: Dict[str, Any] = {
            "member_id_type": member_id_type,
            "page_size": page_size
        }
        if page_token:
            params["page_token"] = page_token
        
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
                raise Exception(f"获取群成员失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def add_chat_members(
        self,
        chat_id: str,
        user_id_list: Optional[List[str]] = None,
        bot_id_list: Optional[List[str]] = None,
        member_id_type: str = "open_id",
        succeed_type: int = 0
    ) -> Dict[str, Any]:
        """
        添加群成员
        
        Args:
            chat_id: 群聊ID
            user_id_list: 用户ID列表
            bot_id_list: 机器人ID列表
            member_id_type: 成员ID类型
            succeed_type: 成功类型 (0-部分成功, 1-全部成功或失败)
        
        Returns:
            操作结果
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"
        
        payload: Dict[str, Any] = {
            "member_id_type": member_id_type,
            "succeed_type": succeed_type
        }
        
        if user_id_list:
            payload["user_id_list"] = user_id_list
        if bot_id_list:
            payload["bot_id_list"] = bot_id_list
        
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
                raise Exception(f"添加群成员失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def remove_chat_members(
        self,
        chat_id: str,
        user_id_list: Optional[List[str]] = None,
        bot_id_list: Optional[List[str]] = None,
        member_id_type: str = "open_id"
    ) -> Dict[str, Any]:
        """
        移除群成员
        
        Args:
            chat_id: 群聊ID
            user_id_list: 用户ID列表
            bot_id_list: 机器人ID列表
            member_id_type: 成员ID类型
        
        Returns:
            操作结果
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"
        
        payload: Dict[str, Any] = {
            "member_id_type": member_id_type
        }
        
        if user_id_list:
            payload["user_id_list"] = user_id_list
        if bot_id_list:
            payload["bot_id_list"] = bot_id_list
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"移除群成员失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def get_chat_list(
        self,
        user_id_type: str = "open_id",
        sort_type: str = "ByCreateTimeDesc",
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取机器人所在的群聊列表
        
        Args:
            user_id_type: 用户ID类型
            sort_type: 排序方式
            page_size: 每页数量
            page_token: 分页token
        
        Returns:
            群聊列表
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats"
        
        params: Dict[str, Any] = {
            "user_id_type": user_id_type,
            "sort_type": sort_type,
            "page_size": page_size
        }
        if page_token:
            params["page_token"] = page_token
        
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
                raise Exception(f"获取群聊列表失败: {result.get('msg')}")
            
            return result.get("data", {})
    
    async def is_user_in_chat(self, chat_id: str, user_id: str) -> bool:
        """
        检查用户是否在群聊中
        
        Args:
            chat_id: 群聊ID
            user_id: 用户ID
        
        Returns:
            是否在群中
        """
        try:
            members_data = await self.get_chat_members(chat_id, page_size=500)
            members = members_data.get("items", [])
            
            for member in members:
                if member.get("member_id") == user_id:
                    return True
            
            return False
        except Exception:
            return False
    
    async def get_chat_admins(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        获取群管理员列表
        
        Args:
            chat_id: 群聊ID
        
        Returns:
            管理员列表
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/admins"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") != 0:
                raise Exception(f"获取群管理员失败: {result.get('msg')}")
            
            return result.get("data", {}).get("items", [])
    
    async def send_chat_announcement(
        self,
        chat_id: str,
        content: str,
        pin: bool = False
    ) -> Dict[str, Any]:
        """
        发送群公告
        
        Args:
            chat_id: 群聊ID
            content: 公告内容
            pin: 是否置顶
        
        Returns:
            发送结果
        """
        # 使用富文本格式发送公告
        announcement_content = {
            "zh_cn": {
                "title": "📢 群公告",
                "content": [
                    [{"tag": "text", "text": content}]
                ]
            }
        }
        
        return await self.bot.send_message(
            receive_id=chat_id,
            content=announcement_content,
            msg_type="post",
            receive_id_type="chat_id"
        )
    
    async def invite_user_by_share_link(
        self,
        chat_id: str,
        link_type: str = "permanent"
    ) -> str:
        """
        获取群分享链接
        
        Args:
            chat_id: 群聊ID
            link_type: 链接类型 (permanent, temporary)
        
        Returns:
            分享链接
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/link"
        
        params = {"link_type": link_type}
        
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
                raise Exception(f"获取分享链接失败: {result.get('msg')}")
            
            return result.get("data", {}).get("link", "")
