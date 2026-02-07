"""
公司模块 - AI虚拟软件公司

包含：
- AgentCompany: 公司主类
- Project: 项目数据类
- PhaseResult: 阶段结果数据类
"""

from .agent_company import (
    AgentCompany,
    Project,
    PhaseResult,
    ProjectStatus,
    run_software_project
)

__all__ = [
    "AgentCompany",
    "Project",
    "PhaseResult",
    "ProjectStatus",
    "run_software_project",
]
