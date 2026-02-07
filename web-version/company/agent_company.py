"""
AI虚拟软件公司主类 - 管理9个阶段的完整工作流

功能：
- 管理8个AI角色
- 协调9个阶段的执行
- 集成WebSocket广播
- 跟踪项目状态
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 导入角色模块
import sys
sys.path.insert(0, '/mnt/okcomputer/output')

from roles import (
    BaseRole, Message, DiscussionContext, RoleFactory,
    Boss, ProductManager, Architect, ProductDesigner,
    ProjectManager, Engineer, QAEngineer, DevOps,
    Role as RoleEnum, Phase, ParticipationType,
    get_participation_type, get_roles_by_phase,
    get_phase_description, get_role_description
)
from discussion.engine import (
    DiscussionEngine, DiscussionStatus, DiscussionResult,
    WebSocketBroadcaster
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """项目状态"""
    IDLE = "idle"                    # 空闲
    INITIALIZING = "initializing"    # 初始化中
    RUNNING = "running"              # 运行中
    PAUSED = "paused"                # 暂停
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: Phase
    status: str
    messages: List[Message]
    deliverables: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Project:
    """项目数据类"""
    id: str
    name: str
    description: str
    status: ProjectStatus = ProjectStatus.IDLE
    current_phase: Optional[Phase] = None
    phase_results: List[PhaseResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentCompany:
    """
    AI虚拟软件公司
    
    管理8个AI角色，协调完成9个阶段的软件开发流程
    """
    
    def __init__(
        self,
        max_discussion_rounds: int = 10,
        enable_websocket: bool = True
    ):
        """
        初始化AI虚拟软件公司
        
        Args:
            max_discussion_rounds: 每阶段最大讨论轮数
            enable_websocket: 是否启用WebSocket广播
        """
        self.max_discussion_rounds = max_discussion_rounds
        self.enable_websocket = enable_websocket
        
        # 角色实例
        self.roles: Dict[str, BaseRole] = {}
        
        # 讨论引擎
        self.discussion_engine: Optional[DiscussionEngine] = None
        
        # WebSocket广播器
        self.broadcaster: Optional[WebSocketBroadcaster] = None
        if enable_websocket:
            self.broadcaster = WebSocketBroadcaster()
        
        # 项目状态
        self.current_project: Optional[Project] = None
        self.projects: List[Project] = []
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            "phase_start": [],
            "phase_end": [],
            "message": [],
            "decision": [],
            "error": []
        }
        
        logger.info("AI虚拟软件公司初始化完成")
    
    def _create_roles(self):
        """创建所有角色实例"""
        self.roles = {
            RoleEnum.BOSS.value: Boss(),
            RoleEnum.PRODUCT_MANAGER.value: ProductManager(),
            RoleEnum.ARCHITECT.value: Architect(),
            RoleEnum.PRODUCT_DESIGNER.value: ProductDesigner(),
            RoleEnum.PROJECT_MANAGER.value: ProjectManager(),
            RoleEnum.ENGINEER.value: Engineer(),
            RoleEnum.QA_ENGINEER.value: QAEngineer(),
            RoleEnum.DEVOPS.value: DevOps(),
        }
        logger.info(f"创建 {len(self.roles)} 个角色实例")
    
    def _init_discussion_engine(self):
        """初始化讨论引擎"""
        self.discussion_engine = DiscussionEngine(
            max_rounds=self.max_discussion_rounds
        )
        
        # 注册角色
        for role in self.roles.values():
            self.discussion_engine.register_role(role)
        
        # 添加消息回调
        self.discussion_engine.add_message_callback(self._on_message)
        
        logger.info("讨论引擎初始化完成")
    
    def _on_message(self, message: Message):
        """消息回调"""
        # 触发事件
        self._trigger_event("message", message)
        
        # WebSocket广播
        if self.broadcaster:
            asyncio.create_task(self._broadcast_message(message))
    
    async def _broadcast_message(self, message: Message):
        """广播消息"""
        if not self.broadcaster:
            return
        
        data = {
            "type": "message",
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None
        }
        
        await self.broadcaster.broadcast(data)
    
    def _trigger_event(self, event_type: str, data: Any):
        """触发事件"""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"事件回调失败: {e}")
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """添加事件监听器"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    async def create_project(
        self,
        project_id: str,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        创建新项目
        
        Args:
            project_id: 项目ID
            name: 项目名称
            description: 项目描述
            metadata: 元数据
            
        Returns:
            项目对象
        """
        project = Project(
            id=project_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )
        
        self.projects.append(project)
        self.current_project = project
        
        logger.info(f"创建项目: {name} ({project_id})")
        
        return project
    
    async def start_project(
        self,
        project: Optional[Project] = None,
        start_phase: Optional[Phase] = None
    ) -> List[PhaseResult]:
        """
        启动项目
        
        Args:
            project: 项目对象，默认使用当前项目
            start_phase: 开始阶段，默认从P1开始
            
        Returns:
            阶段结果列表
        """
        if project is None:
            project = self.current_project
        
        if project is None:
            raise ValueError("没有指定项目")
        
        # 初始化
        project.status = ProjectStatus.INITIALIZING
        self._create_roles()
        self._init_discussion_engine()
        
        # 确定阶段顺序
        phases = [
            Phase.P1_REQUIREMENT_ANALYSIS,
            Phase.P2_TECHNICAL_SOLUTION,
            Phase.P3_UI_UX_DESIGN,
            Phase.P4_TASK_BREAKDOWN,
            Phase.P5_CODING_IMPLEMENTATION,
            Phase.P6_UI_ACCEPTANCE,
            Phase.P7_FUNCTIONAL_TESTING,
            Phase.P8_DEPLOYMENT,
            Phase.P9_OPERATION_MONITORING,
        ]
        
        if start_phase:
            start_idx = phases.index(start_phase)
            phases = phases[start_idx:]
        
        # 执行各阶段
        project.status = ProjectStatus.RUNNING
        results = []
        
        for phase in phases:
            try:
                result = await self._execute_phase(project, phase)
                results.append(result)
                
                # 更新项目状态
                project.current_phase = phase
                project.phase_results.append(result)
                project.updated_at = datetime.now()
                
                # 检查是否需要停止
                if result.status == "failed":
                    project.status = ProjectStatus.FAILED
                    break
                
                if result.status == "need_decision":
                    # 等待决策
                    logger.info("等待老板决策...")
                    # 这里可以添加等待逻辑
                
            except Exception as e:
                logger.error(f"阶段 {phase.value} 执行失败: {e}")
                project.status = ProjectStatus.FAILED
                
                result = PhaseResult(
                    phase=phase,
                    status="failed",
                    messages=[],
                    error=str(e)
                )
                results.append(result)
                break
        
        # 项目完成
        if project.status != ProjectStatus.FAILED:
            project.status = ProjectStatus.COMPLETED
        
        return results
    
    async def _execute_phase(
        self,
        project: Project,
        phase: Phase
    ) -> PhaseResult:
        """
        执行单个阶段
        
        Args:
            project: 项目对象
            phase: 阶段
            
        Returns:
            阶段结果
        """
        logger.info(f"开始执行阶段: {phase.value}")
        
        # 触发阶段开始事件
        self._trigger_event("phase_start", phase)
        
        # 广播阶段开始
        if self.broadcaster:
            await self.broadcaster.broadcast({
                "type": "phase_start",
                "phase": phase.value,
                "description": get_phase_description(phase)
            })
        
        # 获取参与角色
        participating_roles = get_roles_by_phase(phase)
        responsible_roles = [r for r in participating_roles 
                           if get_participation_type(phase, r) == ParticipationType.RESPONSIBLE]
        
        logger.info(f"参与角色: {[r.value for r in participating_roles]}")
        logger.info(f"负责角色: {[r.value for r in responsible_roles]}")
        
        # 构建阶段主题
        topic = self._build_phase_topic(phase, project)
        
        # 构建初始消息
        initial_message = self._build_phase_initial_message(phase, project)
        
        # 执行讨论
        start_time = datetime.now()
        
        discussion_result = await self.discussion_engine.start_discussion(
            phase=phase,
            topic=topic,
            initial_message=initial_message,
            required_roles=[r.value for r in participating_roles]
        )
        
        end_time = datetime.now()
        
        # 处理讨论结果
        phase_status = self._map_discussion_status(discussion_result.status)
        
        # 提取交付物
        deliverables = await self._extract_deliverables(phase, discussion_result)
        
        # 创建阶段结果
        result = PhaseResult(
            phase=phase,
            status=phase_status,
            messages=discussion_result.messages,
            deliverables=deliverables,
            summary=discussion_result.summary,
            started_at=start_time,
            completed_at=end_time
        )
        
        # 触发阶段结束事件
        self._trigger_event("phase_end", result)
        
        # 广播阶段结束
        if self.broadcaster:
            await self.broadcaster.broadcast({
                "type": "phase_end",
                "phase": phase.value,
                "status": phase_status,
                "summary": discussion_result.summary
            })
        
        logger.info(f"阶段 {phase.value} 执行完成，状态: {phase_status}")
        
        return result
    
    def _build_phase_topic(self, phase: Phase, project: Project) -> str:
        """构建阶段主题"""
        topics = {
            Phase.P1_REQUIREMENT_ANALYSIS: f"{project.name} - 需求分析",
            Phase.P2_TECHNICAL_SOLUTION: f"{project.name} - 技术方案设计",
            Phase.P3_UI_UX_DESIGN: f"{project.name} - UI/UX设计",
            Phase.P4_TASK_BREAKDOWN: f"{project.name} - 任务拆解",
            Phase.P5_CODING_IMPLEMENTATION: f"{project.name} - 编码实现",
            Phase.P6_UI_ACCEPTANCE: f"{project.name} - UI验收",
            Phase.P7_FUNCTIONAL_TESTING: f"{project.name} - 功能测试",
            Phase.P8_DEPLOYMENT: f"{project.name} - 部署上线",
            Phase.P9_OPERATION_MONITORING: f"{project.name} - 运维监控",
        }
        return topics.get(phase, f"{project.name} - {phase.value}")
    
    def _build_phase_initial_message(self, phase: Phase, project: Project) -> str:
        """构建阶段初始消息"""
        messages = {
            Phase.P1_REQUIREMENT_ANALYSIS: f"""项目：{project.name}
