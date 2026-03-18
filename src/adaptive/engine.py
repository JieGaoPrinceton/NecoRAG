"""
Adaptive Learning Engine - 自适应学习引擎统一入口

协调反馈收集、偏好预测、策略优化、集体智慧四个子系统，
实现"越用越智能"的核心体验。
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import AdaptiveLearningConfig
from .models import (
    UserFeedback, 
    FeedbackType, 
    FeedbackSignal,
    AdaptiveLearningMetrics,
    CommunityInsight,
)
from .feedback import FeedbackCollector
from .strategy_optimizer import StrategyOptimizer
from .preference_predictor import PreferencePredictor
from .collective import CollectiveIntelligence


logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """
    自适应学习引擎 - 统一协调器
    
    协调反馈收集、偏好预测、策略优化、集体智慧四个子系统，
    实现"越用越智能"的核心体验。
    
    使用示例：
    ```python
    engine = AdaptiveLearningEngine()
    
    # 查询完成后学习
    engine.on_query_completed(
        user_id="user123",
        query="什么是机器学习？",
        response_id="resp456",
        strategy_used="hybrid_search",
        query_type="factoid",
        satisfaction=0.8
    )
    
    # 处理用户反馈
    feedback = UserFeedback(
        query="什么是机器学习？",
        feedback_type=FeedbackType.POSITIVE,
        score=0.9
    )
    engine.on_user_feedback("user123", feedback)
    
    # 获取个性化配置
    config = engine.get_personalized_config("user123", "factoid")
    ```
    """
    
    def __init__(self, config: AdaptiveLearningConfig = None):
        """
        初始化自适应学习引擎
        
        Args:
            config: 自适应学习配置
        """
        self.config = config or AdaptiveLearningConfig.default()
        
        # 延迟初始化子系统
        self._feedback_collector: Optional[FeedbackCollector] = None
        self._strategy_optimizer: Optional[StrategyOptimizer] = None
        self._preference_predictor: Optional[PreferencePredictor] = None
        self._collective_intelligence: Optional[CollectiveIntelligence] = None
        
        # 初始化启用的子系统
        self._initialize_subsystems()
        
        logger.info("AdaptiveLearningEngine initialized")
    
    def _initialize_subsystems(self) -> None:
        """初始化子系统（根据配置延迟初始化）"""
        if self.config.enable_feedback_collection:
            self._feedback_collector = FeedbackCollector(self.config)
        
        if self.config.enable_strategy_optimization:
            self._strategy_optimizer = StrategyOptimizer(self.config)
        
        if self.config.enable_preference_learning:
            self._preference_predictor = PreferencePredictor(self.config)
        
        if self.config.enable_collective_learning:
            self._collective_intelligence = CollectiveIntelligence(
                self.config, 
                self._feedback_collector, 
                self._preference_predictor
            )
    
    @property
    def feedback_collector(self) -> Optional[FeedbackCollector]:
        """获取反馈收集器"""
        return self._feedback_collector
    
    @property
    def strategy_optimizer(self) -> Optional[StrategyOptimizer]:
        """获取策略优化器"""
        return self._strategy_optimizer
    
    @property
    def preference_predictor(self) -> Optional[PreferencePredictor]:
        """获取偏好预测器"""
        return self._preference_predictor
    
    @property
    def collective_intelligence(self) -> Optional[CollectiveIntelligence]:
        """获取集体智慧聚合器"""
        return self._collective_intelligence
    
    def on_query_completed(
        self, 
        user_id: str, 
        query: str, 
        response_id: str,
        strategy_used: str = "", 
        query_type: str = "",
        latency_ms: float = 0, 
        hit: bool = True,
        satisfaction: float = 0.5,
        topics: List[str] = None
    ) -> None:
        """
        查询完成后的学习回调
        
        在每次查询响应后调用，驱动所有子系统学习
        
        Args:
            user_id: 用户ID
            query: 查询内容
            response_id: 响应ID
            strategy_used: 使用的策略名称
            query_type: 查询类型
            latency_ms: 延迟（毫秒）
            hit: 是否命中
            satisfaction: 满意度 (0-1)
            topics: 涉及的主题
        """
        topics = topics or []
        
        # 1. 记录策略效果
        if self._strategy_optimizer and strategy_used:
            self._strategy_optimizer.record_strategy_result(
                strategy_name=strategy_used,
                query_type=query_type or "general",
                satisfaction=satisfaction,
                latency_ms=latency_ms,
                hit=hit
            )
        
        # 2. 更新用户画像
        if self._preference_predictor:
            # 估计查询复杂度
            query_complexity = self._preference_predictor.estimate_query_complexity(query)
            
            self._preference_predictor.on_interaction(
                user_id=user_id,
                query=query,
                response_quality=satisfaction,
                query_complexity=query_complexity,
                topics=topics
            )
        
        # 3. 记录会话查询（用于隐式反馈检测）
        if self._feedback_collector:
            session_id = f"{user_id}_session"  # 简化的会话ID
            self._feedback_collector.record_session_query(
                session_id=session_id,
                query=query,
                response_id=response_id
            )
        
        # 4. 记录集体智慧数据
        if self._collective_intelligence:
            self._collective_intelligence.record_query_data(
                query=query,
                topics=topics,
                satisfaction=satisfaction,
                hit=hit
            )
        
        logger.debug(
            f"Learned from query completion: user={user_id}, "
            f"strategy={strategy_used}, satisfaction={satisfaction:.2f}"
        )
    
    def on_user_feedback(self, user_id: str, feedback: UserFeedback) -> None:
        """
        处理用户反馈
        
        收到用户显式反馈后调用
        
        Args:
            user_id: 用户ID
            feedback: 用户反馈对象
        """
        # 添加用户ID到元数据
        feedback.metadata["user_id"] = user_id
        
        # 1. 收集反馈
        if self._feedback_collector:
            self._feedback_collector.record_feedback(feedback)
        
        # 2. 更新偏好
        if self._preference_predictor:
            self._preference_predictor.update_from_feedback(user_id, feedback)
        
        # 3. 更新策略（如果反馈包含策略信息）
        if self._strategy_optimizer and feedback.metadata.get("strategy_used"):
            strategy_used = feedback.metadata["strategy_used"]
            query_type = feedback.metadata.get("query_type", "general")
            
            # 将反馈转换为满意度分数
            satisfaction = feedback.score
            if feedback.feedback_type == FeedbackType.POSITIVE:
                satisfaction = max(satisfaction, 0.7)
            elif feedback.feedback_type == FeedbackType.NEGATIVE:
                satisfaction = min(satisfaction, 0.3)
            
            self._strategy_optimizer.record_strategy_result(
                strategy_name=strategy_used,
                query_type=query_type,
                satisfaction=satisfaction,
                hit=feedback.metadata.get("hit", True)
            )
        
        logger.debug(
            f"Processed user feedback: user={user_id}, "
            f"type={feedback.feedback_type.value}, score={feedback.score:.2f}"
        )
    
    def detect_implicit_feedback(
        self, 
        user_id: str, 
        query: str
    ) -> Optional[UserFeedback]:
        """
        检测并处理隐式反馈
        
        Args:
            user_id: 用户ID
            query: 当前查询
            
        Returns:
            Optional[UserFeedback]: 检测到的隐式反馈
        """
        if not self._feedback_collector:
            return None
        
        session_id = f"{user_id}_session"
        implicit_feedback = self._feedback_collector.detect_implicit_feedback(
            session_id=session_id,
            query=query
        )
        
        if implicit_feedback:
            # 记录隐式反馈
            implicit_feedback.metadata["user_id"] = user_id
            self._feedback_collector.record_feedback(implicit_feedback)
            
            logger.debug(f"Detected implicit feedback for user {user_id}")
        
        return implicit_feedback
    
    def get_personalized_config(
        self, 
        user_id: str, 
        query_type: str = ""
    ) -> Dict[str, Any]:
        """
        获取个性化配置
        
        综合用户偏好和最优策略，返回本次查询的推荐配置
        
        Args:
            user_id: 用户ID
            query_type: 查询类型
            
        Returns:
            Dict: 个性化配置
        """
        config = {
            "user_id": user_id,
            "query_type": query_type,
            "strategy": {},
            "preference": {},
            "is_personalized": False,
        }
        
        # 获取用户偏好
        if self._preference_predictor:
            preference = self._preference_predictor.predict_preference(user_id)
            config["preference"] = preference
            
            if not preference.get("is_default", True):
                config["is_personalized"] = True
        
        # 获取最优策略
        if self._strategy_optimizer and query_type:
            strategy = self._strategy_optimizer.get_recommended_params(query_type)
            config["strategy"] = strategy
        
        # 合并偏好到策略参数
        if config.get("preference") and config.get("strategy"):
            # 根据用户专业度调整回答深度
            expertise = config["preference"].get("expertise_level", 0.5)
            detail_level = config["preference"].get("detail_level", 0.5)
            
            # 调整 top_k：专业用户可能需要更多结果
            if expertise > 0.7:
                config["strategy"]["top_k"] = min(
                    config["strategy"].get("top_k", 10) + 5, 
                    20
                )
            
            # 调整置信度阈值：新手用户需要更确定的答案
            if expertise < 0.3:
                config["strategy"]["confidence_threshold"] = max(
                    config["strategy"].get("confidence_threshold", 0.7),
                    0.8
                )
        
        return config
    
    def get_learning_metrics(self) -> AdaptiveLearningMetrics:
        """
        获取自适应学习指标
        
        Returns:
            AdaptiveLearningMetrics: 学习指标对象
        """
        metrics = AdaptiveLearningMetrics()
        
        # 满意度趋势
        if self._feedback_collector:
            metrics.satisfaction_trend = self._feedback_collector.get_satisfaction_trend()
            summary = self._feedback_collector.get_feedback_summary()
            metrics.total_feedbacks = summary.get("total_feedbacks", 0)
            metrics.avg_satisfaction = summary.get("avg_score", 0.0)
        
        # 策略优化收益
        if self._strategy_optimizer:
            report = self._strategy_optimizer.get_optimization_report()
            metrics.strategy_optimization_gain = report.get("overall_improvement", 0.0)
        
        # 个性化准确度
        if self._preference_predictor:
            metrics.personalization_accuracy = self._preference_predictor.get_personalization_accuracy()
            profiles = self._preference_predictor.get_all_profiles_summary()
            metrics.active_users = profiles.get("active_users_7d", 0)
        
        # 知识覆盖增长
        if self._collective_intelligence:
            metrics.knowledge_coverage_growth = self._collective_intelligence.get_knowledge_coverage_growth()
        
        metrics.calculated_at = datetime.now()
        
        return metrics
    
    def periodic_optimization(self) -> Dict[str, Any]:
        """
        周期性优化（可由调度器定时调用）
        
        执行集体智慧聚合、洞察生成等批量操作
        
        Returns:
            Dict: 优化结果
        """
        result = {
            "insights_generated": 0,
            "insights": [],
            "feedback_cleaned": 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 生成集体智慧洞察
        if self._collective_intelligence:
            insights = self._collective_intelligence.generate_insights()
            result["insights_generated"] = len(insights)
            result["insights"] = [i.to_dict() for i in insights[:5]]
        
        # 清理旧反馈
        if self._feedback_collector:
            cleaned = self._feedback_collector.clear_old_feedbacks(
                days=self.config.interaction_retention_days
            )
            result["feedback_cleaned"] = cleaned
        
        logger.info(f"Periodic optimization completed: {result['insights_generated']} insights generated")
        
        return result
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表盘数据
        
        Returns:
            Dict: 仪表盘完整数据
        """
        data = {
            "metrics": None,
            "feedback_summary": {},
            "strategy_performance": [],
            "user_profiles_summary": {},
            "community_insights": {},
            "generated_at": datetime.now().isoformat(),
        }
        
        # 学习指标
        metrics = self.get_learning_metrics()
        data["metrics"] = metrics.to_dict()
        
        # 反馈汇总
        if self._feedback_collector:
            data["feedback_summary"] = self._feedback_collector.get_feedback_summary()
            data["feedback_patterns"] = self._feedback_collector.analyze_feedback_patterns()
        
        # 策略表现
        if self._strategy_optimizer:
            performances = self._strategy_optimizer.get_strategy_performance()
            data["strategy_performance"] = [p.to_dict() for p in performances]
            data["optimization_report"] = self._strategy_optimizer.get_optimization_report()
        
        # 用户画像汇总
        if self._preference_predictor:
            data["user_profiles_summary"] = self._preference_predictor.get_all_profiles_summary()
        
        # 集体智慧洞察
        if self._collective_intelligence:
            data["community_insights"] = self._collective_intelligence.get_insights_summary()
        
        return data
    
    def get_user_learning_status(self, user_id: str) -> Dict[str, Any]:
        """
        获取特定用户的学习状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户学习状态
        """
        status = {
            "user_id": user_id,
            "profile": None,
            "preference": {},
            "recent_feedbacks": [],
            "expertise_level": 0.5,
        }
        
        if self._preference_predictor:
            profile = self._preference_predictor.get_user_profile(user_id)
            if profile:
                status["profile"] = profile.to_dict()
            
            status["preference"] = self._preference_predictor.predict_preference(user_id)
            status["expertise_level"] = self._preference_predictor.estimate_expertise(user_id)
        
        if self._feedback_collector:
            feedbacks = self._feedback_collector.get_user_feedbacks(user_id, limit=10)
            status["recent_feedbacks"] = [f.to_dict() for f in feedbacks]
        
        return status
    
    def create_feedback(
        self,
        query: str,
        feedback_type: str = "positive",
        score: float = 0.5,
        comment: str = "",
        correction_text: str = "",
        **metadata
    ) -> UserFeedback:
        """
        创建反馈对象的便捷方法
        
        Args:
            query: 查询内容
            feedback_type: 反馈类型 (positive/negative/correction/supplement/irrelevant)
            score: 评分 (0-1)
            comment: 评论
            correction_text: 修正内容
            **metadata: 额外元数据
            
        Returns:
            UserFeedback: 反馈对象
        """
        type_map = {
            "positive": FeedbackType.POSITIVE,
            "negative": FeedbackType.NEGATIVE,
            "correction": FeedbackType.CORRECTION,
            "supplement": FeedbackType.SUPPLEMENT,
            "irrelevant": FeedbackType.IRRELEVANT,
        }
        
        return UserFeedback(
            query=query,
            feedback_type=type_map.get(feedback_type, FeedbackType.POSITIVE),
            signal=FeedbackSignal.EXPLICIT,
            score=score,
            comment=comment,
            correction_text=correction_text,
            metadata=metadata
        )


def create_adaptive_engine(
    mode: str = "default"
) -> AdaptiveLearningEngine:
    """
    创建自适应学习引擎的便捷函数
    
    Args:
        mode: 配置模式 (default/aggressive/conservative/minimal)
        
    Returns:
        AdaptiveLearningEngine: 引擎实例
    """
    config_map = {
        "default": AdaptiveLearningConfig.default,
        "aggressive": AdaptiveLearningConfig.aggressive,
        "conservative": AdaptiveLearningConfig.conservative,
        "minimal": AdaptiveLearningConfig.minimal,
    }
    
    config_factory = config_map.get(mode, AdaptiveLearningConfig.default)
    config = config_factory()
    
    return AdaptiveLearningEngine(config=config)
