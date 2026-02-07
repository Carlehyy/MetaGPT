"""
角色基类模块 - 定义所有AI角色的通用属性和方法

集成智谱GLM-4 API进行智能对话
"""

import os
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 智谱GLM-4配置
GLM4_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
GLM4_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM4_MODEL = "glm-4"


@dataclass
class Message:
    """消息数据类"""
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    sender: Optional[str] = None  # 发送者角色名称
    
    def to_dict(self) -> Dict[str, str]:
        """转换为OpenAI格式"""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class DiscussionContext:
    """讨论上下文"""
    phase: str
    topic: str
    messages: List[Message] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    consensus_reached: bool = False
    consensus_content: Optional[str] = None
    require_boss_decision: bool = False
    
    def add_message(self, message: Message):
        """添加消息到上下文"""
        self.messages.append(message)
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取最近的消息历史"""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [m.to_dict() for m in recent]


class BaseRole(ABC):
    """
    角色基类
    
    所有AI角色的抽象基类，定义通用属性和方法
    """
    
    def __init__(
        self,
        name: str,
        role_type: str,
        system_prompt: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化角色
        
        Args:
            name: 角色名称
            role_type: 角色类型标识
            system_prompt: 系统提示词，定义角色的行为和专业领域
            api_key: API密钥，默认使用全局配置
            base_url: API基础URL，默认使用全局配置
            model: 模型名称，默认使用全局配置
        """
        self.name = name
        self.role_type = role_type
        self.system_prompt = system_prompt
        self.api_key = api_key or GLM4_API_KEY
        self.base_url = base_url or GLM4_BASE_URL
        self.model = model or GLM4_MODEL
        
        # 消息历史
        self.message_history: List[Message] = []
        
        # 当前讨论上下文
        self.current_context: Optional[DiscussionContext] = None
        
        # LLM客户端（延迟初始化）
        self._client = None
        
        logger.info(f"角色 {name} ({role_type}) 已初始化")
    
    @property
    def client(self):
        """获取或创建LLM客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                logger.error("请先安装openai库: pip install openai")
                raise
        return self._client
    
    def set_context(self, context: DiscussionContext):
        """设置当前讨论上下文"""
        self.current_context = context
    
    def clear_context(self):
        """清除讨论上下文"""
        self.current_context = None
    
    async def chat(
        self,
        message: str,
        context: Optional[DiscussionContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        与LLM进行对话
        
        Args:
            message: 用户消息
            context: 可选的讨论上下文
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            LLM的回复内容
        """
        messages = self._build_messages(message, context)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                # 流式输出处理
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                return content
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return f"[错误] LLM调用失败: {str(e)}"
    
    async def chat_stream(
        self,
        message: str,
        context: Optional[DiscussionContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        流式对话
        
        Args:
            message: 用户消息
            context: 可选的讨论上下文
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            流式输出的内容片段
        """
        messages = self._build_messages(message, context)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}")
            yield f"[错误] LLM调用失败: {str(e)}"
    
    def _build_messages(
        self,
        user_message: str,
        context: Optional[DiscussionContext] = None
    ) -> List[Dict[str, str]]:
        """
        构建消息列表
        
        Args:
            user_message: 用户消息
            context: 讨论上下文
            
        Returns:
            消息列表
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加上下文历史
        if context:
            messages.extend(context.get_history(limit=10))
        elif self.current_context:
            messages.extend(self.current_context.get_history(limit=10))
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    @abstractmethod
    async def participate(
        self,
        context: DiscussionContext,
        topic: str,
        previous_messages: List[Message]
    ) -> str:
        """
        参与讨论
        
        Args:
            context: 讨论上下文
            topic: 讨论主题
            previous_messages: 之前的消息列表
            
        Returns:
            角色的发言内容
        """
        pass
    
    @abstractmethod
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        pass
    
    def should_mention_boss(self, context: DiscussionContext) -> bool:
        """
        判断是否需要@老板
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否需要@老板
        """
        from .role_matrix import should_notify_boss, Phase
        
        try:
            phase = Phase(context.phase)
            from .role_matrix import Role
            role = Role(self.role_type)
            return should_notify_boss(phase, role)
        except (ValueError, KeyError):
            return False
    
    def add_to_history(self, message: Message):
        """添加消息到历史记录"""
        self.message_history.append(message)
        # 限制历史记录长度
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
    
    def get_history(self, limit: int = 20) -> List[Message]:
        """获取历史记录"""
        return self.message_history[-limit:] if len(self.message_history) > limit else self.message_history
    
    def clear_history(self):
        """清除历史记录"""
        self.message_history.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "name": self.name,
            "role_type": self.role_type,
            "system_prompt_length": len(self.system_prompt),
            "history_count": len(self.message_history)
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', role_type='{self.role_type}')"


class RoleFactory:
    """角色工厂类"""
    
    _roles: Dict[str, type] = {}
    
    @classmethod
    def register(cls, role_type: str, role_class: type):
        """注册角色类"""
        cls._roles[role_type] = role_class
        logger.info(f"注册角色类型: {role_type}")
    
    @classmethod
    def create(cls, role_type: str, **kwargs) -> BaseRole:
        """创建角色实例"""
        if role_type not in cls._roles:
            raise ValueError(f"未知的角色类型: {role_type}")
        return cls._roles[role_type](**kwargs)
    
    @classmethod
    def list_roles(cls) -> List[str]:
        """列出所有注册的角色类型"""
        return list(cls._roles.keys())


# 工具函数
def create_system_prompt(
    role_name: str,
    responsibilities: List[str],
    expertise: List[str],
    communication_style: str,
    decision_scope: str
) -> str:
    """
    创建系统提示词
    
    Args:
        role_name: 角色名称
        responsibilities: 职责列表
        expertise: 专业领域列表
        communication_style: 沟通风格
        decision_scope: 决策范围
        
    Returns:
        系统提示词
    """
    prompt = f"""你是{role_name}，一家AI虚拟软件公司的核心成员。

## 你的职责
"""
    for resp in responsibilities:
        prompt += f"- {resp}\n"
    
    prompt += "\n## 你的专业领域\n"
    for exp in expertise:
        prompt += f"- {exp}\n"
    
    prompt += f"""
## 沟通风格
{communication_style}

## 决策范围
{decision_scope}

## 协作规则
1. 在讨论中保持专业、客观的态度
2. 基于你的专业领域提供有价值的意见
3. 尊重其他角色的专业判断
4. 在需要时主动提出问题和建议
5. 如果无法达成共识，可以@老板进行决策

## 输出格式
- 直接给出你的观点或建议
- 必要时说明理由
- 如果需要@老板，请在回复中明确说明"""
    
    return prompt


if __name__ == "__main__":
    # 测试系统提示词生成
    prompt = create_system_prompt(
        role_name="产品经理",
        responsibilities=["需求分析", "PRD编写", "需求评审"],
        expertise=["用户研究", "产品规划", "需求管理"],
        communication_style="清晰、有条理，善于从用户角度思考",
        decision_scope="产品需求相关的决策"
    )
    print(prompt)
