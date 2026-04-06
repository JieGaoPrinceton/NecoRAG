"""
NecoRAG - Layer 2: Memory Layer (记忆层)
基于认知科学的神经符号 RAG 框架

记忆层负责知识的分层存储与管理，模拟人脑的三层记忆系统：
- 工作记忆 (Working Memory): 临时信息处理
- 语义记忆 (Semantic Memory): 结构化知识存储
- 情景记忆 (Episodic Graph): 情境化记忆网络
"""

from .manager import MemoryManager
from .working_memory import WorkingMemory
from .semantic_memory import SemanticMemory
from .episodic_graph import EpisodicGraph
from .decay import MemoryDecay
from .models import MemoryItem, GraphPath, Intent
# 从统一协议层重导出公共类型
from ..core.protocols import MemoryLayer, Entity, Relation, Memory

__all__ = [
    # 核心管理器
    "MemoryManager",
    # 三层记忆系统
    "WorkingMemory",
    "SemanticMemory",
    "EpisodicGraph",
    # 记忆机制
    "MemoryDecay",
    # 数据模型
    "MemoryItem",
    "GraphPath",
    "Intent",
    # 协议类型
    "MemoryLayer",
    "Memory",
    "Entity",
    "Relation",
]