描述：{project.description}

请进行需求分析，输出PRD文档。
需要考虑：
1. 用户需求
2. 业务目标
3. 功能范围
4. 验收标准""",
            
            Phase.P2_TECHNICAL_SOLUTION: """请根据PRD文档制定技术方案。
需要考虑：
1. 系统架构
2. 技术选型
3. 数据库设计
4. API设计
5. 风险评估""",
            
            Phase.P3_UI_UX_DESIGN: """请根据PRD文档进行UI/UX设计。
需要输出：
1. 设计方案
2. 交互流程
3. 视觉规范""",
            
            Phase.P4_TASK_BREAKDOWN: """请进行任务拆解。
需要输出：
1. 任务列表
2. 工作量评估
3. 依赖关系
4. 时间安排""",
            
            Phase.P5_CODING_IMPLEMENTATION: """请进行编码实现。
需要：
1. 按任务完成开发
2. 编写单元测试
3. 代码审查""",
            
            Phase.P6_UI_ACCEPTANCE: """请进行UI验收。
需要检查：
1. 视觉还原度
2. 交互一致性
3. 设计规范符合度""",
            
            Phase.P7_FUNCTIONAL_TESTING: """请进行功能测试。
需要：
1. 执行测试用例
2. 记录缺陷
3. 评估质量
4. UAT验收""",
            
            Phase.P8_DEPLOYMENT: """请进行部署上线。
