"""
Critic - 批判评估器
"""

from typing import List
from src.grooming.models import GeneratedAnswer, CritiqueReport


class Critic:
    """
    批判评估器
    
    评估答案质量和准确性
    """
    
    def __init__(self, llm_model: str = "default"):
        """
        初始化批判器
        
        Args:
            llm_model: LLM 模型名称
        """
        self.llm_model = llm_model
    
    def critique(
        self,
        answer: GeneratedAnswer,
        evidence: List[str]
    ) -> CritiqueReport:
        """
        评估答案质量
        
        Args:
            answer: 生成的答案
            evidence: 证据列表
            
        Returns:
            CritiqueReport: 批判报告
            
        TODO: 实现基于 LLM 的质量评估
        """
        issues = []
        suggestions = []
        
        # 检查是否有证据支撑
        if not answer.citations:
            issues.append("答案缺乏证据支撑")
            suggestions.append("建议重新检索相关证据")
        
        # 检查置信度
        if answer.confidence < 0.5:
            issues.append("答案置信度过低")
            suggestions.append("建议补充更多证据")
        
        # 检查答案完整性
        if len(answer.content) < 20:
            issues.append("答案过于简短")
            suggestions.append("建议提供更详细的回答")
        
        # 计算质量分数
        quality_score = 1.0
        if issues:
            quality_score -= 0.2 * len(issues)
        quality_score = max(quality_score, 0.0)
        
        return CritiqueReport(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_score
        )
