"""
运维工程师(DevOps)角色实现
负责部署、运维和监控
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class SetupInfrastructure(Action):
    """基础设施搭建动作"""
    
    name: str = "SetupInfrastructure"
    context: str = """
    作为运维工程师，你需要：
    1. 设计和搭建基础设施
    2. 配置服务器和网络
    3. 设置CI/CD流水线
    4. 配置监控和日志系统
    5. 确保环境安全和稳定
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行基础设施搭建"""
        prompt = f"""
        作为运维工程师，请搭建基础设施：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 基础设施架构
        2. 服务器配置
        3. CI/CD配置
        4. 监控配置
        """
        response = f"[运维工程师-基础设施] 已完成基础设施搭建。"
        return Message(content=response, role="DevOps")


class DeployApplication(Action):
    """应用部署动作"""
    
    name: str = "DeployApplication"
    context: str = """
    作为运维工程师，你需要：
    1. 执行应用部署
    2. 配置部署环境
    3. 管理部署流程
    4. 处理部署问题
    5. 验证部署结果
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行应用部署"""
        prompt = f"""
        作为运维工程师，请部署应用：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 部署计划
        2. 部署步骤
        3. 回滚方案
        4. 部署结果
        """
        response = f"[运维工程师-应用部署] 已完成应用部署。"
        return Message(content=response, role="DevOps")


class MonitorSystem(Action):
    """系统监控动作"""
    
    name: str = "MonitorSystem"
    context: str = """
    作为运维工程师，你需要：
    1. 监控系统运行状态
    2. 处理系统告警
    3. 分析系统性能
    4. 优化系统资源
    5. 输出运维报告
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行系统监控"""
        prompt = f"""
        作为运维工程师，请监控系统：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 系统状态
        2. 性能指标
        3. 告警处理
        4. 优化建议
        """
        response = f"[运维工程师-系统监控] 系统运行正常。"
        return Message(content=response, role="DevOps")


class DevOps(Role):
    """
    运维工程师角色
    
    Profile: 运维工程师，负责部署、运维和监控
    Goal: 确保系统稳定运行，快速响应问题
    Constraints: 关注系统稳定性、安全性和可扩展性
    """
    
    name: str = "DevOps"
    profile: str = "运维工程师，负责部署、运维和系统监控"
    goal: str = "确保系统稳定运行，快速响应问题，保障业务连续性"
    constraints: str = """
    - 确保系统高可用性和稳定性
    - 快速响应和处理故障
    - 优化系统性能和资源利用率
    - 负责部署上线和运维监控阶段的执行
    - 保障系统安全和数据安全
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([SetupInfrastructure, DeployApplication, MonitorSystem])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取运维工程师在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "DevOps")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断运维工程师是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断运维工程师在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断运维工程师在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断运维工程师在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行运维工程师动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        运维工程师职责：
        1. 需求分析阶段：不参与
        2. 技术方案阶段：咨询 - 提供运维视角
        3. UI/UX设计阶段：不参与
        4. 任务拆解阶段：咨询 - 评估运维任务
        5. 编码实现阶段：不参与
        6. UI验收阶段：不参与
        7. 功能测试阶段：不参与
        8. 部署上线阶段：执行 - 执行部署
        9. 运维监控阶段：负责/执行 - 运维监控
        """
