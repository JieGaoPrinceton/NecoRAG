"""
NecoRAG - Neuro-Cognitive Retrieval-Augmented Generation
基于认知科学理论构建的下一代智能 RAG 框架
"""

__version__ = "1.1.0-alpha"
__author__ = "NecoRAG Team"

# 统一入口
from src.necorag import NecoRAG, create_rag

# 核心抽象层
from src.core import (
    # 配置
    NecoRAGConfig,
    ConfigPresets,
    LLMProvider,
    VectorDBProvider,
    GraphDBProvider,
    # 数据协议
    Document,
    Chunk,
    Embedding,
    Memory,
    Query,
    Response,
    RetrievalResult,
    # LLM 客户端
    BaseLLMClient,
    MockLLMClient,
    # 异常
    NecoRAGError,
)

# 核心模块导出
from src.perception import PerceptionEngine
from src.memory import MemoryManager
from src.retrieval import AdaptiveRetriever, HyDEEnhancer
from src.refinement import RefinementAgent
from src.response import ResponseInterface

# Dashboard 模块（可选，依赖 FastAPI）
try:
    from src.dashboard import DashboardServer, ConfigManager
    _HAS_DASHBOARD = True
except ImportError:
    DashboardServer = None  # type: ignore
    ConfigManager = None  # type: ignore
    _HAS_DASHBOARD = False

# 领域权重模块导出
from src.domain import (
    DomainConfig,
    DomainConfigManager,
    KeywordLevel,
    DomainLevel,
    CompositeWeightCalculator,
    TemporalWeightCalculator,
    DomainRelevanceCalculator,
    create_example_domain,
)

# 意图分类模块导出
from src.intent import (
    IntentType,
    IntentResult,
    IntentRoutingStrategy,
    IntentConfig,
    IntentClassifier,
    IntentRouter,
    SemanticAnalyzer,
    quick_analyze,
)

# 知识演化模块导出
from src.knowledge_evolution import (
    # 枚举类型
    UpdateMode,
    UpdateStatus,
    KnowledgeSource,
    CandidateStatus,
    # 数据类
    KnowledgeCandidate,
    UpdateTask,
    ChangeLogEntry,
    KnowledgeMetrics,
    HealthReport,
    # 配置
    KnowledgeEvolutionConfig,
    # 核心类
    KnowledgeUpdater,
    KnowledgeMetricsCalculator,
    UpdateScheduler,
    KnowledgeVisualizer,
    # 便捷函数
    create_knowledge_evolution,
)

__all__ = [
    # 统一入口
    "NecoRAG",
    "create_rag",
    
    # 配置
    "NecoRAGConfig",
    "ConfigPresets",
    "LLMProvider",
    "VectorDBProvider",
    "GraphDBProvider",
    
    # 数据协议
    "Document",
    "Chunk",
    "Embedding",
    "Memory",
    "Query",
    "Response",
    "RetrievalResult",
    
    # LLM 客户端
    "BaseLLMClient",
    "MockLLMClient",
    
    # 异常
    "NecoRAGError",
    
    # 核心模块
    "PerceptionEngine",
    "MemoryManager",
    "AdaptiveRetriever",
    "HyDEEnhancer",
    "RefinementAgent",
    "ResponseInterface",
    "DashboardServer",
    "ConfigManager",
    
    # 领域权重模块
    "DomainConfig",
    "DomainConfigManager",
    "KeywordLevel",
    "DomainLevel",
    "CompositeWeightCalculator",
    "TemporalWeightCalculator",
    "DomainRelevanceCalculator",
    "create_example_domain",
    
    # 意图分类模块
    "IntentType",
    "IntentResult",
    "IntentRoutingStrategy",
    "IntentConfig",
    "IntentClassifier",
    "IntentRouter",
    "SemanticAnalyzer",
    "quick_analyze",
    
    # 知识演化模块
    "UpdateMode",
    "UpdateStatus",
    "KnowledgeSource",
    "CandidateStatus",
    "KnowledgeCandidate",
    "UpdateTask",
    "ChangeLogEntry",
    "KnowledgeMetrics",
    "HealthReport",
    "KnowledgeEvolutionConfig",
    "KnowledgeUpdater",
    "KnowledgeMetricsCalculator",
    "UpdateScheduler",
    "KnowledgeVisualizer",
    "create_knowledge_evolution",
]
