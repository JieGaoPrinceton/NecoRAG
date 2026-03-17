"""
Whiskers Engine - 胡须感知引擎
感知层核心组件，负责多模态数据的高精度编码与情境标记
"""

from necorag.whiskers.engine import WhiskersEngine
from necorag.whiskers.parser import DocumentParser
from necorag.whiskers.chunker import ChunkStrategy
from necorag.whiskers.tagger import ContextualTagger
from necorag.whiskers.encoder import VectorEncoder
from necorag.whiskers.models import ParsedDocument, EncodedChunk, Chunk

__all__ = [
    "WhiskersEngine",
    "DocumentParser",
    "ChunkStrategy",
    "ContextualTagger",
    "VectorEncoder",
    "ParsedDocument",
    "EncodedChunk",
    "Chunk",
]
