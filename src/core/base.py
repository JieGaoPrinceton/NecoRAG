"""
NecoRAG 抽象基类定义

定义所有核心组件的抽象接口，确保实现的一致性和可替换性。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass

from .protocols import (
    Document, Chunk, EncodedChunk, Embedding,
    Memory, Entity, Relation,
    Query, RetrievalResult, Response,
    GeneratedAnswer, CritiqueResult, HallucinationReport,
    IntentType
)

# 为了支持实现类使用的不同数据类型，使用 TYPE_CHECKING 和 Union
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from src.refinement.models import (
        GeneratedAnswer as RefinementGeneratedAnswer,
        CritiqueReport,
        HallucinationReport as RefinementHallucinationReport,
    )
    from src.intent.models import IntentResult, IntentRoutingStrategy


# ============== 感知层抽象 ==============

class BaseParser(ABC):
    """文档解析器抽象基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Any:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            Any: 解析后的文档对象（Document 或其子类）
        """
        pass
    
    def parse_content(self, content: str, doc_type: str = "text") -> Any:
        """
        解析文本内容（可选实现）
        
        Args:
            content: 文本内容
            doc_type: 文档类型
            
        Returns:
            Any: 解析后的文档对象
        """
        raise NotImplementedError("parse_content is optional")
    
    def supports(self, file_extension: str) -> bool:
        """检查是否支持该文件类型"""
        return True


class BaseChunker(ABC):
    """文本分块器抽象基类"""
    
    @abstractmethod
    def chunk(self, content: str, **kwargs) -> List[Chunk]:
        """
        将文本分割成多个块
        
        Args:
            content: 文本内容
            **kwargs: 额外参数（如 strategy 等）
            
        Returns:
            List[Chunk]: 分块列表
        """
        pass
    
    @property
    def chunk_size(self) -> int:
        """返回分块大小（子类应覆盖）"""
        return getattr(self, '_chunk_size', 512)
    
    @chunk_size.setter
    def chunk_size(self, value: int) -> None:
        """设置分块大小"""
        self._chunk_size = value
    
    @property
    def chunk_overlap(self) -> int:
        """返回分块重叠大小（子类应覆盖）"""
        return getattr(self, '_chunk_overlap', 50)
    
    @chunk_overlap.setter
    def chunk_overlap(self, value: int) -> None:
        """设置分块重叠大小"""
        self._chunk_overlap = value


class BaseEncoder(ABC):
    """向量编码器抽象基类"""
    
    @abstractmethod
    def encode(self, text: str) -> Any:
        """
        编码文本为向量
        
        Args:
            text: 文本内容
            
        Returns:
            Any: 向量表示（可以是 Embedding、List[float] 或多类型元组）
        """
        pass
    
    def encode_batch(self, texts: List[str]) -> List[Any]:
        """
        批量编码文本（默认实现，子类可覆盖优化）
        
        Args:
            texts: 文本列表
            
        Returns:
            List[Any]: 向量列表
        """
        return [self.encode(text) for text in texts]
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回向量维度"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名称"""
        pass


class BaseTagger(ABC):
    """情境标签生成器抽象基类"""
    
    @abstractmethod
    def tag(self, chunk: Chunk) -> Dict[str, Any]:
        """
        为分块生成情境标签
        
        Args:
            chunk: 分块对象
            
        Returns:
            Dict[str, Any]: 标签字典
        """
        pass


# ============== 记忆层抽象 ==============

class BaseMemoryStore(ABC):
    """记忆存储抽象基类"""
    
    @abstractmethod
    def store(self, memory: Memory) -> str:
        """
        存储记忆
        
        Args:
            memory: 记忆对象
            
        Returns:
            str: 记忆ID
        """
        pass
    
    @abstractmethod
    def retrieve(self, memory_id: str) -> Optional[Memory]:
        """
        检索记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[Memory]: 记忆对象或None
        """
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 10) -> List[Memory]:
        """
        向量搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            
        Returns:
            List[Memory]: 匹配的记忆列表
        """
        pass


