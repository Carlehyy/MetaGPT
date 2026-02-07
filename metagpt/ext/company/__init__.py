"""
Agent Company - AI驱动的虚拟软件公司
====================================

实现9个阶段的软件开发流程：
1. 需求分析 -> 2. 技术方案设计 -> 3. UI/UX设计 -> 4. 任务拆解
5. 编码实现 -> 6. UI验收 -> 7. 功能测试 -> 8. 部署上线 -> 9. 运维监控

主要组件：
- AgentCompany: 公司主类，协调所有角色和阶段
- WorkflowManager: 工作流管理器，控制阶段流转
- Phase: 阶段类，管理单个阶段的执行
"""

from .agent_company import AgentCompany, CompanyConfig, ProjectStatus
from .workflow import WorkflowManager, PhaseExecutor, PhaseResult

__version__ = "1.0.0"
__all__ = [
    "AgentCompany",
    "CompanyConfig", 
    "ProjectStatus",
    "WorkflowManager",
    "PhaseExecutor",
    "PhaseResult"
]
