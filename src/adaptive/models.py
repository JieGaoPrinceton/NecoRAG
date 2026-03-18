"""
Adaptive Learning 数据模型

定义自适应学习引擎的所有数据类型和枚举。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import uuid


class FeedbackType(Enum):
    """
    反馈类型
    
    Types of user feedback for learning.
    """
    POSITIVE = "positive"       # 点赞/满意
    NEGATIVE = "negative"       # 点踩/不满意
    CORRECTION = "correction"   # 用户修正
    SUPPLEMENT = "supplement"   # 用户补充
    IRRELEVANT = "irrelevant"   # 标记无关


class FeedbackSignal(Enum):
    """
    反馈信号来源
    
    Source of feedback signal.
    """
    EXPLICIT = "explicit"       # 显式（用户主动操作）
    IMPLICIT = "implicit"       # 隐式（行为推断）
    DELAYED = "delayed"         # 延迟（后续查询关联分析）


@dataclass
class UserFeedback:
    """
    用户反馈
    
    Represents a single piece of user feedback for learning.
    """
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    response_id: str = ""
    feedback_type: FeedbackType = FeedbackType.POSITIVE
    signal: FeedbackSignal = FeedbackSignal.EXPLICIT
    score: float = 0.0          # 0-1 评分
    comment: str = ""           # 用户评论
    correction_text: str = ""   # 修正内容
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "feedback_id": self.feedback_id,
            "query": self.query,
            "response_id": self.response_id,
            "feedback_type": self.feedback_type.value,
            "signal": self.signal.value,
            "score": self.score,
            "comment": self.comment,
            "correction_text": self.correction_text,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserFeedback":
        """从字典创建"""
        data = data.copy()
        if "feedback_type" in data and isinstance(data["feedback_type"], str):
            data["feedback_type"] = FeedbackType(data["feedback_type"])
        if "signal" in data and isinstance(data["signal"], str):
            data["signal"] = FeedbackSignal(data["signal"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class StrategyPerformance:
    """
    策略表现记录
    
    Records the performance of a retrieval strategy.
    """
    strategy_name: str = ""
    query_type: str = ""        # 意图类型
    total_uses: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    avg_satisfaction: float = 0.0
    avg_latency_ms: float = 0.0
    hit_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_uses == 0:
            return 0.5  # 无数据时默认
        return self.positive_feedback / self.total_uses
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_name": self.strategy_name,
            "query_type": self.query_type,
            "total_uses": self.total_uses,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
            "avg_satisfaction": self.avg_satisfaction,
            "avg_latency_ms": self.avg_latency_ms,
            "hit_rate": self.hit_rate,
            "success_rate": self.success_rate,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class UserLearningProfile:
    """
    用户学习画像（比 response/profile_manager 更深度）
    
    A deep learning profile for personalized adaptive behavior.
    """
    user_id: str = ""
    expertise_scores: Dict[str, float] = field(default_factory=dict)  # 领域 -> 专业度 0-1
    preferred_detail_level: float = 0.5  # 0=简洁 1=详尽
    preferred_tone: str = "professional"
    query_complexity_trend: List[float] = field(default_factory=list)  # 最近N次查询的复杂度
    satisfaction_history: List[float] = field(default_factory=list)     # 最近N次满意度
    active_hours: Dict[int, int] = field(default_factory=dict)         # 小时 -> 查询次数
    topic_frequency: Dict[str, int] = field(default_factory=dict)      # 主题 -> 频率
    total_interactions: int = 0
    last_interaction: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "expertise_scores": self.expertise_scores,
            "preferred_detail_level": self.preferred_detail_level,
            "preferred_tone": self.preferred_tone,
            "query_complexity_trend": self.query_complexity_trend[-20:],  # 最近20条
            "satisfaction_history": self.satisfaction_history[-20:],
            "active_hours": self.active_hours,
            "topic_frequency": dict(sorted(
                self.topic_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),  # Top 10
            "total_interactions": self.total_interactions,
            "last_interaction": self.last_interaction.isoformat(),
        }


@dataclass
class CommunityInsight:
    """
    集体智慧洞察
    
    Insights derived from collective user interactions.
    """
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: str = ""      # gap/best_practice/trend/learning_path
    title: str = ""
    description: str = ""
    affected_users: int = 0
    confidence: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "insight_id": self.insight_id,
            "insight_type": self.insight_type,
            "title": self.title,
            "description": self.description,
            "affected_users": self.affected_users,
            "confidence": self.confidence,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }


@dataclass  
class AdaptiveLearningMetrics:
    """
    自适应学习指标
    
    Metrics to quantify the "getting smarter" effect.
    """
    satisfaction_trend: float = 0.0      # 满意度趋势（正=改善）
    strategy_optimization_gain: float = 0.0  # 策略优化收益
    personalization_accuracy: float = 0.0    # 个性化准确度
    knowledge_coverage_growth: float = 0.0   # 知识覆盖增长率
    active_users: int = 0
    total_feedbacks: int = 0
    avg_satisfaction: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "satisfaction_trend": self.satisfaction_trend,
            "strategy_optimization_gain": self.strategy_optimization_gain,
            "personalization_accuracy": self.personalization_accuracy,
            "knowledge_coverage_growth": self.knowledge_coverage_growth,
            "active_users": self.active_users,
            "total_feedbacks": self.total_feedbacks,
            "avg_satisfaction": self.avg_satisfaction,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class InteractionRecord:
    """
    交互记录
    
    Records a single user interaction for learning.
    """
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    query: str = ""
    response_id: str = ""
    query_type: str = ""
    strategy_used: str = ""
    latency_ms: float = 0.0
    hit: bool = False
    satisfaction: float = 0.5
    topics: List[str] = field(default_factory=list)
    complexity: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "response_id": self.response_id,
            "query_type": self.query_type,
            "strategy_used": self.strategy_used,
            "latency_ms": self.latency_ms,
            "hit": self.hit,
            "satisfaction": self.satisfaction,
            "topics": self.topics,
            "complexity": self.complexity,
            "timestamp": self.timestamp.isoformat(),
        }
