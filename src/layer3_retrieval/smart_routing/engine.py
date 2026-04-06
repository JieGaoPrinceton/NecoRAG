"""
智能路由与策略融合引擎主类

负责整合所有子模块，提供统一的智能路由决策接口
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .intent_router import IntentRouter, IntentResult
from .user_adapter import UserProfileAdapter, UserStylePreference
from .cot_controller import CoTController, CoTDepth
from .strategy_fusion import StrategyFusion, FusionConfig, StrategyWeight
from .early_stopping import EarlyStoppingManager, DegradationLevel
from .feedback_loop import FeedbackCollector, StrategyLearner


@dataclass
class RoutingDecision:
    """路由决策结果"""
    intent: IntentResult
    user_profile: Optional[Dict[str, Any]]
    strategies: List[StrategyWeight]
    cot_enabled: bool
    cot_depth: CoTDepth
    early_stop_config: Dict[str, Any]
    degradation_level: DegradationLevel
    confidence: float
    processing_time_ms: int


class StrategyFusionEngine:
    """
    智能路由与策略融合引擎
    
    三层决策架构:
    1. 意图识别层：识别问题类型和复杂度
    2. 用户画像层：匹配用户专业度和偏好
    3. 策略融合层：动态选择最优策略组合
    """
    
    def __init__(
        self,
        intent_router: IntentRouter,
        user_profile_adapter: UserProfileAdapter,
        cot_controller: CoTController,
        strategy_fusion: StrategyFusion,
        early_stopping: EarlyStoppingManager,
        feedback_collector: FeedbackCollector,
        strategy_learner: StrategyLearner,
        config: Optional[Dict[str, Any]] = None
    ):
        self.intent_router = intent_router
        self.user_profile_adapter = user_profile_adapter
        self.cot_controller = cot_controller
        self.strategy_fusion = strategy_fusion
        self.early_stopping = early_stopping
        self.feedback_collector = feedback_collector
        self.strategy_learner = strategy_learner
        self.config = config or {}
        
        # 性能监控
        self._total_requests = 0
        self._avg_processing_time = 0.0
    
    async def route_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        对查询进行智能路由决策
        
        Args:
            query: 用户查询
            user_id: 用户 ID (可选)
            session_context: 会话上下文 (可选)
            
        Returns:
            RoutingDecision: 路由决策结果
        """
        start_time = datetime.now()
        self._total_requests += 1
        
        # Layer 1: 意图识别
        intent_result = await self.intent_router.analyze_intent(
            query,
            session_context=session_context
        )
        
        # Layer 2: 用户画像适配
        user_profile = None
        if user_id:
            user_profile = await self.user_profile_adapter.get_profile(user_id)
        
        # Layer 3: 策略融合决策
        strategies = self._select_strategies(intent_result, user_profile)
        
        # CoT决策
        cot_enabled, cot_depth = await self._decide_cot(
            query, intent_result, user_profile
        )
        
        # 早停配置
        early_stop_config = self.early_stopping.get_config(
            intent_confidence=intent_result.confidence,
            user_profile=user_profile
        )
        
        # 降级等级
        degradation_level = DegradationLevel.NONE
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self._update_avg_processing_time(processing_time)
        
        return RoutingDecision(
            intent=intent_result,
            user_profile=user_profile,
            strategies=strategies,
            cot_enabled=cot_enabled,
            cot_depth=cot_depth,
            early_stop_config=early_stop_config,
            degradation_level=degradation_level,
            confidence=intent_result.confidence,
            processing_time_ms=int(processing_time)
        )
    
    def _select_strategies(
        self,
        intent: IntentResult,
        user_profile: Optional[Dict[str, Any]]
    ) -> List[StrategyWeight]:
        """基于意图和用户画像选择策略"""
        # 获取基础策略模板
        base_strategies = self.strategy_fusion.get_template_for_intent(
            intent.intent_type
        )
        
        # 用户画像调节
        if user_profile:
            expertise = user_profile.get('expertise_level', 0.5)
            preference = user_profile.get('preference', {})
            
            # 专家用户：增加深度检索权重
            if expertise >= 0.8:
                for strategy in base_strategies:
                    if strategy.name == "vector_search":
                        strategy.weight *= 1.2
                    elif strategy.name == "basic_concept":
                        strategy.weight *= 0.5
            
            # 风格偏好调节
            detail_level = preference.get('detail_level', 'balanced')
            if detail_level == 'concise':
                for strategy in base_strategies:
                    if strategy.name in ['hyde', 'cot']:
                        strategy.weight *= 0.7
        
        # 归一化权重
        total_weight = sum(s.weight for s in base_strategies)
        if total_weight > 0:
            for strategy in base_strategies:
                strategy.weight /= total_weight
        
        return base_strategies
    
    async def _decide_cot(
        self,
        query: str,
        intent: IntentResult,
        user_profile: Optional[Dict[str, Any]]
    ) -> tuple[bool, CoTDepth]:
        """决策是否启用 CoT 以及深度等级"""
        # 基础触发判断
        should_trigger = self.cot_controller.should_trigger_cot(
            query=query,
            intent_type=intent.intent_type,
            complexity=intent.complexity,
            confidence=intent.confidence
        )
        
        if not should_trigger:
            return False, CoTDepth.L1_MINIMAL
        
        # 动态深度调节
        depth = await self.cot_controller.determine_depth(
            query=query,
            user_profile=user_profile,
            intent_result=intent
        )
        
        return True, depth
    
    def _update_avg_processing_time(self, current_time: float):
        """更新平均处理时间"""
        alpha = 0.1  # 平滑系数
        self._avg_processing_time = (
            alpha * current_time + 
            (1 - alpha) * self._avg_processing_time
        )
    
    async def execute_and_monitor(
        self,
        query: str,
        decision: RoutingDecision,
        retrieval_func,
        **kwargs
    ):
        """
        执行检索并监控性能
        
        Args:
            query: 查询
            decision: 路由决策
            retrieval_func: 检索函数
            **kwargs: 传递给检索函数的参数
            
        Returns:
            检索结果和性能指标
        """
        # 设置早停回调
        def should_stop(current_results, elapsed_ms):
            return self.early_stopping.check_early_stop(
                results=current_results,
                elapsed_ms=elapsed_ms,
                config=decision.early_stop_config
            )
        
        # 执行检索
        results = await self.strategy_fusion.execute_parallel(
            query=query,
            strategies=decision.strategies,
            cot_enabled=decision.cot_enabled,
            cot_depth=decision.cot_depth,
            early_stop_callback=should_stop,
            **kwargs
        )
        
        # 收集隐式反馈
        await self.feedback_collector.collect_implicit_feedback(
            query=query,
            results=results,
            user_id=decision.user_profile.get('user_id') if decision.user_profile else None
        )
        
        return results
    
    async def update_from_feedback(
        self,
        intent_type: str,
        strategy_id: str,
        reward: float,
        expected_reward: float = 0.5
    ):
        """从反馈中学习更新策略权重"""
        await self.strategy_learner.update_weights(
            intent_type=intent_type,
            strategy_id=strategy_id,
            reward=reward,
            expected_reward=expected_reward
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            'total_requests': self._total_requests,
            'avg_processing_time_ms': round(self._avg_processing_time, 2),
            'strategy_weights': self.strategy_fusion.get_all_weights(),
            'cot_trigger_rate': self.cot_controller.get_trigger_rate(),
        }
