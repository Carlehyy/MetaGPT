"""
职责矩阵模块 - 定义8个角色在9个阶段的参与类型

参与类型定义:
- RESPONSIBLE: 负责/执行 - 主导该阶段，输出主要交付物
- CONSULT: 咨询 - 提供专业意见，参与讨论
- INFORM: 知会 - 了解情况，必要时参与
- NONE: 不参与
"""

from enum import Enum
from typing import Dict, List, Set, Optional


class ParticipationType(Enum):
    """参与类型枚举"""
    RESPONSIBLE = "负责/执行"  # 主导该阶段，输出主要交付物
    CONSULT = "咨询"          # 提供专业意见，参与讨论
    INFORM = "知会"           # 了解情况，必要时参与
    NONE = "-"                # 不参与


class Role(Enum):
    """角色枚举"""
    BOSS = "老板"
    PRODUCT_MANAGER = "产品经理"
    ARCHITECT = "架构师"
    PRODUCT_DESIGNER = "产品设计师"
    PROJECT_MANAGER = "项目经理"
    ENGINEER = "开发工程师"
    QA_ENGINEER = "测试工程师"
    DEVOPS = "运维工程师"


class Phase(Enum):
    """阶段枚举"""
    P1_REQUIREMENT_ANALYSIS = "P1_需求分析"
    P2_TECHNICAL_SOLUTION = "P2_技术方案"
    P3_UI_UX_DESIGN = "P3_UI/UX设计"
    P4_TASK_BREAKDOWN = "P4_任务拆解"
    P5_CODING_IMPLEMENTATION = "P5_编码实现"
    P6_UI_ACCEPTANCE = "P6_UI验收"
    P7_FUNCTIONAL_TESTING = "P7_功能测试"
    P8_DEPLOYMENT = "P8_部署上线"
    P9_OPERATION_MONITORING = "P9_运维监控"


# 职责矩阵定义
# 行: 阶段, 列: 角色
RESPONSIBILITY_MATRIX: Dict[Phase, Dict[Role, ParticipationType]] = {
    Phase.P1_REQUIREMENT_ANALYSIS: {
        Role.BOSS: ParticipationType.CONSULT,
        Role.PRODUCT_MANAGER: ParticipationType.RESPONSIBLE,
        Role.ARCHITECT: ParticipationType.INFORM,
        Role.PRODUCT_DESIGNER: ParticipationType.INFORM,
        Role.PROJECT_MANAGER: ParticipationType.INFORM,
        Role.ENGINEER: ParticipationType.NONE,
        Role.QA_ENGINEER: ParticipationType.NONE,
        Role.DEVOPS: ParticipationType.NONE,
    },
    Phase.P2_TECHNICAL_SOLUTION: {
        Role.BOSS: ParticipationType.CONSULT,
        Role.PRODUCT_MANAGER: ParticipationType.CONSULT,
        Role.ARCHITECT: ParticipationType.RESPONSIBLE,
        Role.PRODUCT_DESIGNER: ParticipationType.NONE,
        Role.PROJECT_MANAGER: ParticipationType.INFORM,
        Role.ENGINEER: ParticipationType.CONSULT,
        Role.QA_ENGINEER: ParticipationType.INFORM,
        Role.DEVOPS: ParticipationType.CONSULT,
    },
    Phase.P3_UI_UX_DESIGN: {
        Role.BOSS: ParticipationType.INFORM,
        Role.PRODUCT_MANAGER: ParticipationType.RESPONSIBLE,  # 验收
        Role.ARCHITECT: ParticipationType.NONE,
        Role.PRODUCT_DESIGNER: ParticipationType.RESPONSIBLE,  # 执行
        Role.PROJECT_MANAGER: ParticipationType.INFORM,
        Role.ENGINEER: ParticipationType.CONSULT,
        Role.QA_ENGINEER: ParticipationType.NONE,
        Role.DEVOPS: ParticipationType.NONE,
    },
    Phase.P4_TASK_BREAKDOWN: {
        Role.BOSS: ParticipationType.NONE,
        Role.PRODUCT_MANAGER: ParticipationType.CONSULT,
        Role.ARCHITECT: ParticipationType.RESPONSIBLE,
        Role.PRODUCT_DESIGNER: ParticipationType.INFORM,
        Role.PROJECT_MANAGER: ParticipationType.RESPONSIBLE,
        Role.ENGINEER: ParticipationType.CONSULT,
        Role.QA_ENGINEER: ParticipationType.CONSULT,
        Role.DEVOPS: ParticipationType.CONSULT,
    },
    Phase.P5_CODING_IMPLEMENTATION: {
        Role.BOSS: ParticipationType.NONE,
        Role.PRODUCT_MANAGER: ParticipationType.INFORM,
        Role.ARCHITECT: ParticipationType.CONSULT,
        Role.PRODUCT_DESIGNER: ParticipationType.NONE,
        Role.PROJECT_MANAGER: ParticipationType.CONSULT,
        Role.ENGINEER: ParticipationType.RESPONSIBLE,
        Role.QA_ENGINEER: ParticipationType.NONE,
        Role.DEVOPS: ParticipationType.NONE,
    },
    Phase.P6_UI_ACCEPTANCE: {
        Role.BOSS: ParticipationType.NONE,
        Role.PRODUCT_MANAGER: ParticipationType.RESPONSIBLE,  # 验收
        Role.ARCHITECT: ParticipationType.NONE,
        Role.PRODUCT_DESIGNER: ParticipationType.RESPONSIBLE,
        Role.PROJECT_MANAGER: ParticipationType.INFORM,
        Role.ENGINEER: ParticipationType.RESPONSIBLE,  # 执行
        Role.QA_ENGINEER: ParticipationType.NONE,
        Role.DEVOPS: ParticipationType.NONE,
    },
    Phase.P7_FUNCTIONAL_TESTING: {
        Role.BOSS: ParticipationType.NONE,
        Role.PRODUCT_MANAGER: ParticipationType.RESPONSIBLE,  # UAT验收
        Role.ARCHITECT: ParticipationType.CONSULT,
        Role.PRODUCT_DESIGNER: ParticipationType.INFORM,
        Role.PROJECT_MANAGER: ParticipationType.CONSULT,
        Role.ENGINEER: ParticipationType.RESPONSIBLE,  # 执行修复
        Role.QA_ENGINEER: ParticipationType.RESPONSIBLE,
        Role.DEVOPS: ParticipationType.NONE,
    },
    Phase.P8_DEPLOYMENT: {
        Role.BOSS: ParticipationType.RESPONSIBLE,  # 验收
        Role.PRODUCT_MANAGER: ParticipationType.INFORM,
        Role.ARCHITECT: ParticipationType.CONSULT,
        Role.PRODUCT_DESIGNER: ParticipationType.NONE,
        Role.PROJECT_MANAGER: ParticipationType.RESPONSIBLE,
        Role.ENGINEER: ParticipationType.CONSULT,
        Role.QA_ENGINEER: ParticipationType.CONSULT,
        Role.DEVOPS: ParticipationType.RESPONSIBLE,  # 执行
    },
    Phase.P9_OPERATION_MONITORING: {
        Role.BOSS: ParticipationType.INFORM,
        Role.PRODUCT_MANAGER: ParticipationType.INFORM,
        Role.ARCHITECT: ParticipationType.CONSULT,
        Role.PRODUCT_DESIGNER: ParticipationType.NONE,
        Role.PROJECT_MANAGER: ParticipationType.NONE,
        Role.ENGINEER: ParticipationType.CONSULT,
        Role.QA_ENGINEER: ParticipationType.INFORM,
        Role.DEVOPS: ParticipationType.RESPONSIBLE,
    },
}


