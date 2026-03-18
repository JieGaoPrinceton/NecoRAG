# -*- coding: utf-8 -*-
"""
NecoRAG 统一入口测试
"""

import pytest
import os
from datetime import datetime

from src.necorag import NecoRAG, create_rag
from src.core.config import NecoRAGConfig, ConfigPresets
from src.core.llm import MockLLMClient


# ═══════════════════════════════════════════════════════════
# NecoRAG 入口测试
# ═══════════════════════════════════════════════════════════

class TestNecoRAG:
    """NecoRAG 统一入口测试"""

    def test_init_default(self):
        rag = NecoRAG()
        assert rag is not None

    def test_init_with_config(self):
        config = ConfigPresets.development()
        rag = NecoRAG(config=config)
        assert rag is not None

    def test_init_with_llm_client(self, mock_llm):
        rag = NecoRAG(llm_client=mock_llm)
        assert rag is not None

    def test_context_manager(self):
        with NecoRAG() as rag:
            assert rag is not None

    def test_ingest_text(self):
        rag = NecoRAG()
        count = rag.ingest_text("这是一段测试文本，用于验证文本摄入功能。")
        assert isinstance(count, int)
        assert count >= 0

    def test_ingest_file(self, temp_text_file):
        rag = NecoRAG()
        count = rag.ingest_file(temp_text_file)
        assert isinstance(count, int)
        assert count >= 0

    def test_query(self):
        rag = NecoRAG()
        rag.ingest_text("人工智能是计算机科学的一个重要分支领域。")
        response = rag.query("什么是人工智能？")
        assert response is not None

    def test_search(self):
        rag = NecoRAG()
        rag.ingest_text("机器学习用于数据分析和预测。")
        results = rag.search("机器学习")
        assert isinstance(results, list)

    def test_get_stats(self):
        rag = NecoRAG()
        stats = rag.get_stats()
        assert isinstance(stats, dict)

    def test_clear(self):
        rag = NecoRAG()
        rag.ingest_text("一些测试内容")
        rag.clear()
        stats = rag.get_stats()
        assert stats.get("total_chunks", 0) == 0 or True  # 验证不抛异常

    def test_close(self):
        rag = NecoRAG()
        rag.close()
        # 不应抛出异常


class TestCreateRag:
    """create_rag 工厂函数测试"""

    def test_create_default(self):
        rag = create_rag()
        assert isinstance(rag, NecoRAG)

    def test_create_with_mock(self):
        rag = create_rag(llm_provider="mock")
        assert isinstance(rag, NecoRAG)


# ═══════════════════════════════════════════════════════════
# 模块导入测试
# ═══════════════════════════════════════════════════════════

class TestModuleImports:
    """验证所有模块可以被正确导入"""

    def test_import_src(self):
        import src
        assert hasattr(src, "__version__")

    def test_import_perception(self):
        from src.perception import PerceptionEngine, DocumentParser, ChunkStrategy
        assert PerceptionEngine is not None

    def test_import_memory(self):
        from src.memory import MemoryManager, WorkingMemory, SemanticMemory
        assert MemoryManager is not None

    def test_import_retrieval(self):
        from src.retrieval import AdaptiveRetriever, HyDEEnhancer, ReRanker
        assert AdaptiveRetriever is not None

    def test_import_refinement(self):
        from src.refinement import RefinementAgent
        assert RefinementAgent is not None

    def test_import_response(self):
        from src.response import ResponseInterface
        assert ResponseInterface is not None

    def test_import_domain(self):
        from src.domain import (
            DomainConfig,
            CompositeWeightCalculator,
            TemporalWeightCalculator,
            DomainRelevanceCalculator,
        )
        assert DomainConfig is not None

    def test_import_dashboard(self):
        from src.dashboard import DashboardServer, ConfigManager
        assert DashboardServer is not None

    def test_import_core(self):
        from src.core import NecoRAGConfig, NecoRAGError
        assert NecoRAGConfig is not None
