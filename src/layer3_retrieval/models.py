"""
Retrieval 数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class RetrievalResult:
    """检索结果"""
    memory_id: str
    content: str
    score: float
    source: str  # vector/graph/hyde
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_path: List[str] = field(default_factory=list)  # 检索路径（用于可视化）
    

@dataclass
class QueryAnalysis:
    """查询分析结果"""
    original_query: str
    rewritten_query: Optional[str] = None
    query_type: str = "factual"  # factual/reasoning/comparative
    entities: List[str] = field(default_factory=list)
    intent: Optional[str] = None
    complexity: str = "simple"  # simple/medium/complex
