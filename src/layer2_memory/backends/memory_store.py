"""
内存存储实现

提供基于内存的向量存储和图存储实现，用于开发和测试。
"""

import math
import uuid
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from .base import (
    BaseVectorStore, BaseGraphStore,
    VectorRecord, SearchResult,
    GraphNode, GraphEdge
)


class InMemoryVectorStore(BaseVectorStore):
    """
    基于内存的向量存储
    
    适用于开发、测试和小规模应用场景。
    """
    
    def __init__(self, dimension: int = 768):
        """
        初始化内存向量存储
        
        Args:
            dimension: 向量维度
        """
        self._dimension = dimension
        self._records: Dict[str, VectorRecord] = {}
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def upsert(self, records: List[VectorRecord]) -> List[str]:
        """插入或更新向量记录"""
        ids = []
        for record in records:
            # 验证向量维度
            if len(record.vector) != self._dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self._dimension}, "
                    f"got {len(record.vector)}"
                )
            self._records[record.id] = record
            ids.append(record.id)
        return ids
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """向量相似度搜索"""
        if len(query_vector) != self._dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self._dimension}, "
                f"got {len(query_vector)}"
            )
        
        results = []
        
        for record in self._records.values():
            # 应用元数据过滤
            if filters and not self._match_filters(record.metadata, filters):
                continue
            
            # 计算余弦相似度
            score = self._cosine_similarity(query_vector, record.vector)
            
            # 应用阈值过滤
            if score >= threshold:
                results.append(SearchResult(
                    id=record.id,
                    score=score,
                    content=record.content,
                    metadata=record.metadata
                ))
        
        # 按相似度降序排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def get(self, ids: List[str]) -> List[Optional[VectorRecord]]:
        """批量获取向量记录"""
        return [self._records.get(id_) for id_ in ids]
    
    def delete(self, ids: List[str]) -> int:
        """删除向量记录"""
        count = 0
        for id_ in ids:
            if id_ in self._records:
                del self._records[id_]
                count += 1
        return count
    
    def count(self) -> int:
        """返回记录总数"""
        return len(self._records)
    
    def clear(self) -> int:
        """清空所有记录"""
        count = len(self._records)
        self._records.clear()
        return count
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _match_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                # 列表匹配：metadata[key] 在 value 列表中
                if metadata[key] not in value:
                    return False
            else:
                # 精确匹配
                if metadata[key] != value:
                    return False
        return True


