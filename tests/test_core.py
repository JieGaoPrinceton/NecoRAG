# -*- coding: utf-8 -*-
"""
核心模块测试 - 配置、协议、异常、LLM 客户端
"""

import pytest
import numpy as np
from datetime import datetime

from src.core.config import (
    NecoRAGConfig,
    ConfigPresets,
    LLMProvider,
    VectorDBProvider,
    GraphDBProvider,
    load_config,
)
from src.core.protocols import (
    Document,
    Chunk,
    Embedding,
    Memory,
    Query,
    Response,
    RetrievalResult as ProtoRetrievalResult,
    DocumentType,
    ChunkType,
    MemoryLayer as ProtoMemoryLayer,
    ResponseTone,
    DetailLevel,
    UserProfile as ProtoUserProfile,
)
from src.core.exceptions import (
    NecoRAGError,
    ParseError,
    ChunkingError,
    EncodingError,
    MemoryError as NecoMemoryError,
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
from src.core.llm import BaseLLMClient, MockLLMClient
from src.core.llm.mock import MockLLMClientWithMemory


# ═══════════════════════════════════════════════════════════
# 配置系统测试
# ═══════════════════════════════════════════════════════════

class TestNecoRAGConfig:
    """NecoRAGConfig 配置类测试"""

    def test_default_config(self):
        config = NecoRAGConfig()
        assert config.llm.provider is not None
        assert config.perception.chunk_size > 0
        assert config.memory.decay_rate >= 0

    def test_development_preset(self):
        config = ConfigPresets.development()
        assert isinstance(config, NecoRAGConfig)

    def test_production_preset(self):
        config = ConfigPresets.production()
        assert isinstance(config, NecoRAGConfig)

    def test_minimal_preset(self):
        config = ConfigPresets.minimal()
        assert isinstance(config, NecoRAGConfig)

    def test_config_attributes(self):
        config = NecoRAGConfig()
        # 验证子配置存在
        assert hasattr(config, "llm")
        assert hasattr(config, "perception")
        assert hasattr(config, "memory")
        assert hasattr(config, "retrieval")
        assert hasattr(config, "refinement")
        assert hasattr(config, "response")


class TestEnumProviders:
    """Provider 枚举测试"""

    def test_llm_providers(self):
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.OLLAMA.value == "ollama"

    def test_vectordb_providers(self):
        assert VectorDBProvider.QDRANT.value == "qdrant"

    def test_graphdb_providers(self):
        assert GraphDBProvider.NEO4J.value == "neo4j"


# ═══════════════════════════════════════════════════════════
# 协议 / 数据模型测试
# ═══════════════════════════════════════════════════════════

class TestProtocols:
    """数据协议/模型测试"""

    def test_document_type_enum(self):
        assert DocumentType.PDF.value is not None
        assert DocumentType.MARKDOWN.value is not None
        assert DocumentType.HTML.value is not None

    def test_response_tone_enum(self):
        assert ResponseTone.PROFESSIONAL is not None
        assert ResponseTone.FRIENDLY is not None

    def test_detail_level_enum(self):
        assert DetailLevel.BRIEF is not None
        assert DetailLevel.DETAILED is not None

    def test_memory_layer_enum(self):
        assert ProtoMemoryLayer.L1_WORKING is not None
        assert ProtoMemoryLayer.L2_SEMANTIC is not None
        assert ProtoMemoryLayer.L3_EPISODIC is not None


# ═══════════════════════════════════════════════════════════
# 异常层级测试
# ═══════════════════════════════════════════════════════════

class TestExceptions:
    """异常层级测试"""

    def test_base_exception(self):
        exc = NecoRAGError("base error")
        assert "base error" in str(exc)
        assert isinstance(exc, Exception)

    def test_perception_exceptions(self):
        assert issubclass(ParseError, NecoRAGError)
        assert issubclass(ChunkingError, NecoRAGError)
        assert issubclass(EncodingError, NecoRAGError)

    def test_memory_exceptions(self):
        assert issubclass(NecoMemoryError, NecoRAGError)
        assert issubclass(VectorStoreError, NecoRAGError)
        assert issubclass(GraphStoreError, NecoRAGError)

    def test_retrieval_exceptions(self):
        assert issubclass(RetrievalError, NecoRAGError)
        assert issubclass(RerankError, NecoRAGError)

    def test_refinement_exceptions(self):
        assert issubclass(GenerationError, NecoRAGError)
        assert issubclass(HallucinationError, NecoRAGError)
        assert issubclass(RefinementError, NecoRAGError)

    def test_llm_exceptions(self):
        assert issubclass(LLMError, NecoRAGError)
        assert issubclass(LLMConnectionError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMResponseError, LLMError)

    def test_config_exceptions(self):
        assert issubclass(ConfigurationError, NecoRAGError)
        assert issubclass(ValidationError, NecoRAGError)

    def test_exception_can_be_raised_and_caught(self):
        with pytest.raises(ParseError):
            raise ParseError("parse failed")

        with pytest.raises(NecoRAGError):
            raise LLMConnectionError("connection failed")


# ═══════════════════════════════════════════════════════════
# MockLLMClient 测试
# ═══════════════════════════════════════════════════════════

class TestMockLLMClient:
    """MockLLMClient 测试"""

    def test_init(self, mock_llm):
        assert mock_llm.model_name == "test-model"
        assert mock_llm.embedding_dimension == 768

    def test_generate(self, mock_llm):
        result = mock_llm.generate("什么是机器学习？")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_embed(self, mock_llm):
        result = mock_llm.embed("测试文本")
        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    def test_embed_deterministic(self, mock_llm):
        """相同文本应生成相同向量"""
        v1 = mock_llm.embed("同样的文本")
        v2 = mock_llm.embed("同样的文本")
        assert v1 == v2

    def test_embed_different_text(self, mock_llm):
        """不同文本应生成不同向量"""
        v1 = mock_llm.embed("文本一")
        v2 = mock_llm.embed("文本二")
        assert v1 != v2

    def test_count_tokens(self, mock_llm):
        count = mock_llm.count_tokens("hello world test")
        assert isinstance(count, int)
        assert count > 0


class TestMockLLMClientWithMemory:
    """MockLLMClientWithMemory 测试"""

    def test_tracks_calls(self):
        client = MockLLMClientWithMemory()
        client.generate("问题一")
        client.generate("问题二")
        client.embed("文本")

        assert len(client.call_history) == 3
        assert len(client.get_generate_calls()) == 2
        assert len(client.get_embed_calls()) == 1

    def test_clear_history(self):
        client = MockLLMClientWithMemory()
        client.generate("测试")
        assert len(client.call_history) > 0
        client.clear_history()
        assert len(client.call_history) == 0
