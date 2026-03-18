# -*- coding: utf-8 -*-
"""
自适应检索测试 - 检索器、HyDE、重排序、融合
"""

import pytest
import numpy as np
from datetime import datetime

from src.retrieval import (
    AdaptiveRetriever,
    HyDEEnhancer,
    ReRanker,
    FusionStrategy,
    RetrievalResult,
)
from src.retrieval.retriever import EarlyTerminationController
from src.memory import MemoryManager


# ═══════════════════════════════════════════════════════════
# EarlyTerminationController 测试
# ═══════════════════════════════════════════════════════════

class TestEarlyTerminationController:
    """提前终止控制器测试"""

    def test_init(self):
        etc = EarlyTerminationController(threshold=0.85)
        assert etc is not None

    def test_evaluate_confidence_empty(self):
        etc = EarlyTerminationController()
        confidence = etc.evaluate_confidence([])
        assert confidence == 0.0

    def test_evaluate_confidence(self, sample_retrieval_results):
        etc = EarlyTerminationController()
        confidence = etc.evaluate_confidence(sample_retrieval_results)
        assert 0 <= confidence <= 1

    def test_should_terminate_high_confidence(self):
        etc = EarlyTerminationController(threshold=0.5)
        assert etc.should_terminate(0.9) is True

    def test_should_not_terminate_low_confidence(self):
        etc = EarlyTerminationController(threshold=0.9)
        assert etc.should_terminate(0.3) is False

    def test_adaptive_threshold(self):
        etc = EarlyTerminationController()
        threshold = etc.calculate_adaptive_threshold("简单问题")
        assert isinstance(threshold, float)
        assert threshold > 0


# ═══════════════════════════════════════════════════════════
# HyDEEnhancer 测试
# ═══════════════════════════════════════════════════════════

class TestHyDEEnhancer:
    """HyDE 增强器测试"""

    def test_init(self):
        hyde = HyDEEnhancer()
        assert hyde is not None

    def test_generate_hypothetical_doc(self):
        hyde = HyDEEnhancer()
        doc = hyde.generate_hypothetical_doc("什么是机器学习？")
        assert isinstance(doc, str)
        assert len(doc) > 0

    def test_generate_multiple_hypotheses(self):
        hyde = HyDEEnhancer(num_hypotheses=3)
        docs = hyde.generate_multiple_hypotheses("什么是深度学习？", num_hypotheses=3)
        assert isinstance(docs, list)
        assert len(docs) >= 1

    def test_enhance_query(self):
        hyde = HyDEEnhancer()
        enhanced = hyde.enhance_query("什么是自然语言处理？")
        assert isinstance(enhanced, list)
        assert len(enhanced) >= 1

    def test_enhance_query_includes_original(self):
        hyde = HyDEEnhancer()
        original = "什么是 AI？"
        enhanced = hyde.enhance_query(original, include_original=True)
        assert original in enhanced


# ═══════════════════════════════════════════════════════════
# ReRanker 测试
# ═══════════════════════════════════════════════════════════

class TestReRanker:
    """重排序器测试"""

    def test_init(self):
        reranker = ReRanker()
        assert reranker is not None

    def test_rerank(self, sample_retrieval_results):
        reranker = ReRanker()
        reranked = reranker.rerank("机器学习", sample_retrieval_results)
        assert isinstance(reranked, list)
        assert len(reranked) == len(sample_retrieval_results)

    def test_rerank_preserves_items(self, sample_retrieval_results):
        """重排序不应丢失结果"""
        reranker = ReRanker()
        reranked = reranker.rerank("测试", sample_retrieval_results)
        original_ids = {r.memory_id for r in sample_retrieval_results}
        reranked_ids = {r.memory_id for r in reranked}
        assert original_ids == reranked_ids

    def test_novelty_penalty(self, sample_retrieval_results):
        reranker = ReRanker(novelty_weight=0.5)
        result = reranker.apply_novelty_penalty(sample_retrieval_results)
        assert isinstance(result, list)
        assert len(result) == len(sample_retrieval_results)

    def test_ensure_diversity(self, sample_retrieval_results):
        reranker = ReRanker(diversity_weight=0.3)
        result = reranker.ensure_diversity(sample_retrieval_results)
        assert isinstance(result, list)

    def test_rerank_empty_list(self):
        reranker = ReRanker()
        result = reranker.rerank("query", [])
        assert result == []

    def test_rerank_single_item(self):
        reranker = ReRanker()
        single = [
            RetrievalResult(
                memory_id="one",
                content="只有一条结果",
                score=0.9,
                source="vector",
                metadata={},
                retrieval_path=[],
            )
        ]
        result = reranker.rerank("query", single)
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════
# FusionStrategy 测试
# ═══════════════════════════════════════════════════════════

class TestFusionStrategy:
    """融合策略测试"""

    def test_init(self):
        fusion = FusionStrategy()
        assert fusion is not None

    def test_rrf_fusion(self, sample_retrieval_results):
        fusion = FusionStrategy()
        list1 = sample_retrieval_results[:3]
        list2 = sample_retrieval_results[2:]
        fused = fusion.reciprocal_rank_fusion([list1, list2])
        assert isinstance(fused, list)
        assert len(fused) > 0

    def test_rrf_fusion_sorted(self, sample_retrieval_results):
        """RRF 结果应按分数降序排列"""
        fusion = FusionStrategy()
        fused = fusion.reciprocal_rank_fusion([sample_retrieval_results])
        scores = [r.score for r in fused]
        assert scores == sorted(scores, reverse=True)

    def test_weighted_fusion(self, sample_retrieval_results):
        fusion = FusionStrategy()
        list1 = sample_retrieval_results[:3]
        list2 = sample_retrieval_results[2:]
        fused = fusion.weighted_fusion([list1, list2], weights=[0.7, 0.3])
        assert isinstance(fused, list)

    def test_rrf_fusion_empty(self):
        fusion = FusionStrategy()
        result = fusion.reciprocal_rank_fusion([])
        assert result == []

    def test_rrf_deduplication(self):
        """相同 memory_id 的结果应被去重合并"""
        fusion = FusionStrategy()
        shared = RetrievalResult(
            memory_id="shared",
            content="共享结果",
            score=0.8,
            source="vector",
            metadata={},
            retrieval_path=[],
        )
        list1 = [shared]
        list2 = [
            RetrievalResult(
                memory_id="shared",
                content="共享结果",
                score=0.7,
                source="graph",
                metadata={},
                retrieval_path=[],
            )
        ]
        fused = fusion.reciprocal_rank_fusion([list1, list2])
        ids = [r.memory_id for r in fused]
        assert ids.count("shared") == 1


# ═══════════════════════════════════════════════════════════
# AdaptiveRetriever 集成测试
# ═══════════════════════════════════════════════════════════

class TestAdaptiveRetriever:
    """自适应检索器集成测试"""

    def test_init(self, memory_manager):
        retriever = AdaptiveRetriever(memory=memory_manager)
        assert retriever is not None

    def test_retrieve(self, memory_manager):
        retriever = AdaptiveRetriever(memory=memory_manager)
        results = retriever.retrieve("什么是人工智能？")
        assert isinstance(results, list)

    def test_retrieval_trace(self, memory_manager):
        retriever = AdaptiveRetriever(memory=memory_manager)
        retriever.retrieve("测试查询")
        trace = retriever.get_retrieval_trace()
        assert isinstance(trace, list)

    def test_multi_hop_retrieve(self, memory_manager):
        retriever = AdaptiveRetriever(memory=memory_manager)
        results = retriever.multi_hop_retrieve("人工智能", hops=2)
        assert isinstance(results, list)