class InMemoryGraphStore(BaseGraphStore):
    """
    基于内存的图存储
    
    适用于开发、测试和小规模应用场景。
    """
    
    def __init__(self):
        """初始化内存图存储"""
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        # 邻接表：node_id -> [(edge_id, neighbor_id, direction)]
        self._adjacency: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
    
    def add_node(self, node: GraphNode) -> str:
        """添加节点"""
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
        return node.id
    
    def add_edge(self, edge: GraphEdge) -> str:
        """添加边"""
        # 确保节点存在
        if edge.source_id not in self._nodes:
            raise ValueError(f"Source node not found: {edge.source_id}")
        if edge.target_id not in self._nodes:
            raise ValueError(f"Target node not found: {edge.target_id}")
        
        self._edges[edge.id] = edge
        
        # 更新邻接表
        self._adjacency[edge.source_id].append((edge.id, edge.target_id, "out"))
        self._adjacency[edge.target_id].append((edge.id, edge.source_id, "in"))
        
        return edge.id
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self._nodes.get(node_id)
    
    def get_neighbors(
        self,
        node_id: str,
        edge_types: Optional[List[str]] = None,
        direction: str = "both"
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        """获取邻居节点"""
        if node_id not in self._adjacency:
            return []
        
        results = []
        
        for edge_id, neighbor_id, edge_direction in self._adjacency[node_id]:
            # 方向过滤
            if direction != "both" and edge_direction != direction:
                continue
            
            edge = self._edges.get(edge_id)
            if edge is None:
                continue
            
            # 边类型过滤
            if edge_types and edge.edge_type not in edge_types:
                continue
            
            neighbor = self._nodes.get(neighbor_id)
            if neighbor:
                results.append((neighbor, edge))
        
        return results
    
    def traverse(
        self,
        start_id: str,
        max_depth: int = 2,
        edge_types: Optional[List[str]] = None
    ) -> List[GraphNode]:
        """图遍历（BFS）"""
        if start_id not in self._nodes:
            return []
        
        visited = {start_id}
        result = [self._nodes[start_id]]
        current_level = [start_id]
        
        for depth in range(max_depth):
            next_level = []
            
            for node_id in current_level:
                neighbors = self.get_neighbors(node_id, edge_types, "out")
                
                for neighbor, edge in neighbors:
                    if neighbor.id not in visited:
                        visited.add(neighbor.id)
                        result.append(neighbor)
                        next_level.append(neighbor.id)
            
            current_level = next_level
            
            if not current_level:
                break
        
        return result
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[GraphNode]]:
        """查找两节点间的路径（BFS）"""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        
        if source_id == target_id:
            return [self._nodes[source_id]]
        
        visited = {source_id}
        # queue: (current_id, path)
        queue = [(source_id, [source_id])]
        
        while queue and len(queue[0][1]) <= max_depth:
            current_id, path = queue.pop(0)
            
            for neighbor, edge in self.get_neighbors(current_id, direction="out"):
                if neighbor.id == target_id:
                    # 找到路径
                    full_path = path + [target_id]
                    return [self._nodes[nid] for nid in full_path]
                
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append((neighbor.id, path + [neighbor.id]))
        
        return None
    
    def delete_node(self, node_id: str) -> bool:
        """删除节点（及相关边）"""
        if node_id not in self._nodes:
            return False
        
        # 删除相关边
        edges_to_delete = []
        for edge_id, neighbor_id, _ in self._adjacency.get(node_id, []):
            edges_to_delete.append(edge_id)
        
        for edge_id in edges_to_delete:
            self.delete_edge(edge_id)
        
        # 删除节点
        del self._nodes[node_id]
        if node_id in self._adjacency:
            del self._adjacency[node_id]
        
        return True
    
    def delete_edge(self, edge_id: str) -> bool:
        """删除边"""
        if edge_id not in self._edges:
            return False
        
        edge = self._edges[edge_id]
        
        # 从邻接表移除
        self._adjacency[edge.source_id] = [
            (eid, nid, d) for eid, nid, d in self._adjacency[edge.source_id]
            if eid != edge_id
        ]
        self._adjacency[edge.target_id] = [
            (eid, nid, d) for eid, nid, d in self._adjacency[edge.target_id]
            if eid != edge_id
        ]
        
        # 删除边
        del self._edges[edge_id]
        
        return True
    
    def node_count(self) -> int:
        """返回节点总数"""
        return len(self._nodes)
    
    def edge_count(self) -> int:
        """返回边总数"""
        return len(self._edges)
    
    def search_nodes(
        self,
        name_pattern: Optional[str] = None,
        node_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[GraphNode]:
        """搜索节点"""
        results = []
        
        for node in self._nodes.values():
            # 名称模式匹配
            if name_pattern and name_pattern.lower() not in node.name.lower():
                continue
            
            # 类型匹配
            if node_type and node.node_type != node_type:
                continue
            
            # 属性匹配
            if properties:
                match = True
                for key, value in properties.items():
                    if key not in node.properties or node.properties[key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(node)
            
            if len(results) >= limit:
                break
        
        return results
    
    def clear(self) -> Tuple[int, int]:
        """
        清空所有数据
        
        Returns:
            Tuple[int, int]: (删除的节点数, 删除的边数)
        """
        node_count = len(self._nodes)
        edge_count = len(self._edges)
        
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        
        return node_count, edge_count
