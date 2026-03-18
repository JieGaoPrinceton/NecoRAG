"""
Adaptive Learning 策略优化器

通过在线学习，为不同查询类型找到最优的检索策略参数组合。
"""

import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import AdaptiveLearningConfig
from .models import StrategyPerformance


logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """
    检索策略自优化器
    
    通过在线学习，为不同查询类型找到最优的检索策略参数组合。
    采用 epsilon-greedy 策略平衡探索与利用。
    """
    
    # 默认策略参数模板
    DEFAULT_STRATEGY_PARAMS = {
        "vector_search": {
            "top_k": 10,
            "enable_hyde": False,
            "confidence_threshold": 0.7,
            "vector_weight": 1.0,
            "graph_weight": 0.0,
        },
        "hybrid_search": {
            "top_k": 10,
            "enable_hyde": False,
            "confidence_threshold": 0.75,
            "vector_weight": 0.7,
            "graph_weight": 0.3,
        },
        "graph_enhanced": {
            "top_k": 15,
            "enable_hyde": False,
            "confidence_threshold": 0.8,
            "vector_weight": 0.5,
            "graph_weight": 0.5,
        },
        "hyde_enhanced": {
            "top_k": 10,
            "enable_hyde": True,
            "confidence_threshold": 0.85,
            "vector_weight": 0.8,
            "graph_weight": 0.2,
        },
    }
    
    def __init__(self, config: AdaptiveLearningConfig = None):
        """
        初始化策略优化器
        
        Args:
            config: 自适应学习配置
        """
        self.config = config or AdaptiveLearningConfig.default()
        
        # 策略表现记录: "strategy:query_type" -> StrategyPerformance
        self._performance_table: Dict[str, StrategyPerformance] = {}
        
        # 策略权重: query_type -> {strategy -> weight}
        self._strategy_weights: Dict[str, Dict[str, float]] = {}
        
        # 初始化默认策略
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self) -> None:
        """初始化默认策略权重"""
        default_strategies = self.config.default_strategies
        
        # 为每种策略初始化相同的权重
        initial_weight = 1.0 / len(default_strategies) if default_strategies else 0.25
        
        self._default_weights = {
            strategy: initial_weight 
            for strategy in default_strategies
        }
    
    def _get_performance_key(self, strategy_name: str, query_type: str) -> str:
        """获取性能记录的键"""
        return f"{strategy_name}:{query_type}"
    
    def record_strategy_result(
        self, 
        strategy_name: str, 
        query_type: str,
        satisfaction: float, 
        latency_ms: float = 0,
        hit: bool = True
    ) -> None:
        """
        记录策略执行结果
        
        Args:
            strategy_name: 策略名称
            query_type: 查询类型
            satisfaction: 满意度 (0-1)
            latency_ms: 延迟（毫秒）
            hit: 是否命中
        """
        if not self.config.enable_strategy_optimization:
            return
        
        key = self._get_performance_key(strategy_name, query_type)
        
        # 获取或创建性能记录
        if key not in self._performance_table:
            self._performance_table[key] = StrategyPerformance(
                strategy_name=strategy_name,
                query_type=query_type,
            )
        
        perf = self._performance_table[key]
        
        # 更新统计
        perf.total_uses += 1
        
        if satisfaction >= 0.6:
            perf.positive_feedback += 1
        elif satisfaction < 0.4:
            perf.negative_feedback += 1
        
        # 更新平均满意度（指数移动平均）
        alpha = 0.1  # 平滑因子
        perf.avg_satisfaction = alpha * satisfaction + (1 - alpha) * perf.avg_satisfaction
        
        # 更新平均延迟
        if latency_ms > 0:
            perf.avg_latency_ms = alpha * latency_ms + (1 - alpha) * perf.avg_latency_ms
        
        # 更新命中率
        old_hit_rate = perf.hit_rate
        perf.hit_rate = (old_hit_rate * (perf.total_uses - 1) + (1.0 if hit else 0.0)) / perf.total_uses
        
        perf.last_updated = datetime.now()
        
        # 更新策略权重
        reward = satisfaction - 0.5  # 以0.5为基准
        self._update_weights(strategy_name, query_type, reward)
        
        logger.debug(
            f"Recorded strategy result: {strategy_name} for {query_type}, "
            f"satisfaction={satisfaction:.2f}, success_rate={perf.success_rate:.2f}"
        )
    
    def _update_weights(
        self, 
        strategy_name: str, 
        query_type: str, 
        reward: float
    ) -> None:
        """
        在线更新策略权重
        
        weight_new = weight_old + lr * (reward - expected_reward)
        
        Args:
            strategy_name: 策略名称
            query_type: 查询类型
            reward: 奖励值（满意度 - 0.5）
        """
        # 确保查询类型有权重记录
        if query_type not in self._strategy_weights:
            self._strategy_weights[query_type] = self._default_weights.copy()
        
        weights = self._strategy_weights[query_type]
        
        # 确保策略在权重表中
        if strategy_name not in weights:
            weights[strategy_name] = 1.0 / len(weights) if weights else 0.25
        
        # 计算期望奖励（当前权重 * 0 = 0，因为我们用满意度-0.5作为奖励）
        expected_reward = 0.0
        
        # 更新权重
        lr = self.config.strategy_learning_rate
        weights[strategy_name] += lr * (reward - expected_reward)
        
        # 确保权重非负
        weights[strategy_name] = max(0.01, weights[strategy_name])
        
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            for s in weights:
                weights[s] /= total
    
    def get_optimal_strategy(self, query_type: str) -> Dict[str, Any]:
        """
        获取指定查询类型的最优策略参数
        
        使用 epsilon-greedy：
        - 以 exploration_rate 概率随机探索
        - 否则选择当前最优
        
        Args:
            query_type: 查询类型
            
        Returns:
            Dict: 策略参数，包含 strategy_name 和 params
        """
        if not self.config.enable_strategy_optimization:
            # 返回默认策略
            return {
                "strategy_name": "hybrid_search",
                "params": self.DEFAULT_STRATEGY_PARAMS.get("hybrid_search", {})
            }
        
        # epsilon-greedy 探索
        if random.random() < self.config.exploration_rate:
            # 随机选择一个策略
            strategies = list(self.DEFAULT_STRATEGY_PARAMS.keys())
            selected = random.choice(strategies)
            logger.debug(f"Exploration: randomly selected {selected}")
        else:
            # 选择最优策略
            selected = self._select_best_strategy(query_type)
        
        return {
            "strategy_name": selected,
            "params": self.DEFAULT_STRATEGY_PARAMS.get(selected, {})
        }
    
    def _select_best_strategy(self, query_type: str) -> str:
        """
        选择最优策略
        
        Args:
            query_type: 查询类型
            
        Returns:
            str: 最优策略名称
        """
        # 获取该查询类型的权重
        weights = self._strategy_weights.get(query_type, self._default_weights)
        
        # 检查是否有足够的样本
        strategies_with_samples = []
        for strategy in weights.keys():
            key = self._get_performance_key(strategy, query_type)
            perf = self._performance_table.get(key)
            if perf and perf.total_uses >= self.config.min_samples_for_optimization:
                strategies_with_samples.append(strategy)
        
        if not strategies_with_samples:
            # 样本不足，返回默认策略
            return "hybrid_search"
        
        # 根据权重选择（加权随机或最大权重）
        # 这里使用最大权重
        best_strategy = max(strategies_with_samples, key=lambda s: weights.get(s, 0))
        
        return best_strategy
    
    def get_recommended_params(self, query_type: str) -> Dict[str, Any]:
        """
        获取推荐的检索参数
        
        Args:
            query_type: 查询类型
            
        Returns:
            Dict: 推荐的检索参数
        """
        optimal = self.get_optimal_strategy(query_type)
        params = optimal["params"].copy()
        
        # 根据查询类型微调参数
        if query_type in ["factoid", "simple"]:
            params["top_k"] = min(params.get("top_k", 10), 5)
            params["confidence_threshold"] = max(params.get("confidence_threshold", 0.7), 0.8)
        elif query_type in ["complex", "analytical"]:
            params["top_k"] = max(params.get("top_k", 10), 15)
            params["enable_hyde"] = True
        elif query_type in ["exploratory", "creative"]:
            params["top_k"] = max(params.get("top_k", 10), 20)
            params["confidence_threshold"] = min(params.get("confidence_threshold", 0.7), 0.6)
        
        return params
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """
        获取优化报告
        
        Returns:
            Dict: 每种查询类型的最优策略和提升
        """
        report = {
            "by_query_type": {},
            "overall_improvement": 0.0,
            "total_optimizations": len(self._performance_table),
        }
        
        # 按查询类型分组
        query_types = set()
        for key in self._performance_table.keys():
            _, qt = key.split(":", 1)
            query_types.add(qt)
        
        improvements = []
        
        for qt in query_types:
            # 找到该查询类型下表现最好的策略
            best_perf = None
            best_strategy = None
            
            for strategy in self.DEFAULT_STRATEGY_PARAMS.keys():
                key = self._get_performance_key(strategy, qt)
                perf = self._performance_table.get(key)
                
                if perf and perf.total_uses >= self.config.min_samples_for_optimization:
                    if best_perf is None or perf.avg_satisfaction > best_perf.avg_satisfaction:
                        best_perf = perf
                        best_strategy = strategy
            
            if best_perf:
                # 计算相对于基准(0.5)的提升
                improvement = best_perf.avg_satisfaction - 0.5
                improvements.append(improvement)
                
                report["by_query_type"][qt] = {
                    "best_strategy": best_strategy,
                    "avg_satisfaction": best_perf.avg_satisfaction,
                    "success_rate": best_perf.success_rate,
                    "total_uses": best_perf.total_uses,
                    "improvement": improvement,
                }
        
        if improvements:
            report["overall_improvement"] = sum(improvements) / len(improvements)
        
        return report
    
    def get_strategy_performance(self) -> List[StrategyPerformance]:
        """
        获取所有策略的表现数据
        
        Returns:
            List[StrategyPerformance]: 策略表现列表
        """
        return list(self._performance_table.values())
    
    def get_strategy_comparison(self, query_type: str) -> List[Dict[str, Any]]:
        """
        获取指定查询类型下各策略的对比
        
        Args:
            query_type: 查询类型
            
        Returns:
            List[Dict]: 策略对比数据
        """
        comparison = []
        
        for strategy in self.DEFAULT_STRATEGY_PARAMS.keys():
            key = self._get_performance_key(strategy, query_type)
            perf = self._performance_table.get(key)
            
            weights = self._strategy_weights.get(query_type, self._default_weights)
            weight = weights.get(strategy, 0.0)
            
            comparison.append({
                "strategy_name": strategy,
                "weight": weight,
                "total_uses": perf.total_uses if perf else 0,
                "avg_satisfaction": perf.avg_satisfaction if perf else 0.0,
                "success_rate": perf.success_rate if perf else 0.5,
                "avg_latency_ms": perf.avg_latency_ms if perf else 0.0,
                "hit_rate": perf.hit_rate if perf else 0.0,
            })
        
        # 按权重排序
        comparison.sort(key=lambda x: x["weight"], reverse=True)
        
        return comparison
    
    def reset_strategy_weights(self, query_type: str = None) -> None:
        """
        重置策略权重
        
        Args:
            query_type: 查询类型，None 则重置所有
        """
        if query_type:
            if query_type in self._strategy_weights:
                self._strategy_weights[query_type] = self._default_weights.copy()
        else:
            self._strategy_weights.clear()
        
        logger.info(f"Reset strategy weights for {query_type or 'all query types'}")
