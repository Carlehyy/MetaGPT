"""
项目经理(ProjectManager)角色实现
负责项目管理、任务拆解和进度跟踪
"""

from typing import Optional, List
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.actions import Action

from .role_matrix import ProjectPhase, ParticipationType, get_participation_type


# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"


class BreakdownTasks(Action):
    """任务拆解动作"""
    
    name: str = "BreakdownTasks"
    context: str = """
    作为项目经理，你需要：
    1. 将需求拆解为具体任务
    2. 估算任务工时
    3. 分配任务给团队成员
    4. 制定项目计划和里程碑
    5. 识别项目风险和依赖
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行任务拆解"""
        prompt = f"""
        作为项目经理，请拆解任务：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出：
        1. 任务清单
        2. 工时估算
        3. 任务分配
        4. 项目计划
        5. 风险识别
        """
        response = f"[项目经理-任务拆解] 已完成任务拆解和计划制定。"
        return Message(content=response, role="ProjectManager")


class TrackProgress(Action):
    """进度跟踪动作"""
    
    name: str = "TrackProgress"
    context: str = """
    作为项目经理，你需要：
    1. 跟踪项目进度
    2. 协调团队成员
    3. 解决项目阻塞
    4. 汇报项目状态
    5. 管理项目变更
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行进度跟踪"""
        prompt = f"""
        作为项目经理，请跟踪项目进度：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出项目状态报告。
        """
        response = f"[项目经理-进度跟踪] 项目进度正常，按计划推进。"
        return Message(content=response, role="ProjectManager")


class ManageDeployment(Action):
    """部署管理动作"""
    
    name: str = "ManageDeployment"
    context: str = """
    作为项目经理，你需要：
    1. 协调部署上线工作
    2. 确认上线 checklist
    3. 管理上线风险
    4. 组织上线评审
    """
    
    async def run(self, messages: List[Message], context: Optional[str] = None) -> Message:
        """执行部署管理"""
        prompt = f"""
        作为项目经理，请管理部署上线：
        
        上下文：{context or '无'}
        历史消息：{[m.content for m in messages]}
        
        请输出上线计划和协调方案。
        """
        response = f"[项目经理-部署管理] 已协调部署上线工作。"
        return Message(content=response, role="ProjectManager")


class ProjectManager(Role):
    """
    项目经理角色
    
    Profile: 项目经理，负责项目管理和团队协调
    Goal: 确保项目按时、按质、按预算完成
    Constraints: 关注进度、质量和资源协调
    """
    
    name: str = "ProjectManager"
    profile: str = "项目经理，负责项目管理、任务拆解和进度跟踪"
    goal: str = "确保项目按时、按质、按预算完成，协调团队高效协作"
    constraints: str = """
    - 关注项目进度和质量
    - 合理分配资源
    - 及时识别和解决风险
    - 负责任务拆解和部署上线阶段的执行
    - 保持团队沟通顺畅
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置智谱API配置
        self.llm.api_key = ZHIPU_API_KEY
        self.llm.base_url = ZHIPU_API_BASE
        self.llm.model = "glm-4"
        
        # 添加动作
        self._init_actions([BreakdownTasks, TrackProgress, ManageDeployment])
    
    def get_participation_type(self, phase: ProjectPhase) -> ParticipationType:
        """
        获取项目经理在指定阶段的参与类型
        
        Args:
            phase: 项目阶段
            
        Returns:
            参与类型
        """
        return get_participation_type(phase, "ProjectManager")
    
    def should_participate(self, phase: ProjectPhase) -> bool:
        """判断项目经理是否需要在指定阶段参与"""
        participation = self.get_participation_type(phase)
        return participation != ParticipationType.NONE
    
    def is_lead(self, phase: ProjectPhase) -> bool:
        """判断项目经理在指定阶段是否负责"""
        return self.get_participation_type(phase) == ParticipationType.LEAD
    
    def is_consult(self, phase: ProjectPhase) -> bool:
        """判断项目经理在指定阶段是否提供咨询"""
        return self.get_participation_type(phase) == ParticipationType.CONSULT
    
    def is_inform(self, phase: ProjectPhase) -> bool:
        """判断项目经理在指定阶段是否需要知会"""
        return self.get_participation_type(phase) == ParticipationType.INFORM
    
    async def _act(self) -> Message:
        """执行项目经理动作"""
        msg = await self._rc.todo.run(self._rc.history)
        return msg
    
    def get_responsibility_description(self) -> str:
        """获取职责描述"""
        return """
        项目经理职责：
        1. 需求分析阶段：知会 - 了解需求
        2. 技术方案阶段：知会 - 了解技术方案
        3. UI/UX设计阶段：知会 - 了解设计进度
        4. 任务拆解阶段：负责/执行 - 拆解任务，制定计划
        5. 编码实现阶段：咨询 - 跟踪进度
        6. UI验收阶段：知会 - 了解验收情况
        7. 功能测试阶段：咨询 - 协调测试
        8. 部署上线阶段：负责 - 协调上线
        9. 运维监控阶段：不参与
        """
