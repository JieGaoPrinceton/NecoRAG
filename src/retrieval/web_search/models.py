"""
Web Search Data Models - 互联网搜索数据模型
定义搜索结果和确认请求的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ConfirmationStatus(str, Enum):
    """确认状态枚举"""
    PENDING = "pending"      # 等待确认
    CONFIRMED = "confirmed"  # 已确认
    REJECTED = "rejected"    # 已拒绝
    EXPIRED = "expired"      # 已超时
    PARTIAL = "partial"      # 部分确认


@dataclass
class WebSearchResult:
    """
    互联网搜索结果
    
    Attributes:
        title: 页面标题
        url: 页面URL
        snippet: 摘要内容
        content: 完整内容（可选）
        credibility_score: 可信度评分 (0-1)
        relevance_score: 相关性评分 (0-1)
        timestamp: 搜索时间戳
        source: 搜索引擎来源
        domain: 域名
        language: 语言
        metadata: 其他元数据
    """
    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    credibility_score: float = 0.0
    relevance_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    domain: str = ""
    language: str = "zh"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.domain and self.url:
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            self.domain = parsed.netloc
            
        # 确保评分在有效范围内
        self.credibility_score = max(0.0, min(1.0, self.credibility_score))
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))
    
    @property
    def composite_score(self) -> float:
        """综合评分 = 可信度 * 相关性"""
        return self.credibility_score * self.relevance_score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "content": self.content,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score,
            "composite_score": self.composite_score,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "domain": self.domain,
            "language": self.language,
            "metadata": self.metadata
        }


@dataclass
class ConfirmationRequest:
    """
    人工确认请求
    
    Attributes:
        request_id: 请求唯一标识
        query: 原始查询
        search_results: 搜索结果列表
        timeout: 超时时间（秒）
        status: 当前状态
        created_at: 创建时间
        expires_at: 过期时间
        confirmed_indices: 已确认的结果索引列表
        rejected_indices: 已拒绝的结果索引列表
        user_feedback: 用户反馈信息
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    search_results: List[WebSearchResult] = field(default_factory=list)
    timeout: int = 300  # 5分钟默认超时
    status: ConfirmationStatus = ConfirmationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(init=False)
    confirmed_indices: List[int] = field(default_factory=list)
    rejected_indices: List[int] = field(default_factory=list)
    user_feedback: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        self.expires_at = datetime.fromtimestamp(
            self.created_at.timestamp() + self.timeout
        )
    
    @property
    def is_expired(self) -> bool:
        """检查是否已过期"""
        return datetime.now() > self.expires_at
    
    @property
    def pending_count(self) -> int:
        """待确认结果数量"""
        total = len(self.search_results)
        confirmed = len(self.confirmed_indices)
        rejected = len(self.rejected_indices)
        return total - confirmed - rejected
    
    @property
    def confirmed_results(self) -> List[WebSearchResult]:
        """已确认的结果"""
        return [self.search_results[i] for i in self.confirmed_indices]
    
    @property
    def pending_results(self) -> List[WebSearchResult]:
        """待确认的结果"""
        confirmed_set = set(self.confirmed_indices)
        rejected_set = set(self.rejected_indices)
        return [
            result for i, result in enumerate(self.search_results)
            if i not in confirmed_set and i not in rejected_set
        ]
    
    def confirm_result(self, index: int, feedback: Optional[str] = None) -> bool:
        """
        确认指定索引的结果
        
        Args:
            index: 结果索引
            feedback: 用户反馈
            
        Returns:
            bool: 操作是否成功
        """
        if index < 0 or index >= len(self.search_results):
            return False
            
        if index in self.confirmed_indices or index in self.rejected_indices:
            return False
            
        self.confirmed_indices.append(index)
        if feedback:
            self.user_feedback = feedback
            
        # 更新状态
        self._update_status()
        return True
    
    def reject_result(self, index: int, feedback: Optional[str] = None) -> bool:
        """
        拒绝指定索引的结果
        
        Args:
            index: 结果索引
            feedback: 用户反馈
            
        Returns:
            bool: 操作是否成功
        """
        if index < 0 or index >= len(self.search_results):
            return False
            
        if index in self.confirmed_indices or index in self.rejected_indices:
            return False
            
        self.rejected_indices.append(index)
        if feedback:
            self.user_feedback = feedback
            
        # 更新状态
        self._update_status()
        return True
    
    def _update_status(self):
        """更新请求状态"""
        if self.is_expired:
            self.status = ConfirmationStatus.EXPIRED
        elif len(self.confirmed_indices) == len(self.search_results):
            self.status = ConfirmationStatus.CONFIRMED
        elif len(self.confirmed_indices) > 0:
            self.status = ConfirmationStatus.PARTIAL
        elif len(self.rejected_indices) == len(self.search_results):
            self.status = ConfirmationStatus.REJECTED
        # 否则保持PENDING状态
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "request_id": self.request_id,
            "query": self.query,
            "search_results": [r.to_dict() for r in self.search_results],
            "timeout": self.timeout,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "confirmed_indices": self.confirmed_indices,
            "rejected_indices": self.rejected_indices,
            "pending_count": self.pending_count,
            "user_feedback": self.user_feedback
        }


@dataclass
class WebSearchConfig:
    """
    互联网搜索配置
    
    Attributes:
        enable_web_search: 是否启用互联网搜索
        search_engines: 搜索引擎列表
        max_results: 最大结果数
        min_credibility: 最低可信度阈值
        min_relevance: 最低相关性阈值
        timeout: 搜索超时时间
        rate_limit: 请求频率限制（次/分钟）
        api_keys: API密钥字典
    """
    enable_web_search: bool = True
    search_engines: List[str] = field(default_factory=lambda: ["google", "bing"])
    max_results: int = 10
    min_credibility: float = 0.5
    min_relevance: float = 0.3
    timeout: int = 30
    rate_limit: int = 10
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证配置参数"""
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")
        if not 0 <= self.min_credibility <= 1:
            raise ValueError("min_credibility must be between 0 and 1")
        if not 0 <= self.min_relevance <= 1:
            raise ValueError("min_relevance must be between 0 and 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.rate_limit <= 0:
            raise ValueError("rate_limit must be positive")