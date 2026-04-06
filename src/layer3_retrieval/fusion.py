"""
Fusion Strategy - 结果融合策略
"""

from typing import List
from .models import RetrievalResult


class FusionStrategy:
    """
    结果融合策略
    
    支持多种融合方法：
    - RRF (Reciprocal Rank Fusion)
    - 加权融合
    """
    
    def reciprocal_rank_fusion(
        self,
        results_list: List[List[RetrievalResult]],
        k: int = 60
    ) -> List[RetrievalResult]:
        """
        倒数排名融合
        
        Args:
            results_list: 多个检索结果列表
            k: RRF 参数
            
        Returns:
            List[RetrievalResult]: 融合后的结果
        """
        if not results_list:
            return []
        
        # 计算 RRF 分数
        rrf_scores = {}
        result_map = {}
        
        for results in results_list:
            for rank, result in enumerate(results):
                memory_id = result.memory_id
                
                # RRF 分数累加
                rrf_score = 1.0 / (k + rank + 1)
                rrf_scores[memory_id] = rrf_scores.get(memory_id, 0) + rrf_score
                
                # 保存结果对象
                if memory_id not in result_map:
                    result_map[memory_id] = result
        
        # 创建融合结果
        fused_results = []
        for memory_id, rrf_score in rrf_scores.items():
            result = result_map[memory_id]
            # 创建新的结果对象（更新分数）
            fused_result = RetrievalResult(
                memory_id=result.memory_id,
                content=result.content,
                score=rrf_score,
                source="fusion",
                metadata=result.metadata,
                retrieval_path=result.retrieval_path
            )
            fused_results.append(fused_result)
        
        # 按分数排序
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results
    
    def weighted_fusion(
        self,
        results_list: List[List[RetrievalResult]],
        weights: List[float]
    ) -> List[RetrievalResult]:
        """
        加权融合
        
        Args:
            results_list: 多个检索结果列表
            weights: 各列表的权重
            
        Returns:
            List[RetrievalResult]: 融合后的结果
        """
        if not results_list or len(results_list) != len(weights):
            raise ValueError("结果列表和权重列表长度不匹配")
        
        # 归一化权重
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # 计算加权分数
        weighted_scores = {}
        result_map = {}
        
        for results, weight in zip(results_list, weights):
            for result in results:
                memory_id = result.memory_id
                
                # 加权分数累加
                weighted_score = result.score * weight
                weighted_scores[memory_id] = weighted_scores.get(memory_id, 0) + weighted_score
                
                # 保存结果对象
                if memory_id not in result_map:
                    result_map[memory_id] = result
        
        # 创建融合结果
        fused_results = []
        for memory_id, weighted_score in weighted_scores.items():
            result = result_map[memory_id]
            fused_result = RetrievalResult(
                memory_id=result.memory_id,
                content=result.content,
                score=weighted_score,
                source="fusion",
                metadata=result.metadata,
                retrieval_path=result.retrieval_path
            )
            fused_results.append(fused_result)
        
        # 按分数排序
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results
