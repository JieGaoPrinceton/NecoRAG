"""
反馈闭环学习系统 (Feedback Loop Learning)

实时反馈收集与在线学习
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


@dataclass
class FeedbackSignal:
    """反馈信号"""
    signal_type: str  # explicit_rating, query_rewrite, session_abandon, etc.
    user_id: Optional[str]
    query: str
    results: List[Any]
    value: float  # 标准化后的值 [-1, 1]
    weight: float  # 信号权重
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def normalized_score(self) -> float:
        """获取标准化的分数"""
        return max(-1.0, min(1.0, self.value))


class FeedbackCollector:
    """
    反馈收集器
    
    功能:
    1. 显式反馈收集
    2. 隐式反馈收集
    3. 信号标准化
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 反馈信号权重配置
        self.signal_weights = {
            'explicit_rating': 1.0,
            'query_rewrite': 0.8,
            'session_abandon': 0.7,
            're_search': 0.6,
            'dwell_time': 0.5,
            'citation_action': 0.9,
        }
        
        # 存储最近的反馈
        self._recent_feedbacks = []
        self._max_recent_size = 1000
    
    async def collect_explicit_feedback(
        self,
        user_id: str,
        query: str,
        results: List[Any],
        rating: int,  # 1-5
        feedback_text: Optional[str] = None
    ) -> FeedbackSignal:
        """
        收集显式反馈
        
        Args:
            user_id: 用户 ID
            query: 查询
            results: 结果列表
            rating: 评分 (1-5)
            feedback_text: 文字反馈
            
        Returns:
            FeedbackSignal: 反馈信号
        """
        # 标准化到 [-1, 1]
        normalized_value = (rating - 3) / 2.0  # 3 分->0, 5 分->1, 1 分->-1
        
        signal = FeedbackSignal(
            signal_type='explicit_rating',
            user_id=user_id,
            query=query,
            results=results,
            value=normalized_value,
            weight=self.signal_weights['explicit_rating'],
            metadata={
                'raw_rating': rating,
                'feedback_text': feedback_text,
            }
        )
        
        await self._store_feedback(signal)
        
        return signal
    
    async def collect_implicit_feedback(
        self,
        query: str,
        results: List[Any],
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        **kwargs
    ):
        """
        收集隐式反馈
        
        Args:
            query: 查询
            results: 结果
            user_id: 用户 ID
            action_type: 行为类型
            **kwargs: 额外参数
        """
        signal = None
        
        if action_type == 'query_rewrite':
            new_query = kwargs.get('new_query', '')
            signal = await self._handle_query_rewrite(
                user_id, query, results, new_query
            )
        
        elif action_type == 'session_abandon':
            signal = await self._handle_session_abandon(
                user_id, query, results
            )
        
        elif action_type == 're_search':
            time_gap = kwargs.get('time_gap_seconds', 0)
            signal = await self._handle_re_search(
                user_id, query, results, time_gap
            )
        
        elif action_type == 'dwell_time':
            dwell_ms = kwargs.get('dwell_time_ms', 0)
            signal = await self._handle_dwell_time(
                user_id, query, results, dwell_ms
            )
        
        elif action_type == 'citation_action':
            citation_type = kwargs.get('citation_type', 'copy')
            signal = await self._handle_citation_action(
                user_id, query, results, citation_type
            )
        
        if signal:
            await self._store_feedback(signal)
    
    async def _handle_query_rewrite(
        self,
        user_id: Optional[str],
        query: str,
        results: List[Any],
        new_query: str
    ) -> FeedbackSignal:
        """处理查询改写"""
        # 计算改写幅度
        similarity = self._calculate_text_similarity(query, new_query)
        
        # 大幅度改写表示不满意
        dissatisfaction = 1.0 - similarity
        
        return FeedbackSignal(
            signal_type='query_rewrite',
            user_id=user_id,
            query=query,
            results=results,
            value=-dissatisfaction,  # 负向反馈
            weight=self.signal_weights['query_rewrite'],
            metadata={'new_query': new_query, 'similarity': similarity}
        )
    
    async def _handle_session_abandon(
        self,
        user_id: Optional[str],
        query: str,
        results: List[Any]
    ) -> FeedbackSignal:
        """处理会话放弃"""
        return FeedbackSignal(
            signal_type='session_abandon',
            user_id=user_id,
            query=query,
            results=results,
            value=-0.8,  # 强负向反馈
            weight=self.signal_weights['session_abandon']
        )
    
    async def _handle_re_search(
        self,
        user_id: Optional[str],
        query: str,
        results: List[Any],
        time_gap: int
    ) -> FeedbackSignal:
        """处理再次搜索"""
        # 短时间内重新搜索表示不满意
        if time_gap < 60:  # 1 分钟内
            value = -0.6
        elif time_gap < 300:  # 5 分钟内
            value = -0.3
        else:
            value = 0.0
        
        return FeedbackSignal(
            signal_type='re_search',
            user_id=user_id,
            query=query,
            results=results,
            value=value,
            weight=self.signal_weights['re_search'],
            metadata={'time_gap_seconds': time_gap}
        )
    
    async def _handle_dwell_time(
        self,
        user_id: Optional[str],
        query: str,
        results: List[Any],
        dwell_time_ms: int
    ) -> FeedbackSignal:
        """处理停留时长"""
        # 停留时间长通常表示感兴趣
        if dwell_time_ms > 30000:  # 30 秒以上
            value = 0.8
        elif dwell_time_ms > 10000:  # 10 秒以上
            value = 0.5
        elif dwell_time_ms > 3000:  # 3 秒以上
            value = 0.2
        else:
            value = 0.0
        
        return FeedbackSignal(
            signal_type='dwell_time',
            user_id=user_id,
            query=query,
            results=results,
            value=value,
            weight=self.signal_weights['dwell_time'],
            metadata={'dwell_time_ms': dwell_time_ms}
        )
    
    async def _handle_citation_action(
        self,
        user_id: Optional[str],
        query: str,
        results: List[Any],
        citation_type: str
    ) -> FeedbackSignal:
        """处理引用行为"""
        # 复制/分享表示高度认可
        value = 0.9 if citation_type in ['copy', 'share'] else 0.5
        
        return FeedbackSignal(
            signal_type='citation_action',
            user_id=user_id,
            query=query,
            results=results,
            value=value,
            weight=self.signal_weights['citation_action'],
            metadata={'citation_type': citation_type}
        )
    
    async def _store_feedback(self, signal: FeedbackSignal):
        """存储反馈"""
        self._recent_feedbacks.append(signal)
        
        # 限制大小
        if len(self._recent_feedbacks) > self._max_recent_size:
            self._recent_feedbacks = self._recent_feedbacks[-self._max_recent_size:]
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 (简单版本)"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_recent_feedbacks(
        self,
        limit: int = 100,
        signal_type: Optional[str] = None
    ) -> List[FeedbackSignal]:
        """获取最近的反馈"""
        feedbacks = self._recent_feedbacks[-limit:]
        
        if signal_type:
            feedbacks = [f for f in feedbacks if f.signal_type == signal_type]
        
        return feedbacks


