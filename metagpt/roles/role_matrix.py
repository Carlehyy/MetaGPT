"""
职责矩阵定义模块
定义项目各阶段中各角色的参与类型
"""

from enum import Enum
from typing import Dict, Optional


class ParticipationType(Enum):
    """参与类型枚举"""
    LEAD = "负责/执行"      # 负责并执行该阶段工作
    CONSULT = "咨询"        # 提供咨询意见
    INFORM = "知会"         # 知会/通知
    NONE = "-"              # 不参与


class ProjectPhase(Enum):
    """项目阶段枚举"""
    REQUIREMENT_ANALYSIS = "1.需求分析"
    TECHNICAL_SOLUTION = "2.技术方案"
    UI_UX_DESIGN = "3.UI/UX设计"
    TASK_BREAKDOWN = "4.任务拆解"
    CODING_IMPLEMENTATION = "5.编码实现"
    UI_ACCEPTANCE = "6.UI验收"
    FUNCTIONAL_TESTING = "7.功能测试"
    DEPLOYMENT = "8.部署上线"
    OPERATIONS_MONITORING = "9.运维监控"


# 职责矩阵定义
# 行：项目阶段
# 列：角色（老板, 产品经理, 架构师, 产品设计师, 项目经理, 开发工程师, 测试工程师, 运维工程师）
RESPONSIBILITY_MATRIX: Dict[ProjectPhase, Dict[str, ParticipationType]] = {
    ProjectPhase.REQUIREMENT_ANALYSIS: {
        "Boss": ParticipationType.CONSULT,
        "ProductManager": ParticipationType.LEAD,
        "Architect": ParticipationType.INFORM,
        "ProductDesigner": ParticipationType.INFORM,
        "ProjectManager": ParticipationType.INFORM,
        "Engineer": ParticipationType.NONE,
        "QAEngineer": ParticipationType.NONE,
        "DevOps": ParticipationType.NONE,
    },
    ProjectPhase.TECHNICAL_SOLUTION: {
        "Boss": ParticipationType.CONSULT,
        "ProductManager": ParticipationType.CONSULT,
        "Architect": ParticipationType.LEAD,
        "ProductDesigner": ParticipationType.NONE,
        "ProjectManager": ParticipationType.INFORM,
        "Engineer": ParticipationType.CONSULT,
        "QAEngineer": ParticipationType.INFORM,
        "DevOps": ParticipationType.CONSULT,
    },
    ProjectPhase.UI_UX_DESIGN: {
        "Boss": ParticipationType.INFORM,
        "ProductManager": ParticipationType.CONSULT,  # 验收
        "Architect": ParticipationType.NONE,
        "ProductDesigner": ParticipationType.LEAD,
        "ProjectManager": ParticipationType.INFORM,
        "Engineer": ParticipationType.CONSULT,
        "QAEngineer": ParticipationType.NONE,
        "DevOps": ParticipationType.NONE,
    },
    ProjectPhase.TASK_BREAKDOWN: {
        "Boss": ParticipationType.NONE,
        "ProductManager": ParticipationType.CONSULT,
        "Architect": ParticipationType.CONSULT,  # 负责
        "ProductDesigner": ParticipationType.INFORM,
        "ProjectManager": ParticipationType.LEAD,
        "Engineer": ParticipationType.CONSULT,
        "QAEngineer": ParticipationType.CONSULT,
        "DevOps": ParticipationType.CONSULT,
    },
    ProjectPhase.CODING_IMPLEMENTATION: {
        "Boss": ParticipationType.NONE,
        "ProductManager": ParticipationType.INFORM,
        "Architect": ParticipationType.CONSULT,
        "ProductDesigner": ParticipationType.NONE,
        "ProjectManager": ParticipationType.CONSULT,
        "Engineer": ParticipationType.LEAD,
        "QAEngineer": ParticipationType.NONE,
        "DevOps": ParticipationType.NONE,
    },
    ProjectPhase.UI_ACCEPTANCE: {
        "Boss": ParticipationType.NONE,
        "ProductManager": ParticipationType.CONSULT,  # 验收
        "Architect": ParticipationType.NONE,
        "ProductDesigner": ParticipationType.LEAD,
        "ProjectManager": ParticipationType.INFORM,
        "Engineer": ParticipationType.CONSULT,  # 执行
        "QAEngineer": ParticipationType.NONE,
        "DevOps": ParticipationType.NONE,
    },
    ProjectPhase.FUNCTIONAL_TESTING: {
        "Boss": ParticipationType.NONE,
        "ProductManager": ParticipationType.CONSULT,  # 验收UAT
        "Architect": ParticipationType.CONSULT,
        "ProductDesigner": ParticipationType.INFORM,
        "ProjectManager": ParticipationType.CONSULT,
        "Engineer": ParticipationType.CONSULT,  # 执行
        "QAEngineer": ParticipationType.LEAD,
        "DevOps": ParticipationType.NONE,
    },
    ProjectPhase.DEPLOYMENT: {
        "Boss": ParticipationType.CONSULT,  # 验收
        "ProductManager": ParticipationType.INFORM,
        "Architect": ParticipationType.CONSULT,
        "ProductDesigner": ParticipationType.NONE,
        "ProjectManager": ParticipationType.LEAD,
        "Engineer": ParticipationType.CONSULT,
        "QAEngineer": ParticipationType.CONSULT,
        "DevOps": ParticipationType.CONSULT,  # 执行
    },
    ProjectPhase.OPERATIONS_MONITORING: {
        "Boss": ParticipationType.INFORM,
        "ProductManager": ParticipationType.INFORM,
        "Architect": ParticipationType.CONSULT,
        "ProductDesigner": ParticipationType.NONE,
        "ProjectManager": ParticipationType.NONE,
        "Engineer": ParticipationType.CONSULT,
        "QAEngineer": ParticipationType.INFORM,
        "DevOps": ParticipationType.LEAD,
    },
}


