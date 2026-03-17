"""
Pounce Retriever - 扑击检索器
模拟猫捕猎时的"锁定-跳跃"机制
"""

from typing import List, Optional
import numpy as np
from necorag.memory.manager import MemoryManager
from necorag.memory.models import MemoryLayer
from necorag.retrieval.models import RetrievalResult, QueryAnalysis
from necorag.retrieval.hyde import HyDEEnhancer
from necorag.retrieval.reranker import ReRanker
from necorag.retrieval.fusion import FusionStrategy


class PounceController:
    """
    扑击控制器
    
    模拟猫捕猎的"锁定-跳跃"行为：
    - 一旦置信度超过阈值，立即终止冗余检索
    - 避免浪费计算资源
    """
    
    def __init__(
        self,
        threshold: float = 0.85,
        min_gain: float = 0.05
    ):
        """
        初始化扑击控制器
        
        Args:
            threshold: 置信度阈值
            min_gain: 最小边际收益
        """
        self.threshold = threshold
        self.min_gain = min_gain
        self.last_confidence = 0.0
    
    def evaluate_confidence(self, results: List[RetrievalResult]) -> float:
        """
        评估检索结果的置信度
        
        Args:
            results: 检索结果列表
            
        Returns:
            float: 置信度 (0-1)
        """
        if not results:
            return 0.0
        
        # 基于 top-1 分数和分数分布
        top_score = results[0].score
        
        # 如果只有少量结果，置信度较低
        if len(results) < 3:
            return top_score * 0.8
        
        # 如果 top-1 与 top-2 差距大，置信度高
        score_gap = results[0].score - results[1].score
        
        confidence = top_score * (1 + score_gap)
        return min(confidence, 1.0)
    
    def should_pounce(self, confidence: float) -> bool:
        """
        判断是否应该"扑击"（返回结果）
        
        Args:
            confidence: 当前置信度
            
        Returns:
            bool: 是否立即返回结果
        """
        # 策略1: 固定阈值
        if confidence > self.threshold:
            return True
        
        # 策略2: 边际收益递减
        marginal_gain = confidence - self.last_confidence
        if self.last_confidence > 0 and marginal_gain < self.min_gain:
            return True
        
        self.last_confidence = confidence
        return False
    
    def calculate_adaptive_threshold(self, query: str) -> float:
        """
        计算自适应阈值
        
        Args:
            query: 查询文本
            
        Returns:
            float: 自适应阈值
            
        TODO: 基于查询复杂度调整阈值
        """
        # 简单实现：基于查询长度
        if len(query) < 20:
            return self.threshold * 0.9  # 简单查询降低阈值
        else:
            return self.threshold


