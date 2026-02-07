"""
AI Team - 公司模块

提供公司主类和工作流管理功能。
"""
from .agent_company import AgentCompany, CompanyConfig
from .workflow import WorkflowManager, PhaseExecutor

__all__ = ['AgentCompany', 'CompanyConfig', 'WorkflowManager', 'PhaseExecutor']
