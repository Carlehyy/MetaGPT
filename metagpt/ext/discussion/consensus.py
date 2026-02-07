"""
共识检测算法模块

实现多种共识检测策略，用于判断讨论是否达成一致
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Callable
from enum import Enum, auto
import re
from difflib import SequenceMatcher


class ConsensusStrategy(Enum):
    """共识检测策略枚举"""
    KEYWORD_MATCH = auto()      # 关键词匹配
    SIMILARITY = auto()         # 文本相似度
    VOTING = auto()             # 投票统计
    LLM_JUDGE = auto()          # LLM判断
    HYBRID = auto()             # 混合策略


@dataclass
class ConsensusResult:
    """共识检测结果"""
    reached: bool                      # 是否达成共识
    confidence: float                  # 置信度 (0-1)
    strategy_used: ConsensusStrategy   # 使用的策略
    reason: str = ""                   # 原因说明
    supporting_evidence: List[str] = field(default_factory=list)
    opposing_evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'reached': self.reached,
            'confidence': self.confidence,
            'strategy_used': self.strategy_used.name,
            'reason': self.reason,
            'supporting_evidence': self.supporting_evidence,
            'opposing_evidence': self.opposing_evidence
        }


class KeywordConsensusDetector:
    """
    关键词匹配共识检测器
    
    通过检测关键词出现频率来判断是否达成共识
    """
    
    def __init__(
        self, 
        agreement_keywords: Optional[List[str]] = None,
        disagreement_keywords: Optional[List[str]] = None,
        threshold: float = 0.7
    ):
        # 同意关键词
        self.agreement_keywords = agreement_keywords or [
            '同意', '赞成', '支持', '认可', '没问题', '好的', '可以',
            'agree', 'support', 'approve', 'yes', 'ok', 'good'
        ]
        # 反对关键词
        self.disagreement_keywords = disagreement_keywords or [
            '反对', '不同意', '不赞成', '不行', '有问题', '不认可',
            'disagree', 'oppose', 'reject', 'no', 'against'
        ]
        self.threshold = threshold
    
    def detect(self, messages: List[str], participants: List[str]) -> ConsensusResult:
        """
        检测是否达成共识
        
        Args:
            messages: 所有消息内容列表
            participants: 参与者列表
            
        Returns:
            共识检测结果
        """
        if not messages or not participants:
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy_used=ConsensusStrategy.KEYWORD_MATCH,
                reason="没有消息或参与者"
            )
        
        agreement_count = 0
        disagreement_count = 0
        
        for msg in messages:
            msg_lower = msg.lower()
            
            # 检查同意关键词
            if any(kw in msg_lower for kw in self.agreement_keywords):
                agreement_count += 1
            
            # 检查反对关键词
            if any(kw in msg_lower for kw in self.disagreement_keywords):
                disagreement_count += 1
        
        total = len(messages)
        agreement_ratio = agreement_count / total if total > 0 else 0
        disagreement_ratio = disagreement_count / total if total > 0 else 0
        
        # 判断是否达成共识
        reached = agreement_ratio >= self.threshold and disagreement_ratio < 0.2
        
        # 计算置信度
        confidence = agreement_ratio * (1 - disagreement_ratio)
        
        reason = f"同意比例: {agreement_ratio:.2%}, 反对比例: {disagreement_ratio:.2%}"
        
        return ConsensusResult(
            reached=reached,
            confidence=confidence,
            strategy_used=ConsensusStrategy.KEYWORD_MATCH,
            reason=reason,
            supporting_evidence=[f"找到 {agreement_count} 条同意表达"],
            opposing_evidence=[f"找到 {disagreement_count} 条反对表达"] if disagreement_count > 0 else []
        )


class SimilarityConsensusDetector:
    """
    相似度共识检测器
    
    通过计算消息间的文本相似度来判断是否达成共识
    """
    
    def __init__(self, similarity_threshold: float = 0.6, min_messages: int = 3):
        self.similarity_threshold = similarity_threshold
        self.min_messages = min_messages
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def detect(self, messages: List[str], participants: List[str]) -> ConsensusResult:
        """检测是否达成共识"""
        if len(messages) < self.min_messages:
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy_used=ConsensusStrategy.SIMILARITY,
                reason=f"消息数量不足（需要至少{self.min_messages}条）"
            )
        
        # 计算所有消息对的平均相似度
        similarities = []
        for i in range(len(messages)):
            for j in range(i + 1, len(messages)):
                sim = self.calculate_similarity(messages[i], messages[j])
                similarities.append(sim)
        
        if not similarities:
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy_used=ConsensusStrategy.SIMILARITY,
                reason="无法计算相似度"
            )
        
        avg_similarity = sum(similarities) / len(similarities)
        
        # 判断是否达成共识
        reached = avg_similarity >= self.similarity_threshold
        confidence = avg_similarity
        
        reason = f"平均相似度: {avg_similarity:.2%} (阈值: {self.similarity_threshold:.2%})"
        
        return ConsensusResult(
            reached=reached,
            confidence=confidence,
            strategy_used=ConsensusStrategy.SIMILARITY,
            reason=reason,
            supporting_evidence=[f"计算了 {len(similarities)} 对消息的相似度"]
        )


class VotingConsensusDetector:
    """
    投票共识检测器
    
    通过统计投票结果来判断是否达成共识
    """
    
    def __init__(
        self, 
        approval_threshold: float = 0.7,
        require_all_vote: bool = True
    ):
        self.approval_threshold = approval_threshold
        self.require_all_vote = require_all_vote
    
    def detect(
        self, 
        votes: Dict[str, str],  # participant_id -> vote (agree/disagree/abstain)
        participants: List[str]
    ) -> ConsensusResult:
        """检测是否达成共识"""
        if not participants:
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy_used=ConsensusStrategy.VOTING,
                reason="没有参与者"
            )
        
        # 统计投票
        agree_count = sum(1 for v in votes.values() if v.lower() in ['agree', '同意', '赞成', 'yes'])
        disagree_count = sum(1 for v in votes.values() if v.lower() in ['disagree', '反对', '不同意', 'no'])
        abstain_count = len(votes) - agree_count - disagree_count
        
        # 检查是否所有人都投票了
        if self.require_all_vote and len(votes) < len(participants):
            return ConsensusResult(
                reached=False,
                confidence=0.0,
                strategy_used=ConsensusStrategy.VOTING,
                reason=f"并非所有人都已投票 ({len(votes)}/{len(participants)})"
            )
        
        # 计算同意比例
        total_votes = len(votes)
        approval_ratio = agree_count / total_votes if total_votes > 0 else 0
        
        reached = approval_ratio >= self.approval_threshold and disagree_count == 0
        confidence = approval_ratio
        
        reason = f"同意: {agree_count}, 反对: {disagree_count}, 弃权: {abstain_count}, 比例: {approval_ratio:.2%}"
        
        return ConsensusResult(
            reached=reached,
            confidence=confidence,
            strategy_used=ConsensusStrategy.VOTING,
            reason=reason,
            supporting_evidence=[f"{agree_count} 人同意"] if agree_count > 0 else [],
            opposing_evidence=[f"{disagree_count} 人反对"] if disagree_count > 0 else []
        )


class StagnationDetector:
    """
    停滞检测器
    
    检测讨论是否陷入停滞（连续N轮没有新观点）
    """
    
    def __init__(self, stagnation_rounds: int = 3, min_messages_per_round: int = 2):
        self.stagnation_rounds = stagnation_rounds
        self.min_messages_per_round = min_messages_per_round
        self._round_messages: Dict[int, List[str]] = {}
        self._round_key_points: Dict[int, Set[str]] = {}
    
    def add_round_messages(self, round_number: int, messages: List[str]) -> None:
        """添加一轮的消息"""
        self._round_messages[round_number] = messages
        # 提取关键点（简单实现：提取包含"认为"、"建议"等的句子）
        key_points = set()
        for msg in messages:
            # 简单提取关键观点
            sentences = re.split(r'[。！？.!?]', msg)
            for sent in sentences:
                if any(kw in sent for kw in ['认为', '建议', '观点', '看法', '想法', 'proposal', 'suggest', 'think']):
                    key_points.add(sent.strip())
        self._round_key_points[round_number] = key_points
    
    def detect_stagnation(self) -> Dict[str, Any]:
        """检测是否停滞"""
        if len(self._round_key_points) < self.stagnation_rounds:
            return {
                'is_stagnant': False,
                'reason': f"轮次不足（需要至少{self.stagnation_rounds}轮）"
            }
        
        # 获取最近N轮
        recent_rounds = sorted(self._round_key_points.keys())[-self.stagnation_rounds:]
        
        # 检查是否有新观点
        all_previous_points: Set[str] = set()
        new_points_found = False
        
        for round_num in recent_rounds:
            current_points = self._round_key_points[round_num]
            
            # 检查当前轮是否有新观点
            new_points = current_points - all_previous_points
            if new_points:
                new_points_found = True
            
            all_previous_points.update(current_points)
        
        is_stagnant = not new_points_found
        
        return {
            'is_stagnant': is_stagnant,
            'reason': "连续多轮没有新观点" if is_stagnant else "仍有新观点产生",
            'rounds_analyzed': len(recent_rounds),
            'total_key_points': len(all_previous_points)
        }
    
    def reset(self) -> None:
        """重置检测器"""
        self._round_messages.clear()
        self._round_key_points.clear()


class HybridConsensusDetector:
    """
    混合共识检测器
    
    综合多种策略进行共识检测
    """
    
    def __init__(
        self,
        keyword_threshold: float = 0.7,
        similarity_threshold: float = 0.6,
        voting_threshold: float = 0.7,
        stagnation_rounds: int = 3
    ):
        self.keyword_detector = KeywordConsensusDetector(threshold=keyword_threshold)
        self.similarity_detector = SimilarityConsensusDetector(
            similarity_threshold=similarity_threshold
        )
        self.voting_detector = VotingConsensusDetector(
            approval_threshold=voting_threshold
        )
        self.stagnation_detector = StagnationDetector(
            stagnation_rounds=stagnation_rounds
        )
        
        # 权重配置
        self.weights = {
            'keyword': 0.3,
            'similarity': 0.3,
            'voting': 0.25,
            'stagnation': 0.15
        }
    
    def detect(
        self,
        messages: List[str],
        participants: List[str],
        votes: Optional[Dict[str, str]] = None,
        current_round: int = 0
    ) -> ConsensusResult:
        """
        综合检测是否达成共识
        
        Args:
            messages: 所有消息
            participants: 参与者列表
            votes: 投票结果（可选）
            current_round: 当前轮次
            
        Returns:
            共识检测结果
        """
        results = []
        
        # 关键词检测
        keyword_result = self.keyword_detector.detect(messages, participants)
        results.append(('keyword', keyword_result))
        
        # 相似度检测
        similarity_result = self.similarity_detector.detect(messages, participants)
        results.append(('similarity', similarity_result))
        
        # 投票检测（如果有投票数据）
        if votes:
            voting_result = self.voting_detector.detect(votes, participants)
            results.append(('voting', voting_result))
        
        # 停滞检测
        stagnation_info = self.stagnation_detector.detect_stagnation()
        
        # 综合判断
        total_confidence = 0.0
        total_weight = 0.0
        agreement_count = 0
        
        for name, result in results:
            weight = self.weights.get(name, 0.25)
            total_confidence += result.confidence * weight
            total_weight += weight
            if result.reached:
                agreement_count += 1
        
        # 考虑停滞因素
        if stagnation_info['is_stagnant']:
            # 停滞时降低置信度
            total_confidence *= 0.8
        
        final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        # 判断是否达成共识：多数策略认为达成共识且置信度足够
        reached = agreement_count >= 2 and final_confidence >= 0.6
        
        # 构建原因说明
        reasons = [f"{name}: {r.reason}" for name, r in results]
        if stagnation_info['is_stagnant']:
            reasons.append(f"停滞检测: {stagnation_info['reason']}")
        
        return ConsensusResult(
            reached=reached,
            confidence=final_confidence,
            strategy_used=ConsensusStrategy.HYBRID,
            reason="; ".join(reasons),
            supporting_evidence=[r.reason for _, r in results if r.reached]
        )
    
    def add_round_for_stagnation_check(self, round_number: int, messages: List[str]) -> None:
        """添加一轮消息用于停滞检测"""
        self.stagnation_detector.add_round_messages(round_number, messages)


class ConsensusChecker:
    """
    共识检查器
    
    提供统一的共识检测接口
    """
    
    def __init__(self, strategy: ConsensusStrategy = ConsensusStrategy.HYBRID):
        self.strategy = strategy
        
        if strategy == ConsensusStrategy.KEYWORD_MATCH:
            self.detector = KeywordConsensusDetector()
        elif strategy == ConsensusStrategy.SIMILARITY:
            self.detector = SimilarityConsensusDetector()
        elif strategy == ConsensusStrategy.VOTING:
            self.detector = VotingConsensusDetector()
        elif strategy == ConsensusStrategy.HYBRID:
            self.detector = HybridConsensusDetector()
        else:
            self.detector = HybridConsensusDetector()  # 默认使用混合策略
    
    def check(
        self,
        messages: List[str],
        participants: List[str],
        **kwargs
    ) -> ConsensusResult:
        """
        检查是否达成共识
        
        Args:
            messages: 消息内容列表
            participants: 参与者列表
            **kwargs: 额外的检测参数
            
        Returns:
            共识检测结果
        """
        if self.strategy == ConsensusStrategy.HYBRID:
            return self.detector.detect(
                messages=messages,
                participants=participants,
                votes=kwargs.get('votes'),
                current_round=kwargs.get('current_round', 0)
            )
        elif self.strategy == ConsensusStrategy.VOTING:
            return self.detector.detect(
                votes=kwargs.get('votes', {}),
                participants=participants
            )
        else:
            return self.detector.detect(messages, participants)
