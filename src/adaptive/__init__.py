"""
Adaptive Learning Module - 自适应学习引擎

实现"越用越智能"的核心能力：
- 反馈闭环学习：收集用户显式/隐式反馈，形成学习闭环
- 用户偏好动态预测：基于交互历史预测用户偏好变化
- 检索策略自优化：为不同查询类型在线学习最优检索参数
- 集体智慧聚合：从多用户交互中提取共性智慧
- 自适应学习指标：量化"越用越智能"的效果
"""

# 数据模型
from .models import (
    FeedbackType,
    FeedbackSignal,
    UserFeedback,
    StrategyPerformance,
    UserLearningProfile,
    CommunityInsight,
    AdaptiveLearningMetrics,
    InteractionRecord,
)

# 配置
from .config import (
    AdaptiveLearningConfig,
    DEFAULT_CONFIG,
    AGGRESSIVE_CONFIG,
    CONSERVATIVE_CONFIG,
    MINIMAL_CONFIG,
)

# 核心组件
from .feedback import FeedbackCollector
from .strategy_optimizer import StrategyOptimizer
from .preference_predictor import PreferencePredictor
from .collective import CollectiveIntelligence
from .engine import AdaptiveLearningEngine, create_adaptive_engine


__all__ = [
    # 数据模型
    "FeedbackType",
    "FeedbackSignal",
    "UserFeedback",
    "StrategyPerformance",
    "UserLearningProfile",
    "CommunityInsight",
    "AdaptiveLearningMetrics",
    "InteractionRecord",
    
    # 配置
    "AdaptiveLearningConfig",
    "DEFAULT_CONFIG",
    "AGGRESSIVE_CONFIG",
    "CONSERVATIVE_CONFIG",
    "MINIMAL_CONFIG",
    
    # 核心组件
    "FeedbackCollector",
    "StrategyOptimizer",
    "PreferencePredictor",
    "CollectiveIntelligence",
    "AdaptiveLearningEngine",
    
    # 便捷函数
    "create_adaptive_engine",
]
