"""
测试工程师角色 - 功能测试、UAT验收

作为质量保障负责人，测试工程师负责：
- 测试计划和用例设计
- 功能测试执行
- 缺陷管理
- UAT测试支持
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class QAEngineer(BaseRole):
    """
    测试工程师角色
    
    职责：
    - 制定测试计划
    - 设计测试用例
    - 执行功能测试
    - 缺陷跟踪和管理
    - 支持UAT测试
    - 质量评估
    """
    
    def __init__(self, name: str = "测试工程师", **kwargs):
        """
        初始化测试工程师角色
        
        Args:
            name: 角色名称，默认为"测试工程师"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="高级测试工程师(QA)",
            responsibilities=[
                "制定测试计划和策略",
                "设计测试用例",
                "执行功能测试",
                "记录和跟踪缺陷",
                "进行回归测试",
                "支持UAT测试",
                "评估产品质量",
                "编写测试报告"
            ],
            expertise=[
                "功能测试",
                "测试用例设计",
                "缺陷管理",
                "自动化测试",
                "性能测试",
                "API测试",
                "测试工具(Selenium/Postman/JMeter)",
                "敏捷测试",
                "质量保证流程"
            ],
            communication_style="""
细致严谨、善于发现问题，能够清晰地描述缺陷。
关注产品质量，对测试覆盖率有高要求。
能够客观地评估产品质量。
""",
            decision_scope="""
测试相关的决策：
- 测试策略和方法
- 测试用例设计
- 缺陷优先级判定
- 质量评估标准
- 上线质量判定

需要@老板的情况：
- 发现重大质量风险
- 上线标准存在争议
- 需要延期发布
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.QA_ENGINEER.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 测试计划
        self.test_plans: List[Dict[str, Any]] = []
        # 测试用例
        self.test_cases: List[Dict[str, Any]] = []
        # 缺陷记录
        self.bugs: List[Dict[str, Any]] = []
        # 测试报告
        self.test_reports: List[Dict[str, Any]] = []
    
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
            测试工程师的发言内容
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

你作为测试工程师，需要从质量保障角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P7_FUNCTIONAL_TESTING:
            prompt += """