需要：
1. 部署计划
2. 上线执行
3. 验证检查""",
            
            Phase.P9_OPERATION_MONITORING: """请进行运维监控。
需要：
1. 配置监控
2. 观察指标
3. 处理问题""",
        }
        return messages.get(phase, f"请完成 {phase.value} 阶段的工作")
    
    def _map_discussion_status(self, status: DiscussionStatus) -> str:
        """映射讨论状态到阶段状态"""
        mapping = {
            DiscussionStatus.CONSENSUS: "completed",
            DiscussionStatus.COMPLETED: "completed",
            DiscussionStatus.NEED_DECISION: "need_decision",
            DiscussionStatus.TIMEOUT: "timeout",
            DiscussionStatus.PENDING: "pending",
            DiscussionStatus.IN_PROGRESS: "in_progress",
        }
        return mapping.get(status, "unknown")
    
    async def _extract_deliverables(
        self,
        phase: Phase,
        result: DiscussionResult
    ) -> Dict[str, Any]:
        """提取阶段交付物"""
        deliverables = {}
        
        # 根据阶段提取相应的交付物
        if phase == Phase.P1_REQUIREMENT_ANALYSIS:
            # 提取PRD
            prd_content = self._extract_content_by_keyword(
                result.messages, ["PRD", "需求文档", "产品需求"]
            )
            if prd_content:
                deliverables["prd"] = prd_content
        
        elif phase == Phase.P2_TECHNICAL_SOLUTION:
            # 提取技术方案
            tech_content = self._extract_content_by_keyword(
                result.messages, ["技术方案", "架构设计", "技术选型"]
            )
            if tech_content:
                deliverables["technical_solution"] = tech_content
        
        elif phase == Phase.P3_UI_UX_DESIGN:
            # 提取设计方案
            design_content = self._extract_content_by_keyword(
                result.messages, ["设计", "UI", "UX"]
            )
            if design_content:
                deliverables["design"] = design_content
        
        elif phase == Phase.P4_TASK_BREAKDOWN:
            # 提取任务列表
            task_content = self._extract_content_by_keyword(
                result.messages, ["任务", "拆解", "WBS"]
            )
            if task_content:
                deliverables["tasks"] = task_content
        
        elif phase == Phase.P7_FUNCTIONAL_TESTING:
            # 提取测试报告
            report_content = self._extract_content_by_keyword(
                result.messages, ["测试报告", "质量评估"]
            )
            if report_content:
                deliverables["test_report"] = report_content
        
        return deliverables
    
    def _extract_content_by_keyword(
        self,
        messages: List[Message],
        keywords: List[str]
    ) -> Optional[str]:
        """根据关键词提取内容"""
        for msg in reversed(messages):
            if any(keyword in msg.content for keyword in keywords):
                return msg.content
        return None
    
    def get_project_status(self) -> Dict[str, Any]:
        """获取项目状态"""
        if not self.current_project:
            return {"error": "没有当前项目"}
        
        project = self.current_project
        
        return {
            "id": project.id,
            "name": project.name,
            "status": project.status.value,
            "current_phase": project.current_phase.value if project.current_phase else None,
            "phase_count": len(project.phase_results),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }
    
    def get_phase_results(self) -> List[PhaseResult]:
        """获取阶段结果列表"""
        if not self.current_project:
            return []
        return self.current_project.phase_results.copy()
    
    def get_role(self, role_name: str) -> Optional[BaseRole]:
        """获取角色实例"""
        return self.roles.get(role_name)
    
    def get_all_roles(self) -> Dict[str, BaseRole]:
        """获取所有角色"""
        return self.roles.copy()


# 便捷函数
async def run_software_project(
    project_name: str,
    project_description: str,
    enable_websocket: bool = True
) -> AgentCompany:
    """
    运行软件项目
    
    Args:
        project_name: 项目名称
        project_description: 项目描述
        enable_websocket: 是否启用WebSocket
        
    Returns:
        公司实例
    """
    company = AgentCompany(enable_websocket=enable_websocket)
    
    # 创建项目
    project = await company.create_project(
        project_id=f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        name=project_name,
        description=project_description
    )
    
    # 启动项目
    await company.start_project(project)
    
    return company


if __name__ == "__main__":
    import asyncio
    
    async def test_company():
        company = AgentCompany()
        print(f"AI虚拟软件公司: {company}")
        print(f"最大讨论轮数: {company.max_discussion_rounds}")
        print(f"WebSocket启用: {company.enable_websocket}")
    
    asyncio.run(test_company())
