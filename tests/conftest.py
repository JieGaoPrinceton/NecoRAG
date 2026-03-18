"""
NecoRAG 测试共享 fixtures

提供测试中复用的配置、Mock 对象和样本数据。
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 确保 src 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import (
    NecoRAGConfig,
    LLMConfig,
    PerceptionConfig,
    MemoryConfig,
    RetrievalConfig,
    RefinementConfig,
    ResponseConfig,
    ConfigPresets,
    LLMProvider,
    VectorDBProvider,
    GraphDBProvider,
)
from src.core.protocols import (
    Document,
    Chunk,
    Query,
    Entity,
    Relation,
    Response,
    UserProfile,
    Memory,
    MemoryLayer,
    ChunkType,
    DocumentType,
    ResponseTone,
    DetailLevel,
)
from src.core.llm import MockLLMClient


# ============== 配置 Fixtures ==============

@pytest.fixture
def default_config() -> NecoRAGConfig:
    """返回默认配置"""
    return NecoRAGConfig()


@pytest.fixture
def development_config() -> NecoRAGConfig:
    """返回开发环境配置"""
    return ConfigPresets.development()


@pytest.fixture
def minimal_config() -> NecoRAGConfig:
    """返回最小配置"""
    return ConfigPresets.minimal()


@pytest.fixture
def custom_config() -> NecoRAGConfig:
    """返回自定义配置"""
    config = NecoRAGConfig(
        project_name="TestProject",
        version="0.0.1",
        debug=True
    )
    config.llm.provider = LLMProvider.MOCK
    config.llm.model_name = "test-model"
    config.llm.embedding_dimension = 384
    config.perception.chunk_size = 256
    config.memory.working_memory_ttl = 1800
    config.retrieval.default_top_k = 5
    return config


@pytest.fixture
def llm_config() -> LLMConfig:
    """返回 LLM 配置"""
    return LLMConfig(
        provider=LLMProvider.MOCK,
        model_name="mock-llm",
        embedding_dimension=768
    )


@pytest.fixture
def perception_config() -> PerceptionConfig:
    """返回感知层配置"""
    return PerceptionConfig(
        chunk_size=512,
        chunk_overlap=50,
        min_chunk_size=100,
        target_chunk_size=200,
        max_chunk_size=500,
        enable_elastic_chunking=True
    )


@pytest.fixture
def memory_config() -> MemoryConfig:
    """返回记忆层配置"""
    return MemoryConfig(
        working_memory_ttl=3600,
        working_memory_max_items=100,
        decay_rate=0.1,
        decay_threshold=0.1
    )


@pytest.fixture
def retrieval_config() -> RetrievalConfig:
    """返回检索层配置"""
    return RetrievalConfig(
        default_top_k=10,
        enable_hyde=True,
        enable_rerank=True
    )


# ============== Mock 客户端 Fixtures ==============

@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """返回 Mock LLM 客户端"""
    return MockLLMClient(
        model_name="test-mock-llm",
        embedding_dim=768,
        deterministic=True
    )


@pytest.fixture
def mock_llm_client_small_dim() -> MockLLMClient:
    """返回小维度的 Mock LLM 客户端"""
    return MockLLMClient(
        model_name="test-mock-llm-small",
        embedding_dim=128,
        deterministic=True
    )


# ============== 样本数据 Fixtures ==============

@pytest.fixture
def sample_document() -> Document:
    """返回样本文档"""
    return Document(
        doc_id="test-doc-001",
        content="这是一个测试文档的内容。它包含多个段落和信息。\n\n第二段内容。",
        doc_type=DocumentType.TEXT,
        title="测试文档",
        metadata={"source": "test", "language": "zh"}
    )


@pytest.fixture
def sample_chunks() -> list:
    """返回样本分块列表"""
    return [
        Chunk(
            chunk_id="chunk-001",
            content="这是第一个测试分块的内容。",
            doc_id="test-doc-001",
            chunk_type=ChunkType.SEMANTIC,
            position=0,
            metadata={"source": "test"}
        ),
        Chunk(
            chunk_id="chunk-002",
            content="This is the second test chunk in English.",
            doc_id="test-doc-001",
            chunk_type=ChunkType.SEMANTIC,
            position=1,
            metadata={"source": "test"}
        ),
        Chunk(
            chunk_id="chunk-003",
            content="第三个分块包含中英文混合 mixed content here。",
            doc_id="test-doc-001",
            chunk_type=ChunkType.SEMANTIC,
            position=2,
            metadata={"source": "test"}
        ),
    ]


@pytest.fixture
def sample_query() -> Query:
    """返回样本查询"""
    return Query(
        query_id="query-001",
        text="什么是深度学习？",
        user_id="user-001",
        session_id="session-001",
        top_k=5
    )


@pytest.fixture
def sample_entity() -> Entity:
    """返回样本实体"""
    return Entity(
        entity_id="entity-001",
        name="深度学习",
        entity_type="concept",
        properties={"domain": "AI", "importance": "high"}
    )


@pytest.fixture
def sample_relation() -> Relation:
    """返回样本关系"""
    return Relation(
        relation_id="relation-001",
        source_id="entity-001",
        target_id="entity-002",
        relation_type="related_to",
        weight=0.8
    )


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """返回样本用户画像"""
    return UserProfile(
        user_id="user-001",
        name="测试用户",
        profession="developer",
        knowledge_level="intermediate",
        preferred_tone=ResponseTone.PROFESSIONAL,
        preferred_detail=DetailLevel.STANDARD,
        interests=["AI", "Machine Learning"]
    )


@pytest.fixture
def sample_memory() -> Memory:
    """返回样本记忆"""
    return Memory(
        memory_id="memory-001",
        content="深度学习是机器学习的一个分支。",
        layer=MemoryLayer.L2_SEMANTIC,
        weight=1.0,
        access_count=0
    )


# ============== 文本样本 Fixtures ==============

@pytest.fixture
def sample_text_short() -> str:
    """返回短文本样本"""
    return "这是一段简短的测试文本。"


@pytest.fixture
def sample_text_medium() -> str:
    """返回中等长度文本样本"""
    return """深度学习是机器学习的一个重要分支，它模拟人脑神经网络的结构和功能。

