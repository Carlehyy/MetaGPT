"""
产品设计师角色 - UI/UX设计、设计稿输出

作为设计负责人，产品设计师负责：
- UI界面设计
- UX交互设计
- 设计规范制定
- 设计稿输出
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class ProductDesigner(BaseRole):
    """
    产品设计师角色
    
    职责：
    - UI界面设计
    - UX交互设计
    - 设计规范制定
    - 设计稿输出
    - 设计走查
    """
    
    def __init__(self, name: str = "产品设计师", **kwargs):
        """
        初始化产品设计师角色
        
        Args:
            name: 角色名称，默认为"产品设计师"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="产品设计师(UI/UX)",
            responsibilities=[
                "设计用户界面(UI)",
                "设计用户体验(UX)",
                "制定设计规范",
                "输出设计稿",
                "进行设计走查",
                "优化交互流程",
                "确保视觉一致性"
            ],
            expertise=[
                "用户界面设计",
                "用户体验设计",
                "交互设计",
                "视觉设计",
                "设计系统",
                "原型设计",
                "可用性测试",
                "设计工具(Figma/Sketch)"
            ],
            communication_style="""
注重细节、富有创意，善于用设计语言表达产品理念。
关注用户体验，能够从用户角度思考问题。
能够清晰地解释设计决策的理由。
""",
            decision_scope="""
设计相关的决策：
- 界面布局和视觉风格
- 交互流程和动效
- 设计规范和组件
- 用户体验优化

需要@老板的情况：
- 设计方案有重大变更
- 涉及品牌视觉调整
- 设计与需求有冲突
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.PRODUCT_DESIGNER.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 设计稿存储
        self.designs: List[Dict[str, Any]] = []
        # 设计规范
        self.design_systems: List[Dict[str, Any]] = []
    
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
            设计师的发言内容
        """
        prompt = self._build_participation_prompt(context, topic, previous_messages)
        response = await self.chat(prompt, context)
        return response
    
    def _build_participation_prompt(
        self,
        context: DiscussionContext,
        topic: str,
        previous_messages: List[Message]
    ) -> str:
        """构建参与讨论的提示"""
        prompt = f"""当前阶段: {context.phase}
讨论主题: {topic}

你作为产品设计师，需要从设计角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P3_UI_UX_DESIGN:
            prompt += """
请从以下角度进行设计：
1. 用户需求分析
2. 信息架构设计
3. 交互流程设计
4. 视觉设计方案
5. 响应式考虑
"""
        elif phase == Phase.P6_UI_ACCEPTANCE:
            prompt += """
请进行UI走查：
1. 视觉还原度检查
2. 交互一致性检查
3. 设计规范符合度
4. 问题记录和反馈
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        设计师在以下情况可以做出决策：
        1. UI/UX设计相关的决策
        2. 设计规范相关的决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.PRODUCT_DESIGNER)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def create_ui_design(
        self,
        context: DiscussionContext,
        prd_content: str
    ) -> Dict[str, Any]:
        """
        创建UI设计
        
        Args:
            context: 讨论上下文
            prd_content: PRD内容
            
        Returns:
            UI设计方案
        """
        prompt = f"""请根据以下PRD创建UI设计方案：

PRD内容:
{prd_content}

请包含：
1. 设计目标和原则
2. 色彩方案
3. 字体规范
4. 布局设计
5. 组件设计
6. 页面设计描述（包含关键页面）
7. 交互说明
8. 响应式设计考虑

请以Markdown格式输出UI设计方案。
"""
        
        response = await self.chat(prompt, context)
        
        design = {
            "content": response,
            "prd_content": prd_content,
            "phase": context.phase,
            "type": "ui_design"
        }
        self.designs.append(design)
        
        return design
    
    async def create_ux_design(
        self,
        context: DiscussionContext,
        user_flow_description: str
    ) -> Dict[str, Any]:
        """
        创建UX设计方案
        
        Args:
            context: 讨论上下文
            user_flow_description: 用户流程描述
            
        Returns:
            UX设计方案
        """
        prompt = f"""请根据以下用户流程创建UX设计方案：

用户流程描述:
{user_flow_description}

请包含：
1. 用户画像
2. 用户旅程地图
3. 信息架构
4. 交互流程图（文本描述）
5. 关键交互说明
6. 可用性考虑
7. 异常流程处理

请以Markdown格式输出UX设计方案。
"""
        
        response = await self.chat(prompt, context)
        
        design = {
            "content": response,
            "user_flow": user_flow_description,
            "phase": context.phase,
            "type": "ux_design"
        }
        self.designs.append(design)
        
        return design
    
    async def create_design_system(
        self,
        context: DiscussionContext,
        brand_guidelines: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建设计系统
        
        Args:
            context: 讨论上下文
            brand_guidelines: 品牌规范
            
        Returns:
            设计系统
        """
        prompt = """请创建一套设计系统：

"""
        if brand_guidelines:
            prompt += f"品牌规范:\n{brand_guidelines}\n\n"
        
        prompt += """设计系统应包含：
1. 设计原则
2. 色彩系统
3. 字体系统
4. 图标系统
5. 间距系统
6. 组件库（按钮、输入框、卡片等）
7. 布局规范
8. 设计模式

请以Markdown格式输出设计系统文档。
"""
        
        response = await self.chat(prompt, context)
        
        design_system = {
            "content": response,
            "brand_guidelines": brand_guidelines,
            "phase": context.phase
        }
        self.design_systems.append(design_system)
        
        return design_system
    
    async def review_ui_implementation(
        self,
        context: DiscussionContext,
        implementation_description: str
    ) -> Dict[str, Any]:
        """
        审核UI实现
        
        Args:
            context: 讨论上下文
            implementation_description: 实现描述
            
        Returns:
            审核结果
        """
        prompt = f"""请审核以下UI实现：

实现描述:
{implementation_description}

请从以下维度进行审核：
1. 视觉还原度
2. 交互一致性
3. 设计规范符合度
4. 响应式适配
5. 性能考虑

请以JSON格式输出审核结果：
{{
    "approved": true/false,
    "score": "评分(1-10)",
    "comments": "审核意见",
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "implementation": implementation_description,
            "review_result": response,
            "phase": context.phase
        }
    
    def get_designs(self) -> List[Dict[str, Any]]:
        """获取所有设计"""
        return self.designs.copy()
    
    def get_design_systems(self) -> List[Dict[str, Any]]:
        """获取所有设计系统"""
        return self.design_systems.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.PRODUCT_DESIGNER.value, ProductDesigner)


if __name__ == "__main__":
    import asyncio
    
    async def test_designer():
        designer = ProductDesigner()
        print(f"创建角色: {designer}")
        print(f"系统提示词长度: {len(designer.system_prompt)}")
    
    asyncio.run(test_designer())
