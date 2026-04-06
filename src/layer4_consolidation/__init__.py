"""
NecoRAG - Layer 4: Consolidation Layer (巩固层)
基于认知科学的神经符号 RAG 框架

巩固层负责知识的异步固化、幻觉自检与记忆修剪，模拟人脑的记忆巩固机制：
- 知识生成器：基于检索结果生成初步响应
- 批判性评估：多轮自我反思与质量检查
- 幻觉检测：识别并纠正虚假信息
- 记忆修剪：优化存储空间，保留高价值知识
"""

from .agent import RefinementAgent
from .generator import Generator
from .critic import Critic
from .refiner import Refiner
from .hallucination import HallucinationDetector
from .consolidator import KnowledgeConsolidator
from .pruner import MemoryPruner
from .models import RefinementResult, HallucinationReport

__all__ = [
    # 核心代理
    "RefinementAgent",
    # 处理组件
    "Generator",
    "Critic",
    "Refiner",
    "HallucinationDetector",
    "KnowledgeConsolidator",
    "MemoryPruner",
    # 数据模型
    "RefinementResult",
    "HallucinationReport",
]