class PounceRetriever:
    """
    扑击检索器
    
    集成多种检索策略和重排序
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        reranker_model: str = "BGE-Reranker-v2",
        pounce_threshold: float = 0.85,
        enable_hyde: bool = True
    ):
        """
        初始化检索器
        
        Args:
            memory: 记忆管理器
            reranker_model: 重排序模型
            pounce_threshold: 扑击阈值
            enable_hyde: 是否启用 HyDE
        """
        self.memory = memory
        self.hyde = HyDEEnhancer() if enable_hyde else None
        self.reranker = ReRanker(model=reranker_model)
        self.pounce_controller = PounceController(threshold=pounce_threshold)
        self.fusion = FusionStrategy()
        
        # 检索路径追踪
        self._retrieval_trace: List[str] = []
    
    def retrieve(
        self,
        query: str,
        query_vector: Optional[np.ndarray] = None,
        top_k: int = 10,
        min_score: float = 0.3
    ) -> List[RetrievalResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回数量
            min_score: 最低分数
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        self._retrieval_trace = []
        
        # 1. 分析查询
        query_analysis = self._analyze_query(query)
        self._retrieval_trace.append(f"Query analyzed: {query_analysis.query_type}")
        
        # 2. 多路检索
        all_results = []
        
        # 向量检索
        if query_vector is not None:
            vector_results = self._vector_retrieve(query_vector, top_k * 2)
            all_results.append(("vector", vector_results))
            self._retrieval_trace.append(f"Vector search: {len(vector_results)} results")
        
        # 图谱检索
        if query_analysis.entities:
            graph_results = self._graph_retrieve(query_analysis.entities, top_k)
            all_results.append(("graph", graph_results))
            self._retrieval_trace.append(f"Graph search: {len(graph_results)} results")
        
        # 3. 结果融合
        fused_results = self.fusion.reciprocal_rank_fusion(
            [results for source, results in all_results]
        )
        self._retrieval_trace.append(f"Fusion: {len(fused_results)} results")
        
        # 4. 重排序
        reranked_results = self.reranker.rerank(query, fused_results[:top_k * 2])
        self._retrieval_trace.append(f"Reranked: {len(reranked_results)} results")
        
        # 5. 过滤低分结果
        filtered_results = [r for r in reranked_results if r.score >= min_score]
        
        # 6. Pounce 判断
        confidence = self.pounce_controller.evaluate_confidence(filtered_results)
        
        if self.pounce_controller.should_pounce(confidence):
            self._retrieval_trace.append(f"Pounced! Confidence: {confidence:.2f}")
            return filtered_results[:top_k]
        else:
            self._retrieval_trace.append(f"Confidence too low: {confidence:.2f}")
            return filtered_results[:top_k]
    
    def retrieve_with_hyde(
        self,
        query: str,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        HyDE 增强检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        if self.hyde is None:
            return self.retrieve(query, top_k=top_k)
        
        # 生成假设文档
        hypothetical_doc = self.hyde.generate_hypothetical_doc(query)
        self._retrieval_trace.append(f"Generated hypothetical doc: {len(hypothetical_doc)} chars")
        
        # 使用假设文档检索
        # TODO: 需要将假设文档向量化
        return self.retrieve(query, top_k=top_k)
    
    def multi_hop_retrieve(
        self,
        entity: str,
        hops: int = 3
    ) -> List[RetrievalResult]:
        """
        多跳检索
        
        Args:
            entity: 起始实体
            hops: 跳数
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        # 从图谱进行多跳查询
        paths = self.memory.episodic_graph.multi_hop_query(entity, hops)
        
        results = []
        for path in paths:
            result = RetrievalResult(
                memory_id="",
                content=" -> ".join(path.nodes),
                score=path.total_strength,
                source="graph",
                retrieval_path=path.nodes
            )
            results.append(result)
        
        self._retrieval_trace.append(f"Multi-hop ({hops}): {len(results)} paths")
        return results
    
    def get_retrieval_trace(self) -> List[str]:
        """
        获取检索路径追踪
        
        Returns:
            List[str]: 检索步骤列表
        """
        return self._retrieval_trace
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        分析查询
        
        Args:
            query: 查询文本
            
        Returns:
            QueryAnalysis: 分析结果
            
        TODO: 实现查询理解和实体识别
        """
        # 最小实现
        return QueryAnalysis(
            original_query=query,
            query_type="factual",
            complexity="simple" if len(query) < 50 else "complex"
        )
    
    def _vector_retrieve(
        self,
        query_vector: np.ndarray,
        top_k: int
    ) -> List[RetrievalResult]:
        """
        向量检索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        search_results = self.memory.semantic_memory.search(query_vector, top_k)
        
        results = []
        for sr in search_results:
            result = RetrievalResult(
                memory_id=sr.memory_id,
                content=sr.content,
                score=sr.score,
                source="vector",
                metadata=sr.metadata
            )
            results.append(result)
        
        return results
    
    def _graph_retrieve(
        self,
        entities: List[str],
        top_k: int
    ) -> List[RetrievalResult]:
        """
        图谱检索
        
        Args:
            entities: 实体列表
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        # 最小实现：返回空列表
        return []
