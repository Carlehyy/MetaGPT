"""
项目经理角色 - 任务拆解、项目计划、进度管理

作为项目管理负责人，项目经理负责：
- 任务拆解和分配
- 项目计划制定
- 进度跟踪和管理
- 风险管控
- 资源协调
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class ProjectManager(BaseRole):
    """
    项目经理角色
    
    职责：
    - 任务拆解和分配
    - 项目计划制定
    - 进度跟踪和管理
    - 风险识别和管控
    - 资源协调
    - 部署上线管理
    """
    
    def __init__(self, name: str = "项目经理", **kwargs):
        """
        初始化项目经理角色
        
        Args:
            name: 角色名称，默认为"项目经理"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="项目经理(PM)",
            responsibilities=[
                "拆解和分配开发任务",
                "制定项目计划和时间表",
                "跟踪项目进度",
                "识别和管理项目风险",
                "协调各方资源",
                "组织项目会议",
                "管理项目文档",
                "推动部署上线"
            ],
            expertise=[
                "项目管理方法论",
                "敏捷开发(Scrum/Kanban)",
                "任务拆解(WBS)",
                "进度管理",
                "风险管理",
                "资源协调",
                "沟通管理",
                "项目工具(Jira/禅道)"
            ],
            communication_style="""
组织能力强、善于协调，能够有效推动项目进展。
注重时间节点，对进度有清晰的把控。
能够及时发现和解决问题。
""",
            decision_scope="""
项目管理相关的决策：
- 任务分配和优先级
- 项目计划和里程碑
- 资源调配
- 进度调整
- 风险应对

需要@老板的情况：
- 项目进度严重滞后
- 需要额外资源支持
- 重大风险需要升级
- 上线时间需要调整
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.PROJECT_MANAGER.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 项目计划
        self.project_plans: List[Dict[str, Any]] = []
        # 任务列表
        self.tasks: List[Dict[str, Any]] = []
        # 风险记录
        self.risks: List[Dict[str, Any]] = []
    
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
            项目经理的发言内容
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

你作为项目经理，需要从项目管理角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P4_TASK_BREAKDOWN:
            prompt += """
请从以下角度指导任务拆解：
1. 任务分解的合理性
2. 任务依赖关系
3. 工作量评估
4. 资源分配建议
5. 时间安排
"""
        elif phase == Phase.P8_DEPLOYMENT:
            prompt += """
请从以下角度管理部署：
1. 部署计划
2. 风险预案
3. 回滚方案
4. 验证清单
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        项目经理在以下情况可以做出决策：
        1. 任务分配相关的决策
        2. 项目计划相关的决策
        3. 部署上线相关的决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.PROJECT_MANAGER)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def create_project_plan(
        self,
        context: DiscussionContext,
        requirements: str,
        technical_solution: str
    ) -> Dict[str, Any]:
        """
        创建项目计划
        
        Args:
            context: 讨论上下文
            requirements: 需求描述
            technical_solution: 技术方案
            
        Returns:
            项目计划
        """
        prompt = f"""请根据以下需求和技术方案创建项目计划：

需求描述:
{requirements}

技术方案:
{technical_solution}

项目计划应包含：
1. 项目阶段划分
2. 每个阶段的关键任务
3. 里程碑设置
4. 时间安排
5. 资源需求
6. 风险识别
7. 交付物清单

请以JSON格式输出项目计划：
{{
    "phases": [
        {{
            "name": "阶段名称",
            "duration": "持续时间",
            "tasks": ["任务1", "任务2"],
            "milestones": ["里程碑1"],
            "deliverables": ["交付物1"]
        }}
    ],
    "timeline": "总体时间线",
    "resources": {{"角色": "数量"}},
    "risks": ["风险1", "风险2"],
    "mitigations": ["缓解措施1", "缓解措施2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        plan = {
            "content": response,
            "requirements": requirements,
            "technical_solution": technical_solution,
            "phase": context.phase,
            "created_at": datetime.now().isoformat()
        }
        self.project_plans.append(plan)
        
        return plan
    
    async def breakdown_tasks(
        self,
        context: DiscussionContext,
        feature_description: str,
        technical_architecture: str
    ) -> Dict[str, Any]:
        """
        拆解任务
        
        Args:
            context: 讨论上下文
            feature_description: 功能描述
            technical_architecture: 技术架构
            
        Returns:
            任务列表
        """
        prompt = f"""请将以下功能拆解为具体的开发任务：

