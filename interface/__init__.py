"""
NecoRAG Interface Module
提供知识库查询、插入、更新等能力的RESTful API和WebSocket服务接口
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Interface Team"

from .api import create_api_app
from .websocket import WebSocketManager
from .knowledge_service import KnowledgeService

__all__ = [
    "create_api_app",
    "WebSocketManager", 
    "KnowledgeService"
]