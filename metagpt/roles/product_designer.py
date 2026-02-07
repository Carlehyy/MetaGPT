"""
产品设计师(ProductDesigner)角色实现
负责UI/UX设计、交互设计和视觉设计
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class DesignUIUX(Action):
    """UI/UX设计动作"""
    
    name: str = "DesignUIUX"
    context: str = """
    作为产品设计师，你需要：
    1. 设计用户界面(UI)
    2. 设计用户体验流程(UX)
    3. 制作原型图和交互设计
    4. 定义设计规范和组件库
    5. 输出设计稿和设计规范文档
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行UI/UX设计"""
        prompt = f"""
        作为产品设计师，请设计UI/UX：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 用户流程图
        2. 线框图/原型图
        3. 视觉设计稿
        4. 交互设计说明
        5. 设计规范
        """
        response = f"[产品设计师-UI/UX设计] 已完成设计稿。"
        return Message(content=response, role="ProductDesigner")


class DesignReview(Action):
    """设计评审动作"""
    
    name: str = "DesignReview"
    context: str = """
    作为产品设计师，你需要：
    1. 评审UI实现效果
    2. 确保设计规范被正确执行
    3. 提供设计优化建议
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行设计评审"""
        prompt = f"""
        作为产品设计师，请评审UI实现：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请给出设计评审意见。
        """
        response = f"[产品设计师-设计评审] 已评审，UI实现符合设计稿。"
        return Message(content=response, role="ProductDesigner")


class ProductDesigner(Role):
    """
    产品设计师角色
    
    Profile: 产品设计师，负责UI/UX设计和交互设计
    Goal: 创造美观、易用、符合用户期望的界面设计
    Constraints: 关注用户体验和视觉一致性
    """
    
    name: str = "ProductDesigner"
    profile: str = "产品设计师，负责UI/UX设计、交互设计和视觉设计"
    goal: str = "创造美观、易用、符合用户期望的界面设计，提升用户体验"
    constraints: str = """
    - 以用户为中心，关注用户体验
    - 保持设计的一致性和规范性
    - 遵循设计原则和行业最佳实践
    - 负责UI/UX设计阶段的执行
    - 与产品经理和开发工程师紧密协作
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([DesignUIUX, DesignReview])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取产品设计师在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "ProductDesigner")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断产品设计师是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断产品设计师在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断产品设计师在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断产品设计师在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行产品设计师动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        产品设计师职责：
        1. 需求分析阶段：知会 - 了解需求
        2. 技术方案阶段：不参与
        3. UI/UX设计阶段：负责/执行 - 设计界面和交互
        4. 任务拆解阶段：知会 - 了解任务分配
        5. 编码实现阶段：不参与
        6. UI验收阶段：负责 - 验收UI实现
        7. 功能测试阶段：知会 - 了解测试情况
        8. 部署上线阶段：不参与
        9. 运维监控阶段：不参与
        """
