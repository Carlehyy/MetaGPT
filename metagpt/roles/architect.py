"""
架构师(Architect)角色实现
负责技术方案设计、架构决策和技术指导
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class DesignArchitecture(Action):
    """架构设计动作"""
    
    name: str = "DesignArchitecture"
    context: str = """
    作为架构师，你需要：
    1. 设计系统整体架构
    2. 选择技术栈和框架
    3. 定义模块划分和接口
    4. 评估技术风险和可行性
    5. 输出技术方案文档
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行架构设计"""
        prompt = f"""
        作为架构师，请设计系统架构：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 系统架构图
        2. 技术选型方案
        3. 模块划分
        4. 接口定义
        5. 风险评估
        """
        response = f"[架构师-架构设计] 已完成技术方案设计。"
        return Message(content=response, role="Architect")


class TechnicalReview(Action):
    """技术评审动作"""
    
    name: str = "TechnicalReview"
    context: str = """
    作为架构师，你需要：
    1. 评审技术实现方案
    2. 提供技术咨询和建议
    3. 解决技术难题
    4. 确保架构规范执行
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行技术评审"""
        prompt = f"""
        作为架构师，请评审以下内容：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请给出技术评审意见。
        """
        response = f"[架构师-技术评审] 已评审，技术方案可行。"
        return Message(content=response, role="Architect")


class Architect(Role):
    """
    架构师角色
    
    Profile: 架构师，负责技术方案设计和架构决策
    Goal: 设计可扩展、高性能、易维护的系统架构
    Constraints: 关注技术可行性、性能和可维护性
    """
    
    name: str = "Architect"
    profile: str = "架构师，负责技术方案设计、架构决策和技术指导"
    goal: str = "设计可扩展、高性能、易维护的系统架构，确保技术方案可行"
    constraints: str = """
    - 关注系统的可扩展性和可维护性
    - 选择成熟稳定的技术栈
    - 平衡技术先进性和稳定性
    - 负责技术方案阶段的执行
    - 参与各阶段的技术咨询
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([DesignArchitecture, TechnicalReview])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取架构师在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "Architect")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断架构师是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断架构师在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断架构师在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断架构师在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行架构师动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        架构师职责：
        1. 需求分析阶段：知会 - 了解需求背景
        2. 技术方案阶段：负责/执行 - 设计系统架构
        3. UI/UX设计阶段：不参与
        4. 任务拆解阶段：咨询 - 提供技术视角
        5. 编码实现阶段：咨询 - 技术指导
        6. UI验收阶段：不参与
        7. 功能测试阶段：咨询 - 技术问题支持
        8. 部署上线阶段：咨询 - 部署架构支持
        9. 运维监控阶段：咨询 - 性能优化建议
        """
