"""
Debug Data Models - 调试数据模型
定义调试面板所需的数据结构和模型
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class DebugSessionStatus(str, Enum):
    """调试会话状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EvidenceType(str, Enum):
    """证据类型"""
    VECTOR = "vector"
    GRAPH = "graph"
    HYDE = "hyde"
    WEB = "web"


@dataclass
class EvidenceInfo:
    """
    证据信息模型
    
    Attributes:
        evidence_id: 证据唯一标识
        source: 证据来源类型
        content: 证据内容
        relevance_score: 相关度评分 (0-1)
        retrieval_time: 检索时间
        metadata: 其他元数据
        source_url: 来源URL（如果是网络证据）
        document_id: 文档ID（如果是本地文档）
    """
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: EvidenceType = EvidenceType.VECTOR
    content: str = ""
    relevance_score: float = 0.0
    retrieval_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_url: Optional[str] = None
    document_id: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保评分在有效范围内
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))
    
    @property
    def is_high_quality(self) -> bool:
        """判断是否为高质量证据"""
        return self.relevance_score >= 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "evidence_id": self.evidence_id,
            "source": self.source.value,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "retrieval_time": self.retrieval_time.isoformat(),
            "metadata": self.metadata,
            "source_url": self.source_url,
            "document_id": self.document_id
        }


@dataclass
class RetrievalStep:
    """
    检索步骤模型
    
    Attributes:
        step_id: 步骤ID
        name: 步骤名称
        description: 步骤描述
        start_time: 开始时间
        end_time: 结束时间
        duration: 耗时（秒）
        status: 步骤状态
        input_data: 输入数据
        output_data: 输出数据
        metrics: 性能指标
    """
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    status: str = "pending"  # pending/running/completed/failed
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def complete(self, output_data: Optional[Dict[str, Any]] = None, 
                 metrics: Optional[Dict[str, float]] = None):
        """标记步骤完成"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "completed"
        if output_data:
            self.output_data = output_data
        if metrics:
            self.metrics = metrics
    
    def fail(self, error_message: str):
        """标记步骤失败"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "failed"
        if self.output_data is None:
            self.output_data = {}
        self.output_data["error"] = error_message
    
    @property
    def is_completed(self) -> bool:
        """检查步骤是否已完成"""
        return self.status in ["completed", "failed"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "metrics": self.metrics
        }


@dataclass
class ReasoningStep:
    """
    推理步骤模型
    
    Attributes:
        step_id: 步骤ID
        iteration: 迭代次数
        confidence: 置信度 (0-1)
        decision: 决策内容
        evidence_used: 使用的证据ID列表
        timestamp: 时间戳
        metadata: 其他元数据
    """
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    iteration: int = 1
    confidence: float = 0.0
    decision: str = ""
    evidence_used: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "step_id": self.step_id,
            "iteration": self.iteration,
            "confidence": self.confidence,
            "decision": self.decision,
            "evidence_used": self.evidence_used,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class DebugSession:
    """
    调试会话模型
    
    Attributes:
        session_id: 会话唯一标识
        query: 查询内容
        start_time: 开始时间
        end_time: 结束时间
        retrieval_steps: 检索步骤列表
        evidence_sources: 证据来源列表
        reasoning_chain: 推理链条
        performance_metrics: 性能指标
        status: 会话状态
        user_id: 用户ID
        session_metadata: 会话元数据
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    retrieval_steps: List[RetrievalStep] = field(default_factory=list)
    evidence_sources: List[EvidenceInfo] = field(default_factory=list)
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    status: DebugSessionStatus = DebugSessionStatus.RUNNING
    user_id: Optional[str] = None
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete_session(self, final_metrics: Optional[Dict[str, float]] = None):
        """完成会话"""
        self.end_time = datetime.now()
        self.status = DebugSessionStatus.COMPLETED
        if final_metrics:
            self.performance_metrics.update(final_metrics)
    
    def fail_session(self, error_message: str):
        """标记会话失败"""
        self.end_time = datetime.now()
        self.status = DebugSessionStatus.FAILED
        self.session_metadata["error"] = error_message
    
    def add_retrieval_step(self, step: RetrievalStep):
        """添加检索步骤"""
        self.retrieval_steps.append(step)
    
    def add_evidence(self, evidence: EvidenceInfo):
        """添加证据"""
        self.evidence_sources.append(evidence)
    
    def add_reasoning_step(self, step: ReasoningStep):
        """添加推理步骤"""
        self.reasoning_chain.append(step)
    
    @property
    def total_duration(self) -> float:
        """总耗时"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def avg_confidence(self) -> float:
        """平均置信度"""
        if not self.reasoning_chain:
            return 0.0
        return sum(step.confidence for step in self.reasoning_chain) / len(self.reasoning_chain)
    
    @property
    def high_quality_evidence_count(self) -> int:
        """高质量证据数量"""
        return len([e for e in self.evidence_sources if e.is_high_quality])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration": self.total_duration,
            "retrieval_steps": [step.to_dict() for step in self.retrieval_steps],
            "evidence_sources": [evidence.to_dict() for evidence in self.evidence_sources],
            "reasoning_chain": [step.to_dict() for step in self.reasoning_chain],
            "performance_metrics": self.performance_metrics,
            "status": self.status.value,
            "user_id": self.user_id,
            "session_metadata": self.session_metadata,
            "avg_confidence": self.avg_confidence,
            "high_quality_evidence_count": self.high_quality_evidence_count
        }


@dataclass
class DebugQueryRecord:
    """
    调试查询记录模型（用于历史记录）
    
    Attributes:
        record_id: 记录ID
        session_id: 关联的会话ID
        query: 查询内容
        timestamp: 查询时间
        duration: 总耗时
        status: 查询状态
        confidence: 最终置信度
        evidence_count: 证据数量
        metrics_summary: 指标摘要
    """
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    query: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    status: DebugSessionStatus = DebugSessionStatus.COMPLETED
    confidence: float = 0.0
    evidence_count: int = 0
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_debug_session(cls, session: DebugSession) -> 'DebugQueryRecord':
        """从DebugSession创建记录"""
        return cls(
            session_id=session.session_id,
            query=session.query,
            timestamp=session.start_time,
            duration=session.total_duration,
            status=session.status,
            confidence=session.avg_confidence,
            evidence_count=len(session.evidence_sources),
            metrics_summary={
                "steps_count": len(session.retrieval_steps),
                "reasoning_iterations": len(session.reasoning_chain),
                "high_quality_evidence": session.high_quality_evidence_count,
                "performance_metrics": session.performance_metrics
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "query": self.query,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "metrics_summary": self.metrics_summary
        }