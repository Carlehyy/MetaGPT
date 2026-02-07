"""
MetaGPT角色模块

包含8个角色：
- Boss: 老板
- ProductManager: 产品经理
- Architect: 架构师
- ProductDesigner: 产品设计师
- ProjectManager: 项目经理
- Engineer: 开发工程师
- QAEngineer: 测试工程师
- DevOps: 运维工程师

以及职责矩阵定义：
- ParticipationType: 参与类型枚举
- ProjectPhase: 项目阶段枚举
- RESPONSIBILITY_MATRIX: 职责矩阵
"""

# 角色类
from .boss import Boss
from .product_manager import ProductManager
from .architect import Architect
from .product_designer import ProductDesigner
from .project_manager import ProjectManager
from .engineer import Engineer
from .qa_engineer import QAEngineer
from .devops import DevOps

# 职责矩阵定义
from .role_matrix import (
    ParticipationType,
    ProjectPhase,
    RESPONSIBILITY_MATRIX,
    get_participation_type,
    get_role_phases,
    get_phase_roles,
    is_lead,
    is_consult,
    is_inform,
    is_participating,
)

# 智谱GLM-4.7 API配置
ZHIPU_API_KEY = "0a45a0e3e24f47c79552db2ab80a8a54.NRH2PVmbIt4wBYre"
ZHIPU_API_BASE = "https://open.bigmodel.cn/api/paas/v4"

# 导出所有角色和常量
__all__ = [
    # 角色类
    "Boss",
    "ProductManager",
    "Architect",
    "ProductDesigner",
    "ProjectManager",
    "Engineer",
    "QAEngineer",
    "DevOps",
    # 职责矩阵
    "ParticipationType",
    "ProjectPhase",
    "RESPONSIBILITY_MATRIX",
    "get_participation_type",
    "get_role_phases",
    "get_phase_roles",
    "is_lead",
    "is_consult",
    "is_inform",
    "is_participating",
    # API配置
    "ZHIPU_API_KEY",
    "ZHIPU_API_BASE",
]


def get_all_roles():
    """获取所有角色实例"""
    return [
        Boss(),
        ProductManager(),
        Architect(),
        ProductDesigner(),
        ProjectManager(),
        Engineer(),
        QAEngineer(),
        DevOps(),
    ]


def get_role_by_name(name: str):
    """根据名称获取角色实例"""
    role_map = {
        "Boss": Boss,
        "ProductManager": ProductManager,
        "Architect": Architect,
        "ProductDesigner": ProductDesigner,
        "ProjectManager": ProjectManager,
        "Engineer": Engineer,
        "QAEngineer": QAEngineer,
        "DevOps": DevOps,
    }
    role_class = role_map.get(name)
    return role_class() if role_class else None


def print_responsibility_matrix():
    """打印职责矩阵表格"""
    from .role_matrix import ProjectPhase
    
    print("=" * 120)
    print("职责矩阵（9个阶段×8个角色）")
    print("=" * 120)
    
    # 表头
    header = f"{'阶段':<15} | {'老板':<8} | {'产品经理':<10} | {'架构师':<8} | {'产品设计师':<10} | {'项目经理':<10} | {'开发工程师':<10} | {'测试工程师':<10} | {'运维工程师':<10}"
    print(header)
    print("-" * 120)
    
    # 数据行
    for phase in ProjectPhase:
        roles = RESPONSIBILITY_MATRIX.get(phase, {})
        row = f"{phase.value:<15} | {roles.get('Boss', ParticipationType.NONE).value:<8} | {roles.get('ProductManager', ParticipationType.NONE).value:<10} | {roles.get('Architect', ParticipationType.NONE).value:<8} | {roles.get('ProductDesigner', ParticipationType.NONE).value:<10} | {roles.get('ProjectManager', ParticipationType.NONE).value:<10} | {roles.get('Engineer', ParticipationType.NONE).value:<10} | {roles.get('QAEngineer', ParticipationType.NONE).value:<10} | {roles.get('DevOps', ParticipationType.NONE).value:<10}"
        print(row)
    
    print("=" * 120)


if __name__ == "__main__":
    # 测试导入
    print("MetaGPT角色模块加载成功！")
    print(f"\n可用角色：")
    for role in get_all_roles():
        print(f"  - {role.name}: {role.profile}")
    
    print("\n")
    print_responsibility_matrix()
