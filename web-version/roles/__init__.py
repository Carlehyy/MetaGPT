"""
角色模块 - AI虚拟软件公司角色系统

提供8个AI角色的实现和职责矩阵管理
"""

# 职责矩阵
from .role_matrix import (
    ParticipationType,
    Role,
    Phase,
    get_participation_type,
    get_roles_by_phase,
    get_responsible_roles,
    get_consult_roles,
    get_inform_roles,
    should_notify_boss,
    get_phase_description,
    get_role_description,
    print_matrix,
)

# 基类
from .base_role import (
    BaseRole,
    Message,
    DiscussionContext,
    RoleFactory,
    create_system_prompt,
    GLM4_API_KEY,
    GLM4_BASE_URL,
    GLM4_MODEL,
)

# 8个角色
from .boss import Boss
from .product_manager import ProductManager
from .architect import Architect
from .product_designer import ProductDesigner
from .project_manager import ProjectManager
from .engineer import Engineer
from .qa_engineer import QAEngineer
from .devops import DevOps

__all__ = [
    # 职责矩阵
    "ParticipationType",
    "Role",
    "Phase",
    "get_participation_type",
    "get_roles_by_phase",
    "get_responsible_roles",
    "get_consult_roles",
    "get_inform_roles",
    "should_notify_boss",
    "get_phase_description",
    "get_role_description",
    "print_matrix",
    # 基类
    "BaseRole",
    "Message",
    "DiscussionContext",
    "RoleFactory",
    "create_system_prompt",
    "GLM4_API_KEY",
    "GLM4_BASE_URL",
    "GLM4_MODEL",
    # 角色
    "Boss",
    "ProductManager",
    "Architect",
    "ProductDesigner",
    "ProjectManager",
    "Engineer",
    "QAEngineer",
    "DevOps",
]