请从以下角度分析：
1. 测试覆盖率评估
2. 缺陷分析和优先级
3. 质量风险评估
4. 上线建议
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        测试工程师在以下情况可以做出决策：
        1. 测试相关的决策
        2. 缺陷优先级判定
        3. 质量评估
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.QA_ENGINEER)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def create_test_plan(
        self,
        context: DiscussionContext,
        prd_content: str,
        technical_design: str
    ) -> Dict[str, Any]:
        """
        创建测试计划
        
        Args:
            context: 讨论上下文
            prd_content: PRD内容
            technical_design: 技术设计
            
        Returns:
            测试计划
        """
        prompt = f"""请根据以下PRD和技术设计创建测试计划：

PRD内容:
{prd_content}

技术设计:
{technical_design}

测试计划应包含：
1. 测试范围和目标
2. 测试策略
3. 测试类型（功能、性能、安全等）
4. 测试环境
5. 测试资源
6. 时间安排
7. 风险识别

请以Markdown格式输出测试计划。
"""
        
        response = await self.chat(prompt, context)
        
        test_plan = {
            "content": response,
            "prd_content": prd_content,
            "phase": context.phase
        }
        self.test_plans.append(test_plan)
        
        return test_plan
    
    async def design_test_cases(
        self,
        context: DiscussionContext,
        feature_description: str
    ) -> Dict[str, Any]:
        """
        设计测试用例
        
        Args:
            context: 讨论上下文
            feature_description: 功能描述
            
        Returns:
            测试用例
        """
        prompt = f"""请为以下功能设计测试用例：

功能描述:
{feature_description}

测试用例应包含：
1. 用例ID
2. 用例标题
3. 前置条件
4. 测试步骤
5. 预期结果
6. 优先级
7. 测试类型（正例/反例）

请以JSON格式输出测试用例：
{{
    "test_cases": [
        {{
            "id": "TC001",
            "title": "用例标题",
            "precondition": "前置条件",
            "steps": ["步骤1", "步骤2"],
            "expected_result": "预期结果",
            "priority": "优先级(high/medium/low)",
            "type": "类型(positive/negative)"
        }}
    ]
}}
"""
        
        response = await self.chat(prompt, context)
        
        test_case = {
            "content": response,
            "feature": feature_description,
            "phase": context.phase
        }
        self.test_cases.append(test_case)
        
        return test_case
    
    async def report_bug(
        self,
        context: DiscussionContext,
        bug_description: str
    ) -> Dict[str, Any]:
        """
        报告缺陷
        
        Args:
            context: 讨论上下文
            bug_description: 缺陷描述
            
        Returns:
            缺陷报告
        """
        prompt = f"""请根据以下描述生成规范的缺陷报告：

缺陷描述:
{bug_description}

缺陷报告应包含：
1. 缺陷标题
2. 缺陷描述
3. 重现步骤
4. 预期结果
5. 实际结果
6. 严重程度
7. 优先级
8. 环境信息

请以JSON格式输出缺陷报告：
{{
    "title": "缺陷标题",
    "description": "缺陷描述",
    "reproduce_steps": ["步骤1", "步骤2"],
    "expected_result": "预期结果",
    "actual_result": "实际结果",
    "severity": "严重程度(critical/major/minor/trivial)",
    "priority": "优先级(high/medium/low)",
    "environment": "环境信息"
}}
"""
        
        response = await self.chat(prompt, context)
        
        bug = {
            "content": response,
            "description": bug_description,
            "phase": context.phase,
            "status": "open"
        }
        self.bugs.append(bug)
        
        return bug
    
    async def generate_test_report(
        self,
        context: DiscussionContext,
        test_results: str
    ) -> Dict[str, Any]:
        """
        生成测试报告
        
        Args:
            context: 讨论上下文
            test_results: 测试结果
            
        Returns:
            测试报告
        """
        prompt = f"""请根据以下测试结果生成测试报告：

测试结果:
{test_results}

测试报告应包含：
1. 测试概述
2. 测试范围
3. 测试执行情况
4. 缺陷统计
5. 质量评估
6. 风险评估
7. 上线建议

请以JSON格式输出测试报告：
{{
    "summary": "测试概述",
    "scope": "测试范围",
    "execution": {{"total": "总用例数", "passed": "通过数", "failed": "失败数"}},
    "defects": {{"critical": "严重缺陷数", "major": "主要缺陷数", "minor": "轻微缺陷数"}},
    "quality_assessment": "质量评估",
    "risk_assessment": "风险评估",
    "recommendation": "上线建议(go/no-go)"
}}
"""
        
        response = await self.chat(prompt, context)
        
        test_report = {
            "content": response,
            "test_results": test_results,
            "phase": context.phase
        }
        self.test_reports.append(test_report)
        
        return test_report
    
    async def assess_quality(
        self,
        context: DiscussionContext,
        project_status: str
    ) -> Dict[str, Any]:
        """
        评估产品质量
        
        Args:
            context: 讨论上下文
            project_status: 项目状态
            
        Returns:
            质量评估结果
        """
        prompt = f"""请评估以下项目状态的产品质量：

项目状态:
{project_status}

请从以下维度进行质量评估：
1. 功能完整性
2. 缺陷密度
3. 测试覆盖率
4. 性能表现
5. 稳定性
6. 用户体验

请以JSON格式输出质量评估：
{{
    "overall_score": "总体评分(1-10)",
    "dimensions": {{
        "functionality": "功能完整性评分",
        "reliability": "可靠性评分",
        "performance": "性能评分",
        "usability": "易用性评分"
    }},
    "assessment": "评估结论",
    "blockers": ["阻塞问题1"],
    "recommendations": ["建议1", "建议2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "content": response,
            "project_status": project_status,
            "phase": context.phase
        }
    
    def get_test_plans(self) -> List[Dict[str, Any]]:
        """获取所有测试计划"""
        return self.test_plans.copy()
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """获取所有测试用例"""
        return self.test_cases.copy()
    
    def get_bugs(self) -> List[Dict[str, Any]]:
        """获取所有缺陷"""
        return self.bugs.copy()
    
    def get_test_reports(self) -> List[Dict[str, Any]]:
        """获取所有测试报告"""
        return self.test_reports.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.QA_ENGINEER.value, QAEngineer)


if __name__ == "__main__":
    import asyncio
    
    async def test_qa():
        qa = QAEngineer()
        print(f"创建角色: {qa}")
        print(f"系统提示词长度: {len(qa.system_prompt)}")
    
    asyncio.run(test_qa())
