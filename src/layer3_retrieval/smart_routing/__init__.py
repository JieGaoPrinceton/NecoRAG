"""
智能路由与策略融合引擎 (Intelligent Routing & Strategy Fusion Engine)

整合语义意图分类、CoT思维链推理和用户画像三大核心能力，
构建智能化的检索 - 响应决策引擎。

版本：v1.9-Alpha
日期：2026-03-19
"""

from .engine import StrategyFusionEngine
from .intent_router import IntentRouter
from .user_adapter import UserProfileAdapter
from .cot_controller import CoTController
from .strategy_fusion import StrategyFusion, FusionConfig
from .early_stopping import EarlyStoppingManager, DegradationLevel
from .feedback_loop import FeedbackCollector, StrategyLearner

__all__ = [
    'StrategyFusionEngine',
    'IntentRouter',
    'UserProfileAdapter',
    'CoTController',
    'StrategyFusion',
    'FusionConfig',
    'EarlyStoppingManager',
    'DegradationLevel',
    'FeedbackCollector',
    'StrategyLearner',
]
