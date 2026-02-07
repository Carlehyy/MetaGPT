"""
产品经理角色 - 需求分析、PRD编写、需求评审

作为产品的核心负责人，产品经理负责：
- 用户需求分析和调研
- 产品需求文档(PRD)编写
- 需求评审和确认
- UI/UX设计的验收
- UAT测试的验收
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class ProductManager(BaseRole):
    """
    产品经理角色
    
    职责：
    - 需求分析：分析用户需求，理解业务目标
    - PRD编写：编写产品需求文档
    - 需求评审：组织和参与需求评审
    - UI验收：验收UI/UX设计
    - UAT验收：进行用户验收测试
    """
    
    def __init__(self, name: str = "产品经理", **kwargs):
        """
        初始化产品经理角色
        
        Args:
            name: 角色名称，默认为"产品经理"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="产品经理(PM)",
            responsibilities=[
                "深入分析用户需求和业务目标",
                "编写清晰完整的产品需求文档(PRD)",
                "组织和参与需求评审会议",
                "验收UI/UX设计稿",
                "进行用户验收测试(UAT)",
                "协调各方资源推进项目",
                "跟踪产品上线后的效果"
            ],
            expertise=[
                "用户研究和需求分析",
                "产品规划和路线图制定",
                "PRD文档编写",
                "用户体验设计理解",
                "数据分析和效果评估",
                "敏捷开发流程"
            ],
            communication_style="""
清晰、有条理，善于从用户角度思考问题。
能够用通俗易懂的语言解释复杂的产品逻辑。
注重细节，对需求有清晰的把控。
""",
            decision_scope="""
产品需求相关的决策：
- 功能需求的确定和优先级排序
- 用户体验方案的确认
- 产品逻辑的设计
- 验收标准的制定

需要@老板的情况：
- 涉及重大产品方向调整
- 资源需求超出预算
- 与其他部门有重大冲突
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.PRODUCT_MANAGER.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # PRD文档存储
        self.prd_documents: List[Dict[str, Any]] = []
        # 需求列表
        self.requirements: List[Dict[str, Any]] = []
    
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
            产品经理的发言内容
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

你作为产品经理，需要从产品角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P1_REQUIREMENT_ANALYSIS:
            prompt += """
请从以下角度分析：
1. 用户需求的合理性
2. 业务价值的评估
3. 功能范围的界定
4. 潜在的风险和挑战
"""
        elif phase == Phase.P3_UI_UX_DESIGN:
            prompt += """
请从以下角度评估设计方案：
1. 是否符合产品需求
2. 用户体验是否流畅
3. 交互逻辑是否清晰
4. 是否有遗漏的场景
"""
        elif phase == Phase.P7_FUNCTIONAL_TESTING:
            prompt += """
请进行UAT验收：
1. 功能是否符合需求
2. 用户体验是否达标
3. 是否满足上线标准
4. 是否有遗留问题
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        产品经理在以下情况可以做出决策：
        1. 产品需求相关的决策
        2. UI/UX设计的验收
        3. UAT测试的验收
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.PRODUCT_MANAGER)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def analyze_requirements(
        self,
        context: DiscussionContext,
        user_needs: str
    ) -> Dict[str, Any]:
        """
        分析用户需求
        
        Args:
            context: 讨论上下文
            user_needs: 用户需求描述
            
        Returns:
            需求分析结果
        """
        prompt = f"""请分析以下用户需求：

{user_needs}

请从以下维度进行分析：
1. 需求背景和目标
2. 目标用户群体
3. 核心功能点
4. 业务流程
5. 非功能性需求
6. 潜在风险

请以JSON格式输出分析结果：
{{
    "background": "需求背景",
    "objectives": ["目标1", "目标2"],
    "target_users": "目标用户",
    "core_features": ["功能1", "功能2"],
    "business_flow": "业务流程描述",
    "non_functional": ["性能要求", "安全要求"],
    "risks": ["风险1", "风险2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        # 存储需求
        requirement = {
            "raw_needs": user_needs,
            "analysis": response,
            "phase": context.phase
        }
        self.requirements.append(requirement)
        
        return requirement
    
    async def write_prd(
        self,
        context: DiscussionContext,
        requirement_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        编写产品需求文档
        
        Args:
            context: 讨论上下文
            requirement_analysis: 需求分析结果
            
        Returns:
            PRD文档
        """
        prompt = f"""请根据以下需求分析编写PRD文档：

需求分析:
{requirement_analysis.get('analysis', '')}

PRD文档应包含以下内容：
1. 文档概述
2. 需求背景和目标
3. 功能需求（详细描述每个功能）
4. 非功能性需求
5. 用户故事
6. 验收标准
7. 发布标准

请以Markdown格式输出完整的PRD文档。
"""
        
        response = await self.chat(prompt, context)
        
        prd = {
            "content": response,
            "requirement_analysis": requirement_analysis,
            "phase": context.phase,
            "status": "draft"
        }
        self.prd_documents.append(prd)
        
        return prd
    
    async def review_ui_design(
        self,
        context: DiscussionContext,
        design_content: str
    ) -> Dict[str, Any]:
        """
        审核UI设计
        
        Args:
            context: 讨论上下文
            design_content: 设计内容
            
        Returns:
            审核结果
        """
        prompt = f"""请审核以下UI设计方案：

{design_content}

请从以下维度进行审核：
1. 是否符合产品需求
2. 用户体验是否良好
3. 交互逻辑是否合理
4. 视觉设计是否一致
5. 是否考虑了各种场景

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
            "design_content": design_content,
            "review_result": response,
            "phase": context.phase
        }
    
    async def conduct_uat(
        self,
        context: DiscussionContext,
        test_results: str
    ) -> Dict[str, Any]:
        """
        进行UAT验收
        
        Args:
            context: 讨论上下文
            test_results: 测试结果
            
        Returns:
            UAT验收结果
        """
        prompt = f"""请根据以下测试结果进行UAT验收：

测试结果:
{test_results}

请从以下维度进行验收：
1. 功能完整性
2. 需求符合度
3. 用户体验
4. 已知问题评估
5. 上线风险评估

请以JSON格式输出验收结果：
{{
    "approved": true/false,
    "score": "评分(1-10)",
    "comments": "验收意见",
    "blockers": ["阻塞问题1", "阻塞问题2"],
    "acceptable_issues": ["可接受问题1"],
    "recommendations": ["建议1", "建议2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "test_results": test_results,
            "uat_result": response,
            "phase": context.phase
        }
    
    def get_prd_documents(self) -> List[Dict[str, Any]]:
        """获取所有PRD文档"""
        return self.prd_documents.copy()
    
    def get_requirements(self) -> List[Dict[str, Any]]:
        """获取所有需求"""
        return self.requirements.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.PRODUCT_MANAGER.value, ProductManager)


if __name__ == "__main__":
    import asyncio
    
    async def test_pm():
        pm = ProductManager()
        print(f"创建角色: {pm}")
        print(f"系统提示词长度: {len(pm.system_prompt)}")
    
    asyncio.run(test_pm())
