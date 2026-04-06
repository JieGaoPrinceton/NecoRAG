"""
NecoRAG - Layer 1: Perception Layer (感知层)
基于认知科学的神经符号 RAG 框架

感知层负责多模态数据的编码和处理，模拟人脑的感觉记忆系统。
"""

from .engine import PerceptionEngine
from .parser import DocumentParser
from .chunker import ChunkStrategy, AdaptiveChunker
from .tagger import ContextualTagger, SemanticTagger
from .encoder import VectorEncoder, MultiModalEncoder
from .models import ParsedDocument, LocalEncodedChunk, PerceptualData, ChunkMetadata
# 从统一协议层重导出公共类型
from ..core.protocols import Chunk, EncodedChunk, ChunkType

__all__ = [
    # 核心引擎
    "PerceptionEngine",
    # 处理组件
    "DocumentParser",
    "AdaptiveChunker",
    "ContextualTagger",
    "SemanticTagger",
    "VectorEncoder",
    "MultiModalEncoder",
    # 数据模型
    "ParsedDocument",
    "LocalEncodedChunk",
    "PerceptualData",
    "ChunkMetadata",
    # 协议类型
    "Chunk",
    "EncodedChunk",
    "ChunkType",
    "ChunkStrategy",
]
