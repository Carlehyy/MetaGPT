"""
MetaGPT群聊讨论系统 - 共识检测模块
==================================
定义共识检测策略和检测器
"""

from typing import List, Set, Dict, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from architecture.base import ConsensusStrategyType, DiscussionConfig
from architecture.message import Message, DiscussionMessage
from architecture.role import Role


@dataclass
class ConsensusResult:
    """共识检测结果"""
    reached: bool
    confidence: float  # 置信度 (0-1)
    strategy: str  # 使用的策略
    details: Dict[str, Any]  # 详细信息
    

class ConsensusStrategy(ABC):
    """共识检测策略基类"""
    
    def __init__(self, strategy_type: ConsensusStrategyType):
        self.strategy_type = strategy_type
    
    @abstractmethod
    def detect(self, messages: List[Message], roles: List[Role], 
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """
        检测是否达成共识
        
        Args:
            messages: 消息列表
            roles: 参与角色列表
            phase_id: 当前阶段ID
            config: 讨论配置
            
        Returns:
            共识检测结果
        """
        pass
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return self.strategy_type.value


class ExplicitAgreementStrategy(ConsensusStrategy):
    """
    显式同意检测策略
    
    检测所有必需角色是否都显式表示同意
    """
    
    def __init__(self):
        super().__init__(ConsensusStrategyType.EXPLICIT_AGREEMENT)
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """检测显式同意"""
        # 获取必需角色
        required_roles = [r for r in roles if r.is_required_for_phase(phase_id)]
        
        if not required_roles:
            return ConsensusResult(
                reached=True,
                confidence=1.0,
                strategy=self.get_strategy_name(),
                details={"reason": "No required roles for this phase"}
            )
        
        # 统计同意状态
        agreed_roles = set()
        disagreed_roles = set()
        
        for msg in messages:
            if isinstance(msg, DiscussionMessage) and msg.action == "agree":
                agreed_roles.add(msg.sender)
            elif isinstance(msg, DiscussionMessage) and msg.action == "disagree":
                disagreed_roles.add(msg.sender)
        
        # 检查是否所有必需角色都同意
        required_role_ids = {r.role_id for r in required_roles}
        all_agreed = required_role_ids.issubset(agreed_roles)
        any_disagreed = len(disagreed_roles & required_role_ids) > 0
        
        if all_agreed and not any_disagreed:
            return ConsensusResult(
                reached=True,
                confidence=1.0,
                strategy=self.get_strategy_name(),
                details={
                    "agreed_roles": list(agreed_roles),
                    "required_roles": list(required_role_ids)
                }
            )
        
        # 计算同意率
        agreed_count = len(agreed_roles & required_role_ids)
        agreement_rate = agreed_count / len(required_role_ids)
        
        return ConsensusResult(
            reached=False,
            confidence=agreement_rate,
            strategy=self.get_strategy_name(),
            details={
                "agreed_roles": list(agreed_roles),
                "disagreed_roles": list(disagreed_roles),
                "required_roles": list(required_role_ids),
                "agreement_rate": agreement_rate
            }
        )


class RoundLimitStrategy(ConsensusStrategy):
    """
    轮次上限检测策略
    
    检测是否达到最大轮数
    """
    
    def __init__(self):
        super().__init__(ConsensusStrategyType.ROUND_LIMIT)
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """检测轮次上限"""
        # 获取当前轮数
        max_round = 0
        for msg in messages:
            if isinstance(msg, DiscussionMessage) and msg.phase == phase_id:
                max_round = max(max_round, msg.round_num)
        
        reached = max_round >= config.max_rounds_per_phase
        
        return ConsensusResult(
            reached=reached,
            confidence=1.0 if reached else max_round / config.max_rounds_per_phase,
            strategy=self.get_strategy_name(),
            details={
                "current_round": max_round,
                "max_rounds": config.max_rounds_per_phase
            }
        )


class PassRatioStrategy(ConsensusStrategy):
    """
    Pass比例检测策略
    
    检测连续N轮是否所有角色都pass
    """
    
    def __init__(self):
        super().__init__(ConsensusStrategyType.PASS_RATIO)
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """检测pass比例"""
        # 按轮次分组统计
        round_passes: Dict[int, Set[str]] = {}
        
        for msg in messages:
            if isinstance(msg, DiscussionMessage) and msg.phase == phase_id:
                if msg.action == "pass":
                    if msg.round_num not in round_passes:
                        round_passes[msg.round_num] = set()
                    round_passes[msg.round_num].add(msg.sender)
        
        # 检查连续pass的轮数
        role_ids = {r.role_id for r in roles}
        consecutive_pass_rounds = 0
        max_consecutive = 0
        
        for round_num in sorted(round_passes.keys()):
            if round_passes[round_num] == role_ids:
                consecutive_pass_rounds += 1
                max_consecutive = max(max_consecutive, consecutive_pass_rounds)
            else:
                consecutive_pass_rounds = 0
        
        reached = max_consecutive >= config.pass_threshold
        
        return ConsensusResult(
            reached=reached,
            confidence=min(1.0, max_consecutive / config.pass_threshold),
            strategy=self.get_strategy_name(),
            details={
                "consecutive_pass_rounds": max_consecutive,
                "pass_threshold": config.pass_threshold
            }
        )


class ContentSimilarityStrategy(ConsensusStrategy):
    """
    内容相似度检测策略
    
    检测连续N轮发言内容是否相似
    """
    
    def __init__(self):
        super().__init__(ConsensusStrategyType.CONTENT_SIMILARITY)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度（简化版Jaccard相似度）
        
        实际实现中可以使用更复杂的NLP方法
        """
        # 提取关键词（简化处理）
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """检测内容相似度"""
        # 按轮次获取发言内容
        round_contents: Dict[int, List[str]] = {}
        
        for msg in messages:
            if isinstance(msg, DiscussionMessage) and msg.phase == phase_id:
                if msg.action == "speak":
                    if msg.round_num not in round_contents:
                        round_contents[msg.round_num] = []
                    round_contents[msg.round_num].append(msg.content)
        
        # 检查连续相似轮数
        consecutive_similar_rounds = 0
        max_consecutive = 0
        prev_content = ""
        
        for round_num in sorted(round_contents.keys()):
            current_content = " ".join(round_contents[round_num])
            
            if prev_content:
                similarity = self._calculate_similarity(prev_content, current_content)
                if similarity >= config.content_similarity_threshold:
                    consecutive_similar_rounds += 1
                    max_consecutive = max(max_consecutive, consecutive_similar_rounds)
                else:
                    consecutive_similar_rounds = 0
            
            prev_content = current_content
        
        reached = max_consecutive >= config.pass_threshold
        
        return ConsensusResult(
            reached=reached,
            confidence=min(1.0, max_consecutive / config.pass_threshold),
            strategy=self.get_strategy_name(),
            details={
                "consecutive_similar_rounds": max_consecutive,
                "similarity_threshold": config.content_similarity_threshold
            }
        )


class LLMJudgmentStrategy(ConsensusStrategy):
    """
    LLM判断策略
    
    使用LLM判断是否达成共识
    """
    
    def __init__(self):
        super().__init__(ConsensusStrategyType.LLM_JUDGMENT)
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str, config: DiscussionConfig) -> ConsensusResult:
        """使用LLM判断是否达成共识"""
        # 获取当前阶段的讨论内容
        phase_messages = [
            msg for msg in messages 
            if isinstance(msg, DiscussionMessage) and msg.phase == phase_id
        ]
        
        if not phase_messages:
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy=self.get_strategy_name(),
                details={"reason": "No messages in current phase"}
            )
        
        # 构建LLM提示
        discussion_text = "\n".join([
            f"[{msg.sender}]: {msg.content}" 
            for msg in phase_messages[-10:]  # 最近10条消息
        ])
        
        # 实际实现中应调用LLM进行判断
        # 这里返回模拟结果
        prompt = f"""
        请判断以下讨论是否达成了共识：
        
        {discussion_text}
        
        请回答：
        1. 是否达成共识？（是/否）
        2. 置信度（0-1）
        3. 理由
        """
        
        # 模拟LLM判断结果
        # 实际实现中调用LLM API
        return ConsensusResult(
            reached=False,  # 默认未达成
            confidence=0.5,
            strategy=self.get_strategy_name(),
            details={
                "prompt": prompt,
                "note": "This is a placeholder. Actual LLM call should be implemented."
            }
        )


class ConsensusDetector:
    """
    共识检测器
    
    管理多种共识检测策略，综合判断是否达成共识
    """
    
    def __init__(self, config: DiscussionConfig):
        self.config = config
        self._strategies: Dict[ConsensusStrategyType, ConsensusStrategy] = {
            ConsensusStrategyType.EXPLICIT_AGREEMENT: ExplicitAgreementStrategy(),
            ConsensusStrategyType.ROUND_LIMIT: RoundLimitStrategy(),
            ConsensusStrategyType.PASS_RATIO: PassRatioStrategy(),
            ConsensusStrategyType.CONTENT_SIMILARITY: ContentSimilarityStrategy(),
        }
        
        if config.enable_llm_judgment:
            self._strategies[ConsensusStrategyType.LLM_JUDGMENT] = LLMJudgmentStrategy()
    
    def add_strategy(self, strategy: ConsensusStrategy) -> None:
        """添加检测策略"""
        self._strategies[strategy.strategy_type] = strategy
    
    def detect(self, messages: List[Message], roles: List[Role],
               phase_id: str) -> ConsensusResult:
        """
        检测是否达成共识
        
        按优先级依次检测各种策略，任一策略达成即返回
        
        Args:
            messages: 消息列表
            roles: 参与角色列表
            phase_id: 当前阶段ID
            
        Returns:
            共识检测结果
        """
        # 按优先级排序的策略
        priority_order = [
            ConsensusStrategyType.EXPLICIT_AGREEMENT,
            ConsensusStrategyType.ROUND_LIMIT,
            ConsensusStrategyType.PASS_RATIO,
            ConsensusStrategyType.CONTENT_SIMILARITY,
            ConsensusStrategyType.LLM_JUDGMENT,
        ]
        
        for strategy_type in priority_order:
            if strategy_type not in self._strategies:
                continue
            
            strategy = self._strategies[strategy_type]
            result = strategy.detect(messages, roles, phase_id, self.config)
            
            if result.reached:
                return result
        
        # 如果没有策略达成，返回最高置信度的结果
        all_results = []
        for strategy_type in priority_order:
            if strategy_type in self._strategies:
                result = self._strategies[strategy_type].detect(
                    messages, roles, phase_id, self.config
                )
                all_results.append(result)
        
        if all_results:
            best_result = max(all_results, key=lambda r: r.confidence)
            return best_result
        
        return ConsensusResult(
            reached=False,
            confidence=0.0,
            strategy="none",
            details={"reason": "No strategies available"}
        )
    
    def calculate_consensus_score(self, messages: List[Message], 
                                   roles: List[Role], phase_id: str) -> float:
        """
        计算共识分数
        
        Args:
            messages: 消息列表
            roles: 参与角色列表
            phase_id: 当前阶段ID
            
        Returns:
            共识分数 (0-1)
        """
        result = self.detect(messages, roles, phase_id)
        return result.confidence
