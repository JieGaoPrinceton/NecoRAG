"""
Refinement 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HallucinationReport:
    """幻觉检测报告"""
    is_hallucination: bool
    fact_score: float  # 事实一致性分数 (0-1)
    logic_score: float  # 逻辑连贯性分数 (0-1)
    support_score: float  # 证据支撑度分数 (0-1)
    issues: List[str] = field(default_factory=list)  # 问题列表


@dataclass
class GeneratedAnswer:
    """生成的答案"""
    content: str
    citations: List[str]  # 引用的证据 ID
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CritiqueReport:
    """批判报告"""
    is_valid: bool
    issues: List[str]  # 发现的问题
    suggestions: List[str]  # 改进建议
    quality_score: float  # 质量评分 (0-1)


@dataclass
class RefinementResult:
    """精炼结果"""
    query: str
    answer: str
    confidence: float
    citations: List[str]
    hallucination_report: Optional[HallucinationReport] = None
    iterations: int = 1  # 迭代次数
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGap:
    """知识缺口"""
    gap_id: str
    topic: str
    description: str
    frequency: int  # 查询频率
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPattern:
    """查询模式"""
    pattern: str
    count: int
    hit_rate: float  # 命中率
    examples: List[str] = field(default_factory=list)
