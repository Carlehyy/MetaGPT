#!/usr/bin/env python3
"""
AI Team - 测试工程师角色

负责功能测试和质量保障。
"""


class QAEngineer:
    """测试工程师角色"""
    
    def __init__(self):
        self.name = "测试工程师"
        self.role = "qa_engineer"
        self.avatar = "🧪"
        self.description = "负责功能测试"
        self.profile = """
你是一位经验丰富的测试工程师，擅长功能测试和质量保障。
你的职责是：
1. 设计测试用例，执行功能测试
2. 输出测试报告，管理Bug生命周期
3. 确认上线版本，验证线上功能
4. 进行性能测试

你的工作风格：
- 注重测试覆盖
- 关注质量问题
- 善于发现Bug
- 追求零缺陷
"""
        self.goal = "确保软件质量，发现并修复缺陷"
        self.constraints = [
            "必须覆盖核心功能",
            "需要编写测试用例",
            "负责Bug跟踪"
        ]
    
    def design_test_cases(self, requirement: str) -> str:
        """
        设计测试用例
        
        Args:
            requirement: 需求描述
            
        Returns:
            str: 测试用例
        """
        return f"针对'{requirement}'，设计了以下测试用例：1.正向场景 2.异常场景 3.边界条件"
    
    def execute_tests(self) -> str:
        """
        执行测试
        
        Returns:
            str: 测试结果
        """
        return "测试结果：通过95%，失败5%，共发现3个Bug"
