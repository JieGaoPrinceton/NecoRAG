"""
Hallucination Detector - 幻觉检测器
"""

from typing import List
from src.refinement.models import HallucinationReport


class HallucinationDetector:
    """
    幻觉检测器
    
    检测类型：
    1. 事实性幻觉：与检索证据矛盾
    2. 逻辑性幻觉：推理链条断裂
    3. 来源性幻觉：无证据支撑的断言
    """
    
    def __init__(
        self,
        fact_threshold: float = 0.7,
        support_threshold: float = 0.5
    ):
        """
        初始化幻觉检测器
        
        Args:
            fact_threshold: 事实一致性阈值
            support_threshold: 证据支撑度阈值
        """
        self.fact_threshold = fact_threshold
        self.support_threshold = support_threshold
    
    def detect(
        self,
        answer: str,
        evidence: List[str]
    ) -> HallucinationReport:
        """
        检测幻觉
        
        Args:
            answer: 答案文本
            evidence: 证据列表
            
        Returns:
            HallucinationReport: 幻觉检测报告
        """
        # 检查各项指标
        fact_score = self.check_factual_consistency(answer, evidence)
        logic_score = self.check_logical_coherence(answer)
        support_score = self.check_evidence_support(answer, evidence)
        
        # 判断是否存在幻觉
        is_hallucination = (
            fact_score < self.fact_threshold or
            support_score < self.support_threshold
        )
        
        # 识别问题
        issues = []
        if fact_score < self.fact_threshold:
            issues.append("事实一致性较低")
        if logic_score < 0.6:
            issues.append("逻辑连贯性不足")
        if support_score < self.support_threshold:
            issues.append("证据支撑度不足")
        
        return HallucinationReport(
            is_hallucination=is_hallucination,
            fact_score=fact_score,
            logic_score=logic_score,
            support_score=support_score,
            issues=issues
        )
    
    def check_factual_consistency(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        检查事实一致性
        
        Args:
            answer: 答案文本
            evidence: 证据列表
            
        Returns:
            float: 事实一致性分数 (0-1)
            
        TODO: 实现更准确的事实一致性检测
        """
        if not evidence:
            return 0.0
        
        # 最小实现：基于关键词重叠
        answer_words = set(answer.lower().split())
        evidence_words = set()
        for e in evidence:
            evidence_words.update(e.lower().split())
        
        if not answer_words:
            return 0.0
        
        overlap = answer_words & evidence_words
        return len(overlap) / len(answer_words)
    
    def check_logical_coherence(self, answer: str) -> float:
        """
        检查逻辑连贯性
        
        Args:
            answer: 答案文本
            
        Returns:
            float: 逻辑连贯性分数 (0-1)
            
        TODO: 实现逻辑连贯性检测
        """
        # 最小实现：基于答案长度和结构
        if len(answer) < 10:
            return 0.3
        
        # 检查是否有逻辑连接词
        logic_words = ['因此', '所以', '但是', '然而', '因为', '所以', 'first', 'second', 'therefore']
        has_logic = any(word in answer.lower() for word in logic_words)
        
        return 0.8 if has_logic else 0.6
    
    def check_evidence_support(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        检查证据支撑度
        
        Args:
            answer: 答案文本
            evidence: 证据列表
            
        Returns:
            float: 证据支撑度分数 (0-1)
            
        TODO: 实现证据支撑度检测
        """
        if not evidence:
            return 0.0
        
        # 最小实现：基于证据数量
        # 证据越多，支撑度越高
        return min(len(evidence) / 5.0, 1.0)