def get_participation_type(phase: Phase, role: Role) -> ParticipationType:
    """
    获取指定阶段和角色的参与类型
    
    Args:
        phase: 阶段枚举
        role: 角色枚举
        
    Returns:
        参与类型枚举
    """
    return RESPONSIBILITY_MATRIX.get(phase, {}).get(role, ParticipationType.NONE)


def get_roles_by_phase(phase: Phase, participation_filter: Optional[ParticipationType] = None) -> List[Role]:
    """
    获取指定阶段的所有角色
    
    Args:
        phase: 阶段枚举
        participation_filter: 可选的参与类型过滤器，只返回指定类型的角色
        
    Returns:
        角色列表
    """
    phase_roles = RESPONSIBILITY_MATRIX.get(phase, {})
    
    if participation_filter is None:
        # 返回所有参与的角色（排除NONE）
        return [role for role, ptype in phase_roles.items() if ptype != ParticipationType.NONE]
    else:
        # 返回指定参与类型的角色
        return [role for role, ptype in phase_roles.items() if ptype == participation_filter]


def get_responsible_roles(phase: Phase) -> List[Role]:
    """
    获取指定阶段的负责/执行角色
    
    Args:
        phase: 阶段枚举
        
    Returns:
        负责角色列表
    """
    return get_roles_by_phase(phase, ParticipationType.RESPONSIBLE)


def get_consult_roles(phase: Phase) -> List[Role]:
    """
    获取指定阶段的咨询角色
    
    Args:
        phase: 阶段枚举
        
    Returns:
        咨询角色列表
    """
    return get_roles_by_phase(phase, ParticipationType.CONSULT)


def get_inform_roles(phase: Phase) -> List[Role]:
    """
    获取指定阶段的知会角色
    
    Args:
        phase: 阶段枚举
        
    Returns:
        知会角色列表
    """
    return get_roles_by_phase(phase, ParticipationType.INFORM)


