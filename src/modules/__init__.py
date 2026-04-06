"""
NecoRAG - Modules (功能模块)
基于认知科学的神经符号 RAG 框架

功能模块层提供高级认知能力增强：
- 意图分析：理解用户查询的真实意图
- 知识演化：知识的持续更新与优化
- 自适应学习：根据用户反馈优化系统行为
"""

# 意图分析模块
from .classifier import IntentClassifier
from .router import IntentRouter
from .semantic_analyzer import SemanticAnalyzer
from .models import (
    IntentType,
    IntentResult,
    IntentRoutingStrategy,
    HierarchicalIntent,
    IntentExpansion,
)

# 知识演化模块
from .updater import KnowledgeUpdater
from .scheduler import UpdateScheduler
from .metrics import KnowledgeMetricsCalculator
from .visualizer import KnowledgeVisualizer
from .models import (
    KnowledgeCandidate,
    UpdateTask,
    ChangeLogEntry,
    KnowledgeMetrics,
    HealthReport,
    UpdateMode,
    UpdateStatus,
    KnowledgeSource,
    CandidateStatus,
)

# 自适应学习模块
from .engine import AdaptiveLearningEngine, create_adaptive_engine
from .feedback import FeedbackCollector
from .strategy_optimizer import StrategyOptimizer
from .preference_predictor import PreferencePredictor
from .collective import CollectiveIntelligence
from .config import (
    AdaptiveLearningConfig,
    DEFAULT_CONFIG,
    AGGRESSIVE_CONFIG,
    CONSERVATIVE_CONFIG,
    MINIMAL_CONFIG,
)
from .models import (
    UserFeedback,
    StrategyPerformance,
    UserLearningProfile,
    CommunityInsight,
    AdaptiveLearningMetrics,
    FeedbackType,
    FeedbackSignal,
    InteractionRecord,
)

__all__ = [
    # 意图分析
    "IntentClassifier",
    "IntentRouter",
    "SemanticAnalyzer",
    "IntentType",
    "IntentResult",
    "IntentRoutingStrategy",
    "HierarchicalIntent",
    "IntentExpansion",
    
    # 知识演化
    "KnowledgeUpdater",
    "UpdateScheduler",
    "KnowledgeMetricsCalculator",
    "KnowledgeVisualizer",
    "KnowledgeCandidate",
    "UpdateTask",
    "ChangeLogEntry",
    "KnowledgeMetrics",
    "HealthReport",
    "UpdateMode",
    "UpdateStatus",
    "KnowledgeSource",
    "CandidateStatus",
    
    # 自适应学习
    "AdaptiveLearningEngine",
    "create_adaptive_engine",
    "FeedbackCollector",
    "StrategyOptimizer",
    "PreferencePredictor",
    "CollectiveIntelligence",
    "AdaptiveLearningConfig",
    "DEFAULT_CONFIG",
    "AGGRESSIVE_CONFIG",
    "CONSERVATIVE_CONFIG",
    "MINIMAL_CONFIG",
    "UserFeedback",
    "StrategyPerformance",
    "UserLearningProfile",
    "CommunityInsight",
    "AdaptiveLearningMetrics",
    "FeedbackType",
    "FeedbackSignal",
    "InteractionRecord",
]
