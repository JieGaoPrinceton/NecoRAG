"""
NecoRAG 意图路由器模块

根据意图分类结果确定最优检索策略
"""

from typing import List, Tuple, Dict, Optional, Any
import logging

from .models import IntentType, IntentResult, IntentRoutingStrategy
from .config import IntentConfig


logger = logging.getLogger(__name__)


class IntentRouter:
    """
    意图路由器
    
    Intent router that determines optimal retrieval strategy based on
    classified intent results.
    
    根据意图分类结果，路由到最优的检索策略，支持多意图融合。
    
    使用示例:
    ```python
    from src.intent import IntentRouter, IntentConfig, IntentResult, IntentType
    
    config = IntentConfig.default()
    router = IntentRouter(config)
    
    intent_result = IntentResult(
        primary_intent=IntentType.EXPLANATION,
        confidence=0.85
    )
    
    strategy = router.route(intent_result)
    print(strategy.retrieval_mode)  # "vector"
    print(strategy.enable_hyde)  # True
    ```
    """
    
    def __init__(self, config: IntentConfig = None):
        """
        初始化意图路由器
        
        Args:
            config: 意图分类配置，None 则使用默认配置
        """
        self.config = config or IntentConfig.default()
        logger.info("IntentRouter initialized")
    
    def route(self, intent_result: IntentResult) -> IntentRoutingStrategy:
        """
        根据意图结果获取路由策略
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            IntentRoutingStrategy: 路由策略
        """
        # 获取主要意图的策略
        primary_strategy = self.config.get_routing_strategy(intent_result.primary_intent)
        
        # 如果没有次要意图或置信度很高，直接返回主要策略
        if (not intent_result.secondary_intents or 
            intent_result.confidence >= 0.85 or
            not self.config.enable_multi_intent):
            return primary_strategy
        
        # 多意图策略融合
        all_intents = [(intent_result.primary_intent, intent_result.confidence)]
        all_intents.extend(intent_result.secondary_intents)
        
        return self._merge_strategies(all_intents)
    
    def _merge_strategies(
        self, 
        intents: List[Tuple[IntentType, float]]
    ) -> IntentRoutingStrategy:
        """
        融合多个意图的策略
        
        使用置信度加权的方式融合多个意图的路由策略。
        
        Args:
            intents: 意图及其置信度列表
            
        Returns:
            融合后的路由策略
        """
        if not intents:
            return IntentRoutingStrategy()
        
        if len(intents) == 1:
            return self.config.get_routing_strategy(intents[0][0])
        
        # 计算权重总和（用于归一化）
        total_confidence = sum(conf for _, conf in intents)
        
        # 收集所有策略
        strategies_with_weights = []
        for intent_type, confidence in intents:
            strategy = self.config.get_routing_strategy(intent_type)
            weight = confidence / total_confidence
            strategies_with_weights.append((strategy, weight))
        
        # 融合策略
        merged = strategies_with_weights[0][0]
        accumulated_weight = strategies_with_weights[0][1]
        
        for strategy, weight in strategies_with_weights[1:]:
            # 计算当前策略在累计中的比例
            relative_weight = accumulated_weight / (accumulated_weight + weight)
            merged = merged.merge_with(strategy, relative_weight)
            accumulated_weight += weight
        
        return merged
    
    def get_weight_factor(self, intent_result: IntentResult) -> float:
        """
        计算意图权重因子
        
        根据意图类型和置信度计算一个综合权重因子，
        用于调整检索结果的最终得分。
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            float: 权重因子 (通常在 0.8-1.5 之间)
        """
        # 获取基础权重
        base_weight = self.config.get_intent_weight(intent_result.primary_intent)
        
        # 根据置信度调整
        # 高置信度 -> 更大的权重影响
        # 低置信度 -> 权重趋近于 1.0
        confidence_factor = 0.5 + intent_result.confidence * 0.5
        
        # 计算最终权重
        weight_factor = 1.0 + (base_weight - 1.0) * confidence_factor
        
        # 如果有次要意图，进行加权平均
        if intent_result.secondary_intents:
            secondary_weights = []
            for intent_type, conf in intent_result.secondary_intents:
                sec_weight = self.config.get_intent_weight(intent_type)
                secondary_weights.append((sec_weight, conf))
            
            # 计算次要意图的贡献
            if secondary_weights:
                total_conf = sum(conf for _, conf in secondary_weights)
                secondary_contribution = sum(
                    w * (c / total_conf) for w, c in secondary_weights
                ) * 0.3  # 次要意图贡献 30%
                
                weight_factor = weight_factor * 0.7 + secondary_contribution
        
        # 限制在合理范围内
        return max(0.5, min(2.0, weight_factor))
    
    def get_retrieval_params(
        self, 
        intent_result: IntentResult
    ) -> Dict[str, any]:
        """
        获取完整的检索参数
        
        根据意图结果返回所有检索相关的参数，
        方便直接传递给检索模块。
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            Dict: 检索参数字典
        """
        strategy = self.route(intent_result)
        weight_factor = self.get_weight_factor(intent_result)
        
        return {
            "retrieval_mode": strategy.retrieval_mode,
            "top_k": strategy.top_k,
            "enable_graph_search": strategy.enable_graph_search,
            "enable_hyde": strategy.enable_hyde,
            "rerank_strategy": strategy.rerank_strategy,
            "weight_adjustments": strategy.weight_adjustments,
            "intent_weight_factor": weight_factor,
            "intent_type": intent_result.primary_intent.value,
            "intent_confidence": intent_result.confidence,
            "keywords": intent_result.keywords,
            "entities": intent_result.entities,
        }
    
    def should_use_graph(self, intent_result: IntentResult) -> bool:
        """
        判断是否应该使用图谱搜索
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            bool: 是否启用图谱搜索
        """
        strategy = self.route(intent_result)
        return strategy.enable_graph_search
    
    def should_use_hyde(self, intent_result: IntentResult) -> bool:
        """
        判断是否应该使用 HyDE 增强
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            bool: 是否启用 HyDE
        """
        strategy = self.route(intent_result)
        return strategy.enable_hyde
    
    def get_optimal_top_k(self, intent_result: IntentResult) -> int:
        """
        获取最优的 top_k 值
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            int: 推荐的检索数量
        """
        strategy = self.route(intent_result)
        return strategy.top_k
    
    def explain_routing(self, intent_result: IntentResult) -> str:
        """
        生成路由决策的解释
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            str: 路由决策说明
        """
        strategy = self.route(intent_result)
        weight_factor = self.get_weight_factor(intent_result)
        
        explanation_parts = [
            f"意图类型: {intent_result.primary_intent.value}",
            f"置信度: {intent_result.confidence:.2%}",
            f"检索模式: {strategy.retrieval_mode}",
            f"Top-K: {strategy.top_k}",
            f"图谱搜索: {'启用' if strategy.enable_graph_search else '禁用'}",
            f"HyDE 增强: {'启用' if strategy.enable_hyde else '禁用'}",
            f"重排序策略: {strategy.rerank_strategy}",
            f"权重因子: {weight_factor:.2f}",
        ]
        
        if intent_result.secondary_intents:
            secondary_str = ", ".join(
                f"{i.value}({c:.0%})" 
                for i, c in intent_result.secondary_intents
            )
            explanation_parts.append(f"次要意图: {secondary_str}")
        
        return " | ".join(explanation_parts)


