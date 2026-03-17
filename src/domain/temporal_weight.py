"""
NecoRAG 时间权重计算模块

实现基于时间的知识权重衰减机制
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
from enum import Enum


class TemporalTier(Enum):
    """时间层级"""
    RECENT = "recent"           # 最近期: 0-30天
    NEAR = "near"               # 近期: 30-90天
    MEDIUM = "medium"           # 中期: 90-365天
    DISTANT = "distant"         # 远期: 1-3年
    HISTORICAL = "historical"   # 历史: >3年
    EVERGREEN = "evergreen"     # 常青: 不受时间衰减影响


@dataclass
class TemporalWeightConfig:
    """时间权重配置"""
    # 各层级的权重范围 (min, max)
    recent_weight: Tuple[float, float] = (1.0, 1.2)
    near_weight: Tuple[float, float] = (0.8, 1.0)
    medium_weight: Tuple[float, float] = (0.5, 0.8)
    distant_weight: Tuple[float, float] = (0.3, 0.5)
    historical_weight: Tuple[float, float] = (0.1, 0.3)
    
    # 时间分界点（天数）
    recent_days: int = 30
    near_days: int = 90
    medium_days: int = 365
    distant_days: int = 1095  # 3年
    
    # 衰减系数
    decay_rate: float = 0.001  # λ: 每天的衰减系数
    
    # 是否启用时间衰减
    enabled: bool = True


class TemporalWeightCalculator:
    """时间权重计算器"""
    
    def __init__(self, config: Optional[TemporalWeightConfig] = None):
        self.config = config or TemporalWeightConfig()
    
    def get_temporal_tier(self, document_time: datetime, 
                          current_time: Optional[datetime] = None) -> TemporalTier:
        """
        获取文档的时间层级
        
        Args:
            document_time: 文档时间戳
            current_time: 当前时间（默认为now）
        
        Returns:
            TemporalTier: 时间层级
        """
        if current_time is None:
            current_time = datetime.now()
        
        days_diff = (current_time - document_time).days
        
        if days_diff < 0:
            # 未来日期视为最近期
            return TemporalTier.RECENT
        elif days_diff <= self.config.recent_days:
            return TemporalTier.RECENT
        elif days_diff <= self.config.near_days:
            return TemporalTier.NEAR
        elif days_diff <= self.config.medium_days:
            return TemporalTier.MEDIUM
        elif days_diff <= self.config.distant_days:
            return TemporalTier.DISTANT
        else:
            return TemporalTier.HISTORICAL
    
    def calculate_exponential_decay(self, document_time: datetime,
                                    current_time: Optional[datetime] = None,
                                    decay_rate: Optional[float] = None) -> float:
        """
        计算指数衰减权重
        
        公式: weight = e^(-λ × days_diff)
        
        Args:
            document_time: 文档时间戳
            current_time: 当前时间
            decay_rate: 衰减系数（可选，默认使用配置值）
        
        Returns:
            float: 衰减后的权重 (0, 1]
        """
        if current_time is None:
            current_time = datetime.now()
        
        if decay_rate is None:
            decay_rate = self.config.decay_rate
        
        days_diff = max(0, (current_time - document_time).days)
        weight = math.exp(-decay_rate * days_diff)
        
        return weight
    
    def calculate_tiered_weight(self, document_time: datetime,
                                current_time: Optional[datetime] = None) -> float:
        """
        计算分层权重
        
        根据时间层级返回对应的权重值
        
        Args:
            document_time: 文档时间戳
            current_time: 当前时间
        
        Returns:
            float: 分层权重值
        """
        if current_time is None:
            current_time = datetime.now()
        
        tier = self.get_temporal_tier(document_time, current_time)
        days_diff = max(0, (current_time - document_time).days)
        
        # 根据层级获取权重范围
        weight_ranges = {
            TemporalTier.RECENT: (self.config.recent_weight, 0, self.config.recent_days),
            TemporalTier.NEAR: (self.config.near_weight, self.config.recent_days, self.config.near_days),
            TemporalTier.MEDIUM: (self.config.medium_weight, self.config.near_days, self.config.medium_days),
            TemporalTier.DISTANT: (self.config.distant_weight, self.config.medium_days, self.config.distant_days),
            TemporalTier.HISTORICAL: (self.config.historical_weight, self.config.distant_days, float('inf')),
            TemporalTier.EVERGREEN: ((1.0, 1.0), 0, 0),
        }
        
        weight_range, start_days, end_days = weight_ranges[tier]
        min_weight, max_weight = weight_range
        
        if tier == TemporalTier.EVERGREEN:
            return 1.0
        
        # 在层级内线性插值
        if end_days == float('inf'):
            return min_weight
        
        range_days = end_days - start_days
        if range_days <= 0:
            return max_weight
        
        position = (days_diff - start_days) / range_days
        weight = max_weight - position * (max_weight - min_weight)
        
        return max(min_weight, min(max_weight, weight))
    
    def calculate_weight(self, document_time: datetime,
                         current_time: Optional[datetime] = None,
                         is_evergreen: bool = False,
                         method: str = "tiered") -> float:
        """
        计算时间权重（主接口）
        
        Args:
            document_time: 文档时间戳
            current_time: 当前时间
            is_evergreen: 是否为常青内容（不受时间衰减影响）
            method: 计算方法 ("tiered" | "exponential" | "hybrid")
        
        Returns:
            float: 时间权重值
        """
        if not self.config.enabled:
            return 1.0
        
        if is_evergreen:
            return 1.0
        
        if current_time is None:
            current_time = datetime.now()
        
        if method == "exponential":
            return self.calculate_exponential_decay(document_time, current_time)
        elif method == "tiered":
            return self.calculate_tiered_weight(document_time, current_time)
        elif method == "hybrid":
            # 混合方法：分层基础上加指数衰减
            tiered = self.calculate_tiered_weight(document_time, current_time)
            exponential = self.calculate_exponential_decay(document_time, current_time)
            return (tiered + exponential) / 2
        else:
            return self.calculate_tiered_weight(document_time, current_time)
    
    def get_weight_description(self, weight: float) -> str:
        """获取权重的文字描述"""
        if weight >= 1.0:
            return "最高优先级"
        elif weight >= 0.8:
            return "高优先级"
        elif weight >= 0.5:
            return "中等优先级"
        elif weight >= 0.3:
            return "低优先级"
        else:
            return "历史参考"


def create_temporal_calculator(decay_rate: float = 0.001,
                                enabled: bool = True) -> TemporalWeightCalculator:
    """
    创建时间权重计算器的便捷函数
    
    Args:
        decay_rate: 衰减系数
        enabled: 是否启用时间衰减
    
    Returns:
        TemporalWeightCalculator: 计算器实例
    """
    config = TemporalWeightConfig(
        decay_rate=decay_rate,
        enabled=enabled
    )
    return TemporalWeightCalculator(config)


# 预设的衰减配置
class DecayPresets:
    """预设的衰减配置"""
    
    @staticmethod
    def fast_changing_domain() -> TemporalWeightConfig:
        """快速变化领域（如新闻、科技）"""
        return TemporalWeightConfig(
            decay_rate=0.01,  # 快速衰减
            recent_days=7,
            near_days=30,
            medium_days=90,
            distant_days=365,
        )
    
    @staticmethod
    def normal_domain() -> TemporalWeightConfig:
        """正常变化领域（如学术、技术文档）"""
        return TemporalWeightConfig(
            decay_rate=0.001,
            recent_days=30,
            near_days=90,
            medium_days=365,
            distant_days=1095,
        )
    
    @staticmethod
    def slow_changing_domain() -> TemporalWeightConfig:
        """缓慢变化领域（如历史、法律）"""
        return TemporalWeightConfig(
            decay_rate=0.0001,
            recent_days=90,
            near_days=365,
            medium_days=1095,
            distant_days=3650,
        )
    
    @staticmethod
    def evergreen_domain() -> TemporalWeightConfig:
        """常青领域（如基础科学）- 禁用时间衰减"""
        return TemporalWeightConfig(enabled=False)
