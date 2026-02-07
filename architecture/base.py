"""
MetaGPT群聊讨论系统 - 基础类和枚举
================================
定义系统中使用的基础类型、枚举和常量
"""

from enum import Enum, auto
from typing import List, Set, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod


class PhaseStatus(Enum):
    """阶段状态枚举"""
    PENDING = "pending"          # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    CONSENSUS_REACHED = "consensus_reached"  # 已达成一致
    TIMEOUT = "timeout"          # 超时
    BOSS_INTERVENTION = "boss_intervention"  # 老板介入
    COMPLETED = "completed"      # 已完成


class RoleAction(Enum):
    """角色动作枚举"""
    SPEAK = "speak"              # 发言
    PASS = "pass"                # 跳过
    AGREE = "agree"              # 同意
    DISAGREE = "disagree"        # 反对
    REQUEST_BOSS = "request_boss"  # 请求老板介入
    INTERVENE = "intervene"      # 介入（老板专用）
    FORCE_DECISION = "force_decision"  # 强制决策（老板专用）


class ConsensusStrategyType(Enum):
    """共识检测策略类型"""
    EXPLICIT_AGREEMENT = "explicit_agreement"  # 显式同意
    ROUND_LIMIT = "round_limit"                # 轮次上限
    PASS_RATIO = "pass_ratio"                  # Pass比例
    CONTENT_SIMILARITY = "content_similarity"  # 内容相似度
    LLM_JUDGMENT = "llm_judgment"              # LLM判断


@dataclass
class Responsibility:
    """
    角色职责定义 (RACI模型)
    
    Attributes:
        accountable_phases: 最终负责的阶段列表
        responsible_phases: 负责执行的阶段列表
        consulted_phases: 被咨询的阶段列表
        informed_phases: 被告知的阶段列表
    """
    accountable_phases: List[str] = field(default_factory=list)
    responsible_phases: List[str] = field(default_factory=list)
    consulted_phases: List[str] = field(default_factory=list)
    informed_phases: List[str] = field(default_factory=list)
    
    def get_weight_for_phase(self, phase_id: str) -> int:
        """获取角色在指定阶段的权重"""
        if phase_id in self.accountable_phases:
            return 5
        elif phase_id in self.responsible_phases:
            return 3
        elif phase_id in self.consulted_phases:
            return 2
        elif phase_id in self.informed_phases:
            return 1
        return 0


@dataclass
class PhaseConfig:
    """阶段配置"""
    phase_id: str
    name: str
    description: str
    max_rounds: int = 20
    required_roles: List[str] = field(default_factory=list)
    optional_roles: List[str] = field(default_factory=list)
    deliverable_type: Optional[str] = None
    consensus_threshold: float = 0.8


@dataclass
class DiscussionConfig:
    """讨论系统配置"""
    max_rounds_per_phase: int = 20
    consensus_threshold: float = 0.8
    auto_save_interval: int = 60
    pass_threshold: int = 3  # 连续pass多少轮触发共识检测
    content_similarity_threshold: float = 0.9
    enable_llm_judgment: bool = True
    boss_intervention_timeout: int = 300  # 老板介入超时时间(秒)


class MetaGPTException(Exception):
    """MetaGPT基础异常"""
    pass


class PhaseTimeoutException(MetaGPTException):
    """阶段超时异常"""
    pass


class ConsensusFailedException(MetaGPTException):
    """无法达成一致异常"""
    pass


class RoleNotRespondingException(MetaGPTException):
    """角色无响应异常"""
    pass


class FeishuAPIException(MetaGPTException):
    """飞书API异常"""
    pass
