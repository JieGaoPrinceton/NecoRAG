"""
Knowledge Evolution 数据模型

定义知识库更新与演化模块的所有数据类型和枚举。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
import uuid


class UpdateMode(Enum):
    """
    更新模式
    
    Update mode for knowledge base operations.
    """
    REAL_TIME = "real_time"          # 实时更新
    SCHEDULED_BATCH = "scheduled"    # 定时批量更新
    EVENT_DRIVEN = "event_driven"    # 事件触发更新


class UpdateStatus(Enum):
    """
    更新状态
    
    Status of an update task.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class KnowledgeSource(Enum):
    """
    知识来源
    
    Source type for knowledge candidates.
    """
    USER_QUERY = "user_query"              # 用户查询产生
    LLM_GENERATED = "llm_generated"        # LLM 生成的高质量回答
    USER_FEEDBACK = "user_feedback"        # 用户反馈
    EXTERNAL_IMPORT = "external_import"    # 外部导入
    GAP_FILLING = "gap_filling"            # 知识缺口补充


class CandidateStatus(Enum):
    """
    候选条目状态
    
    Status of a knowledge candidate.
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class KnowledgeCandidate:
    """
    知识候选条目（待审查）
    
    A knowledge candidate awaiting review before being added to the knowledge base.
    """
    candidate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    source: KnowledgeSource = KnowledgeSource.USER_QUERY
    relevance_score: float = 0.0     # 相关性评分
    novelty_score: float = 0.0       # 新颖性评分
    credibility_score: float = 0.0   # 可信度评分
    composite_score: float = 0.0     # 综合评分
    target_layer: str = "L1"         # 目标层级
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    status: CandidateStatus = CandidateStatus.PENDING
    
    @property
    def is_pending(self) -> bool:
        """是否待审核"""
        return self.status == CandidateStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "candidate_id": self.candidate_id,
            "content": self.content,
            "source": self.source.value,
            "relevance_score": self.relevance_score,
            "novelty_score": self.novelty_score,
            "credibility_score": self.credibility_score,
            "composite_score": self.composite_score,
            "target_layer": self.target_layer,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "status": self.status.value,
        }


@dataclass
class UpdateTask:
    """
    更新任务
    
    A batch update task for the knowledge base.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: UpdateMode = UpdateMode.SCHEDULED_BATCH
    target_layers: List[str] = field(default_factory=lambda: ["L1", "L2", "L3"])
    description: str = ""
    status: UpdateStatus = UpdateStatus.PENDING
    items_processed: int = 0
    items_total: int = 0
    items_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress(self) -> float:
        """获取任务进度（0-1）"""
        if self.items_total == 0:
            return 0.0
        return self.items_processed / self.items_total
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """获取任务持续时间（秒）"""
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "mode": self.mode.value,
            "target_layers": self.target_layers,
            "description": self.description,
            "status": self.status.value,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "items_failed": self.items_failed,
            "progress": self.progress,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class ChangeLogEntry:
    """
    变更日志条目
    
    A log entry recording a change to the knowledge base.
    """
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""              # "insert" / "update" / "delete" / "archive"
    layer: str = "L1"                # "L1" / "L2" / "L3"
    item_id: str = ""
    content_summary: str = ""
    previous_content: Optional[str] = None  # 用于回滚
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    rollback_executed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "log_id": self.log_id,
            "operation": self.operation,
            "layer": self.layer,
            "item_id": self.item_id,
            "content_summary": self.content_summary,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata,
            "rollback_executed": self.rollback_executed,
        }


