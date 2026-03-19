"""
策略融合引擎 (Strategy Fusion Engine)

多策略并行检索与结果融合
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import asyncio
import time


@dataclass
class StrategyWeight:
    """策略权重"""
    name: str
    weight: float
    priority: int = 0  # 优先级，数字越小优先级越高
    enabled: bool = True


@dataclass
class RetrievalResult:
    """检索结果"""
    strategy: str
    items: List[Any]
    scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0


@dataclass
class FusionConfig:
    """融合配置"""
    diversity_enabled: bool = True
    novelty_boost: float = 0.1
    max_same_domain_ratio: float = 0.6
    min_cross_domain_count: int = 2
    temporal_diversity: bool = True
    source_diversity: bool = True


class StrategyFusion:
    """
    策略融合引擎
    
    功能:
    1. 多策略并行执行
    2. 结果融合与归一化
    3. 多样性保证
    4. 重排序
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.strategy_templates = {}
        
        # 注册默认模板
        self._register_default_templates()
    
    def _register_default_templates(self):
        """注册默认策略模板"""
        from .intent_router import INTENT_STRATEGY_TEMPLATES, IntentType
        
        for intent_type, strategies in INTENT_STRATEGY_TEMPLATES.items():
            self.strategy_templates[intent_type.value] = [
                StrategyWeight(
                    name=s['name'],
                    weight=s['weight']
                )
                for s in strategies
            ]
    
    def get_template_for_intent(self, intent_type: str) -> List[StrategyWeight]:
        """获取意图对应的策略权重列表"""
        return self.strategy_templates.get(intent_type, []).copy()
    
    async def execute_parallel(
        self,
        query: str,
        strategies: List[StrategyWeight],
        cot_enabled: bool = False,
        cot_depth: Any = None,
        early_stop_callback=None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        并行执行多个检索策略
        
        Args:
            query: 查询
            strategies: 策略权重列表
            cot_enabled: 是否启用 CoT
            cot_depth: CoT 深度
            early_stop_callback: 早停回调函数
            **kwargs: 传递给各策略执行函数的参数
            
        Returns:
            融合后的结果
        """
        start_time = time.time()
        results = []
        
        # 按优先级排序
        sorted_strategies = sorted(strategies, key=lambda s: s.priority)
        
        # 创建任务
        tasks = []
        for strategy in sorted_strategies:
            if not strategy.enabled:
                continue
            
            task = self._execute_single_strategy(
                strategy=strategy.name,
                query=query,
                weight=strategy.weight,
                cot_enabled=cot_enabled,
                **kwargs
            )
            tasks.append(task)
        
        # 并行执行
        strategy_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(strategy_results):
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # 检查早停
            if early_stop_callback and callable(early_stop_callback):
                if early_stop_callback(results, elapsed_ms):
                    break
            
            if isinstance(result, Exception):
                # 记录错误但继续
                continue
            
            if isinstance(result, RetrievalResult):
                results.append(result)
        
        # 融合结果
        fused_results = self._fuse_results(results)
        
        # 多样性调整
        if self.config.diversity_enabled:
            fused_results = self._apply_diversity(fused_results)
        
        # 重排序
        final_results = self._rerank(fused_results, query)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return {
            'results': final_results,
            'strategy_results': results,
            'total_time_ms': total_time,
            'strategies_used': len(results),
        }
    
    async def _execute_single_strategy(
        self,
        strategy: str,
        query: str,
        weight: float,
        cot_enabled: bool = False,
        **kwargs
    ) -> RetrievalResult:
        """执行单个策略"""
        start_time = time.time()
        
        # TODO: 这里需要集成实际的检索器
        # 现在是示例实现
        items = []
        scores = []
        
        if strategy == 'vector_search':
            items, scores = await self._vector_search(query, **kwargs)
        elif strategy == 'graph_multi_hop':
            items, scores = await self._graph_search(query, **kwargs)
        elif strategy == 'hyde':
            items, scores = await self._hyde_search(query, **kwargs)
        elif strategy == 'cot_reasoning' and cot_enabled:
            items, scores = await self._cot_reasoning(query, **kwargs)
        else:
            # 其他策略...
            pass
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return RetrievalResult(
            strategy=strategy,
            items=items,
            scores=scores,
            processing_time_ms=processing_time
        )
    
    async def _vector_search(self, query: str, **kwargs) -> tuple[List, List]:
        """向量检索"""
        # TODO: 集成实际向量检索器
        return [], []
    
    async def _graph_search(self, query: str, **kwargs) -> tuple[List, List]:
        """图谱多跳检索"""
        # TODO: 集成实际图谱检索器
        return [], []
    
    async def _hyde_search(self, query: str, **kwargs) -> tuple[List, List]:
        """HyDE 假设答案检索"""
        # TODO: 集成实际 HyDE 检索器
        return [], []
    
    async def _cot_reasoning(self, query: str, **kwargs) -> tuple[List, List]:
        """CoT 推理"""
        # TODO: 集成实际 CoT 推理器
        return [], []
    
    def _fuse_results(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """
        融合多个策略的结果
        
        使用融合评分公式:
        fusion_score(d) = Σ w_s * norm(score_s,d) * (1 + novelty_d) * diversity_penalty
        """
        all_items = {}
        
        for result in results:
            for i, item in enumerate(result.items):
                item_id = self._get_item_id(item)
                
                if item_id not in all_items:
                    all_items[item_id] = {
                        'item': item,
                        'strategies': [],
                        'scores': [],
                        'novelty': 0.0,
                    }
                
                all_items[item_id]['strategies'].append(result.strategy)
                all_items[item_id]['scores'].append(result.scores[i])
        
        # 计算融合分数
        fused = []
        for item_data in all_items.values():
            # 归一化分数
            normalized_scores = self._normalize_scores(item_data['scores'])
            
            # 计算基础分数
            base_score = sum(
                w * s for w, s in zip([1.0] * len(normalized_scores), normalized_scores)
            ) / len(normalized_scores)
            
            # 新颖性加成
            novelty_boost = 1.0 + (item_data['novelty'] * self.config.novelty_boost)
            
            # 多样性惩罚
            diversity_penalty = self._calculate_diversity_penalty(item_data)
            
            # 最终分数
            final_score = base_score * novelty_boost * diversity_penalty
            
            fused.append({
                'item': item_data['item'],
                'score': final_score,
                'strategies': item_data['strategies'],
                'original_scores': item_data['scores'],
            })
        
        # 按分数排序
        fused.sort(key=lambda x: x['score'], reverse=True)
        
        return fused
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """归一化分数到 [0, 1] 范围"""
        if not scores:
            return []
        
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def _calculate_diversity_penalty(self, item_data: Dict) -> float:
        """计算多样性惩罚项"""
        penalty = 1.0
        
        # 避免单一来源垄断
        if self.config.source_diversity:
            num_strategies = len(item_data['strategies'])
            if num_strategies == 1:
                penalty *= 0.9  # 轻微惩罚
        
        return penalty
    
    def _apply_diversity(self, results: List[Dict]) -> List[Dict]:
        """应用多样性调整"""
        if not results:
            return results
        
        # 领域分布检查
        domain_counts = {}
        for result in results:
            domain = self._get_item_domain(result['item'])
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # 调整过高比例的领域
        total = len(results)
        for domain, count in domain_counts.items():
            ratio = count / total
            if ratio > self.config.max_same_domain_ratio:
                # 降低该领域项目的分数
                for result in results:
                    if self._get_item_domain(result['item']) == domain:
                        result['score'] *= 0.8
        
        # 重新排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def _rerank(self, results: List[Dict], query: str) -> List[Dict]:
        """重排序 (可以使用 BGE-Reranker 等)"""
        # TODO: 集成实际的重排序模型
        # 现在保持原顺序
        return results
    
    def _get_item_id(self, item: Any) -> str:
        """获取物品唯一标识"""
        # TODO: 根据实际数据结构实现
        return str(hash(str(item)))
    
    def _get_item_domain(self, item: Any) -> str:
        """获取物品所属领域"""
        # TODO: 根据实际数据结构实现
        return "default"
    
    def get_all_weights(self) -> Dict[str, List[Dict]]:
        """获取所有策略权重配置"""
        return {
            intent_type: [
                {'name': s.name, 'weight': s.weight}
                for s in strategies
            ]
            for intent_type, strategies in self.strategy_templates.items()
        }
