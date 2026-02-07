"""
AI Team - 角色模块

提供8个AI角色的定义和职责矩阵。
"""
from .role_matrix import ParticipationType, RoleMatrix
from .boss import Boss
from .product_manager import ProductManager
from .architect import Architect
from .product_designer import ProductDesigner
from .project_manager import ProjectManager
from .engineer import Engineer
from .qa_engineer import QAEngineer
from .devops import DevOps

__all__ = [
    'ParticipationType',
    'RoleMatrix',
    'Boss',
    'ProductManager',
    'Architect',
    'ProductDesigner',
    'ProjectManager',
    'Engineer',
    'QAEngineer',
    'DevOps'
]
