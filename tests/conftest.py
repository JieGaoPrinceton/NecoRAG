# -*- coding: utf-8 -*-
"""
NecoRAG 测试夹具 (Test Fixtures)
提供各模块测试所需的共享 fixtures
"""

import os
import sys
import tempfile
import pytest
from datetime import datetime, timedelta

# 确保 src 模块可被导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.core.llm import MockLLMClient
from src.core.config import NecoRAGConfig, ConfigPresets
from src.perception.models import Chunk, ParsedDocument, EncodedChunk, ContextTags
from src.memory.models import MemoryItem, MemoryLayer, Entity, Relation, Intent
from src.memory import MemoryManager, WorkingMemory, SemanticMemory, EpisodicGraph, MemoryDecay
from src.retrieval.models import RetrievalResult
from src.refinement.models import GeneratedAnswer, CritiqueReport, HallucinationReport
from src.domain.config import DomainConfig, KeywordConfig, KeywordLevel, create_example_domain


# ─── LLM Fixtures ──────────────────────────────────────────

@pytest.fixture
def mock_llm():
    """提供一个 MockLLMClient 实例"""
    return MockLLMClient(model_name="test-model", embedding_dim=768)


# ─── Configuration Fixtures ─────────────────────────────────

@pytest.fixture
def default_config():
    """默认配置"""
    return NecoRAGConfig()


@pytest.fixture
def dev_config():
    """开发环境配置"""
    return ConfigPresets.development()


# ─── Perception Fixtures ────────────────────────────────────

@pytest.fixture
def sample_chunk():
    """示例 Chunk"""
    return Chunk(
        content="人工智能是计算机科学的重要分支。它包括机器学习、深度学习和自然语言处理。",
        index=0,
        start_char=0,
        end_char=35,
        metadata={"source": "test"},
    )


@pytest.fixture
def sample_chunks():
    """多个 Chunk"""
    return [
        Chunk(content="机器学习是人工智能的核心技术。", index=0, start_char=0, end_char=14, metadata={}),
        Chunk(content="深度学习使用神经网络处理复杂数据。", index=1, start_char=14, end_char=30, metadata={}),
        Chunk(content="自然语言处理让机器理解人类语言。", index=2, start_char=30, end_char=45, metadata={}),
    ]


@pytest.fixture
def sample_text():
    """示例文本"""
    return (
        "NecoRAG 是一个基于认知科学的 RAG 框架。\n\n"
        "它模拟了人脑的双系统记忆理论。\n\n"
        "第一层是感知引擎，负责文档解析和向量编码。\n\n"
        "第二层是层次记忆，包含工作记忆、语义记忆和情景图谱。"
    )


@pytest.fixture
def sample_parsed_doc(sample_text):
    """示例 ParsedDocument"""
    return ParsedDocument(
        file_path="test.txt",
        content=sample_text,
        chunks=[
            Chunk(content=p.strip(), index=i, start_char=0, end_char=len(p.strip()), metadata={})
            for i, p in enumerate(sample_text.split("\n\n"))
            if p.strip()
        ],
        tables=[],
        images=[],
        metadata={"format": "txt"},
        parsed_at=datetime.now(),
    )


@pytest.fixture
def sample_encoded_chunk():
    """示例 EncodedChunk"""
    return EncodedChunk(
        content="人工智能是一个重要领域",
        chunk_id="test-chunk-001",
        dense_vector=np.random.rand(768),
        sparse_vector={"人工智能": 0.8, "领域": 0.5},
        entities=[("人工智能", "是", "重要领域")],
        context_tags=ContextTags(
            time_tag=None,
            sentiment_tag="neutral",
            importance_score=0.7,
            topic_tags=["人工智能"],
        ),
        metadata={"source": "test"},
        created_at=datetime.now(),
    )


@pytest.fixture
def temp_text_file(tmp_path):
    """创建临时文本文件"""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text(
        "NecoRAG 是一个创新的 RAG 框架。\n"
        "它结合了认知科学和人工智能技术。\n"
        "主要特点包括五层认知架构。\n",
        encoding="utf-8",
    )
    return str(file_path)


