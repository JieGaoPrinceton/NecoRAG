"""
Whiskers Engine 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np


@dataclass
class Chunk:
    """文本块"""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextTags:
    """情境标签"""
    time_tag: Optional[str] = None  # 时间标签
    sentiment_tag: Optional[str] = None  # 情感标签
    importance_score: float = 0.5  # 重要性评分 (0-1)
    topic_tags: List[str] = field(default_factory=list)  # 主题标签


@dataclass
class EncodedChunk:
    """编码后的文本块"""
    content: str
    chunk_id: str
    dense_vector: np.ndarray  # 稠密向量
    sparse_vector: Dict[str, float]  # 稀疏向量
    entities: List[tuple]  # 实体三元组
    context_tags: ContextTags
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Table:
    """表格数据"""
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None


@dataclass
class Image:
    """图片数据"""
    image_path: str
    caption: Optional[str] = None
    ocr_text: Optional[str] = None


@dataclass
class ParsedDocument:
    """解析后的文档"""
    file_path: str
    content: str
    chunks: List[Chunk]
    tables: List[Table] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.now)