功能描述:
{feature_description}

技术架构:
{technical_architecture}

任务拆解要求：
1. 任务粒度适中（一般1-3天）
2. 明确任务依赖关系
3. 估算工作量
4. 指定负责人角色
5. 定义完成标准

请以JSON格式输出任务列表：
{{
    "tasks": [
        {{
            "id": "任务ID",
            "title": "任务标题",
            "description": "任务描述",
            "estimated_hours": "预估工时",
            "assignee_role": "负责人角色",
            "dependencies": ["依赖任务ID"],
            "acceptance_criteria": ["验收标准1"],
            "priority": "优先级(high/medium/low)"
        }}
    ],
    "total_hours": "总工时",
    "critical_path": ["关键路径任务"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        task_breakdown = {
            "content": response,
            "feature": feature_description,
            "phase": context.phase,
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task_breakdown)
        
        return task_breakdown
    
    async def assess_risks(
        self,
        context: DiscussionContext,
        project_status: str
    ) -> Dict[str, Any]:
        """
        评估项目风险
        
        Args:
            context: 讨论上下文
            project_status: 项目状态
            
        Returns:
            风险评估结果
        """
        prompt = f"""请评估以下项目状态的风险：

项目状态:
{project_status}

请从以下维度进行风险评估：
1. 进度风险
2. 技术风险
3. 资源风险
4. 需求风险
5. 外部依赖风险

请以JSON格式输出风险评估：
{{
    "risks": [
        {{
            "type": "风险类型",
            "description": "风险描述",
            "probability": "发生概率(high/medium/low)",
            "impact": "影响程度(high/medium/low)",
            "mitigation": "缓解措施",
            "owner": "负责人"
        }}
    ],
    "overall_risk_level": "总体风险等级",
    "recommendations": ["建议1", "建议2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        risk_assessment = {
            "content": response,
            "project_status": project_status,
            "phase": context.phase,
            "assessed_at": datetime.now().isoformat()
        }
        self.risks.append(risk_assessment)
        
        return risk_assessment
    
    async def create_deployment_plan(
        self,
        context: DiscussionContext,
        release_content: str
    ) -> Dict[str, Any]:
        """
        创建部署计划
        
        Args:
            context: 讨论上下文
            release_content: 发布内容
            
        Returns:
            部署计划
        """
        prompt = f"""请为以下发布内容创建部署计划：

发布内容:
{release_content}

部署计划应包含：
1. 部署前准备
2. 部署步骤
3. 验证清单
4. 回滚方案
5. 监控项
6. 应急联系人

请以JSON格式输出部署计划：
{{
    "preparation": ["准备项1", "准备项2"],
    "deployment_steps": ["步骤1", "步骤2"],
    "verification": ["验证项1", "验证项2"],
    "rollback_plan": "回滚方案",
    "monitoring": ["监控项1", "监控项2"],
    "estimated_downtime": "预计停机时间",
    "contacts": ["联系人1", "联系人2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "release_content": release_content,
            "phase": context.phase,
            "created_at": datetime.now().isoformat()
        }
    
    def get_project_plans(self) -> List[Dict[str, Any]]:
        """获取所有项目计划"""
        return self.project_plans.copy()
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return self.tasks.copy()
    
    def get_risks(self) -> List[Dict[str, Any]]:
        """获取所有风险记录"""
        return self.risks.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.PROJECT_MANAGER.value, ProjectManager)


if __name__ == "__main__":
    import asyncio
    
    async def test_pm():
        pm = ProjectManager()
        print(f"创建角色: {pm}")
        print(f"系统提示词长度: {len(pm.system_prompt)}")
    
    asyncio.run(test_pm())
