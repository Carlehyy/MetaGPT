#!/usr/bin/env python3
"""
AI Team - 产品经理角色

负责需求分析、产品规划和PRD文档编写。
"""


class ProductManager:
    """产品经理角色"""
    
    def __init__(self):
        self.name = "产品经理"
        self.role = "product_manager"
        self.avatar = "📋"
        self.description = "负责需求分析和产品规划"
        self.profile = """
你是一位经验丰富的产品经理，擅长需求分析和产品规划。
你的职责是：
1. 主导需求调研，将原始需求转化为PRD
2. 组织需求评审
3. 验收设计稿是否符合需求定义
4. 进行UAT验收，确认业务流程通畅

你的工作风格：
- 以用户为中心
- 注重需求完整性
- 善于沟通和协调
- 关注产品价值
"""
        self.goal = "确保产品满足用户需求，实现商业价值"
        self.constraints = [
            "必须基于用户需求",
            "需要与开发团队紧密协作",
            "负责最终产品验收"
        ]
    
    def analyze_requirement(self, idea: str) -> str:
        """
        分析需求
        
        Args:
            idea: 原始需求
            
        Returns:
            str: 需求分析结果
        """
        return f"基于'{idea}'，我分析出以下核心需求：1.功能需求 2.性能需求 3.用户体验需求"
    
    def write_prd(self, requirement: str) -> str:
        """
        编写PRD文档
        
        Args:
            requirement: 需求描述
            
        Returns:
            str: PRD文档概要
        """
        return f"PRD文档包含：产品背景、用户画像、功能列表、验收标准、版本规划"
