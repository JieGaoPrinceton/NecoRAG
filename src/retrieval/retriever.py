"""
Adaptive Retriever - 自适应检索器
实现智能化的“早停机制”和领域权重计算
"""

import logging
import time
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
from src.memory.manager import MemoryManager
from src.memory.models import MemoryLayer
from src.retrieval.models import RetrievalResult, QueryAnalysis
from src.retrieval.hyde import HyDEEnhancer
from src.retrieval.reranker import ReRanker
from src.retrieval.fusion import FusionStrategy
from src.retrieval.web_search import (
    WebSearchEngine,
    SearchResultValidator,
    HumanConfirmationManager,
    WebSearchResult,
    WebSearchConfig
)
from src.core.base import BaseRetriever

# 领域权重模块
try:
    from src.domain import (
        DomainConfig,
        CompositeWeightCalculator,
        DocumentMetadata,
        WeightedScore,
        QueryRelevanceEnhancer,
    )
    DOMAIN_WEIGHT_AVAILABLE = True
except ImportError:
    DOMAIN_WEIGHT_AVAILABLE = False


logger = logging.getLogger(__name__)


class EarlyTerminationController:
    """
    早停控制器
    
    智能检索终止策略：
    - 一旦置信度超过阈值，立即终止冗余检索
    - 避免浪费计算资源
    """
    
    def __init__(
        self,
        threshold: float = 0.85,
        min_gain: float = 0.05
    ):
        """
        初始化早停控制器
        
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
    
    def should_terminate(self, confidence: float) -> bool:
        """
        判断是否应该提前终止（返回结果）
        
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


