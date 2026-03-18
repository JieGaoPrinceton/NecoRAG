"""
API数据模型定义
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class QueryIntent(str, Enum):
    """查询意图类型"""
    FACTUAL = "factual"           # 事实查询
    COMPARATIVE = "comparative"   # 比较分析
    REASONING = "reasoning"       # 推理演绎
    CONCEPT = "concept"           # 概念解释
    SUMMARY = "summary"           # 摘要总结
    PROCEDURAL = "procedural"     # 操作指导
    EXPLORATORY = "exploratory"   # 探索发散


class KnowledgeEntry(BaseModel):
    """知识条目模型"""
    id: str = Field(..., description="知识条目唯一标识")
    content: str = Field(..., description="知识内容")
    title: Optional[str] = Field(None, description="标题")
    tags: List[str] = Field(default=[], description="标签列表")
    domain: Optional[str] = Field(None, description="领域分类")
    language: str = Field(default="zh", description="语言(zh/en)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    metadata: Dict[str, Any] = Field(default={}, description="元数据")


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="查询内容")
    intent: Optional[QueryIntent] = Field(None, description="查询意图")
    domain: Optional[str] = Field(None, description="目标领域")
    language: str = Field(default="zh", description="查询语言")
    top_k: int = Field(default=5, description="返回结果数量")
    filters: Dict[str, Any] = Field(default={}, description="过滤条件")


class QueryResponse(BaseModel):
    """查询响应模型"""
    query_id: str = Field(..., description="查询ID")
    results: List[Dict[str, Any]] = Field(..., description="检索结果")
    execution_time: float = Field(..., description="执行时间(秒)")
    intent_detected: Optional[QueryIntent] = Field(None, description="检测到的意图")
    confidence: float = Field(..., description="置信度")
    suggestions: List[str] = Field(default=[], description="相关查询建议")


class InsertRequest(BaseModel):
    """插入请求模型"""
    entries: List[KnowledgeEntry] = Field(..., description="要插入的知识条目列表")
    batch_size: int = Field(default=100, description="批处理大小")


class UpdateRequest(BaseModel):
    """更新请求模型"""
    entry_id: str = Field(..., description="要更新的知识条目ID")
    updates: Dict[str, Any] = Field(..., description="更新内容")
    partial_update: bool = Field(default=True, description="是否部分更新")


class DeleteRequest(BaseModel):
    """删除请求模型"""
    entry_ids: List[str] = Field(..., description="要删除的知识条目ID列表")


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str = Field(..., description="消息类型(query/insert/update/delete)")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str = Field(..., description="服务状态(healthy/degraded/unhealthy)")
    components: Dict[str, str] = Field(..., description="各组件状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    uptime: float = Field(..., description="运行时间(秒)")