def should_notify_boss(phase: Phase, role: Role) -> bool:
    """
    判断是否需要通知老板
    
    规则:
    1. 如果老板在该阶段是负责/执行，则一定通知
    2. 如果老板在该阶段是咨询，则根据发起角色决定是否通知
    3. 如果老板在该阶段是知会，则仅在特定情况下通知
    
    Args:
        phase: 阶段枚举
        role: 发起通知的角色
        
    Returns:
        是否需要通知老板
    """
    boss_participation = get_participation_type(phase, Role.BOSS)
    
    # 老板负责，必须通知
    if boss_participation == ParticipationType.RESPONSIBLE:
        return True
    
    # 老板不参与，不通知
    if boss_participation == ParticipationType.NONE:
        return False
    
    # 老板是咨询或知会，根据阶段和角色判断
    # P1, P2, P8 等关键决策点需要通知
    critical_phases = [Phase.P1_REQUIREMENT_ANALYSIS, Phase.P2_TECHNICAL_SOLUTION, Phase.P8_DEPLOYMENT]
    
    if phase in critical_phases:
        return True
    
    # 如果是负责角色发起，且老板是咨询，则通知
    if get_participation_type(phase, role) == ParticipationType.RESPONSIBLE and boss_participation == ParticipationType.CONSULT:
        return True
    
    return False


def get_phase_description(phase: Phase) -> str:
    """
    获取阶段描述
    
    Args:
        phase: 阶段枚举
        
    Returns:
        阶段描述字符串
    """
    descriptions = {
        Phase.P1_REQUIREMENT_ANALYSIS: "需求分析阶段 - 产品经理主导，分析用户需求，编写PRD文档",
        Phase.P2_TECHNICAL_SOLUTION: "技术方案阶段 - 架构师主导，设计系统架构和技术方案",
        Phase.P3_UI_UX_DESIGN: "UI/UX设计阶段 - 设计师主导，输出设计稿",
        Phase.P4_TASK_BREAKDOWN: "任务拆解阶段 - 项目经理和架构师主导，拆解开发任务",
        Phase.P5_CODING_IMPLEMENTATION: "编码实现阶段 - 开发工程师主导，完成代码开发",
        Phase.P6_UI_ACCEPTANCE: "UI验收阶段 - 产品经理和设计师主导，验收UI实现",
        Phase.P7_FUNCTIONAL_TESTING: "功能测试阶段 - 测试工程师主导，完成功能测试和UAT",
        Phase.P8_DEPLOYMENT: "部署上线阶段 - 项目经理和运维主导，完成部署上线",
        Phase.P9_OPERATION_MONITORING: "运维监控阶段 - 运维工程师主导，持续监控系统",
    }
    return descriptions.get(phase, "未知阶段")


def get_role_description(role: Role) -> str:
    """
    获取角色描述
    
    Args:
        role: 角色枚举
        
    Returns:
        角色描述字符串
    """
    descriptions = {
        Role.BOSS: "老板 - 战略决策、资源分配、最终验收",
        Role.PRODUCT_MANAGER: "产品经理 - 需求分析、PRD编写、需求评审",
        Role.ARCHITECT: "架构师 - 技术方案设计、架构设计",
        Role.PRODUCT_DESIGNER: "产品设计师 - UI/UX设计、设计稿输出",
        Role.PROJECT_MANAGER: "项目经理 - 任务拆解、项目计划、进度管理",
        Role.ENGINEER: "开发工程师 - 编码实现、单元测试",
        Role.QA_ENGINEER: "测试工程师 - 功能测试、UAT验收",
        Role.DEVOPS: "运维工程师 - 部署上线、运维监控",
    }
    return descriptions.get(role, "未知角色")


def print_matrix():
    """打印职责矩阵（用于调试）"""
    print("=" * 120)
    print("职责矩阵")
    print("=" * 120)
    
    # 打印表头
    header = "阶段".ljust(20)
    for role in Role:
        header += role.value.ljust(12)
    print(header)
    print("-" * 120)
    
    # 打印每行
    for phase in Phase:
        row = phase.value.ljust(20)
        for role in Role:
            ptype = get_participation_type(phase, role)
            row += ptype.value.ljust(12)
        print(row)
    
    print("=" * 120)


if __name__ == "__main__":
    # 测试职责矩阵
    print_matrix()
    
    print("\n测试函数:")
    print(f"P1阶段产品经理参与类型: {get_participation_type(Phase.P1_REQUIREMENT_ANALYSIS, Role.PRODUCT_MANAGER)}")
    print(f"P1阶段负责角色: {[r.value for r in get_responsible_roles(Phase.P1_REQUIREMENT_ANALYSIS)]}")
    print(f"P2阶段是否需要通知老板(架构师发起): {should_notify_boss(Phase.P2_TECHNICAL_SOLUTION, Role.ARCHITECT)}")