深度学习通过多层神经网络来学习数据的特征表示，能够自动从原始数据中提取有意义的模式。

在过去十年中，深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。"""


@pytest.fixture
def sample_text_long() -> str:
    """返回长文本样本"""
    paragraphs = []
    for i in range(10):
        paragraphs.append(f"这是第{i+1}段落的内容。包含一些测试文本和数据。每个段落都有足够的内容来测试分块功能。")
    return "\n\n".join(paragraphs)


@pytest.fixture
def sample_text_chinese() -> str:
    """返回中文文本样本"""
    return """人工智能（AI）是计算机科学的一个重要分支，旨在创建能够执行通常需要人类智能的任务的系统。

机器学习是人工智能的核心技术之一，它使计算机能够从数据中学习并改进其性能，而无需明确编程。

深度学习是机器学习的子集，使用多层神经网络来模拟人脑的学习过程。"""


@pytest.fixture
def sample_text_english() -> str:
    """返回英文文本样本"""
    return """Artificial Intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence.

Machine learning is one of the core technologies of AI, enabling computers to learn from data and improve their performance without being explicitly programmed.

Deep learning is a subset of machine learning that uses multi-layer neural networks to simulate the learning process of the human brain."""


@pytest.fixture
def sample_text_mixed() -> str:
    """返回中英文混合文本样本"""
    return """人工智能 (Artificial Intelligence) 正在改变我们的生活方式。

Machine Learning 和 Deep Learning 是 AI 的两个重要领域。它们被广泛应用于 Computer Vision、NLP (自然语言处理) 等场景。

未来，AI 技术将会更加普及，我们需要 Responsible AI 来确保技术的健康发展。"""


# ============== 辅助 Fixtures ==============

@pytest.fixture
def current_time() -> datetime:
    """返回当前时间"""
    return datetime.now()


@pytest.fixture
def past_time() -> datetime:
    """返回过去的时间（1天前）"""
    return datetime.now() - timedelta(days=1)


@pytest.fixture
def future_time() -> datetime:
    """返回未来的时间（1天后）"""
    return datetime.now() + timedelta(days=1)
