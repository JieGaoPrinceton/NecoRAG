"""
Purr 数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

# 从统一协议层导入公共数据类
from src.core.protocols import UserProfile, Response, ResponseTone, DetailLevel


@dataclass
class Interaction:
    """交互记录"""
    interaction_id: str
    user_id: str
    query: str
    response: str
    satisfaction: Optional[float] = None  # 用户满意度 (0-1)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalVisualization:
    """检索可视化"""
    query_understanding: str
    retrieval_steps: List[str]
    evidence_sources: List[Dict[str, Any]]
    reasoning_chain: List[str]
