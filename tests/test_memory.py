# -*- coding: utf-8 -*-
"""
记忆系统测试 - 工作记忆、语义记忆、情景图谱、衰减机制
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from src.memory import (
    MemoryManager,
    WorkingMemory,
    SemanticMemory,
    EpisodicGraph,
    MemoryDecay,
    MemoryItem,
    MemoryLayer,
)
from src.memory.models import Entity, Relation, Intent, GraphPath
from src.perception.models import EncodedChunk, ContextTags


# ═══════════════════════════════════════════════════════════
# WorkingMemory (L1) 测试
# ═══════════════════════════════════════════════════════════

class TestWorkingMemory:
    """工作记忆测试"""

    def test_init(self, working_memory):
        assert working_memory is not None

    def test_add_and_get_context(self, working_memory):
        working_memory.add_context("session-1", {"query": "测试", "topic": "AI"})
        ctx = working_memory.get_context("session-1")
        assert ctx is not None
        assert ctx.get("query") == "测试"

    def test_get_nonexistent_session(self, working_memory):
        ctx = working_memory.get_context("nonexistent")
        assert ctx == {} or ctx is None

    def test_track_intent(self, working_memory, sample_intent):
        working_memory.add_context("session-1", {})
        working_memory.track_intent("session-1", sample_intent)
        trajectory = working_memory.get_intent_trajectory("session-1")
        assert isinstance(trajectory, list)
        assert len(trajectory) >= 1

    def test_clear_session(self, working_memory):
        working_memory.add_context("session-1", {"data": "test"})
        working_memory.clear_session("session-1")
        ctx = working_memory.get_context("session-1")
        assert ctx == {} or ctx is None

    def test_exists(self, working_memory):
        working_memory.add_context("session-1", {"data": "test"})
        assert working_memory.exists("session-1") is True
        assert working_memory.exists("nonexistent") is False

    def test_multiple_sessions(self, working_memory):
        working_memory.add_context("s1", {"data": "one"})
        working_memory.add_context("s2", {"data": "two"})
        assert working_memory.get_context("s1").get("data") == "one"
        assert working_memory.get_context("s2").get("data") == "two"


# ═══════════════════════════════════════════════════════════
# SemanticMemory (L2) 测试
# ═══════════════════════════════════════════════════════════

class TestSemanticMemory:
    """语义记忆测试"""

    def test_init(self, semantic_memory):
        assert semantic_memory is not None

    def test_store_and_search(self, semantic_memory):
        items = [
            MemoryItem(
                memory_id="sm-001",
                content="机器学习是AI的核心",
                layer=MemoryLayer.L2_SEMANTIC,
                vector=np.random.rand(768),
                metadata={},
                weight=1.0,
                access_count=0,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
            )
        ]
        ids = semantic_memory.store_vectors(items)
        assert len(ids) == 1

        query_vector = np.random.rand(768)
        results = semantic_memory.search(query_vector, top_k=5)
        assert isinstance(results, list)

    def test_search_returns_sorted_results(self, semantic_memory):
        """搜索结果应按分数降序排列"""
        for i in range(5):
            semantic_memory.store_vectors([
                MemoryItem(
                    memory_id=f"sm-{i:03d}",
                    content=f"内容 {i}",
                    layer=MemoryLayer.L2_SEMANTIC,
                    vector=np.random.rand(768),
                    metadata={},
                    weight=1.0,
                    access_count=0,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                )
            ])
        results = semantic_memory.search(np.random.rand(768), top_k=5)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_delete(self, semantic_memory):
        semantic_memory.store_vectors([
            MemoryItem(
                memory_id="del-001",
                content="待删除",
                layer=MemoryLayer.L2_SEMANTIC,
                vector=np.random.rand(768),
                metadata={},
                weight=1.0,
                access_count=0,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
            )
        ])
        result = semantic_memory.delete("del-001")
        assert result is True

    def test_delete_nonexistent(self, semantic_memory):
        result = semantic_memory.delete("nonexistent")
        assert result is False


# ═══════════════════════════════════════════════════════════
# EpisodicGraph (L3) 测试
# ═══════════════════════════════════════════════════════════

class TestEpisodicGraph:
    """情景图谱测试"""

    def test_init(self, episodic_graph):
        assert episodic_graph is not None

    def test_add_entity(self, episodic_graph, sample_entity):
        entity_id = episodic_graph.add_entity(sample_entity)
        assert entity_id is not None

    def test_get_entity(self, episodic_graph, sample_entity):
        episodic_graph.add_entity(sample_entity)
        entity = episodic_graph.get_entity(sample_entity.entity_id)
        assert entity is not None
        assert entity.name == sample_entity.name

    def test_add_relation(self, episodic_graph):
        e1 = Entity(entity_id="e1", name="AI", entity_type="concept", properties={})
        e2 = Entity(entity_id="e2", name="ML", entity_type="concept", properties={})
        episodic_graph.add_entity(e1)
        episodic_graph.add_entity(e2)

        rel = Relation(
            source_id="e1",
            target_id="e2",
            relation_type="includes",
            strength=0.9,
            properties={},
        )
        result = episodic_graph.add_relation("e1", "e2", rel)
        assert result is not None

    def test_get_related_entities(self, episodic_graph):
        e1 = Entity(entity_id="e1", name="AI", entity_type="concept", properties={})
        e2 = Entity(entity_id="e2", name="ML", entity_type="concept", properties={})
        episodic_graph.add_entity(e1)
        episodic_graph.add_entity(e2)

        rel = Relation(
            source_id="e1",
            target_id="e2",
            relation_type="includes",
            strength=0.9,
            properties={},
        )
        episodic_graph.add_relation("e1", "e2", rel)

        related = episodic_graph.get_related_entities("e1")
        assert isinstance(related, list)

    def test_multi_hop_query(self, episodic_graph):
        # 创建简单的 A -> B -> C 图
        entities = [
            Entity(entity_id=f"n{i}", name=f"Node{i}", entity_type="concept", properties={})
            for i in range(3)
        ]
        for e in entities:
            episodic_graph.add_entity(e)

        episodic_graph.add_relation(
            "n0", "n1",
            Relation(source_id="n0", target_id="n1", relation_type="related", strength=1.0, properties={}),
        )
        episodic_graph.add_relation(
            "n1", "n2",
            Relation(source_id="n1", target_id="n2", relation_type="related", strength=1.0, properties={}),
        )

        paths = episodic_graph.multi_hop_query("n0", hops=2)
        assert isinstance(paths, list)

    def test_find_causal_chain(self, episodic_graph):
        e1 = Entity(entity_id="cause", name="原因", entity_type="event", properties={})
        e2 = Entity(entity_id="effect", name="结果", entity_type="event", properties={})
        episodic_graph.add_entity(e1)
        episodic_graph.add_entity(e2)

        rel = Relation(
            source_id="cause",
            target_id="effect",
            relation_type="causes",
            strength=0.8,
            properties={},
        )
        episodic_graph.add_relation("cause", "effect", rel)

        chains = episodic_graph.find_causal_chain("原因")
        assert isinstance(chains, list)


# ═══════════════════════════════════════════════════════════
# MemoryDecay 测试
# ═══════════════════════════════════════════════════════════

class TestMemoryDecay:
    """记忆衰减测试"""

    def test_init(self, memory_decay):
        assert memory_decay is not None
        assert memory_decay.decay_rate == 0.1

    def test_calculate_weight(self, memory_decay, sample_memory_item):
        weight = memory_decay.calculate_weight(sample_memory_item)
        assert isinstance(weight, float)
        assert weight > 0

    def test_weight_decreases_over_time(self, memory_decay):
        """权重应随时间降低"""
        now = datetime.now()
        recent = MemoryItem(
            memory_id="recent",
            content="新记忆",
            layer=MemoryLayer.L2_SEMANTIC,
            vector=None,
            metadata={},
            weight=1.0,
            access_count=0,
            created_at=now,
            last_accessed=now,
        )
        old = MemoryItem(
            memory_id="old",
            content="旧记忆",
            layer=MemoryLayer.L2_SEMANTIC,
            vector=None,
            metadata={},
            weight=1.0,
            access_count=0,
            created_at=now - timedelta(days=365),
            last_accessed=now - timedelta(days=365),
        )
        w_recent = memory_decay.calculate_weight(recent, current_time=now)
        w_old = memory_decay.calculate_weight(old, current_time=now)
        assert w_recent > w_old

    def test_access_frequency_boosts_weight(self, memory_decay):
        """高频访问应提升权重"""
        now = datetime.now()
        base = MemoryItem(
            memory_id="base",
            content="测试",
            layer=MemoryLayer.L2_SEMANTIC,
            vector=None,
            metadata={},
            weight=1.0,
            access_count=0,
            created_at=now - timedelta(days=30),
            last_accessed=now,
        )
        frequent = MemoryItem(
            memory_id="frequent",
            content="测试",
            layer=MemoryLayer.L2_SEMANTIC,
            vector=None,
            metadata={},
            weight=1.0,
            access_count=100,
            created_at=now - timedelta(days=30),
            last_accessed=now,
        )
        w_base = memory_decay.calculate_weight(base, current_time=now)
        w_frequent = memory_decay.calculate_weight(frequent, current_time=now)
        assert w_frequent > w_base

    def test_apply_decay_batch(self, memory_decay, sample_memory_items):
        weights = memory_decay.apply_decay(sample_memory_items)
        assert isinstance(weights, dict)
        assert len(weights) == len(sample_memory_items)

    def test_reinforce(self, memory_decay, sample_memory_item):
        new_weight = memory_decay.reinforce(sample_memory_item, boost_factor=1.5)
        assert isinstance(new_weight, float)
        assert new_weight > 0

    def test_should_archive(self, memory_decay):
        now = datetime.now()
        very_old = MemoryItem(
            memory_id="archive",
            content="极旧记忆",
            layer=MemoryLayer.L2_SEMANTIC,
            vector=None,
            metadata={},
            weight=0.01,
            access_count=0,
            created_at=now - timedelta(days=3650),
            last_accessed=now - timedelta(days=3650),
        )
        result = memory_decay.should_archive(very_old)
        assert isinstance(result, bool)

    def test_archive_low_weight(self, memory_decay, sample_memory_items):
        archived = memory_decay.archive_low_weight(sample_memory_items)
        assert isinstance(archived, list)


# ═══════════════════════════════════════════════════════════
# MemoryManager 集成测试
# ═══════════════════════════════════════════════════════════

class TestMemoryManager:
    """记忆管理器集成测试"""

    def test_init(self, memory_manager):
        assert memory_manager is not None

    def test_store_and_retrieve(self, memory_manager, sample_encoded_chunk):
        memory_id = memory_manager.store(sample_encoded_chunk)
        assert memory_id is not None
        assert isinstance(memory_id, str)

    def test_retrieve(self, memory_manager, sample_encoded_chunk):
        memory_manager.store(sample_encoded_chunk)
        results = memory_manager.retrieve("人工智能", top_k=5)
        assert isinstance(results, list)

    def test_consolidate(self, memory_manager):
        memory_manager.consolidate()
        # 不应抛出异常

    def test_forget(self, memory_manager):
        count = memory_manager.forget(threshold=0.05)
        assert isinstance(count, int)
        assert count >= 0
