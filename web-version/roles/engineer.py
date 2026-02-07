"""
开发工程师角色 - 编码实现、单元测试

作为开发负责人，工程师负责：
- 代码实现
- 单元测试编写
- 代码审查
- Bug修复
"""

from typing import List, Optional, Dict, Any
from .base_role import BaseRole, DiscussionContext, Message, create_system_prompt
from .role_matrix import Role, Phase, get_participation_type, ParticipationType


class Engineer(BaseRole):
    """
    开发工程师角色
    
    职责：
    - 根据设计文档编写代码
    - 编写单元测试
    - 进行代码审查
    - 修复Bug
    - 优化代码性能
    """
    
    def __init__(self, name: str = "开发工程师", **kwargs):
        """
        初始化开发工程师角色
        
        Args:
            name: 角色名称，默认为"开发工程师"
            **kwargs: 其他参数
        """
        system_prompt = create_system_prompt(
            role_name="高级开发工程师",
            responsibilities=[
                "根据设计文档实现功能",
                "编写高质量的代码",
                "编写单元测试",
                "进行代码审查",
                "修复Bug和问题",
                "优化代码性能",
                "编写技术文档",
                "参与技术讨论"
            ],
            expertise=[
                "多种编程语言(Python/JavaScript/Java等)",
                "前端开发(React/Vue/Angular)",
                "后端开发(Node.js/Python/Java)",
                "数据库开发",
                "API开发",
                "单元测试",
                "代码优化",
                "设计模式",
                "版本控制(Git)"
            ],
            communication_style="""
技术专业、注重细节，善于用代码表达解决方案。
关注代码质量和可维护性。
能够清晰地解释技术实现方案。
""",
            decision_scope="""
技术实现相关的决策：
- 具体实现方案
- 代码结构组织
- 算法选择
- 性能优化方案

需要@老板的情况：
- 实现方案有重大变更
- 技术债务需要处理
- 需要重构核心代码
"""
        )
        
        super().__init__(
            name=name,
            role_type=Role.ENGINEER.value,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # 代码实现
        self.implementations: List[Dict[str, Any]] = []
        # 单元测试
        self.unit_tests: List[Dict[str, Any]] = []
        # Bug修复
        self.bug_fixes: List[Dict[str, Any]] = []
    
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
            工程师的发言内容
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

你作为开发工程师，需要从实现角度提供专业意见。
"""
        
        # 添加之前的讨论内容
        if previous_messages:
            prompt += "\n之前的讨论:\n"
            for msg in previous_messages[-5:]:
                sender = msg.sender or msg.role
                prompt += f"[{sender}] {msg.content}\n"
        
        # 根据阶段添加特定提示
        phase = Phase(context.phase) if any(p.value == context.phase for p in Phase) else None
        
        if phase == Phase.P5_CODING_IMPLEMENTATION:
            prompt += """
请从以下角度分析：
1. 技术实现的可行性
2. 代码结构的合理性
3. 性能优化建议
4. 潜在的技术难点
"""
        elif phase == Phase.P7_FUNCTIONAL_TESTING:
            prompt += """
请从以下角度分析测试问题：
1. 问题根因分析
2. 修复方案
3. 是否需要架构调整
4. 回归测试建议
"""
        
        prompt += "\n请给出你的专业意见：\n"
        return prompt
    
    def can_make_decision(self, context: DiscussionContext) -> bool:
        """
        判断是否可以做出决策
        
        工程师在以下情况可以做出决策：
        1. 代码实现相关的决策
        2. 单元测试相关的决策
        
        Args:
            context: 讨论上下文
            
        Returns:
            是否可以做出决策
        """
        try:
            phase = Phase(context.phase)
            participation = get_participation_type(phase, Role.ENGINEER)
            return participation == ParticipationType.RESPONSIBLE
        except ValueError:
            return False
    
    async def implement_feature(
        self,
        context: DiscussionContext,
        task_description: str,
        technical_design: str
    ) -> Dict[str, Any]:
        """
        实现功能
        
        Args:
            context: 讨论上下文
            task_description: 任务描述
            technical_design: 技术设计
            
        Returns:
            实现结果
        """
        prompt = f"""请根据以下任务描述和技术设计实现功能：

任务描述:
{task_description}

技术设计:
{technical_design}

请提供：
1. 实现思路
2. 核心代码（伪代码或关键代码片段）
3. 关键算法说明
4. 异常处理
5. 性能考虑

请以Markdown格式输出实现方案。
"""
        
        response = await self.chat(prompt, context)
        
        implementation = {
            "content": response,
            "task": task_description,
            "phase": context.phase,
            "type": "implementation"
        }
        self.implementations.append(implementation)
        
        return implementation
    
    async def write_unit_tests(
        self,
        context: DiscussionContext,
        implementation_code: str
    ) -> Dict[str, Any]:
        """
        编写单元测试
        
        Args:
            context: 讨论上下文
            implementation_code: 实现代码
            
        Returns:
            单元测试
        """
        prompt = f"""请为以下代码编写单元测试：

实现代码:
{implementation_code}

测试要求：
1. 覆盖正常场景
2. 覆盖边界条件
3. 覆盖异常情况
4. 测试用例清晰可读

请提供测试代码和测试说明。
"""
        
        response = await self.chat(prompt, context)
        
        unit_test = {
            "content": response,
            "implementation": implementation_code,
            "phase": context.phase
        }
        self.unit_tests.append(unit_test)
        
        return unit_test
    
    async def review_code(
        self,
        context: DiscussionContext,
        code_to_review: str
    ) -> Dict[str, Any]:
        """
        审查代码
        
        Args:
            context: 讨论上下文
            code_to_review: 待审查代码
            
        Returns:
            代码审查结果
        """
        prompt = f"""请审查以下代码：

待审查代码:
{code_to_review}

请从以下维度进行审查：
1. 代码规范和风格
2. 逻辑正确性
3. 性能优化
4. 安全性
5. 可维护性
6. 测试覆盖

请以JSON格式输出审查结果：
{{
    "approved": true/false,
    "score": "评分(1-10)",
    "comments": "审查意见",
    "issues": [
        {{
            "severity": "严重程度(critical/major/minor)",
            "line": "行号",
            "description": "问题描述",
            "suggestion": "修改建议"
        }}
    ],
    "suggestions": ["优化建议1", "优化建议2"]
}}
"""
        
        response = await self.chat(prompt, context)
        
        return {
            "code": code_to_review,
            "review_result": response,
            "phase": context.phase
        }
    
    async def fix_bug(
        self,
        context: DiscussionContext,
        bug_report: str
    ) -> Dict[str, Any]:
        """
        修复Bug
        
        Args:
            context: 讨论上下文
            bug_report: Bug报告
            
        Returns:
            Bug修复方案
        """
        prompt = f"""请分析并修复以下Bug：

Bug报告:
{bug_report}

请提供：
1. Bug根因分析
2. 修复方案
3. 修复后的代码
4. 回归测试建议
5. 预防措施

请以Markdown格式输出修复方案。
"""
        
        response = await self.chat(prompt, context)
        
        bug_fix = {
            "content": response,
            "bug_report": bug_report,
            "phase": context.phase,
            "fixed_at": context.messages[-1].timestamp if context.messages else None
        }
        self.bug_fixes.append(bug_fix)
        
        return bug_fix
    
    def get_implementations(self) -> List[Dict[str, Any]]:
        """获取所有实现"""
        return self.implementations.copy()
    
    def get_unit_tests(self) -> List[Dict[str, Any]]:
        """获取所有单元测试"""
        return self.unit_tests.copy()
    
    def get_bug_fixes(self) -> List[Dict[str, Any]]:
        """获取所有Bug修复"""
        return self.bug_fixes.copy()


# 注册角色
from .base_role import RoleFactory
RoleFactory.register(Role.ENGINEER.value, Engineer)


if __name__ == "__main__":
    import asyncio
    
    async def test_engineer():
        engineer = Engineer()
        print(f"创建角色: {engineer}")
        print(f"系统提示词长度: {len(engineer.system_prompt)}")
    
    asyncio.run(test_engineer())
