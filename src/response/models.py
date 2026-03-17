"""
Purr 数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    professional_level: str = "intermediate"  # beginner/intermediate/expert
    interaction_style: str = "friendly"  # formal/friendly/humorous
    preferred_domains: List[str] = field(default_factory=list)
    query_history: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


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
class Response:
    """响应"""
    content: str
    thinking_chain: str  # 思维链可视化
    tone: str
    detail_level: int
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalVisualization:
    """检索可视化"""
    query_understanding: str
    retrieval_steps: List[str]
    evidence_sources: List[Dict[str, Any]]
    reasoning_chain: List[str]
