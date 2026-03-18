"""
Memory Manager - 记忆管理器
统一管理三层记忆
"""

from typing import List, Optional
from src.perception.models import EncodedChunk
from src.memory.working_memory import WorkingMemory
from src.memory.semantic_memory import SemanticMemory
from src.memory.episodic_graph import EpisodicGraph
from src.memory.decay import MemoryDecay
from src.memory.models import MemoryItem, MemoryLayer, Entity, Relation
import uuid


class MemoryManager:
    """
    记忆管理器
    
    统一管理 L1、L2、L3 三层记忆
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        neo4j_url: Optional[str] = None,
        decay_rate: float = 0.1
    ):
        """
        初始化记忆管理器
        
        Args:
            redis_url: Redis 连接 URL（L1）
            qdrant_url: Qdrant 连接 URL（L2）
            neo4j_url: Neo4j 连接 URL（L3）
            decay_rate: 衰减速率
        """
        # 初始化三层记忆
        self.working_memory = WorkingMemory()
        self.semantic_memory = SemanticMemory()
        self.episodic_graph = EpisodicGraph()
        self.decay = MemoryDecay(decay_rate=decay_rate)
        
        # 统一存储（用于跨层检索）
        self._memory_store: dict[str, MemoryItem] = {}
    
    def store(self, chunk: EncodedChunk) -> str:
        """
        存储知识到记忆系统
        
        Args:
            chunk: 编码后的文本块
            
        Returns:
            str: 记忆 ID
        """
        memory_id = str(uuid.uuid4())
        
        # 创建记忆项
        memory_item = MemoryItem(
            memory_id=memory_id,
            content=chunk.content,
            layer=MemoryLayer.L2_SEMANTIC,
            vector=chunk.dense_vector,
            metadata={
                "sparse_vector": chunk.sparse_vector,
                "entities": chunk.entities,
                "context_tags": chunk.context_tags,
                **chunk.metadata
            }
        )
        
        # 存储到 L2 语义记忆
        self.semantic_memory.store_vectors([memory_item])
        
        # 存储实体到 L3 图谱
        for entity_triple in chunk.entities:
            if len(entity_triple) == 3:
                subject, relation, obj = entity_triple
                
                # 创建实体
                subject_entity = Entity(
                    entity_id=str(uuid.uuid4()),
                    name=subject,
                    entity_type="unknown"
                )
                obj_entity = Entity(
                    entity_id=str(uuid.uuid4()),
                    name=obj,
                    entity_type="unknown"
                )
                
                self.episodic_graph.add_entity(subject_entity)
                self.episodic_graph.add_entity(obj_entity)
                
                # 创建关系
                rel = Relation(
                    source_id=subject_entity.entity_id,
                    target_id=obj_entity.entity_id,
                    relation_type=relation
                )
                self.episodic_graph.add_relation(
                    subject_entity.entity_id,
                    obj_entity.entity_id,
                    rel
                )
        
        # 统一存储
        self._memory_store[memory_id] = memory_item
        
        return memory_id
    
    def retrieve(
        self,
        query: str,
        query_vector=None,
        layers: Optional[List[MemoryLayer]] = None,
        top_k: int = 10
    ) -> List[MemoryItem]:
        """
        从记忆系统检索知识
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            layers: 检索层级（None 则检索所有层）
            top_k: 返回数量
            
        Returns:
            List[MemoryItem]: 检索结果
        """
        layers = layers or [MemoryLayer.L1_WORKING, MemoryLayer.L2_SEMANTIC]
        results = []
        
        # L2 向量检索
        if MemoryLayer.L2_SEMANTIC in layers and query_vector is not None:
            search_results = self.semantic_memory.search(query_vector, top_k)
            
            for result in search_results:
                if result.memory_id in self._memory_store:
                    memory_item = self._memory_store[result.memory_id]
                    # 强化访问的记忆
                    self.decay.reinforce(memory_item)
                    results.append(memory_item)
        
        return results
    
    def consolidate(self) -> None:
        """
        记忆巩固
        
        - L1 高频数据 → L2 持久化
        - 低频数据 → 归档
        """
        # 应用衰减
        memories = list(self._memory_store.values())
        self.decay.apply_decay(memories)
        
        # 识别需要归档的记忆
        to_archive = self.decay.archive_low_weight(memories)
        
        # 移除归档记忆
        for memory_id in to_archive:
            self.semantic_memory.delete(memory_id)
            self._memory_store.pop(memory_id, None)
    
    def forget(self, threshold: float = 0.05) -> int:
        """
        主动遗忘低价值记忆
        
        Args:
            threshold: 遗忘阈值
            
        Returns:
            int: 遗忘的记忆数量
        """
        memories = list(self._memory_store.values())
        to_forget = self.decay.archive_low_weight(memories, threshold)
        
        for memory_id in to_forget:
            self.semantic_memory.delete(memory_id)
            self._memory_store.pop(memory_id, None)
        
        return len(to_forget)
    
    def count(self) -> int:
        """
        获取记忆条目总数
        
        Returns:
            int: 条目总数
        """
        return len(self._memory_store)
