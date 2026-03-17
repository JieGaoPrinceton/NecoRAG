"""
Memory 数据模型
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import numpy as np


class MemoryLayer(Enum):
    """记忆层级"""
    L1_WORKING = "L1"  # 工作记忆
    L2_SEMANTIC = "L2"  # 语义记忆
    L3_EPISODIC = "L3"  # 情景图谱


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
class Entity:
    """实体"""
    entity_id: str
    name: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """关系"""
    source_id: str
    target_id: str
    relation_type: str
    strength: float = 1.0  # 关系强度
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphPath:
    """图谱路径"""
    nodes: List[str]
    edges: List[Relation]
    total_strength: float


@dataclass
class Intent:
    """用户意图"""
    intent_type: str
    confidence: float
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
