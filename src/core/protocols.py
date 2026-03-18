"""
NecoRAG 数据协议定义

定义系统中所有模块使用的统一数据类型和协议，确保模块间数据交换的一致性。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime
import uuid


# ============== 枚举类型 ==============

class DocumentType(Enum):
    """文档类型"""
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    UNKNOWN = "unknown"


class ChunkType(Enum):
    """分块类型"""
    FIXED = "fixed"           # 固定大小分块
    SEMANTIC = "semantic"     # 语义分块
    STRUCTURAL = "structural" # 结构化分块
    ELASTIC = "elastic"       # 弹性分块（智能调整块大小）
    SENTENCE = "sentence"     # 句子级分块


class MemoryLayer(Enum):
    """记忆层级"""
    L1_WORKING = "working"    # 工作记忆
    L2_SEMANTIC = "semantic"  # 语义记忆
    L3_EPISODIC = "episodic"  # 情景记忆


class RetrievalSource(Enum):
    """检索来源"""
    VECTOR = "vector"         # 向量检索
    GRAPH = "graph"           # 图检索
    HYDE = "hyde"             # HyDE 增强检索
    HYBRID = "hybrid"         # 混合检索


class ResponseTone(Enum):
    """响应语气"""
    PROFESSIONAL = "professional"  # 专业
    FRIENDLY = "friendly"          # 友好
    HUMOROUS = "humorous"          # 幽默


class DetailLevel(Enum):
    """详细程度"""
    BRIEF = 1       # 简洁
    STANDARD = 2    # 标准
    DETAILED = 3    # 详细
    COMPREHENSIVE = 4  # 全面


class IntentType(Enum):
    """
    意图类型
    
    Query intent types for semantic analysis.
    """
    FACTUAL = "factual"           # 事实查询
    COMPARATIVE = "comparative"   # 比较分析
    REASONING = "reasoning"       # 推理演绎
    EXPLANATION = "explanation"   # 概念解释
    SUMMARIZATION = "summarization"  # 摘要总结
    PROCEDURAL = "procedural"     # 操作指导
    EXPLORATORY = "exploratory"   # 探索发散


# ============== 文档相关 ==============

@dataclass
class Document:
    """统一文档类型"""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    doc_type: DocumentType = DocumentType.TEXT
    file_path: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.title and self.file_path:
            import os
            self.title = os.path.basename(self.file_path)


@dataclass
class Chunk:
    """统一分块类型"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    doc_id: Optional[str] = None
    chunk_type: ChunkType = ChunkType.FIXED
    position: int = 0  # 在文档中的位置
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 字符位置信息（来自 perception/models.py 合并）
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    
    # 上下文信息
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None


@dataclass
class ContextTag:
    """情境标签"""
    time_tag: Optional[str] = None        # 时间标签
    emotion_tag: Optional[str] = None     # 情感标签
    importance: float = 0.5               # 重要性 (0-1)
    topics: List[str] = field(default_factory=list)  # 主题标签
    entities: List[str] = field(default_factory=list)  # 实体标签


# ============== 向量相关 ==============

@dataclass
class Embedding:
    """统一向量类型"""
    embedding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str = ""
    dense_vector: List[float] = field(default_factory=list)
    sparse_vector: Dict[str, float] = field(default_factory=dict)  # token -> weight
    dimension: int = 0
    model_name: Optional[str] = None
    
    def __post_init__(self):
        if self.dense_vector and not self.dimension:
            self.dimension = len(self.dense_vector)


@dataclass
class EncodedChunk:
    """编码后的分块（包含向量和标签）"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    dense_vector: List[float] = field(default_factory=list)
    sparse_vector: Dict[str, float] = field(default_factory=dict)
    entities: List[tuple] = field(default_factory=list)  # (subject, relation, object)
    context_tags: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============== 记忆相关 ==============

@dataclass
class Memory:
    """统一记忆类型"""
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    layer: MemoryLayer = MemoryLayer.L2_SEMANTIC
    vector: List[float] = field(default_factory=list)
    weight: float = 1.0
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class Entity:
    """知识图谱实体"""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entity_type: str = "unknown"
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Relation:
    """知识图谱关系"""
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relation_type: str = ""
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ============== 查询相关 ==============

@dataclass
class Query:
    """统一查询类型"""
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    vector: Optional[List[float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    top_k: int = 10
    threshold: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalResult:
    """检索结果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_id: str = ""
    content: str = ""
    score: float = 0.0
    source: RetrievalSource = RetrievalSource.VECTOR
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_path: List[str] = field(default_factory=list)  # 检索路径


# ============== 响应相关 ==============

@dataclass
class GeneratedAnswer:
    """生成的答案"""
    answer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    iteration: int = 0
    is_refined: bool = False


@dataclass
class CritiqueResult:
    """批判结果"""
    critique_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class HallucinationReport:
    """幻觉检测报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    has_hallucination: bool = False
    factual_score: float = 1.0      # 事实一致性
    logical_score: float = 1.0      # 逻辑连贯性
    evidence_score: float = 1.0     # 证据支撑度
    issues: List[str] = field(default_factory=list)


@dataclass
class Response:
    """最终响应"""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str = ""
    content: str = ""
    confidence: float = 0.0
    sources: List[RetrievalResult] = field(default_factory=list)
    thinking_chain: List[Dict[str, Any]] = field(default_factory=list)
    tone: ResponseTone = ResponseTone.PROFESSIONAL
    detail_level: DetailLevel = DetailLevel.STANDARD
    citations: List[str] = field(default_factory=list)  # 来自 response/models.py 合并
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ============== 用户相关 ==============

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    profession: Optional[str] = None
    knowledge_level: str = "intermediate"  # beginner, intermediate, expert
    preferred_tone: ResponseTone = ResponseTone.PROFESSIONAL
    preferred_detail: DetailLevel = DetailLevel.STANDARD
    interests: List[str] = field(default_factory=list)
    preferred_domains: List[str] = field(default_factory=list)  # 来自 response/models.py 合并
    query_history: List[str] = field(default_factory=list)  # 来自 response/models.py 合并
    interaction_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)  # 来自 response/models.py 合并
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
