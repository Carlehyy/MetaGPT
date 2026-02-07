"""
架构师角色 - 技术方案设计、架构设计

作为技术负责人，架构师负责：
- 系统架构设计
- 技术方案制定
- 技术选型
- 任务拆解的技术指导
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class Architect(BaseRole):
    """
    架构师角色
    
    职责：
    - 系统架构设计
    - 技术方案制定
    - 技术选型决策
    - 指导任务拆解
    - 技术风险评估
    """
    
    def __init__(self, name: str = "架构师", **kwargs):
        """
        初始化架构师角色
        
        Args:
            name: 角色名称，默认为"架构师"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="系统架构师",
            responsibilities=[
                "设计系统整体架构",
                "制定技术方案和选型",
                "评估技术可行性",
                "指导开发任务拆解",
                "解决技术难题",
                "把控技术质量",
                "评估技术风险"
            ],
            expertise=[
                "系统架构设计",
                "微服务架构",
                "数据库设计",
                "API设计",
                "性能优化",
                "安全架构",
                "云原生技术",
                "DevOps实践"
            ],
            communication_style="""
技术专业、逻辑清晰，善于用架构图和流程图表达设计思想。
注重系统的可扩展性、可维护性和性能。
能够平衡技术理想和项目实际。
""",
            decision_scope="""
技术相关的决策：
- 系统架构方案
- 技术栈选型
- 数据库设计
- API接口设计
- 技术实现方案

需要@老板的情况：
- 技术方案有重大变更
- 需要额外的技术资源
- 技术风险超出预期
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.ARCHITECT.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 架构设计文档
        self.architecture_docs: List[Dict[str, Any]] = []
        # 技术方案
        self.technical_solutions: List[Dict[str, Any]] = []
    
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
            架构师的发言内容
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

你作为架构师，需要从技术角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P2_TECHNICAL_SOLUTION:
            prompt += """
请从以下角度分析：
1. 技术方案的可行性
2. 架构设计的合理性
3. 技术选型的适用性
4. 性能和扩展性考虑
5. 潜在的技术风险
"""
        elif phase == Phase.P4_TASK_BREAKDOWN:
            prompt += """
请从以下角度指导任务拆解：
1. 模块划分的合理性
2. 接口定义的规范性
3. 技术依赖关系
4. 开发顺序建议
"""
        elif phase == Phase.P7_FUNCTIONAL_TESTING:
            prompt += """
请从以下角度分析测试问题：
1. 问题根因分析
2. 修复方案建议
3. 是否需要架构调整
4. 性能问题诊断
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        架构师在以下情况可以做出决策：
        1. 技术方案相关的决策
        2. 架构设计相关的决策
        3. 技术选型相关的决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.ARCHITECT)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def design_architecture(
        self,
        context: DiscussionContext,
        requirements: str
    ) -> Dict[str, Any]:
        """
        设计系统架构
        
        Args:
            context: 讨论上下文
            requirements: 需求描述
            
        Returns:
            架构设计文档
        """
        prompt = f"""请根据以下需求设计系统架构：

需求描述:
{requirements}

请包含以下内容：
1. 系统整体架构（用文本描述架构图）
2. 核心模块划分
3. 模块间交互关系
4. 数据流向
5. 技术栈建议
6. 部署架构

请以Markdown格式输出架构设计文档。
"""
        
        response = await self.chat(prompt, context)
        
        doc = {
            "content": response,
            "requirements": requirements,
            "phase": context.phase,
            "type": "architecture"
        }
        self.architecture_docs.append(doc)
        
        return doc
    
    async def create_technical_solution(
        self,
        context: DiscussionContext,
        prd_content: str
    ) -> Dict[str, Any]:
        """
        制定技术方案
        
        Args:
            context: 讨论上下文
            prd_content: PRD内容
            
        Returns:
            技术方案文档
        """
        prompt = f"""请根据以下PRD制定技术方案：

PRD内容:
{prd_content}

技术方案应包含：
1. 技术选型及理由
2. 系统架构设计
3. 数据库设计
4. API接口设计
5. 关键技术实现方案
6. 性能优化方案
7. 安全方案
8. 风险评估

请以JSON格式输出技术方案：
{{
    "tech_stack": {{
        "frontend": "前端技术栈",
        "backend": "后端技术栈",
        "database": "数据库",
        "infrastructure": "基础设施"
    }},
    "architecture": "架构描述",
    "database_design": "数据库设计",
    "api_design": "API设计要点",
    "key_implementations": ["关键点1", "关键点2"],
    "performance_optimization": "性能优化方案",
    "security": "安全方案",
    "risks": ["风险1", "风险2"],
    "mitigations": ["缓解措施1", "缓解措施2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        solution = {
            "content": response,
            "prd_content": prd_content,
            "phase": context.phase
        }
        self.technical_solutions.append(solution)
        
        return solution
    
    async def design_database(
        self,
        context: DiscussionContext,
        requirements: str
    ) -> Dict[str, Any]:
        """
        设计数据库
        
        Args:
            context: 讨论上下文
            requirements: 需求描述
            
        Returns:
            数据库设计
        """
        prompt = f"""请根据以下需求设计数据库：

需求描述:
{requirements}

请包含：
1. 数据库选型及理由
2. 数据表设计（包含字段、类型、约束）
3. 表关系设计
4. 索引设计
5. 数据迁移策略

请以Markdown格式输出数据库设计文档。
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "requirements": requirements,
            "phase": context.phase,
            "type": "database"
        }
    
    async def design_api(
        self,
        context: DiscussionContext,
        feature_description: str
    ) -> Dict[str, Any]:
        """
        设计API接口
        
        Args:
            context: 讨论上下文
            feature_description: 功能描述
            
        Returns:
            API设计
        """
        prompt = f"""请为以下功能设计API接口：

功能描述:
{feature_description}

请包含：
1. 接口路径和HTTP方法
2. 请求参数
3. 响应格式
4. 错误码定义
5. 接口安全要求

请以JSON格式输出API设计：
{{
    "apis": [
        {{
            "path": "/api/xxx",
            "method": "GET/POST/PUT/DELETE",
            "description": "接口描述",
            "request": {{"参数名": "参数说明"}},
            "response": {{"字段名": "字段说明"}},
            "errors": ["错误码: 错误说明"]
        }}
    ]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "feature_description": feature_description,
            "phase": context.phase,
            "type": "api"
        }
    
    def get_architecture_docs(self) -> List[Dict[str, Any]]:
        """获取所有架构文档"""
        return self.architecture_docs.copy()
    
    def get_technical_solutions(self) -> List[Dict[str, Any]]:
        """获取所有技术方案"""
        return self.technical_solutions.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.ARCHITECT.value, Architect)


if __name__ == "__main__":
    import asyncio
    
    async def test_architect():
        architect = Architect()
        print(f"创建角色: {architect}")
        print(f"系统提示词长度: {len(architect.system_prompt)}")
    
    asyncio.run(test_architect())
