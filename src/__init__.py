"""
NecoRAG - Neuro-Cognitive Retrieval-Augmented Generation
基于认知科学理论构建的下一代智能 RAG 框架
"""

__version__ = "1.0.0-alpha"
__author__ = "NecoRAG Team"

# 核心模块导出
from src.perception import PerceptionEngine
from src.memory import MemoryManager
from src.retrieval import AdaptiveRetriever
from src.refinement import RefinementAgent
from src.response import ResponseInterface
from src.dashboard import DashboardServer, ConfigManager

__all__ = [
    "PerceptionEngine",
    "MemoryManager",
    "AdaptiveRetriever",
    "RefinementAgent",
    "ResponseInterface",
    "DashboardServer",
    "ConfigManager",
]