class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def upsert(self, embeddings: List[Embedding]) -> List[str]:
        """
        插入或更新向量
        
        Args:
            embeddings: 向量列表
            
        Returns:
            List[str]: 向量ID列表
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        向量搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filters: 过滤条件
            
        Returns:
            List[tuple]: (id, score, metadata) 元组列表
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """
        删除向量
        
        Args:
            ids: 向量ID列表
            
        Returns:
            int: 删除数量
        """
        pass
    
    def get(self, ids: List[str]) -> List[Optional[Any]]:
        """
        批量获取向量记录（来自 backends/base.py 合并）
        
        Args:
            ids: 记录ID列表
            
        Returns:
            List[Optional[Any]]: 记录列表（不存在返回None）
        """
        raise NotImplementedError("get() not implemented")
    
    def count(self) -> int:
        """返回记录总数（来自 backends/base.py 合并）"""
        raise NotImplementedError("count() not implemented")
    
    def clear(self) -> int:
        """
        清空所有记录（来自 backends/base.py 合并）
        
        Returns:
            int: 删除的记录数
        """
        raise NotImplementedError("clear() not implemented")
    
    @property
    def dimension(self) -> int:
        """返回向量维度（来自 backends/base.py 合并）"""
        raise NotImplementedError("dimension not implemented")


class BaseGraphStore(ABC):
    """图存储抽象基类"""
    
    @abstractmethod
    def add_entity(self, entity: Entity) -> str:
        """
        添加实体
        
        Args:
            entity: 实体对象
            
        Returns:
            str: 实体ID
        """
        pass
    
    @abstractmethod
    def add_relation(self, relation: Relation) -> str:
        """
        添加关系
        
        Args:
            relation: 关系对象
            
        Returns:
            str: 关系ID
        """
        pass
    
    @abstractmethod
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[Entity]: 实体对象或None
        """
        pass
    
    @abstractmethod
    def traverse(
        self,
        start_id: str,
        max_depth: int = 2,
        relation_types: Optional[List[str]] = None
    ) -> List[Entity]:
        """
        图遍历
        
        Args:
            start_id: 起始实体ID
            max_depth: 最大深度
            relation_types: 关系类型过滤
            
        Returns:
            List[Entity]: 遍历到的实体列表
        """
        pass
    
    def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体（及相关关系）（来自 backends/base.py 合并）
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否成功
        """
        raise NotImplementedError("delete_entity() not implemented")
    
    def delete_relation(self, relation_id: str) -> bool:
        """
        删除关系（来自 backends/base.py 合并）
        
        Args:
            relation_id: 关系ID
            
        Returns:
            bool: 是否成功
        """
        raise NotImplementedError("delete_relation() not implemented")
    
    def entity_count(self) -> int:
        """返回实体总数（来自 backends/base.py 合并）"""
        raise NotImplementedError("entity_count() not implemented")
    
    def relation_count(self) -> int:
        """返回关系总数（来自 backends/base.py 合并）"""
        raise NotImplementedError("relation_count() not implemented")


# ============== 检索层抽象 ==============

class BaseRetriever(ABC):
    """检索器抽象基类"""
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            **kwargs: 额外参数
            
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        pass


class BaseReranker(ABC):
    """重排序器抽象基类"""
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        重排序
        
        Args:
            query: 查询文本
            results: 待排序结果
            top_k: 返回数量（可选）
            
        Returns:
            List[RetrievalResult]: 重排后的结果
        """
        pass


# ============== 巩固层抽象 ==============

class BaseGenerator(ABC):
    """答案生成器抽象基类"""
    
    @abstractmethod
    def generate(
        self,
        query: str,
        evidence: List[str],
        **kwargs
    ) -> GeneratedAnswer:
        """
        生成答案
        
        Args:
            query: 查询文本
            evidence: 证据列表
            **kwargs: 额外参数
            
        Returns:
            GeneratedAnswer: 生成的答案
        """
        pass


class BaseCritic(ABC):
    """批判器抽象基类"""
    
    @abstractmethod
    def critique(
        self,
        answer: Any,
        evidence: List[str]
    ) -> Any:
        """
        批判评估
        
        Args:
            answer: 待评估答案 (GeneratedAnswer 或兼容类型)
            evidence: 证据列表
            
        Returns:
            Any: 批判结果 (CritiqueResult 或 CritiqueReport)
        """
        pass


class BaseRefiner(ABC):
    """修正器抽象基类"""
    
    @abstractmethod
    def refine(
        self,
        answer: Any,
        critique: Any,
        additional_evidence: Optional[List[str]] = None
    ) -> Any:
        """
        修正答案
        
        Args:
            answer: 原始答案 (GeneratedAnswer 或兼容类型)
            critique: 批判结果 (CritiqueResult 或 CritiqueReport)
            additional_evidence: 补充证据列表
            
        Returns:
            Any: 修正后的答案
        """
        pass


class BaseHallucinationDetector(ABC):
    """幻觉检测器抽象基类"""
    
    @abstractmethod
    def detect(
        self,
        answer: Any,
        evidence: List[str]
    ) -> Any:
        """
        检测幻觉
        
        Args:
            answer: 待检测答案 (str 或 GeneratedAnswer)
            evidence: 证据列表
            
        Returns:
            Any: 检测报告 (HallucinationReport)
        """
        pass


