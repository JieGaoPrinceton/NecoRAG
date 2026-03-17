"""
L2 语义记忆 (Qdrant/Milvus)
高维向量存储，模糊匹配与直觉检索
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
from src.memory.models import MemoryItem, MemoryLayer


@dataclass
class SearchResult:
    """检索结果"""
    memory_id: str
    content: str
    score: float
    metadata: Dict[str, any]


class SemanticMemory:
    """
    L2 语义记忆
    
    特性：
    - 高维向量存储
    - 混合搜索（向量+关键词）
    - HNSW 索引
    - 模糊匹配
    """
    
    def __init__(
        self,
        collection_name: str = "necorag",
        vector_size: int = 1024
    ):
        """
        初始化语义记忆
        
        Args:
            collection_name: 集合名称
            vector_size: 向量维度
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        # 最小实现：使用内存存储模拟向量数据库
        self._vectors: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict] = {}
    
    def store_vectors(
        self,
        memory_items: List[MemoryItem]
    ) -> List[str]:
        """
        存储向量
        
        Args:
            memory_items: 记忆项列表
            
        Returns:
            List[str]: 记忆 ID 列表
            
        TODO: 集成 Qdrant/Milvus
        """
        memory_ids = []
        
        for item in memory_items:
            if item.vector is not None:
                self._vectors[item.memory_id] = item.vector
                self._metadata[item.memory_id] = {
                    "content": item.content,
                    "layer": item.layer.value,
                    "weight": item.weight,
                    **item.metadata
                }
                memory_ids.append(item.memory_id)
        
        return memory_ids
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        向量检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            min_score: 最低分数
            
        Returns:
            List[SearchResult]: 检索结果列表
            
        TODO: 实现 HNSW 检索
        """
        # 最小实现：余弦相似度计算
        results = []
        
        for memory_id, vector in self._vectors.items():
            # 计算余弦相似度
            score = np.dot(query_vector, vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vector)
            )
            
            if score >= min_score:
                results.append(SearchResult(
                    memory_id=memory_id,
                    content=self._metadata[memory_id].get("content", ""),
                    score=float(score),
                    metadata=self._metadata[memory_id]
                ))
        
        # 排序并返回 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def hybrid_search(
        self,
        query_vector: np.ndarray,
        keywords: Dict[str, float],
        top_k: int = 10,
        vector_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        混合检索（向量 + 关键词）
        
        Args:
            query_vector: 查询向量
            keywords: 关键词权重字典
            top_k: 返回数量
            vector_weight: 向量权重
            
        Returns:
            List[SearchResult]: 检索结果列表
            
        TODO: 实现混合检索算法
        """
        # 最小实现：仅使用向量检索
        return self.search(query_vector, top_k)
    
    def update_metadata(
        self,
        memory_id: str,
        metadata: Dict
    ) -> bool:
        """
        更新元数据
        
        Args:
            memory_id: 记忆 ID
            metadata: 新元数据
            
        Returns:
            bool: 是否成功
        """
        if memory_id in self._metadata:
            self._metadata[memory_id].update(metadata)
            return True
        return False
    
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            bool: 是否成功
        """
        if memory_id in self._vectors:
            del self._vectors[memory_id]
            del self._metadata[memory_id]
            return True
        return False
