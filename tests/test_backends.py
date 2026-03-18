# -*- coding: utf-8 -*-
"""
内存后端测试 - InMemoryVectorStore, InMemoryGraphStore
"""

import pytest
import numpy as np
from datetime import datetime

from src.memory.backends import (
    InMemoryVectorStore,
    InMemoryGraphStore,
)
from src.memory.backends.base import VectorRecord, GraphNode, GraphEdge, SearchResult


# ═══════════════════════════════════════════════════════════
# InMemoryVectorStore 测试
# ═══════════════════════════════════════════════════════════

class TestInMemoryVectorStore:
    """内存向量存储测试"""

    def test_init(self):
        store = InMemoryVectorStore(dimension=128)
        assert store is not None
        assert store.dimension == 128

    def test_upsert_and_count(self):
        store = InMemoryVectorStore(dimension=4)
        records = [
            VectorRecord(
                id="v1",
                vector=np.array([1.0, 0.0, 0.0, 0.0]),
                content="向量 1",
                metadata={},
                created_at=datetime.now(),
            ),
            VectorRecord(
                id="v2",
                vector=np.array([0.0, 1.0, 0.0, 0.0]),
                content="向量 2",
                metadata={},
                created_at=datetime.now(),
            ),
        ]
        store.upsert(records)
        assert store.count() == 2

    def test_search(self):
        store = InMemoryVectorStore(dimension=4)
        records = [
            VectorRecord(
                id=f"v{i}",
                vector=np.eye(4)[i],
                content=f"向量 {i}",
                metadata={},
                created_at=datetime.now(),
            )
            for i in range(4)
        ]
        store.upsert(records)

        results = store.search(query_vector=np.array([1.0, 0.0, 0.0, 0.0]), top_k=2)
        assert len(results) > 0
        assert results[0].id == "v0"  # 最相似的应该是 v0

    def test_get(self):
        store = InMemoryVectorStore(dimension=4)
        store.upsert([
            VectorRecord(
                id="g1",
                vector=np.array([1.0, 0.0, 0.0, 0.0]),
                content="测试",
                metadata={},
                created_at=datetime.now(),
            )
        ])
        results = store.get(["g1"])
        assert len(results) == 1

    def test_delete(self):
        store = InMemoryVectorStore(dimension=4)
        store.upsert([
            VectorRecord(
                id="d1",
                vector=np.array([1.0, 0.0, 0.0, 0.0]),
                content="删除测试",
                metadata={},
                created_at=datetime.now(),
            )
        ])
        store.delete(["d1"])
        assert store.count() == 0

    def test_clear(self):
        store = InMemoryVectorStore(dimension=4)
        store.upsert([
            VectorRecord(
                id="c1",
                vector=np.array([1.0, 0.0, 0.0, 0.0]),
                content="清空测试",
                metadata={},
                created_at=datetime.now(),
            )
        ])
        store.clear()
        assert store.count() == 0


# ═══════════════════════════════════════════════════════════
# InMemoryGraphStore 测试
# ═══════════════════════════════════════════════════════════

class TestInMemoryGraphStore:
    """内存图存储测试"""

    def test_init(self):
        store = InMemoryGraphStore()
        assert store is not None

    def test_add_node(self):
        store = InMemoryGraphStore()
        node = GraphNode(
            id="n1",
            name="AI",
            node_type="concept",
            properties={},
            created_at=datetime.now(),
        )
        store.add_node(node)
        assert store.node_count() == 1

    def test_get_node(self):
        store = InMemoryGraphStore()
        node = GraphNode(
            id="n1", name="AI", node_type="concept",
            properties={}, created_at=datetime.now(),
        )
        store.add_node(node)
        retrieved = store.get_node("n1")
        assert retrieved is not None
        assert retrieved.name == "AI"

    def test_add_edge(self):
        store = InMemoryGraphStore()
        store.add_node(GraphNode(id="a", name="A", node_type="t", properties={}, created_at=datetime.now()))
        store.add_node(GraphNode(id="b", name="B", node_type="t", properties={}, created_at=datetime.now()))
        edge = GraphEdge(
            id="e1",
            source_id="a",
            target_id="b",
            edge_type="related",
            weight=1.0,
            properties={},
            created_at=datetime.now(),
        )
        store.add_edge(edge)
        assert store.edge_count() == 1

    def test_get_neighbors(self):
        store = InMemoryGraphStore()
        store.add_node(GraphNode(id="a", name="A", node_type="t", properties={}, created_at=datetime.now()))
        store.add_node(GraphNode(id="b", name="B", node_type="t", properties={}, created_at=datetime.now()))
        store.add_edge(GraphEdge(
            id="e1", source_id="a", target_id="b",
            edge_type="related", weight=1.0, properties={}, created_at=datetime.now(),
        ))
        neighbors = store.get_neighbors("a")
        assert len(neighbors) > 0

    def test_traverse(self):
        store = InMemoryGraphStore()
        for i in range(3):
            store.add_node(GraphNode(
                id=f"t{i}", name=f"Node{i}", node_type="concept",
                properties={}, created_at=datetime.now(),
            ))
        store.add_edge(GraphEdge(
            id="e01", source_id="t0", target_id="t1",
            edge_type="r", weight=1.0, properties={}, created_at=datetime.now(),
        ))
        store.add_edge(GraphEdge(
            id="e12", source_id="t1", target_id="t2",
            edge_type="r", weight=1.0, properties={}, created_at=datetime.now(),
        ))
        result = store.traverse("t0", max_depth=2)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_find_path(self):
        store = InMemoryGraphStore()
        for i in range(3):
            store.add_node(GraphNode(
                id=f"p{i}", name=f"P{i}", node_type="t",
                properties={}, created_at=datetime.now(),
            ))
        store.add_edge(GraphEdge(
            id="ep01", source_id="p0", target_id="p1",
            edge_type="r", weight=1.0, properties={}, created_at=datetime.now(),
        ))
        store.add_edge(GraphEdge(
            id="ep12", source_id="p1", target_id="p2",
            edge_type="r", weight=1.0, properties={}, created_at=datetime.now(),
        ))
        path = store.find_path("p0", "p2")
        assert path is not None
        assert len(path) > 0

    def test_delete_node(self):
        store = InMemoryGraphStore()
        store.add_node(GraphNode(
            id="del", name="DeleteMe", node_type="t",
            properties={}, created_at=datetime.now(),
        ))
        store.delete_node("del")
        assert store.node_count() == 0

    def test_search_nodes(self):
        store = InMemoryGraphStore()
        store.add_node(GraphNode(
            id="s1", name="机器学习", node_type="concept",
            properties={}, created_at=datetime.now(),
        ))
        store.add_node(GraphNode(
            id="s2", name="深度学习", node_type="concept",
            properties={}, created_at=datetime.now(),
        ))
        results = store.search_nodes(node_type="concept")
        assert len(results) == 2

    def test_clear(self):
        store = InMemoryGraphStore()
        store.add_node(GraphNode(
            id="c1", name="ClearMe", node_type="t",
            properties={}, created_at=datetime.now(),
        ))
        result = store.clear()
        assert store.node_count() == 0
