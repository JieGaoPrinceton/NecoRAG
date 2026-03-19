"""
智能路由与策略融合引擎 - 单元测试
"""

import pytest
import asyncio
from datetime import datetime

from src.retrieval.smart_routing.intent_router import IntentRouter, IntentType, IntentResult
from src.retrieval.smart_routing.user_adapter import (
    UserProfileAdapter, UserProfile, UserStylePreference, DetailLevel, Tone
)
from src.retrieval.smart_routing.cot_controller import CoTController, CoTDepth
from src.retrieval.smart_routing.strategy_fusion import StrategyFusion, FusionConfig
from src.retrieval.smart_routing.early_stopping import EarlyStoppingManager, EarlyStopConfig, DegradationLevel
from src.retrieval.smart_routing.feedback_loop import FeedbackCollector, StrategyLearner


class TestIntentRouter:
    """意图路由器测试"""
    
    @pytest.mark.asyncio
    async def test_factual_query(self):
        """测试事实查询识别"""
        router = IntentRouter()
        
        query = "Python 是什么？"
        result = await router.analyze_intent(query)
        
        assert result.intent_type == IntentType.FACTUAL_QUERY
        assert result.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_comparative_analysis(self):
        """测试比较分析识别"""
        router = IntentRouter()
        
        query = "Redis 和 Memcached 有什么区别？"
        result = await router.analyze_intent(query)
        
        assert result.intent_type == IntentType.COMPARATIVE_ANALYSIS
        assert result.complexity > 0.3
    
    @pytest.mark.asyncio
    async def test_reasoning_inference(self):
        """测试推理演绎识别"""
        router = IntentRouter()
        
        query = "为什么微服务架构更适合大规模系统？"
        result = await router.analyze_intent(query)
        
        assert result.intent_type == IntentType.REASONING_INFERENCE
    
    def test_strategy_template(self):
        """测试策略模板获取"""
        router = IntentRouter()
        
        template = router.get_strategy_template(IntentType.FACTUAL_QUERY)
        
        assert len(template) > 0
        assert any(s.name == 'vector_search' for s in template)
    
    def test_cot_trigger_probability(self):
        """测试 CoT 触发概率"""
        router = IntentRouter()
        
        prob = router.get_cot_trigger_probability(IntentType.REASONING_INFERENCE)
        assert prob == 0.9
        
        prob = router.get_cot_trigger_probability(IntentType.FACTUAL_QUERY)
        assert prob == 0.1


class TestUserProfileAdapter:
    """用户画像适配器测试"""
    
    @pytest.mark.asyncio
    async def test_get_profile(self):
        """测试获取用户画像"""
        adapter = UserProfileAdapter()
        
        profile = await adapter.get_profile("test_user")
        
        assert profile is not None
        assert profile.user_id == "test_user"
        assert profile.get_expertise_level() == 0.5  # 默认中等
    
    @pytest.mark.asyncio
    async def test_update_expertise(self):
        """测试更新专业度"""
        adapter = UserProfileAdapter()
        
        await adapter.update_expertise("test_user", "architecture", 0.1, is_positive=True)
        profile = await adapter.get_profile("test_user")
        
        expertise = profile.get_expertise_level("architecture")
        assert expertise > 0.5
    
    def test_expertise_category(self):
        """测试专业度分类"""
        adapter = UserProfileAdapter()
        
        assert adapter.get_expertise_category(0.9) == "expert"
        assert adapter.get_expertise_category(0.6) == "intermediate"
        assert adapter.get_expertise_category(0.2) == "novice"
    
    def test_response_style_adaptation(self):
        """测试响应风格适配"""
        adapter = UserProfileAdapter()
        
        content = "这是一个技术概念的解释。它包含很多细节。"
        
        # 专家用户
        expert_profile = UserProfile(
            user_id="expert",
            expertise_domains={"tech": 0.9},
            preference=UserStylePreference(detail_level=DetailLevel.CONCISE)
        )
        adapted = adapter.adapt_response_style(content, expert_profile, "tech")
        assert adapted is not None


class TestCoTController:
    """CoT 控制器测试"""
    
    def test_should_trigger_cot_reasoning(self):
        """测试推理类问题的 CoT 触发"""
        controller = CoTController()
        
        should_trigger = controller.should_trigger_cot(
            query="为什么微服务更适合大规模系统？",
            intent_type="reasoning_inference",
            complexity=0.8,
            confidence=0.7
        )
        
        assert should_trigger is True
    
    def test_should_not_trigger_cot_factual(self):
        """测试事实类问题不触发 CoT"""
        controller = CoTController()
        
        should_trigger = controller.should_trigger_cot(
            query="Python 是什么？",
            intent_type="factual_query",
            complexity=0.2,
            confidence=0.95
        )
        
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_determine_depth_for_expert(self):
        """测试为专家用户确定深度"""
        controller = CoTController()
        
        user_profile = {
            'expertise_domains': {'tech': 0.9},
            'preference': {'cot_detail': 'minimal'}
        }
        
        from unittest.mock import Mock
        intent_result = Mock()
        intent_result.complexity = 0.7
        intent_result.domain = 'tech'
        
        depth = await controller.determine_depth(
            query="技术问题",
            user_profile=user_profile,
            intent_result=intent_result
        )
        
        assert depth in [CoTDepth.L1_MINIMAL, CoTDepth.L2_STANDARD]


