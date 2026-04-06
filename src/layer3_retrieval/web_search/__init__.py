"""
Web Search Module - 互联网搜索模块
当本地RAG检索不足时，自动进行互联网搜索并提交人工确认
"""

from .models import WebSearchResult, ConfirmationRequest, ConfirmationStatus, WebSearchConfig
from .engine import WebSearchEngine
from .validator import SearchResultValidator
from .confirmation import HumanConfirmationManager

__all__ = [
    "WebSearchResult",
    "ConfirmationRequest", 
    "ConfirmationStatus",
    "WebSearchConfig",
    "WebSearchEngine",
    "SearchResultValidator",
    "HumanConfirmationManager"
]