"""
NecoRAG - Neuro-Cognitive Retrieval-Augmented Generation
模拟人脑双系统记忆与猫科动物的敏捷直觉，构建下一代认知型 RAG 框架
"""

__version__ = "1.0.0-alpha"
__author__ = "NecoRAG Team"

# 核心模块导出
from src.perception import WhiskersEngine
from src.memory import MemoryManager
from src.retrieval import PounceRetriever
from src.refinement import GroomingAgent
from src.response import PurrInterface
from src.dashboard import DashboardServer, ConfigManager

__all__ = [
    "WhiskersEngine",
    "MemoryManager",
    "PounceRetriever",
    "GroomingAgent",
    "PurrInterface",
    "DashboardServer",
    "ConfigManager",
]
