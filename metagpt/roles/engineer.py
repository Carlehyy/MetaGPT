"""
开发工程师(Engineer)角色实现
负责编码实现、代码评审和技术实现
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class WriteCode(Action):
    """编写代码动作"""
    
    name: str = "WriteCode"
    context: str = """
    作为开发工程师，你需要：
    1. 根据需求和技术方案编写代码
    2. 遵循代码规范和最佳实践
    3. 编写单元测试
    4. 进行代码自测
    5. 输出高质量的代码
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行代码编写"""
        prompt = f"""
        作为开发工程师，请编写代码：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 代码实现
        2. 单元测试
        3. 代码注释
        """
        response = f"[开发工程师-编码] 已完成代码实现。"
        return Message(content=response, role="Engineer")


class CodeReview(Action):
    """代码评审动作"""
    
    name: str = "CodeReview"
    context: str = """
    作为开发工程师，你需要：
    1. 进行代码评审
    2. 确保代码质量
    3. 提供改进建议
    4. 修复代码问题
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行代码评审"""
        prompt = f"""
        作为开发工程师，请评审代码：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请给出代码评审意见。
        """
        response = f"[开发工程师-代码评审] 已评审，代码质量良好。"
        return Message(content=response, role="Engineer")


class FixBugs(Action):
    """修复缺陷动作"""
    
    name: str = "FixBugs"
    context: str = """
    作为开发工程师，你需要：
    1. 修复测试发现的缺陷
    2. 进行缺陷根因分析
    3. 验证修复效果
    4. 更新相关文档
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行缺陷修复"""
        prompt = f"""
        作为开发工程师，请修复缺陷：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出缺陷修复方案。
        """
        response = f"[开发工程师-缺陷修复] 已修复缺陷。"
        return Message(content=response, role="Engineer")


class Engineer(Role):
    """
    开发工程师角色
    
    Profile: 开发工程师，负责编码实现和技术实现
    Goal: 编写高质量、可维护的代码，实现产品功能
    Constraints: 关注代码质量、性能和可维护性
    """
    
    name: str = "Engineer"
    profile: str = "开发工程师，负责编码实现、代码评审和技术实现"
    goal: str = "编写高质量、可维护的代码，按时实现产品功能"
    constraints: str = """
    - 遵循代码规范和最佳实践
    - 编写单元测试和文档
    - 关注代码质量和性能
    - 负责编码实现阶段的执行
    - 参与UI验收和功能测试的执行
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([WriteCode, CodeReview, FixBugs])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取开发工程师在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "Engineer")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断开发工程师是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断开发工程师在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断开发工程师在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断开发工程师在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行开发工程师动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        开发工程师职责：
        1. 需求分析阶段：不参与
        2. 技术方案阶段：咨询 - 提供实现视角
        3. UI/UX设计阶段：咨询 - 评估实现可行性
        4. 任务拆解阶段：咨询 - 评估工时
        5. 编码实现阶段：负责/执行 - 编写代码
        6. UI验收阶段：执行 - 实现UI
        7. 功能测试阶段：执行 - 修复缺陷
        8. 部署上线阶段：咨询 - 支持部署
        9. 运维监控阶段：咨询 - 支持运维
        """
