"""
ReRanker - 重排序器
基于 BGE-Reranker 和新颖性惩罚
"""

from typing import List, Optional
from .models import RetrievalResult
from src.core.base import BaseReranker


class ReRanker(BaseReranker):
    """
    重排序器
    
    功能：
    - BGE-Reranker 精排
    - Novelty 惩罚（抑制重复）
    - 多样性保证
    """
    
    def __init__(
        self,
        model: str = "BGE-Reranker-v2",
        novelty_weight: float = 0.3,
        diversity_weight: float = 0.2,
        redundancy_penalty: float = 0.4
    ):
        """
        初始化重排序器
        
        Args:
            model: 重排序模型
            novelty_weight: 新颖性权重
            diversity_weight: 多样性权重
            redundancy_penalty: 冗余惩罚
        """
        self.model = model
        self.novelty_weight = novelty_weight
        self.diversity_weight = diversity_weight
        self.redundancy_penalty = redundancy_penalty
    
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        重排序检索结果
        
        Args:
            query: 查询文本
            results: 检索结果
            top_k: 返回数量（可选）
            
        Returns:
            List[RetrievalResult]: 重排序后的结果
            
        TODO: 集成 BGE-Reranker-v2 模型
        """
        if not results:
            return results
        
        # 应用新颖性惩罚
        results = self.apply_novelty_penalty(results)
        
        # 应用多样性
        results = self.ensure_diversity(results)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 如果指定了 top_k，截取结果
        if top_k is not None:
            results = results[:top_k]
        
        return results
    
    def apply_novelty_penalty(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        应用新颖性惩罚
        
        Args:
            results: 检索结果
            
        Returns:
            List[RetrievalResult]: 应用惩罚后的结果
        """
        if len(results) <= 1:
            return results
        
        # 计算相似度矩阵
        for i, result_i in enumerate(results):
            redundancy_score = 0.0
            
            # 与之前已选结果的重复度
            for j in range(i):
                result_j = results[j]
                # 简单的文本相似度计算
                similarity = self._text_similarity(
                    result_i.content,
                    result_j.content
                )
                redundancy_score += similarity
            
            # 应用惩罚
            if i > 0:
                penalty = self.redundancy_penalty * (redundancy_score / i)
                result_i.score *= (1 - penalty)
        
        return results
    
    def ensure_diversity(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        确保结果多样性
        
        Args:
            results: 检索结果
            
        Returns:
            List[RetrievalResult]: 多样化后的结果
        """
        if len(results) <= 1:
            return results
        
        # 简单实现：MMR-like 策略
        selected = [results[0]]
        remaining = results[1:]
        
        while remaining and len(selected) < len(results):
            best_idx = 0
            best_score = -1
            
            for i, candidate in enumerate(remaining):
                # 相关性分数
                relevance = candidate.score
                
                # 与已选结果的最大相似度
                max_similarity = max(
                    self._text_similarity(candidate.content, s.content)
                    for s in selected
                )
                
                # MMR 分数
                mmr_score = self.diversity_weight * relevance - (1 - self.diversity_weight) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            selected.append(remaining[best_idx])
            remaining.pop(best_idx)
        
        return selected
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            float: 相似度 (0-1)
            
        TODO: 实现更准确的相似度计算
        """
        # 最小实现：Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
