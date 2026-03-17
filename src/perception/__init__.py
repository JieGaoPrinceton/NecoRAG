"""
Perception Engine - 感知引擎
感知层核心组件，负责多模态数据的高精度编码与情境标记
"""

from src.perception.engine import PerceptionEngine
from src.perception.parser import DocumentParser
from src.perception.chunker import ChunkStrategy
from src.perception.tagger import ContextualTagger
from src.perception.encoder import VectorEncoder
from src.perception.models import ParsedDocument, EncodedChunk, Chunk

__all__ = [
    "PerceptionEngine",
    "DocumentParser",
    "ChunkStrategy",
    "ContextualTagger",
    "VectorEncoder",
    "ParsedDocument",
    "EncodedChunk",
    "Chunk",
]
