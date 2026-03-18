"""
Whiskers Engine 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

# 从统一协议层导入公共数据类
from src.core.protocols import Chunk, ChunkType, EncodedChunk, ContextTag


@dataclass
class ContextTags:
    """情境标签（模块特有版本，与 ContextTag 略有不同）"""
    time_tag: Optional[str] = None  # 时间标签
    sentiment_tag: Optional[str] = None  # 情感标签
    importance_score: float = 0.5  # 重要性评分 (0-1)
    topic_tags: List[str] = field(default_factory=list)  # 主题标签


@dataclass
class LocalEncodedChunk:
    """编码后的文本块（模块特有版本，使用 np.ndarray）"""
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
    chunks: List[Chunk]  # 使用导入的 Chunk
    tables: List[Table] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.now)