class AdaptiveRouter(IntentRouter):
    """
    自适应意图路由器
    
    在基础路由器之上添加自适应调整功能，
    可以根据历史反馈动态调整路由策略。
    """
    
    def __init__(self, config: IntentConfig = None):
        super().__init__(config)
        
        # 策略效果统计
        self._strategy_stats: Dict[str, Dict[str, float]] = {}
        
        # 动态调整因子
        self._dynamic_adjustments: Dict[str, float] = {}
    
    def record_feedback(
        self, 
        intent_type: IntentType, 
        strategy: IntentRoutingStrategy,
        success_score: float
    ):
        """
        记录策略反馈
        
        Args:
            intent_type: 意图类型
            strategy: 使用的策略
            success_score: 成功度评分 (0-1)
        """
        key = f"{intent_type.value}_{strategy.retrieval_mode}"
        
        if key not in self._strategy_stats:
            self._strategy_stats[key] = {
                "total_score": 0.0,
                "count": 0
            }
        
        self._strategy_stats[key]["total_score"] += success_score
        self._strategy_stats[key]["count"] += 1
        
        # 更新动态调整因子
        avg_score = (
            self._strategy_stats[key]["total_score"] / 
            self._strategy_stats[key]["count"]
        )
        self._dynamic_adjustments[key] = avg_score
    
    def route(self, intent_result: IntentResult) -> IntentRoutingStrategy:
        """
        自适应路由
        
        在基础路由的基础上，根据历史反馈进行微调。
        """
        strategy = super().route(intent_result)
        
        # 应用动态调整
        key = f"{intent_result.primary_intent.value}_{strategy.retrieval_mode}"
        if key in self._dynamic_adjustments:
            adjustment = self._dynamic_adjustments[key]
            
            # 如果历史效果不好，增加 top_k
            if adjustment < 0.5:
                strategy.top_k = min(30, strategy.top_k + 5)
            
            # 如果历史效果很好，可以减少 top_k 以提高效率
            elif adjustment > 0.8:
                strategy.top_k = max(5, strategy.top_k - 2)
        
        return strategy
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "strategy_stats": self._strategy_stats,
            "dynamic_adjustments": self._dynamic_adjustments
        }
