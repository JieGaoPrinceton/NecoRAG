"""
NecoRAG - 统一入口类

Neuro-Cognitive Retrieval-Augmented Generation
基于认知科学理论构建的下一代智能 RAG 框架
"""

from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import logging

from src.core.config import NecoRAGConfig, ConfigPresets, LLMProvider
from src.core.llm import MockLLMClient, BaseLLMClient
from src.core.protocols import Response, Query, RetrievalResult, UserProfile
from src.core.exceptions import NecoRAGError, ConfigurationError

# 核心模块
from src.perception import PerceptionEngine
from src.memory import MemoryManager
from src.retrieval import AdaptiveRetriever, HyDEEnhancer
from src.refinement import RefinementAgent
from src.response import ResponseInterface


logger = logging.getLogger(__name__)


class NecoRAG:
    """
    NecoRAG 统一入口类
    
    提供简洁的 API 用于：
    - 文档导入和索引
    - 智能问答检索
    - 配置管理
    
    使用示例：
    ```python
    # 快速开始
    rag = NecoRAG()
    rag.ingest("./documents/")
    response = rag.query("什么是深度学习？")
    print(response.content)
    
    # 使用自定义配置
    config = NecoRAGConfig()
    config.retrieval.top_k = 5
    rag = NecoRAG(config=config)
    ```
    """
    
    def __init__(
        self,
        config: Optional[NecoRAGConfig] = None,
        llm_client: Optional[BaseLLMClient] = None
    ):
        """
        初始化 NecoRAG
        
        Args:
            config: 配置对象（可选）
            llm_client: LLM 客户端（可选）
        """
        self.config = config or ConfigPresets.development()
        self._llm_client = llm_client
        self._initialized = False
        
        # 延迟初始化组件
        self._perception: Optional[PerceptionEngine] = None
        self._memory: Optional[MemoryManager] = None
        self._retrieval: Optional[AdaptiveRetriever] = None
        self._refinement: Optional[RefinementAgent] = None
        self._response: Optional[ResponseInterface] = None
        self._hyde: Optional[HyDEEnhancer] = None
        
        # 统计信息
        self._stats = {
            "documents_ingested": 0,
            "queries_processed": 0,
            "total_chunks": 0
        }
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化所有组件"""
        # 创建 LLM 客户端
        if self._llm_client is None:
            self._llm_client = self._create_llm_client()
        
        # 初始化各层组件
        self._perception = PerceptionEngine()
        self._memory = MemoryManager(decay_rate=self.config.memory.decay_rate)
        self._retrieval = AdaptiveRetriever(memory_manager=self._memory)
        self._refinement = RefinementAgent(llm_client=self._llm_client)
        self._response = ResponseInterface()
        self._hyde = HyDEEnhancer(llm_client=self._llm_client)
        
        self._initialized = True
        logger.info("NecoRAG initialized successfully")
    
    def _create_llm_client(self) -> BaseLLMClient:
        """根据配置创建 LLM 客户端"""
        provider = self.config.llm.provider
        
        if provider == LLMProvider.MOCK:
            return MockLLMClient(
                model_name=self.config.llm.model_name,
                embedding_dim=self.config.llm.embedding_dimension
            )
        
        # 其他提供商需要额外实现
        logger.warning(f"LLM provider {provider} not fully implemented, using mock")
        return MockLLMClient()
    
    # ============== 文档导入 ==============
    
    def ingest(
        self,
        source: Union[str, Path, List[str]],
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        导入文档到知识库
        
        Args:
            source: 文件路径、目录路径或路径列表
            recursive: 是否递归处理子目录
            file_types: 文件类型过滤（如 ['.txt', '.md', '.pdf']）
            
        Returns:
            Dict: 导入统计信息
        """
        if isinstance(source, (str, Path)):
            source = Path(source)
            if source.is_dir():
                files = self._collect_files(source, recursive, file_types)
            else:
                files = [source]
        else:
            files = [Path(p) for p in source]
        
        results = {
            "total_files": len(files),
            "processed": 0,
            "failed": 0,
            "chunks_created": 0,
            "errors": []
        }
        
        for file_path in files:
            try:
                chunks = self.ingest_file(file_path)
                results["processed"] += 1
                results["chunks_created"] += chunks
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"file": str(file_path), "error": str(e)})
                logger.error(f"Failed to ingest {file_path}: {e}")
        
        self._stats["documents_ingested"] += results["processed"]
        self._stats["total_chunks"] += results["chunks_created"]
        
        return results
    
    def ingest_file(self, file_path: Union[str, Path]) -> int:
        """
        导入单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 创建的分块数量
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 感知层处理
        encoded_chunks = self._perception.process(str(file_path))
        
        # 存储到记忆层
        for chunk in encoded_chunks:
            self._memory.store(chunk)
        
        logger.info(f"Ingested {file_path}: {len(encoded_chunks)} chunks")
        return len(encoded_chunks)
    
    def ingest_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        导入文本内容
        
        Args:
            text: 文本内容
            metadata: 元数据
            
        Returns:
            int: 创建的分块数量
        """
        # 感知层处理
        encoded_chunks = self._perception.process_text(text, metadata or {})
        
        # 存储到记忆层
        for chunk in encoded_chunks:
            self._memory.store(chunk)
        
        self._stats["total_chunks"] += len(encoded_chunks)
        return len(encoded_chunks)
    
    def _collect_files(
        self,
        directory: Path,
        recursive: bool,
        file_types: Optional[List[str]]
    ) -> List[Path]:
        """收集目录下的文件"""
        if file_types is None:
            file_types = self.config.perception.supported_formats
        
        # 确保文件类型以点开头
        file_types = [f".{ft}" if not ft.startswith('.') else ft for ft in file_types]
        
        files = []
        pattern = "**/*" if recursive else "*"
        
        for path in directory.glob(pattern):
            if path.is_file() and path.suffix.lower() in file_types:
                files.append(path)
        
        return files
    
    # ============== 查询检索 ==============
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
        use_hyde: Optional[bool] = None,
        use_refinement: bool = True
    ) -> Response:
        """
        查询知识库
        
        Args:
            question: 查询问题
            user_id: 用户ID（用于个性化响应）
            top_k: 返回结果数量
            use_hyde: 是否使用 HyDE 增强
            use_refinement: 是否使用答案精炼
            
        Returns:
            Response: 响应对象
        """
        top_k = top_k or self.config.retrieval.default_top_k
        use_hyde = use_hyde if use_hyde is not None else self.config.retrieval.enable_hyde
        
        # 构建查询对象
        query = Query(text=question, user_id=user_id, top_k=top_k)
        
        # HyDE 增强
        if use_hyde and self._hyde:
            hypothesis_embedding = self._hyde.get_hypothesis_embedding(question)
            if hypothesis_embedding:
                query.vector = hypothesis_embedding
        
        # 检索
        results = self._retrieval.retrieve(query.text, top_k=top_k)
        
        # 提取证据
        evidence = [r.content for r in results]
        
        # 答案精炼
        if use_refinement and self._refinement:
            refinement_result = self._refinement.refine(question, evidence)
            content = refinement_result.content
            confidence = refinement_result.confidence
        else:
            # 简单拼接
            content = self._simple_answer(question, evidence)
            confidence = 0.7 if evidence else 0.0
        
        # 响应适配
        response = self._response.generate(
            content=content,
            user_id=user_id,
            sources=results
        )
        
        self._stats["queries_processed"] += 1
        
        return Response(
            query_id=query.query_id,
            content=response.content,
            confidence=confidence,
            sources=[RetrievalResult(
                memory_id=r.memory_id,
                content=r.content,
                score=r.score,
                source=r.source
            ) for r in results],
            metadata={"user_id": user_id}
        )
    
    def _simple_answer(self, question: str, evidence: List[str]) -> str:
        """简单答案生成（不使用精炼）"""
        if not evidence:
            return "抱歉，我无法找到与您问题相关的信息。"
        
        parts = [f"针对您的问题「{question}」，以下是相关信息：", ""]
        for i, e in enumerate(evidence[:3]):
            parts.append(f"{i+1}. {e[:200]}...")
        
        return "\n".join(parts)
    
    # ============== 便捷方法 ==============
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        简单搜索（仅检索，不生成答案）
        
        Args:
            query: 搜索查询
            top_k: 返回数量
            
        Returns:
            List[RetrievalResult]: 检索结果列表
        """
        results = self._retrieval.retrieve(query, top_k=top_k)
        return [RetrievalResult(
            memory_id=r.memory_id,
            content=r.content,
            score=r.score,
            source=r.source
        ) for r in results]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "memory_count": self._memory.count() if self._memory else 0,
            "config": {
                "llm_provider": self.config.llm.provider.value,
                "model": self.config.llm.model_name,
            }
        }
    
    def clear(self):
        """清空知识库"""
        if self._memory:
            # 重新初始化记忆管理器
            self._memory = MemoryManager(decay_rate=self.config.memory.decay_rate)
            self._retrieval = AdaptiveRetriever(memory_manager=self._memory)
        
        self._stats = {
            "documents_ingested": 0,
            "queries_processed": 0,
            "total_chunks": 0
        }
        
        logger.info("Knowledge base cleared")
    
    # ============== 上下文管理 ==============
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """关闭并清理资源"""
        logger.info("NecoRAG closed")
    
    # ============== 类方法 ==============
    
    @classmethod
    def from_config_file(cls, config_path: str) -> "NecoRAG":
        """
        从配置文件创建实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            NecoRAG: 实例
        """
        config = NecoRAGConfig.load(config_path)
        return cls(config=config)
    
    @classmethod
    def quick_start(cls) -> "NecoRAG":
        """
        快速启动（最小配置）
        
        Returns:
            NecoRAG: 使用最小配置的实例
        """
        return cls(config=ConfigPresets.minimal())


# 便捷函数
def create_rag(
    llm_provider: str = "mock",
    **kwargs
) -> NecoRAG:
    """
    创建 NecoRAG 实例的便捷函数
    
    Args:
        llm_provider: LLM 提供商 (mock, openai, ollama)
        **kwargs: 其他配置参数
        
    Returns:
        NecoRAG: 实例
    """
    config = NecoRAGConfig()
    config.llm.provider = LLMProvider(llm_provider)
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return NecoRAG(config=config)