# ─── Memory Fixtures ────────────────────────────────────────

@pytest.fixture
def memory_manager():
    """MemoryManager 实例"""
    return MemoryManager()


@pytest.fixture
def working_memory():
    """WorkingMemory 实例"""
    return WorkingMemory()


@pytest.fixture
def semantic_memory():
    """SemanticMemory 实例"""
    return SemanticMemory(vector_size=768)


@pytest.fixture
def episodic_graph():
    """EpisodicGraph 实例"""
    return EpisodicGraph()


@pytest.fixture
def memory_decay():
    """MemoryDecay 实例"""
    return MemoryDecay(decay_rate=0.1)


@pytest.fixture
def sample_memory_item():
    """示例 MemoryItem"""
    return MemoryItem(
        memory_id="mem-001",
        content="人工智能正在改变世界",
        layer=MemoryLayer.L2_SEMANTIC,
        vector=np.random.rand(768),
        metadata={"source": "test"},
        weight=1.0,
        access_count=0,
        created_at=datetime.now(),
        last_accessed=datetime.now(),
    )


@pytest.fixture
def sample_memory_items():
    """多个 MemoryItem"""
    now = datetime.now()
    return [
        MemoryItem(
            memory_id=f"mem-{i:03d}",
            content=content,
            layer=MemoryLayer.L2_SEMANTIC,
            vector=np.random.rand(768),
            metadata={"source": "test", "index": i},
            weight=1.0,
            access_count=i,
            created_at=now - timedelta(days=i * 10),
            last_accessed=now - timedelta(days=i * 5),
        )
        for i, content in enumerate(
            [
                "机器学习是人工智能的核心技术",
                "深度学习使用神经网络",
                "自然语言处理研究语言理解",
                "计算机视觉识别图像内容",
                "强化学习通过奖励机制学习",
            ]
        )
    ]


@pytest.fixture
def sample_entity():
    """示例 Entity"""
    return Entity(
        entity_id="ent-001",
        name="人工智能",
        entity_type="concept",
        properties={"domain": "technology"},
    )


@pytest.fixture
def sample_intent():
    """示例 Intent"""
    return Intent(
        intent_type="factual_query",
        confidence=0.9,
        entities=["人工智能", "机器学习"],
        metadata={},
    )


# ─── Retrieval Fixtures ─────────────────────────────────────

@pytest.fixture
def sample_retrieval_results():
    """示例检索结果"""
    return [
        RetrievalResult(
            memory_id=f"ret-{i:03d}",
            content=content,
            score=score,
            source=source,
            metadata={},
            retrieval_path=["vector_search"],
        )
        for i, (content, score, source) in enumerate(
            [
                ("机器学习用于数据分析", 0.95, "vector"),
                ("深度学习处理非结构化数据", 0.88, "vector"),
                ("自然语言处理帮助理解文本", 0.82, "graph"),
                ("强化学习用于决策优化", 0.75, "hyde"),
                ("计算机视觉识别图像", 0.68, "vector"),
            ]
        )
    ]


# ─── Refinement Fixtures ────────────────────────────────────

@pytest.fixture
def sample_generated_answer():
    """示例生成答案"""
    return GeneratedAnswer(
        content="机器学习是人工智能的核心技术之一，它使计算机能够从数据中学习。",
        citations=["source_1", "source_2"],
        confidence=0.85,
        metadata={"model": "test"},
    )


@pytest.fixture
def sample_critique():
    """示例评审报告"""
    return CritiqueReport(
        is_valid=True,
        issues=[],
        suggestions=["可以补充更多具体例子"],
        quality_score=0.8,
    )


@pytest.fixture
def sample_evidence():
    """示例证据列表"""
    return [
        "机器学习是人工智能的一个子领域。",
        "深度学习是机器学习的一种方法。",
        "自然语言处理属于人工智能范畴。",
    ]


# ─── Domain Fixtures ────────────────────────────────────────

@pytest.fixture
def domain_config():
    """示例领域配置"""
    return create_example_domain()
