"""
产品经理(ProductManager)角色实现
负责需求分析、产品规划和验收
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class AnalyzeRequirements(Action):
    """需求分析动作"""
    
    name: str = "AnalyzeRequirements"
    context: str = """
    作为产品经理，你需要：
    1. 收集和分析用户需求
    2. 编写产品需求文档(PRD)
    3. 定义功能优先级
    4. 确定产品目标和成功指标
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行需求分析"""
        prompt = f"""
        作为产品经理，请分析以下需求：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 用户需求分析
        2. 功能需求列表
        3. 优先级排序
        4. 产品目标定义
        """
        response = f"[产品经理-需求分析] 已完成需求分析，输出PRD文档。"
        return Message(content=response, role="ProductManager")


class ProductAcceptance(Action):
    """产品验收动作"""
    
    name: str = "ProductAcceptance"
    context: str = """
    作为产品经理，你需要：
    1. 验收UI设计是否符合需求
    2. 进行UAT测试验收
    3. 确认产品功能完整性
    4. 批准产品上线
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行产品验收"""
        prompt = f"""
        作为产品经理，请验收以下内容：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请给出验收意见。
        """
        response = f"[产品经理-验收] 已验收，符合需求，可以上线。"
        return Message(content=response, role="ProductManager")


class ProductManager(Role):
    """
    产品经理角色
    
    Profile: 产品经理，负责产品规划和需求管理
    Goal: 确保产品满足用户需求，实现产品目标
    Constraints: 关注用户体验和商业价值
    """
    
    name: str = "ProductManager"
    profile: str = "产品经理，负责产品规划、需求分析和验收"
    goal: str = "确保产品满足用户需求，实现产品目标和商业价值"
    constraints: str = """
    - 以用户为中心，关注用户体验
    - 平衡功能、时间和资源
    - 编写清晰的需求文档
    - 负责需求分析阶段的执行
    - 参与各阶段的验收工作
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([AnalyzeRequirements, ProductAcceptance])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取产品经理在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "ProductManager")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断产品经理是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断产品经理在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断产品经理在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断产品经理在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行产品经理动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        产品经理职责：
        1. 需求分析阶段：负责/执行 - 收集需求，编写PRD
        2. 技术方案阶段：咨询 - 提供产品视角
        3. UI/UX设计阶段：咨询 - 验收设计
        4. 任务拆解阶段：咨询 - 确认任务完整性
        5. 编码实现阶段：知会 - 了解进度
        6. UI验收阶段：咨询 - 验收UI
        7. 功能测试阶段：咨询 - UAT验收
        8. 部署上线阶段：知会 - 了解上线计划
        9. 运维监控阶段：知会 - 了解运营数据
        """
