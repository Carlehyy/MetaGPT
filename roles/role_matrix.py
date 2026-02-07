from enum import Enum
from typing import Dict

class ParticipationType(Enum):
    LEAD = "负责/执行"
    CONSULT = "参与/评审"
    INFORM = "知会"
    NONE = "-"

class ProjectPhase(Enum):
    REQUIREMENT_ANALYSIS = "1.需求分析"
    TECHNICAL_SOLUTION = "2.技术方案"
    UI_UX_DESIGN = "3.UI/UX设计"
    TASK_BREAKDOWN = "4.任务拆解"
    CODING_IMPLEMENTATION = "5.编码实现"
    UI_ACCEPTANCE = "6.UI验收"
    FUNCTIONAL_TESTING = "7.功能测试"
    DEPLOYMENT = "8.部署上线"
    OPERATIONS_MONITORING = "9.运维监控"

class RoleMatrix:
    def __init__(self):
        pass