class StrategyLearner:
    """
    策略学习器
    
    功能:
    1. 在线学习更新策略权重
    2. 用户画像实时更新
    3. 学习效果监控
    """
    
    def __init__(
        self,
        feedback_collector: FeedbackCollector,
        config: Optional[Dict[str, Any]] = None
    ):
        self.feedback_collector = feedback_collector
        self.config = config or {}
        
        # 学习率
        self.learning_rate = self.config.get('learning_rate', 0.1)
        
        # 策略权重存储
        self.strategy_weights = {}  # {intent_type: {strategy_id: weight}}
        
        # 统计信息
        self._update_count = 0
        self._total_reward = 0.0
    
    async def update_weights(
        self,
        intent_type: str,
        strategy_id: str,
        reward: float,
        expected_reward: float = 0.5
    ):
        """
        更新策略权重 (类似 MAB 算法)
        
        Args:
            intent_type: 意图类型
            strategy_id: 策略 ID
            reward: 实际奖励
            expected_reward: 期望奖励
        """
        # 初始化
        if intent_type not in self.strategy_weights:
            self.strategy_weights[intent_type] = {}
        
        current_weight = self.strategy_weights[intent_type].get(strategy_id, 1.0)
        
        # 增量更新
        prediction_error = reward - expected_reward
        new_weight = current_weight + self.learning_rate * prediction_error
        
        # 平滑限制
        new_weight = max(0.1, min(2.0, new_weight))
        
        self.strategy_weights[intent_type][strategy_id] = new_weight
        self._update_count += 1
        self._total_reward += reward
    
    async def update_user_profile_from_feedback(
        self,
        user_id: str,
        feedback_signal: FeedbackSignal,
        profile_updater
    ):
        """
        从反馈更新用户画像
        
        Args:
            user_id: 用户 ID
            feedback_signal: 反馈信号
            profile_updater: 画像更新器回调
        """
        if feedback_signal.signal_type == 'explicit_rating':
            is_positive = feedback_signal.value > 0
            
            # 更新领域专业度
            domain = feedback_signal.metadata.get('domain')
            if domain:
                delta = 0.02 if is_positive else -0.01
                await profile_updater.update_expertise(user_id, domain, delta, is_positive)
            
            # 更新风格偏好
            if feedback_signal.value > 0.5:
                # 正面反馈：强化当前偏好
                detail_level = feedback_signal.metadata.get('preferred_detail_level')
                if detail_level:
                    await profile_updater.update_preference(
                        user_id, 'detail_level', detail_level
                    )
    
    def get_optimal_strategy(
        self,
        intent_type: str,
        candidate_strategies: List[str]
    ) -> str:
        """
        选择最优策略
        
        Args:
            intent_type: 意图类型
            candidate_strategies: 候选策略列表
            
        Returns:
            最优策略 ID
        """
        weights = self.strategy_weights.get(intent_type, {})
        
        best_strategy = None
        best_weight = -1
        
        for strategy in candidate_strategies:
            weight = weights.get(strategy, 1.0)
            if weight > best_weight:
                best_weight = weight
                best_strategy = strategy
        
        return best_strategy or (candidate_strategies[0] if candidate_strategies else None)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取学习统计"""
        return {
            'total_updates': self._update_count,
            'total_reward': self._total_reward,
            'avg_reward': self._total_reward / self._update_count if self._update_count > 0 else 0.0,
            'intent_distribution': {
                intent_type: len(strategies)
                for intent_type, strategies in self.strategy_weights.items()
            },
        }
    
    def reset(self):
        """重置学习状态"""
        self.strategy_weights.clear()
        self._update_count = 0
        self._total_reward = 0.0