class AdaptiveRetriever(BaseRetriever):
    """
    自适应检索器
    
    集成多种检索策略、重排序和领域权重计算
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        reranker_model: str = "BGE-Reranker-v2",
        confidence_threshold: float = 0.85,
        enable_hyde: bool = True,
        domain_config: Optional["DomainConfig"] = None
    ):
        """
        初始化检索器
        
        Args:
            memory: 记忆管理器
            reranker_model: 重排序模型
            confidence_threshold: 置信度阈值
            enable_hyde: 是否启用 HyDE
            domain_config: 领域配置（用于领域权重计算）
        """
        self.memory = memory
        self.hyde = HyDEEnhancer() if enable_hyde else None
        self.reranker = ReRanker(model=reranker_model)
        self.termination_controller = EarlyTerminationController(threshold=confidence_threshold)
        self.fusion = FusionStrategy()
        
        # 领域权重计算器
        self.domain_config = domain_config
        self.weight_calculator: Optional["CompositeWeightCalculator"] = None
        self.query_enhancer: Optional["QueryRelevanceEnhancer"] = None
        
        # 互联网搜索组件
        self.web_search_engine: Optional[WebSearchEngine] = None
        self.search_validator: Optional[SearchResultValidator] = None
        self.confirmation_manager: Optional[HumanConfirmationManager] = None
        
        if domain_config and DOMAIN_WEIGHT_AVAILABLE:
            self.weight_calculator = CompositeWeightCalculator(domain_config)
            self.query_enhancer = QueryRelevanceEnhancer(domain_config)
        
        # 检索路径追踪
        self._retrieval_trace: List[str] = []
    
    def set_domain_config(self, domain_config: "DomainConfig") -> None:
        """
        设置领域配置
        
        Args:
            domain_config: 领域配置
        """
        self.domain_config = domain_config
        if DOMAIN_WEIGHT_AVAILABLE:
            self.weight_calculator = CompositeWeightCalculator(domain_config)
            self.query_enhancer = QueryRelevanceEnhancer(domain_config)
    
    def set_web_search_config(self, config: "RetrievalConfig") -> None:
        """
        设置互联网搜索配置
        
        Args:
            config: 检索配置
        """
        if not config.enable_web_search:
            return
        
        # 创建Web搜索配置
        web_config = WebSearchConfig(
            enable_web_search=config.enable_web_search,
            search_engines=config.search_engines,
            max_results=config.web_search_max_results,
            timeout=30,
            rate_limit=10
        )
        
        # 初始化Web搜索组件
        self.web_search_engine = WebSearchEngine(web_config)
        self.search_validator = SearchResultValidator(
            min_credibility=0.5,
            min_relevance=0.3
        )
        self.confirmation_manager = HumanConfirmationManager(
            confirmation_timeout=config.confirmation_timeout
        )
    
    def retrieve(
        self,
        query: str,
        query_vector: Optional[np.ndarray] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        apply_domain_weight: bool = True
    ) -> List[RetrievalResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回数量
            min_score: 最低分数
            apply_domain_weight: 是否应用领域权重
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        _start = time.time()
        logger.info(f"Retrieval started: query='{query[:30]}...', top_k={top_k}")
        self._retrieval_trace = []
        
        # 0. 查询增强（识别领域关键字）
        query_keywords = []
        query_boost = 1.0
        if self.query_enhancer and apply_domain_weight:
            _, query_keywords, query_boost = self.query_enhancer.enhance_query(query)
            if query_keywords:
                self._retrieval_trace.append(f"Query keywords: {', '.join(query_keywords)} (boost: {query_boost:.2f})")
        
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
        
        # 5. 应用领域权重
        if self.weight_calculator and apply_domain_weight and DOMAIN_WEIGHT_AVAILABLE:
            reranked_results = self._apply_domain_weights(reranked_results, query)
            self._retrieval_trace.append(f"Domain weights applied")
        
        # 6. 过滤低分结果
        filtered_results = [r for r in reranked_results if r.score >= min_score]
        
        # 7. 早停判断
        confidence = self.termination_controller.evaluate_confidence(filtered_results)
        
        if self.termination_controller.should_terminate(confidence):
            self._retrieval_trace.append(f"Early terminated! Confidence: {confidence:.2f}")
            _elapsed = time.time() - _start
            logger.info(f"Retrieval completed: {len(filtered_results[:top_k])} results in {_elapsed:.3f}s (early terminated)")
            logger.debug(f"Retrieval trace: {self._retrieval_trace}")
            return filtered_results[:top_k]
        else:
            self._retrieval_trace.append(f"Confidence too low: {confidence:.2f}")
            _elapsed = time.time() - _start
            logger.info(f"Retrieval completed: {len(filtered_results[:top_k])} results in {_elapsed:.3f}s")
            logger.debug(f"Retrieval trace: {self._retrieval_trace}")
            return filtered_results[:top_k]
    
    def _apply_domain_weights(
        self, 
        results: List[RetrievalResult],
        query: str
    ) -> List[RetrievalResult]:
        """
        应用领域权重到检索结果
        
        Args:
            results: 检索结果列表
            query: 查询文本
            
        Returns:
            List[RetrievalResult]: 加权后的结果（按分数重新排序）
        """
        if not self.weight_calculator:
            return results
        
        weighted_results = []
        for result in results:
            # 创建文档元数据
            doc_metadata = DocumentMetadata(
                doc_id=result.memory_id,
                content=result.content,
                created_at=result.metadata.get("created_at", datetime.now()) 
                    if result.metadata else datetime.now(),
                is_evergreen=result.metadata.get("is_evergreen", False)
                    if result.metadata else False
            )
            
            # 计算加权分数
            weighted_score = self.weight_calculator.calculate_weight(
                base_score=result.score,
                doc_metadata=doc_metadata,
                query=query
            )
            
            # 更新结果分数
            result.score = weighted_score.final_score
            result.metadata = result.metadata or {}
            result.metadata["weight_details"] = {
                "base_score": weighted_score.base_score,
                "keyword_weight": weighted_score.keyword_weight,
                "temporal_weight": weighted_score.temporal_weight,
                "domain_weight": weighted_score.domain_weight,
            }
            weighted_results.append(result)
        
        # 按新分数重新排序
        weighted_results.sort(key=lambda x: x.score, reverse=True)
        return weighted_results
    
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
        logger.info(f"HyDE retrieval started: query='{query[:30]}...'")
        if self.hyde is None:
            logger.debug("HyDE not enabled, falling back to standard retrieval")
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
        logger.info(f"Multi-hop retrieval: entity='{entity}', hops={hops}")
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
        logger.debug(f"Multi-hop retrieval found {len(results)} paths")
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
    
    async def retrieve_async(
        self,
        query: str,
        query_vector: Optional[np.ndarray] = None,
        top_k: int = 10,
        min_score: float = 0.3,
        apply_domain_weight: bool = True,
        web_search_config: Optional["RetrievalConfig"] = None
    ) -> List[RetrievalResult]:
        """
        异步执行检索（支持互联网搜索回退）
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回数量
            min_score: 最低分数
            apply_domain_weight: 是否应用领域权重
            web_search_config: 互联网搜索配置
            
        Returns:
            List[RetrievalResult]: 检索结果
        """
        # 首先执行标准检索
        local_results = self.retrieve(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            min_score=min_score,
            apply_domain_weight=apply_domain_weight
        )
        
        # 如果启用了互联网搜索且回退条件满足
        if (web_search_config and web_search_config.enable_web_search and
            len(local_results) < web_search_config.web_search_min_results):
            
            # 执行互联网搜索
            web_results = await self._perform_web_search_fallback(query, top_k, web_search_config)
            
            # 合并结果
            combined_results = self._combine_results(local_results, web_results)
            
            # 重新排序和过滤
            combined_results.sort(key=lambda x: x.score, reverse=True)
            return combined_results[:top_k]
        
        return local_results[:top_k]
    
    async def _perform_web_search_fallback(
        self, 
        query: str, 
        top_k: int,
        config: Optional["RetrievalConfig"] = None
    ) -> List[RetrievalResult]:
        """
        执行互联网搜索回退
        
        Args:
            query: 查询文本
            top_k: 返回数量
            config: 检索配置
            
        Returns:
            List[RetrievalResult]: 搜索结果转换为检索结果
        """
        if not self.web_search_engine:
            return []
        
        try:
            # 执行网络搜索
            web_results = await self.web_search_engine.search(
                query, 
                max_results=config.web_search_max_results if config else 10
            )
            
            # 验证和过滤结果
            if self.search_validator:
                web_results = self.search_validator.validate_and_filter(web_results)
            
            # 转换为检索结果格式
            retrieval_results = []
            for i, web_result in enumerate(web_results[:top_k]):
                retrieval_result = RetrievalResult(
                    memory_id=f"web_{i}_{hash(web_result.url)}",
                    content=web_result.snippet,
                    score=web_result.composite_score,
                    source=f"web:{web_result.source}",
                    metadata={
                        "url": web_result.url,
                        "title": web_result.title,
                        "domain": web_result.domain,
                        "credibility": web_result.credibility_score,
                        "relevance": web_result.relevance_score,
                        "search_timestamp": web_result.timestamp.isoformat()
                    }
                )
                retrieval_results.append(retrieval_result)
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Web search fallback failed: {e}")
            return []
    
    def _combine_results(
        self, 
        local_results: List[RetrievalResult], 
        web_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        合并本地和网络检索结果
        
        Args:
            local_results: 本地检索结果
            web_results: 网络检索结果
            
        Returns:
            List[RetrievalResult]: 合并后的结果
        """
        # 为不同类型的结果设置不同的权重基础
        combined = []
        
        # 本地结果保持原有分数
        for result in local_results:
            combined.append(result)
        
        # 网络结果适当调整分数
        for result in web_results:
            # 网络结果分数通常较低，但可以适当提升
            adjusted_score = min(1.0, result.score * 1.2)  # 最多提升20%
            result.score = adjusted_score
            combined.append(result)
        
        # 去重（基于内容相似度）
        seen_contents = set()
        unique_results = []
        
        for result in combined:
            content_hash = hash(result.content.lower().strip())
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        return unique_results