def get_participation_type(phase: ProjectPhase, role_name: str) -> ParticipationType:
    """
    获取指定角色在指定阶段的参与类型
    
    Args:
        phase: 项目阶段
        role_name: 角色名称
        
    Returns:
        参与类型
    """
    if phase in RESPONSIBILITY_MATRIX:
        return RESPONSIBILITY_MATRIX[phase].get(role_name, ParticipationType.NONE)
    return ParticipationType.NONE


def get_role_phases(role_name: str) -> Dict[ProjectPhase, ParticipationType]:
    """
    获取指定角色在所有阶段的参与情况
    
    Args:
        role_name: 角色名称
        
    Returns:
        阶段到参与类型的映射字典
    """
    result = {}
    for phase in ProjectPhase:
        result[phase] = get_participation_type(phase, role_name)
    return result


def get_phase_roles(phase: ProjectPhase) -> Dict[str, ParticipationType]:
    """
    获取指定阶段所有角色的参与情况
    
    Args:
        phase: 项目阶段
        
    Returns:
        角色名称到参与类型的映射字典
    """
    return RESPONSIBILITY_MATRIX.get(phase, {})


def is_lead(phase: ProjectPhase, role_name: str) -> bool:
    """判断角色在指定阶段是否负责/执行"""
    return get_participation_type(phase, role_name) == ParticipationType.LEAD


def is_consult(phase: ProjectPhase, role_name: str) -> bool:
    """判断角色在指定阶段是否提供咨询"""
    return get_participation_type(phase, role_name) == ParticipationType.CONSULT


def is_inform(phase: ProjectPhase, role_name: str) -> bool:
    """判断角色在指定阶段是否被知会"""
    return get_participation_type(phase, role_name) == ParticipationType.INFORM


def is_participating(phase: ProjectPhase, role_name: str) -> bool:
    """判断角色在指定阶段是否参与（非NONE）"""
    return get_participation_type(phase, role_name) != ParticipationType.NONE
