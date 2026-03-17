"""
NecoRAG Core 模块

提供系统核心组件：抽象基类、数据协议、配置管理、异常定义。
"""

# 抽象基类
from .base import (
    # 感知层
    BaseParser,
    BaseChunker,
    BaseEncoder,
    BaseTagger,
    # 记忆层
    BaseMemoryStore,
    BaseVectorStore,
    BaseGraphStore,
    # 检索层
    BaseRetriever,
    BaseReranker,
    # 巩固层
    BaseGenerator,
    BaseCritic,
    BaseRefiner,
    BaseHallucinationDetector,
    # LLM
    BaseLLMClient,
    BaseAsyncLLMClient,
    # 响应层
    BaseResponseAdapter,
)

# 数据协议
from .protocols import (
    # 枚举类型
    DocumentType,
    ChunkType,
    MemoryLayer,
    RetrievalSource,
    ResponseTone,
    DetailLevel,
    # 文档相关
    Document,
    Chunk,
    ContextTag,
    # 向量相关
    Embedding,
    EncodedChunk,
    # 记忆相关
    Memory,
    Entity,
    Relation,
    # 查询相关
    Query,
    RetrievalResult,
    # 响应相关
    GeneratedAnswer,
    CritiqueResult,
    HallucinationReport,
    Response,
    # 用户相关
    UserProfile,
)

# 配置管理
from .config import (
    # 枚举
    LLMProvider,
    VectorDBProvider,
    GraphDBProvider,
    # 配置类
    BaseConfig,
    LLMConfig,
    PerceptionConfig,
    MemoryConfig,
    RetrievalConfig,
    RefinementConfig,
    ResponseConfig,
    DomainWeightConfig,
    NecoRAGConfig,
    # 工具函数
    load_config,
    ConfigPresets,
)

# 异常定义
from .exceptions import (
    NecoRAGError,
    ParseError,
    ChunkingError,
    EncodingError,
    MemoryError,
    VectorStoreError,
    GraphStoreError,
    RetrievalError,
    RerankError,
    GenerationError,
    HallucinationError,
    RefinementError,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    ConfigurationError,
    ValidationError,
)

# LLM 客户端
from .llm import (
    MockLLMClient,
)


__all__ = [
    # 抽象基类
    "BaseParser",
    "BaseChunker",
    "BaseEncoder",
    "BaseTagger",
    "BaseMemoryStore",
    "BaseVectorStore",
    "BaseGraphStore",
    "BaseRetriever",
    "BaseReranker",
    "BaseGenerator",
    "BaseCritic",
    "BaseRefiner",
    "BaseHallucinationDetector",
    "BaseLLMClient",
    "BaseAsyncLLMClient",
    "BaseResponseAdapter",
    
    # 数据协议
    "DocumentType",
    "ChunkType",
    "MemoryLayer",
    "RetrievalSource",
    "ResponseTone",
    "DetailLevel",
    "Document",
    "Chunk",
    "ContextTag",
    "Embedding",
    "EncodedChunk",
    "Memory",
    "Entity",
    "Relation",
    "Query",
    "RetrievalResult",
    "GeneratedAnswer",
    "CritiqueResult",
    "HallucinationReport",
    "Response",
    "UserProfile",
    
    # 配置
    "LLMProvider",
    "VectorDBProvider",
    "GraphDBProvider",
    "BaseConfig",
    "LLMConfig",
    "PerceptionConfig",
    "MemoryConfig",
    "RetrievalConfig",
    "RefinementConfig",
    "ResponseConfig",
    "DomainWeightConfig",
    "NecoRAGConfig",
    "load_config",
    "ConfigPresets",
    
    # 异常
    "NecoRAGError",
    "ParseError",
    "ChunkingError",
    "EncodingError",
    "MemoryError",
    "VectorStoreError",
    "GraphStoreError",
    "RetrievalError",
    "RerankError",
    "GenerationError",
    "HallucinationError",
    "RefinementError",
    "LLMError",
    "LLMConnectionError",
    "LLMRateLimitError",
    "LLMResponseError",
    "ConfigurationError",
    "ValidationError",
    
    # LLM 客户端
    "MockLLMClient",
]
