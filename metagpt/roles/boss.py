"""
老板(Boss)角色实现
负责战略决策、资源分配和最终验收
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class BossAction(Action):
    """老板决策动作"""
    
    name: str = "BossAction"
    context: str = """
    作为公司老板，你需要：
    1. 审批产品需求和战略规划
    2. 分配资源和预算
    3. 对技术方案提供高层意见
    4. 最终验收产品上线
    5. 关注业务目标和ROI
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行老板决策"""
        prompt = f"""
        作为公司老板，请基于以下信息做出决策：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请从战略高度给出意见或决策。
        """
        # 这里可以集成智谱GLM-4.7 API
        response = f"[老板决策] 已审阅相关内容，同意推进。"
        return Message(content=response, role="Boss")


class Boss(Role):
    """
    老板角色
    
    Profile: 公司老板/CEO
    Goal: 确保项目符合公司战略方向，实现业务目标
    Constraints: 关注宏观决策，不过度介入执行细节
    """
    
    name: str = "Boss"
    profile: str = "公司老板/CEO，负责战略决策和资源分配"
    goal: str = "确保项目符合公司战略方向，实现业务目标和ROI最大化"
    constraints: str = """
    - 关注宏观战略决策，不过度介入执行细节
    - 审批关键节点：需求、技术方案、部署上线
    - 提供资源支持和高层指导
    - 对最终结果负责
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([BossAction])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取老板在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "Boss")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断老板是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断老板在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断老板在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断老板在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行老板动作"""
        # 获取当前阶段（可以从环境或上下文中获取）
        # 这里简化处理
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    async def _observe(self, ignore_pinned: bool = False) -> int:
        """观察环境消息"""
        return await super()._observe(ignore_pinned)
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        老板职责：
        1. 需求分析阶段：咨询 - 提供战略方向
        2. 技术方案阶段：咨询 - 审批技术选型
        3. UI/UX设计阶段：知会 - 了解设计方向
        4. 任务拆解阶段：不参与
        5. 编码实现阶段：不参与
        6. UI验收阶段：不参与
        7. 功能测试阶段：不参与
        8. 部署上线阶段：咨询 - 最终验收
        9. 运维监控阶段：知会 - 了解运营状况
        """