class TestEarlyStopping:
    """早停机制测试"""
    
    def test_confidence_threshold_stop(self):
        """测试置信度阈值早停"""
        config = EarlyStopConfig(confidence_threshold=0.95)
        manager = EarlyStoppingManager(config)
        
        mock_results = [{'confidence': 0.96}]
        
        should_stop = manager.check_early_stop(
            results=mock_results,
            elapsed_ms=500
        )
        
        assert should_stop is True
    
    def test_latency_budget_stop(self):
        """测试延迟预算早停"""
        config = EarlyStopConfig(max_allowed_latency_ms=1000)
        manager = EarlyStoppingManager(config)
        
        should_stop = manager.check_early_stop(
            results=[],
            elapsed_ms=850  # 超过 80% 预算
        )
        
        assert should_stop is True
    
    def test_degradation_level(self):
        """测试降级等级"""
        config = EarlyStopConfig(
            level1_latency_ms=500,
            level2_latency_ms=700,
            level3_latency_ms=900,
        )
        manager = EarlyStoppingManager(config)
        
        assert manager.get_degradation_level(400) == DegradationLevel.NONE
        assert manager.get_degradation_level(600) == DegradationLevel.LEVEL_1
        assert manager.get_degradation_level(800) == DegradationLevel.LEVEL_2
        assert manager.get_degradation_level(950) == DegradationLevel.LEVEL_3


class TestFeedbackLoop:
    """反馈闭环测试"""
    
    @pytest.mark.asyncio
    async def test_collect_explicit_feedback(self):
        """测试收集显式反馈"""
        collector = FeedbackCollector()
        
        signal = await collector.collect_explicit_feedback(
            user_id="user_123",
            query="测试查询",
            results=[],
            rating=5
        )
        
        assert signal.signal_type == 'explicit_rating'
        assert signal.value == 1.0  # 5 分标准化为 1.0
    
    @pytest.mark.asyncio
    async def test_collect_query_rewrite(self):
        """测试收集查询改写反馈"""
        collector = FeedbackCollector()
        
        await collector.collect_implicit_feedback(
            query="原查询",
            results=[],
            user_id="user_456",
            action_type='query_rewrite',
            new_query="新查询"
        )
        
        feedbacks = collector.get_recent_feedbacks(signal_type='query_rewrite')
        assert len(feedbacks) > 0
    
    @pytest.mark.asyncio
    async def test_strategy_learning(self):
        """测试策略学习"""
        collector = FeedbackCollector()
        learner = StrategyLearner(collector)
        
        await learner.update_weights(
            intent_type="reasoning_inference",
            strategy_id="graph_multi_hop",
            reward=0.8,
            expected_reward=0.5
        )
        
        optimal = learner.get_optimal_strategy(
            intent_type="reasoning_inference",
            candidate_strategies=["vector_search", "graph_multi_hop"]
        )
        
        assert optimal == "graph_multi_hop"


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_routing_pipeline(self):
        """测试完整路由流程"""
        from src.retrieval.smart_routing.engine import StrategyFusionEngine
        
        # 初始化所有组件
        intent_router = IntentRouter()
        user_adapter = UserProfileAdapter()
        cot_controller = CoTController()
        strategy_fusion = StrategyFusion(FusionConfig())
        early_stopping = EarlyStoppingManager(EarlyStopConfig())
        feedback_collector = FeedbackCollector()
        strategy_learner = StrategyLearner(feedback_collector)
        
        # 创建引擎
        engine = StrategyFusionEngine(
            intent_router=intent_router,
            user_profile_adapter=user_adapter,
            cot_controller=cot_controller,
            strategy_fusion=strategy_fusion,
            early_stopping=early_stopping,
            feedback_collector=feedback_collector,
            strategy_learner=strategy_learner,
        )
        
        # 测试查询
        query = "为什么微服务架构更适合大规模系统？"
        decision = await engine.route_query(
            query=query,
            user_id="test_user"
        )
        
        # 验证决策结果
        assert decision is not None
        assert decision.intent.intent_type == IntentType.REASONING_INFERENCE
        assert len(decision.strategies) > 0
        assert isinstance(decision.cot_depth, CoTDepth)
        
        # 验证统计信息
        stats = engine.get_stats()
        assert 'total_requests' in stats
        assert 'avg_processing_time_ms' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