# ============== LLM 抽象 ==============

class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本
        """
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        文本向量化
        
        Args:
            text: 文本内容
            
        Returns:
            List[float]: 向量
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名称"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """返回嵌入向量维度"""
        pass


class BaseAsyncLLMClient(ABC):
    """异步 LLM 客户端抽象基类"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """异步生成文本"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """异步文本向量化"""
        pass


# ============== 响应层抽象 ==============

class BaseResponseAdapter(ABC):
    """响应适配器抽象基类"""
    
    @abstractmethod
    def adapt(self, content: str, **kwargs) -> str:
        """
        适配响应内容
        
        Args:
            content: 原始内容
            **kwargs: 额外参数
            
        Returns:
            str: 适配后的内容
        """
        pass


# ============== 意图分类层抽象 ==============

# IntentResult 定义在 src/intent/models.py 中
# 这里为了向后兼容保留类型别名引用


class BaseIntentClassifier(ABC):
    """意图分类器抽象基类"""
    
    @abstractmethod
    def classify(self, query: str) -> Any:
        """
        对查询进行意图分类
        
        Args:
            query: 用户查询文本
            
        Returns:
            Any: 意图分类结果 (IntentResult)
        """
        pass
    
    @abstractmethod
    def batch_classify(self, queries: List[str]) -> List[Any]:
        """
        批量意图分类
        
        Args:
            queries: 查询列表
            
        Returns:
            List[Any]: 分类结果列表
        """
        pass
    
    @property
    @abstractmethod
    def backend(self) -> str:
        """返回分类器后端名称"""
        pass


class BaseIntentRouter(ABC):
    """意图路由器抽象基类"""
    
    @abstractmethod
    def route(self, intent_result: Any) -> Any:
        """
        根据意图结果获取路由策略
        
        Args:
            intent_result: 意图分类结果 (IntentResult)
            
        Returns:
            Any: 路由策略 (IntentRoutingStrategy 或 Dict)
        """
        pass
    
    @abstractmethod
    def get_weight_factor(self, intent_result: Any) -> float:
        """
        计算意图权重因子
        
        Args:
            intent_result: 意图分类结果
            
        Returns:
            float: 权重因子
        """
        pass


# ============== 知识演化层抽象 ==============

class BaseKnowledgeUpdater(ABC):
    """
    知识更新器抽象基类
    
    Abstract base class for knowledge updater implementations.
    """
    
    @abstractmethod
    def realtime_update(
        self,
        content: str,
        source: Any,
        target_layer: str = "L1",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        实时更新知识
        
        Args:
            content: 知识内容
            source: 知识来源 (str 或 KnowledgeSource 枚举)
            target_layer: 目标层级
            metadata: 元数据
            
        Returns:
            Optional[str]: 新记忆的 ID，如果失败则返回 None
        """
        pass
    
    @abstractmethod
    def execute_batch_update(self, task_id: str) -> Any:
        """
        执行批量更新任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Any: 更新结果 (UpdateTask)
        """
        pass
    
    @abstractmethod
    def on_query_completed(
        self,
        query: str,
        answer: str,
        evidence: List[str],
        hit: bool,
        confidence: float = 0.0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        查询完成后的回调
        
        Args:
            query: 查询文本
            answer: 回答内容
            evidence: 证据列表
            hit: 是否命中
            confidence: 回答置信度
            latency_ms: 响应延迟
            metadata: 额外元数据
        """
        pass


class BaseMetricsCalculator(ABC):
    """
    指标计算器抽象基类
    
    Abstract base class for metrics calculator implementations.
    """
    
    @abstractmethod
    def calculate_metrics(self, force_refresh: bool = False) -> Any:
        """
        计算当前指标
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Any: 指标对象 (KnowledgeMetrics)
        """
        pass
    
    @abstractmethod
    def generate_health_report(self) -> Any:
        """
        生成健康报告
        
        Returns:
            Any: 健康报告对象 (HealthReport)
        """
        pass


# ============== 自适应学习层抽象 ==============

class BaseAdaptiveLearner(ABC):
    """
    自适应学习器抽象基类
    
    Abstract base class for adaptive learning implementations.
    """
    
    @abstractmethod
    def learn(self, feedback: Any) -> None:
        """
        从反馈中学习
        
        Args:
            feedback: 用户反馈数据
        """
        pass
    
    @abstractmethod
    def predict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于学习预测
        
        Args:
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 预测结果
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取学习指标
        
        Returns:
            Dict[str, Any]: 学习指标数据
        """
        pass
