"""
Memory 数据模型
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

# 从统一协议层导入公共数据类
from src.core.protocols import MemoryLayer, Entity, Relation


@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    content: str
    layer: MemoryLayer
    vector: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # 权重（用于衰减）
    access_count: int = 0  # 访问次数
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)


@dataclass
class GraphPath:
    """图谱路径"""
    nodes: List[str]
    edges: List[Relation]  # 使用导入的 Relation
    total_strength: float


@dataclass
class Intent:
    """用户意图"""
    intent_type: str
    confidence: float
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
