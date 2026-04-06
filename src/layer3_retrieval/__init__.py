"""
NecoRAG - Layer 3: Retrieval Layer (检索层)
基于认知科学的神经符号 RAG 框架

检索层负责智能化的信息检索与重排序，模拟人脑的记忆提取机制：
- 自适应检索：根据查询类型动态调整检索策略
- HyDE 增强：假设性文档嵌入提升检索质量
- 多路融合：整合多种检索源的结果
- 智能重排序：基于相关性对结果进行优化排序
"""

from .retriever import AdaptiveRetriever
from .hyde import HyDEEnhancer
from .reranker import ReRanker
from .fusion import FusionStrategy
from .models import RetrievalResult
from .smart_routing.intent_router import IntentRouter
from .smart_routing.strategy_fusion import StrategyFusionEngine
from .web_search import (
    WebSearchEngine,
    SearchResultValidator, 
    HumanConfirmationManager,
    WebSearchResult,
    ConfirmationRequest,
    ConfirmationStatus
)

__all__ = [
    # 核心检索器
    "AdaptiveRetriever",
    # 增强组件
    "HyDEEnhancer",
    "ReRanker",
    "FusionStrategy",
    # 智能路由
    "IntentRouter",
    "StrategyFusionEngine",
    # 网络搜索
    "WebSearchEngine",
    "SearchResultValidator",
    "HumanConfirmationManager",
    "WebSearchResult",
    "ConfirmationRequest",
    "ConfirmationStatus",
    # 数据模型
    "RetrievalResult",
]
