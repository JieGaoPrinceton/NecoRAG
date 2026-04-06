"""
早停与降级机制 (Early Stopping & Degradation)

平衡效果和延迟的智能决策
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass


class DegradationLevel(Enum):
    """降级等级"""
    NONE = 0  # 无降级
    LEVEL_1 = 1  # 轻微：减少并行策略数
    LEVEL_2 = 2  # 中等：跳过 CoT
    LEVEL_3 = 3  # 显著：仅向量检索
    LEVEL_4 = 4  # 较大：返回缓存或简化答案


@dataclass
class EarlyStopConfig:
    """早停配置"""
    enabled: bool = True
    confidence_threshold: float = 0.95
    diminishing_returns_threshold: float = 0.02
    latency_budget_ratio: float = 0.8
    satisfaction_threshold: float = 4.5
    max_allowed_latency_ms: int = 1000
    
    # 降级配置
    degradation_enabled: bool = True
    level1_latency_ms: int = 500
    level2_latency_ms: int = 700
    level3_latency_ms: int = 900
    level4_latency_ms: int = 1000


class EarlyStoppingManager:
    """
    早停管理器
    
    功能:
    1. 多维度早停判断
    2. 动态降级决策
    3. 性能监控
    """
    
    def __init__(self, config: Optional[EarlyStopConfig] = None):
        self.config = config or EarlyStopConfig()
        
        # 统计信息
        self._total_checks = 0
        self._early_stops_triggered = 0
        self._degradation_events = {level: 0 for level in DegradationLevel}
    
    def check_early_stop(
        self,
        results: List[Any],
        elapsed_ms: int,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检查是否应该早停
        
        Args:
            results: 当前结果列表
            elapsed_ms: 已耗时 (毫秒)
            config: 覆盖配置
            
        Returns:
            bool: 是否应该停止
        """
        if not self.config.enabled:
            return False
        
        self._total_checks += 1
        
        # 使用覆盖配置
        effective_config = self._merge_config(config)
        
        # 检查各个条件
        should_stop = False
        reason = None
        
        # 1. 置信度阈值达成
        if self._check_confidence_threshold(results, effective_config):
            should_stop = True
            reason = "high_confidence"
        
        # 2. 边际收益递减
        elif self._check_diminishing_returns(results, effective_config):
            should_stop = True
            reason = "diminishing_returns"
        
        # 3. 资源约束
        elif self._check_latency_budget(elapsed_ms, effective_config):
            should_stop = True
            reason = "latency_budget"
        
        # 4. 用户满意度预测
        elif self._check_satisfaction_prediction(results, effective_config):
            should_stop = True
            reason = "satisfaction_optimized"
        
        if should_stop:
            self._early_stops_triggered += 1
        
        return should_stop
    
    def _check_confidence_threshold(
        self,
        results: List[Any],
        config: EarlyStopConfig
    ) -> bool:
        """检查置信度阈值"""
        if not results:
            return False
        
        # 获取最佳结果的置信度
        best_confidence = self._get_best_confidence(results)
        
        return best_confidence >= config.confidence_threshold
    
    def _check_diminishing_returns(
        self,
        results: List[Any],
        config: EarlyStopConfig
    ) -> bool:
        """检查边际收益递减"""
        if len(results) < 2:
            return False
        
        # 计算最近两次迭代的改进
        recent_improvement = self._calculate_improvement(results[-2], results[-1])
        
        return recent_improvement < config.diminishing_returns_threshold
    
    def _check_latency_budget(
        self,
        elapsed_ms: int,
        config: EarlyStopConfig
    ) -> bool:
        """检查延迟预算"""
        return elapsed_ms >= config.max_allowed_latency_ms * config.latency_budget_ratio
    
    def _check_satisfaction_prediction(
        self,
        results: List[Any],
        config: EarlyStopConfig
    ) -> bool:
        """检查用户满意度预测"""
        predicted_satisfaction = self._predict_satisfaction(results)
        
        return predicted_satisfaction >= config.satisfaction_threshold
    
    def get_degradation_level(self, elapsed_ms: int) -> DegradationLevel:
        """
        获取当前应该应用的降级等级
        
        Args:
            elapsed_ms: 已耗时
            
        Returns:
            DegradationLevel: 降级等级
        """
        if not self.config.degradation_enabled:
            return DegradationLevel.NONE
        
        if elapsed_ms >= self.config.level4_latency_ms:
            level = DegradationLevel.LEVEL_4
        elif elapsed_ms >= self.config.level3_latency_ms:
            level = DegradationLevel.LEVEL_3
        elif elapsed_ms >= self.config.level2_latency_ms:
            level = DegradationLevel.LEVEL_2
        elif elapsed_ms >= self.config.level1_latency_ms:
            level = DegradationLevel.LEVEL_1
        else:
            level = DegradationLevel.NONE
        
        self._degradation_events[level] += 1
        
        return level
    
    def get_actions_for_level(self, level: DegradationLevel) -> List[str]:
        """获取指定降级等级应采取的动作"""
        actions = {
            DegradationLevel.NONE: [],
            DegradationLevel.LEVEL_1: [
                "减少并行策略数 (保留最优 2 个)",
                "降低多样性要求",
            ],
            DegradationLevel.LEVEL_2: [
                "跳过 CoT 推理",
                "使用直接回答模式",
            ],
            DegradationLevel.LEVEL_3: [
                "仅执行向量检索",
                "跳过图谱多跳",
                "简化重排序",
            ],
            DegradationLevel.LEVEL_4: [
                "返回缓存结果",
                "使用简化答案",
                "降级为基本检索",
            ],
        }
        return actions.get(level, [])
    
    def get_config(
        self,
        intent_confidence: float,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取动态调整后的配置
        
        Args:
            intent_confidence: 意图置信度
            user_profile: 用户画像
            
        Returns:
            Dict: 配置字典
        """
        config_dict = {
            'enabled': self.config.enabled,
            'confidence_threshold': self.config.confidence_threshold,
            'max_allowed_latency_ms': self.config.max_allowed_latency_ms,
        }
        
        # 高置信度时放宽阈值
        if intent_confidence >= 0.9:
            config_dict['confidence_threshold'] *= 0.95
        
        # 专家用户对延迟更敏感
        if user_profile:
            expertise = user_profile.get('expertise_level', 0.5)
            if expertise >= 0.8:
                config_dict['max_allowed_latency_ms'] = int(
                    config_dict['max_allowed_latency_ms'] * 0.8
                )
        
        return config_dict
    
    def _merge_config(self, override: Optional[Dict[str, Any]]) -> EarlyStopConfig:
        """合并配置"""
        if not override:
            return self.config
        
        return EarlyStopConfig(
            enabled=override.get('enabled', self.config.enabled),
            confidence_threshold=override.get('confidence_threshold', self.config.confidence_threshold),
            diminishing_returns_threshold=override.get('diminishing_returns_threshold', self.config.diminishing_returns_threshold),
            latency_budget_ratio=override.get('latency_budget_ratio', self.config.latency_budget_ratio),
            satisfaction_threshold=override.get('satisfaction_threshold', self.config.satisfaction_threshold),
            max_allowed_latency_ms=override.get('max_allowed_latency_ms', self.config.max_allowed_latency_ms),
        )
    
    def _get_best_confidence(self, results: List[Any]) -> float:
        """获取最佳结果的置信度"""
        # TODO: 根据实际数据结构提取置信度
        if not results:
            return 0.0
        
        # 假设结果包含 confidence 字段
        confidences = [
            r.get('confidence', 0.0) 
            for r in results 
            if isinstance(r, dict) and 'confidence' in r
        ]
        
        return max(confidences) if confidences else 0.5
    
    def _calculate_improvement(self, prev_result: Any, curr_result: Any) -> float:
        """计算改进幅度"""
        # TODO: 根据实际指标计算改进
        prev_score = prev_result.get('score', 0.0) if isinstance(prev_result, dict) else 0.0
        curr_score = curr_result.get('score', 0.0) if isinstance(curr_result, dict) else 0.0
        
        if prev_score == 0:
            return 0.0
        
        return (curr_score - prev_score) / prev_score
    
    def _predict_satisfaction(self, results: List[Any]) -> float:
        """预测用户满意度"""
        # TODO: 使用机器学习模型预测满意度
        # 现在基于结果质量简单估计
        
        if not results:
            return 0.0
        
        # 基于结果数量和质量的简单评分
        quantity_score = min(len(results) / 10, 1.0) * 0.5
        
        avg_quality = sum(
            r.get('score', 0.0) for r in results if isinstance(r, dict)
        ) / len(results) if results else 0.0
        quality_score = avg_quality * 0.5
        
        predicted = quantity_score + quality_score
        
        # 映射到 5 分制
        return predicted * 5.0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_checks': self._total_checks,
            'early_stops_triggered': self._early_stops_triggered,
            'early_stop_rate': (
                self._early_stops_triggered / self._total_checks 
                if self._total_checks > 0 else 0.0
            ),
            'degradation_events': {
                level.name: count 
                for level, count in self._degradation_events.items()
            },
        }
    
    def reset_stats(self):
        """重置统计"""
        self._total_checks = 0
        self._early_stops_triggered = 0
        self._degradation_events = {level: 0 for level in DegradationLevel}
