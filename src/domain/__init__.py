"""
NecoRAG Domain Module - 领域知识与权重管理

提供领域配置、时间权重、领域相关性评分和综合权重计算功能
"""

from .config import (
    KeywordLevel,
    DomainLevel,
    KeywordConfig,
    DomainConfig,
    DomainConfigManager,
    create_example_domain,
)

from .temporal_weight import (
    TemporalTier,
    TemporalWeightConfig,
    TemporalWeightCalculator,
    DecayPresets,
    create_temporal_calculator,
)

from .relevance import (
    RelevanceScore,
    DomainRelevanceCalculator,
    QueryRelevanceEnhancer,
)

from .weight_calculator import (
    DocumentMetadata,
    WeightedScore,
    CompositeWeightCalculator,
    WeightCalculatorFactory,
    create_weight_calculator,
    quick_rerank,
)


__all__ = [
    # 配置相关
    "KeywordLevel",
    "DomainLevel",
    "KeywordConfig",
    "DomainConfig",
    "DomainConfigManager",
    "create_example_domain",
    
    # 时间权重
    "TemporalTier",
    "TemporalWeightConfig",
    "TemporalWeightCalculator",
    "DecayPresets",
    "create_temporal_calculator",
    
    # 领域相关性
    "RelevanceScore",
    "DomainRelevanceCalculator",
    "QueryRelevanceEnhancer",
    
    # 综合权重
    "DocumentMetadata",
    "WeightedScore",
    "CompositeWeightCalculator",
    "WeightCalculatorFactory",
    "create_weight_calculator",
    "quick_rerank",
]
