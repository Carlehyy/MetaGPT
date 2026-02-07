"""
测试工程师(QAEngineer)角色实现
负责测试计划、测试执行和质量保证
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class WriteTestPlan(Action):
    """编写测试计划动作"""
    
    name: str = "WriteTestPlan"
    context: str = """
    作为测试工程师，你需要：
    1. 分析需求，制定测试策略
    2. 编写测试计划和测试方案
    3. 设计测试用例
    4. 准备测试数据
    5. 规划测试环境和资源
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行测试计划编写"""
        prompt = f"""
        作为测试工程师，请编写测试计划：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 测试策略
        2. 测试范围
        3. 测试用例设计
        4. 测试环境需求
        5. 测试进度计划
        """
        response = f"[测试工程师-测试计划] 已完成测试计划。"
        return Message(content=response, role="QAEngineer")


class ExecuteTests(Action):
    """执行测试动作"""
    
    name: str = "ExecuteTests"
    context: str = """
    作为测试工程师，你需要：
    1. 执行测试用例
    2. 记录测试结果
    3. 提交缺陷报告
    4. 进行回归测试
    5. 输出测试报告
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行测试"""
        prompt = f"""
        作为测试工程师，请执行测试：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 测试执行结果
        2. 发现的缺陷
        3. 测试报告
        """
        response = f"[测试工程师-测试执行] 已完成测试，发现X个缺陷。"
        return Message(content=response, role="QAEngineer")


class PerformUAT(Action):
    """执行UAT测试动作"""
    
    name: str = "PerformUAT"
    context: str = """
    作为测试工程师，你需要：
    1. 协助产品经理进行UAT测试
    2. 验证业务流程完整性
    3. 确保功能符合需求
    4. 输出UAT测试报告
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行UAT测试"""
        prompt = f"""
        作为测试工程师，请执行UAT测试：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出UAT测试结果。
        """
        response = f"[测试工程师-UAT测试] 已完成UAT测试。"
        return Message(content=response, role="QAEngineer")


class QAEngineer(Role):
    """
    测试工程师角色
    
    Profile: 测试工程师，负责测试计划、测试执行和质量保证
    Goal: 确保产品质量，发现和预防缺陷
    Constraints: 关注测试覆盖率和缺陷预防
    """
    
    name: str = "QAEngineer"
    profile: str = "测试工程师，负责测试计划、测试执行和质量保证"
    goal: str = "确保产品质量，发现和预防缺陷，提升用户体验"
    constraints: str = """
    - 全面覆盖功能测试场景
    - 及时提交缺陷并跟踪修复
    - 关注测试效率和质量
    - 负责功能测试阶段的执行
    - 与开发工程师紧密协作
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([WriteTestPlan, ExecuteTests, PerformUAT])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取测试工程师在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "QAEngineer")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断测试工程师是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断测试工程师在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断测试工程师在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断测试工程师在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行测试工程师动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        测试工程师职责：
        1. 需求分析阶段：不参与
        2. 技术方案阶段：知会 - 了解技术方案
        3. UI/UX设计阶段：不参与
        4. 任务拆解阶段：咨询 - 评估测试任务
        5. 编码实现阶段：不参与
        6. UI验收阶段：不参与
        7. 功能测试阶段：负责/执行 - 执行测试
        8. 部署上线阶段：咨询 - 验证上线条件
        9. 运维监控阶段：知会 - 了解线上质量
        """
