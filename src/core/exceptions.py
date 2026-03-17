"""
NecoRAG 统一异常定义

定义系统中所有模块使用的异常类型，便于统一的错误处理和追踪。
"""

from typing import Optional, Any, Dict


class NecoRAGError(Exception):
    """NecoRAG 基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            code: 错误码（可选）
            details: 详细信息（可选）
        """
        super().__init__(message)
        self.message = message
        self.code = code or "NECORAG_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# ============== 感知层异常 ==============

class ParseError(NecoRAGError):
    """文档解析错误"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "file_path": file_path,
            "file_type": file_type
        })
        super().__init__(
            message=message,
            code="PARSE_ERROR",
            details=details,
            **kwargs
        )


class ChunkingError(NecoRAGError):
    """文本分块错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, code="CHUNKING_ERROR", **kwargs)


class EncodingError(NecoRAGError):
    """向量编码错误"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["model_name"] = model_name
        super().__init__(
            message=message,
            code="ENCODING_ERROR",
            details=details,
            **kwargs
        )


# ============== 记忆层异常 ==============

class MemoryError(NecoRAGError):
    """记忆存储错误"""
    
    def __init__(self, message: str, layer: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        details["layer"] = layer
        super().__init__(
            message=message,
            code="MEMORY_ERROR",
            details=details,
            **kwargs
        )


class VectorStoreError(MemoryError):
    """向量存储错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, layer="L2_SEMANTIC", **kwargs)
        self.code = "VECTOR_STORE_ERROR"


class GraphStoreError(MemoryError):
    """图存储错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, layer="L3_EPISODIC", **kwargs)
        self.code = "GRAPH_STORE_ERROR"


# ============== 检索层异常 ==============

class RetrievalError(NecoRAGError):
    """检索错误"""
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["query"] = query
        super().__init__(
            message=message,
            code="RETRIEVAL_ERROR",
            details=details,
            **kwargs
        )


class RerankError(RetrievalError):
    """重排序错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)
        self.code = "RERANK_ERROR"


# ============== 巩固层异常 ==============

class GenerationError(NecoRAGError):
    """生成错误"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["model_name"] = model_name
        super().__init__(
            message=message,
            code="GENERATION_ERROR",
            details=details,
            **kwargs
        )


class HallucinationError(NecoRAGError):
    """幻觉检测错误"""
    
    def __init__(
        self,
        message: str,
        detection_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["detection_type"] = detection_type
        super().__init__(
            message=message,
            code="HALLUCINATION_ERROR",
            details=details,
            **kwargs
        )


class RefinementError(NecoRAGError):
    """精炼错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, code="REFINEMENT_ERROR", **kwargs)


# ============== LLM 相关异常 ==============

class LLMError(NecoRAGError):
    """LLM 客户端错误"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "provider": provider,
            "model": model
        })
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details=details,
            **kwargs
        )


class LLMConnectionError(LLMError):
    """LLM 连接错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)
        self.code = "LLM_CONNECTION_ERROR"


class LLMRateLimitError(LLMError):
    """LLM 限流错误"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        details = kwargs.pop("details", {})
        details["retry_after"] = retry_after
        super().__init__(message=message, details=details, **kwargs)
        self.code = "LLM_RATE_LIMIT_ERROR"


class LLMResponseError(LLMError):
    """LLM 响应错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)
        self.code = "LLM_RESPONSE_ERROR"


# ============== 配置相关异常 ==============

class ConfigurationError(NecoRAGError):
    """配置错误"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["config_key"] = config_key
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            **kwargs
        )


class ValidationError(NecoRAGError):
    """验证错误"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "field": field,
            "value": str(value) if value is not None else None
        })
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            **kwargs
        )
