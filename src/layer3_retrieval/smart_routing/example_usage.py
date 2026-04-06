"""
智能路由与策略融合引擎 - 使用示例

演示如何使用智能路由系统进行查询处理
"""

import asyncio
from typing import Dict, Any
from .engine import StrategyFusionEngine
from .intent_router import IntentRouter
from .user_adapter import UserProfileAdapter
from .cot_controller import CoTController
from .strategy_fusion import StrategyFusion, FusionConfig
from .early_stopping import EarlyStoppingManager, EarlyStopConfig
from .feedback_loop import FeedbackCollector, StrategyLearner


async def example_basic_usage():
    """基础使用示例"""
    
    # 1. 初始化各个组件
    intent_router = IntentRouter()
    user_profile_adapter = UserProfileAdapter()
    cot_controller = CoTController()
    strategy_fusion = StrategyFusion(FusionConfig())
    early_stopping = EarlyStoppingManager(EarlyStopConfig())
    feedback_collector = FeedbackCollector()
    strategy_learner = StrategyLearner(feedback_collector)
    
    # 2. 创建引擎
    engine = StrategyFusionEngine(
        intent_router=intent_router,
        user_profile_adapter=user_profile_adapter,
        cot_controller=cot_controller,
        strategy_fusion=strategy_fusion,
        early_stopping=early_stopping,
        feedback_collector=feedback_collector,
        strategy_learner=strategy_learner,
    )
    
    # 3. 路由决策
    query = "为什么微服务架构更适合大规模系统？"
    decision = await engine.route_query(
        query=query,
        user_id="user_123",
        session_context=None
    )
    
    print(f"意图类型：{decision.intent.intent_type}")
    print(f"置信度：{decision.confidence}")
    print(f"CoT 启用：{decision.cot_enabled}")
    print(f"CoT 深度：{decision.cot_depth}")
    print(f"策略数量：{len(decision.strategies)}")
    
    # 4. 执行检索 (需要集成实际检索器)
    # results = await engine.execute_and_monitor(...)
    
    return decision


async def example_user_adaptation():
    """用户画像适配示例"""
    
    from .user_adapter import DetailLevel, Tone, FormatPreference
    
    # 初始化
    user_adapter = UserProfileAdapter()
    
    # 模拟专家用户
    expert_profile = {
        'user_id': 'expert_user',
        'expertise_domains': {'architecture': 0.9},
        'preference': {
            'detail_level': DetailLevel.CONCISE,
            'tone': Tone.FORMAL,
            'format_preference': FormatPreference.BULLET_POINTS,
        }
    }
    
    # 模拟新手用户
    novice_profile = {
        'user_id': 'novice_user',
        'expertise_domains': {'architecture': 0.3},
        'preference': {
            'detail_level': DetailLevel.COMPREHENSIVE,
            'tone': Tone.CASUAL,
            'cot_detail': 'maximal',
        }
    }
    
    # 获取专业度分类
    expertise = expert_profile['expertise_domains']['architecture']
    category = user_adapter.get_expertise_category(expertise)
    print(f"专家用户类别：{category}")  # 输出：expert
    
    return expert_profile, novice_profile


async def example_feedback_learning():
    """反馈学习示例"""
    
    # 初始化
    feedback_collector = FeedbackCollector()
    strategy_learner = StrategyLearner(feedback_collector)
    
    # 收集显式反馈
    await feedback_collector.collect_explicit_feedback(
        user_id="user_123",
        query="微服务架构",
        results=[],
        rating=5,  # 非常满意
    )
    
    # 收集隐式反馈 (查询改写)
    await feedback_collector.collect_implicit_feedback(
        query="微服务",
        results=[],
        user_id="user_456",
        action_type='query_rewrite',
        new_query="微服务架构优缺点"
    )
    
    # 从反馈中学习
    await strategy_learner.update_weights(
        intent_type="reasoning_inference",
        strategy_id="graph_multi_hop",
        reward=0.8,
        expected_reward=0.5
    )
    
    # 获取最优策略
    optimal = strategy_learner.get_optimal_strategy(
        intent_type="reasoning_inference",
        candidate_strategies=["vector_search", "graph_multi_hop", "hyde"]
    )
    print(f"最优策略：{optimal}")  # 可能输出：graph_multi_hop
    
    return strategy_learner.get_stats()


async def example_early_stopping():
    """早停机制示例"""
    
    from .early_stopping import EarlyStopConfig, DegradationLevel
    
    # 配置早停
    config = EarlyStopConfig(
        enabled=True,
        confidence_threshold=0.95,
        max_allowed_latency_ms=1000,
    )
    
    early_stopping = EarlyStoppingManager(config)
    
    # 模拟检查
    mock_results = [{'confidence': 0.96, 'score': 0.9}]
    elapsed_ms = 600
    
    should_stop = early_stopping.check_early_stop(
        results=mock_results,
        elapsed_ms=elapsed_ms
    )
    print(f"是否早停：{should_stop}")  # True (置信度达标)
    
    # 获取降级等级
    level = early_stopping.get_degradation_level(elapsed_ms=750)
    print(f"降级等级：{level.name}")  # LEVEL_2
    
    # 获取降级动作
    actions = early_stopping.get_actions_for_level(level)
    print(f"应采取的动作：{actions}")
    
    return early_stopping.get_stats()


async def main():
    """运行所有示例"""
    
    print("=" * 60)
    print("智能路由与策略融合引擎 - 使用示例")
    print("=" * 60)
    
    print("\n【示例 1: 基础使用】")
    await example_basic_usage()
    
    print("\n【示例 2: 用户画像适配】")
    await example_user_adaptation()
    
    print("\n【示例 3: 反馈学习】")
    stats = await example_feedback_learning()
    print(f"学习统计：{stats}")
    
    print("\n【示例 4: 早停机制】")
    stats = await example_early_stopping()
    print(f"早停统计：{stats}")
    
    print("\n" + "=" * 60)
    print("示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