@dataclass
class KnowledgeMetrics:
    """
    知识库量化指标
    
    Quantitative metrics for the knowledge base.
    """
    # 规模指标
    total_entries: int = 0
    l1_entries: int = 0
    l2_entries: int = 0
    l3_entities: int = 0
    l3_relations: int = 0
    vector_coverage: float = 0.0     # 向量覆盖率
    
    # 新鲜度指标
    avg_knowledge_age_days: float = 0.0
    recent_update_rate: float = 0.0   # 近7天更新率
    oldest_entry_days: float = 0.0
    newest_entry_days: float = 0.0
    
    # 质量指标
    retrieval_hit_rate: float = 0.0   # 检索命中率
    fragmentation_rate: float = 0.0   # 碎片率（孤立节点/总节点）
    avg_relevance_score: float = 0.0  # 平均相关性评分
    
    # 健康度指标
    decay_distribution: Dict[str, int] = field(default_factory=dict)  # 权重区间分布
    redundancy_rate: float = 0.0      # 冗余度
    health_score: float = 0.0         # 综合健康分 0-100
    
    # 更新指标
    total_updates_today: int = 0
    realtime_updates_today: int = 0
    batch_updates_today: int = 0
    pending_candidates: int = 0
    
    # 查询统计
    total_queries_today: int = 0
    queries_with_hits: int = 0
    queries_without_hits: int = 0
    
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            # 规模指标
            "total_entries": self.total_entries,
            "l1_entries": self.l1_entries,
            "l2_entries": self.l2_entries,
            "l3_entities": self.l3_entities,
            "l3_relations": self.l3_relations,
            "vector_coverage": self.vector_coverage,
            # 新鲜度指标
            "avg_knowledge_age_days": self.avg_knowledge_age_days,
            "recent_update_rate": self.recent_update_rate,
            "oldest_entry_days": self.oldest_entry_days,
            "newest_entry_days": self.newest_entry_days,
            # 质量指标
            "retrieval_hit_rate": self.retrieval_hit_rate,
            "fragmentation_rate": self.fragmentation_rate,
            "avg_relevance_score": self.avg_relevance_score,
            # 健康度指标
            "decay_distribution": self.decay_distribution,
            "redundancy_rate": self.redundancy_rate,
            "health_score": self.health_score,
            # 更新指标
            "total_updates_today": self.total_updates_today,
            "realtime_updates_today": self.realtime_updates_today,
            "batch_updates_today": self.batch_updates_today,
            "pending_candidates": self.pending_candidates,
            # 查询统计
            "total_queries_today": self.total_queries_today,
            "queries_with_hits": self.queries_with_hits,
            "queries_without_hits": self.queries_without_hits,
            # 时间戳
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class HealthReport:
    """
    知识库健康报告
    
    A comprehensive health report for the knowledge base.
    """
    health_score: float = 0.0        # 综合健康分 0-100
    level: str = "unknown"           # healthy / warning / critical
    metrics: Optional[KnowledgeMetrics] = None
    
    # 维度评分
    scale_score: float = 0.0         # 规模评分
    freshness_score: float = 0.0     # 新鲜度评分
    quality_score: float = 0.0       # 质量评分
    connectivity_score: float = 0.0  # 连通性评分
    
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "health_score": self.health_score,
            "level": self.level,
            "scale_score": self.scale_score,
            "freshness_score": self.freshness_score,
            "quality_score": self.quality_score,
            "connectivity_score": self.connectivity_score,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }


@dataclass
class QueryRecord:
    """
    查询记录
    
    A record of a query for statistics and knowledge accumulation.
    """
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    answer: str = ""
    evidence: List[str] = field(default_factory=list)
    hit: bool = False
    latency_ms: float = 0.0
    confidence: float = 0.0
    user_feedback: Optional[str] = None  # positive / negative / neutral
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "answer": self.answer[:200] + "..." if len(self.answer) > 200 else self.answer,
            "evidence_count": len(self.evidence),
            "hit": self.hit,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "user_feedback": self.user_feedback,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class GrowthTrend:
    """
    知识增长趋势数据点
    
    A data point for knowledge growth trend.
    """
    date: str = ""
    total_entries: int = 0
    new_entries: int = 0
    deleted_entries: int = 0
    net_growth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "date": self.date,
            "total_entries": self.total_entries,
            "new_entries": self.new_entries,
            "deleted_entries": self.deleted_entries,
            "net_growth": self.net_growth,
        }
