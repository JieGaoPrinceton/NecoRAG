"""
Adaptive Learning 反馈收集器

收集和分析用户的显式反馈和隐式反馈，形成学习闭环。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from .config import AdaptiveLearningConfig
from .models import UserFeedback, FeedbackType, FeedbackSignal


logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    反馈收集与分析器
    
    收集用户的显式反馈（评分、修正）和隐式反馈（查询改写、会话放弃），
    形成学习闭环。
    """
    
    def __init__(self, config: AdaptiveLearningConfig = None):
        """
        初始化反馈收集器
        
        Args:
            config: 自适应学习配置
        """
        self.config = config or AdaptiveLearningConfig.default()
        self._feedback_store: List[UserFeedback] = []  # 内存存储
        self._session_queries: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> queries
        self._user_feedback_index: Dict[str, List[str]] = defaultdict(list)  # user_id -> feedback_ids
    
    def record_feedback(self, feedback: UserFeedback) -> None:
        """
        记录用户反馈
        
        Args:
            feedback: 用户反馈对象
        """
        if not self.config.enable_feedback_collection:
            return
        
        # 存入反馈库
        self._feedback_store.append(feedback)
        
        # 更新索引
        user_id = feedback.metadata.get("user_id", "anonymous")
        self._user_feedback_index[user_id].append(feedback.feedback_id)
        
        # 保持 feedback_history_size 以内
        if len(self._feedback_store) > self.config.feedback_history_size:
            # 移除最旧的反馈
            removed = self._feedback_store.pop(0)
            # 更新索引
            old_user_id = removed.metadata.get("user_id", "anonymous")
            if removed.feedback_id in self._user_feedback_index[old_user_id]:
                self._user_feedback_index[old_user_id].remove(removed.feedback_id)
        
        logger.debug(f"Recorded feedback: {feedback.feedback_type.value} for query: {feedback.query[:50]}...")
    
    def record_session_query(
        self, 
        session_id: str, 
        query: str,
        response_id: str = "",
        timestamp: datetime = None
    ) -> None:
        """
        记录会话中的查询（用于检测隐式反馈）
        
        Args:
            session_id: 会话ID
            query: 查询内容
            response_id: 响应ID
            timestamp: 时间戳
        """
        if session_id not in self._session_queries:
            self._session_queries[session_id] = []
        
        self._session_queries[session_id].append({
            "query": query,
            "response_id": response_id,
            "timestamp": timestamp or datetime.now()
        })
        
        # 限制会话历史长度
        if len(self._session_queries[session_id]) > 50:
            self._session_queries[session_id] = self._session_queries[session_id][-50:]
    
    def detect_implicit_feedback(
        self, 
        session_id: str, 
        query: str, 
        previous_query: str = None
    ) -> Optional[UserFeedback]:
        """
        检测隐式反馈
        
        - 查询改写（reformulation）：用户换了一种问法 → 隐式负反馈
        - 连续追问（follow-up）：用户继续深入 → 隐式正反馈
        - 会话放弃（abandonment）：无后续交互 → 隐式负反馈
        
        Args:
            session_id: 会话ID
            query: 当前查询
            previous_query: 上一次查询（可选）
            
        Returns:
            Optional[UserFeedback]: 检测到的隐式反馈，无则返回 None
        """
        if not self.config.implicit_feedback_enabled:
            return None
        
        # 如果没有提供 previous_query，从会话历史获取
        if previous_query is None:
            session_history = self._session_queries.get(session_id, [])
            if len(session_history) >= 1:
                previous_query = session_history[-1]["query"]
            else:
                return None
        
        # 计算查询相似度（简单方式：字符重叠度）
        similarity = self._calculate_similarity(query, previous_query)
        
        # 检测追问关键词
        follow_up_keywords = ["为什么", "怎么", "详细", "更多", "进一步", "然后", "接下来", 
                             "还有", "具体", "例如", "比如", "解释"]
        has_follow_up = any(kw in query for kw in follow_up_keywords)
        
        # 判断反馈类型
        if similarity > 0.3 and similarity < 0.9:
            # 相似但不完全相同 → reformulation → negative
            feedback = UserFeedback(
                query=previous_query,
                feedback_type=FeedbackType.NEGATIVE,
                signal=FeedbackSignal.IMPLICIT,
                score=0.3,  # 隐式负反馈给较低分
                metadata={
                    "session_id": session_id,
                    "detection_type": "reformulation",
                    "similarity": similarity,
                    "new_query": query
                }
            )
            logger.debug(f"Detected implicit negative feedback (reformulation): {previous_query[:50]}...")
            return feedback
        
        elif has_follow_up and similarity < 0.5:
            # 有深入关键词且不太相似 → follow-up → positive
            feedback = UserFeedback(
                query=previous_query,
                feedback_type=FeedbackType.POSITIVE,
                signal=FeedbackSignal.IMPLICIT,
                score=0.7,  # 隐式正反馈给较高分
                metadata={
                    "session_id": session_id,
                    "detection_type": "follow_up",
                    "follow_up_query": query
                }
            )
            logger.debug(f"Detected implicit positive feedback (follow-up): {previous_query[:50]}...")
            return feedback
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（基于字符重叠）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            float: 相似度 0-1
        """
        if not text1 or not text2:
            return 0.0
        
        # 简单的字符集重叠计算
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def get_satisfaction_trend(
        self, 
        user_id: str = None, 
        window_days: int = 30
    ) -> float:
        """
        计算满意度趋势
        
        返回值 > 0 表示改善，< 0 表示下降
        
        Args:
            user_id: 用户ID（可选，不指定则计算全局）
            window_days: 时间窗口（天）
            
        Returns:
            float: 满意度趋势值
        """
        # 过滤时间范围内的反馈
        cutoff = datetime.now() - timedelta(days=window_days)
        
        feedbacks = [
            f for f in self._feedback_store
            if f.created_at >= cutoff
            and (user_id is None or f.metadata.get("user_id") == user_id)
        ]
        
        if len(feedbacks) < 4:  # 至少需要4条数据
            return 0.0
        
        # 按时间排序
        feedbacks.sort(key=lambda x: x.created_at)
        
        # 分为前半段和后半段
        mid = len(feedbacks) // 2
        early_feedbacks = feedbacks[:mid]
        late_feedbacks = feedbacks[mid:]
        
        # 计算平均满意度
        early_avg = sum(f.score for f in early_feedbacks) / len(early_feedbacks) if early_feedbacks else 0.5
        late_avg = sum(f.score for f in late_feedbacks) / len(late_feedbacks) if late_feedbacks else 0.5
        
        return late_avg - early_avg
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        获取反馈汇总统计
        
        Returns:
            Dict: 反馈统计汇总
        """
        if not self._feedback_store:
            return {
                "total_feedbacks": 0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "by_type": {},
                "by_signal": {},
                "avg_score": 0.0,
            }
        
        total = len(self._feedback_store)
        
        # 按类型统计
        by_type = defaultdict(int)
        by_signal = defaultdict(int)
        positive_count = 0
        negative_count = 0
        total_score = 0.0
        
        for f in self._feedback_store:
            by_type[f.feedback_type.value] += 1
            by_signal[f.signal.value] += 1
            total_score += f.score
            
            if f.feedback_type in [FeedbackType.POSITIVE, FeedbackType.SUPPLEMENT]:
                positive_count += 1
            elif f.feedback_type in [FeedbackType.NEGATIVE, FeedbackType.IRRELEVANT]:
                negative_count += 1
        
        return {
            "total_feedbacks": total,
            "positive_ratio": positive_count / total if total > 0 else 0.0,
            "negative_ratio": negative_count / total if total > 0 else 0.0,
            "by_type": dict(by_type),
            "by_signal": dict(by_signal),
            "avg_score": total_score / total if total > 0 else 0.0,
        }
    
    def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """
        分析反馈模式
        
        - 哪些查询类型满意度高/低
        - 哪些时段用户反馈最活跃
        - 常见的修正模式
        
        Returns:
            Dict: 反馈模式分析结果
        """
        if not self._feedback_store:
            return {
                "query_type_satisfaction": {},
                "hourly_activity": {},
                "correction_patterns": [],
                "low_satisfaction_queries": [],
            }
        
        # 按查询类型的满意度
        query_type_scores: Dict[str, List[float]] = defaultdict(list)
        
        # 按小时的活动
        hourly_activity: Dict[int, int] = defaultdict(int)
        
        # 修正内容收集
        corrections: List[str] = []
        
        # 低满意度查询
        low_satisfaction_queries: List[Dict[str, Any]] = []
        
        for f in self._feedback_store:
            # 按查询类型
            query_type = f.metadata.get("query_type", "unknown")
            query_type_scores[query_type].append(f.score)
            
            # 按小时
            hour = f.created_at.hour
            hourly_activity[hour] += 1
            
            # 修正
            if f.feedback_type == FeedbackType.CORRECTION and f.correction_text:
                corrections.append(f.correction_text)
            
            # 低满意度
            if f.score < 0.3:
                low_satisfaction_queries.append({
                    "query": f.query,
                    "score": f.score,
                    "feedback_type": f.feedback_type.value,
                })
        
        # 计算每种查询类型的平均满意度
        query_type_satisfaction = {
            qt: sum(scores) / len(scores) if scores else 0.0
            for qt, scores in query_type_scores.items()
        }
        
        return {
            "query_type_satisfaction": query_type_satisfaction,
            "hourly_activity": dict(hourly_activity),
            "correction_patterns": corrections[:20],  # 最近20条
            "low_satisfaction_queries": low_satisfaction_queries[:10],  # Top 10
        }
    
    def get_user_feedbacks(self, user_id: str, limit: int = 50) -> List[UserFeedback]:
        """
        获取指定用户的反馈列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            List[UserFeedback]: 用户反馈列表
        """
        feedback_ids = self._user_feedback_index.get(user_id, [])[-limit:]
        
        return [
            f for f in self._feedback_store
            if f.feedback_id in feedback_ids
        ]
    
    def clear_old_feedbacks(self, days: int = 90) -> int:
        """
        清理旧反馈数据
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的反馈数量
        """
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self._feedback_store)
        
        # 保留 cutoff 之后的反馈
        self._feedback_store = [
            f for f in self._feedback_store
            if f.created_at >= cutoff
        ]
        
        # 重建索引
        self._user_feedback_index.clear()
        for f in self._feedback_store:
            user_id = f.metadata.get("user_id", "anonymous")
            self._user_feedback_index[user_id].append(f.feedback_id)
        
        removed_count = original_count - len(self._feedback_store)
        logger.info(f"Cleared {removed_count} old feedbacks (older than {days} days)")
        
        return removed_count
