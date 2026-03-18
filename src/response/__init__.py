"""
Response Interface - 响应接口
交互层核心组件，情境自适应生成与可解释性输出
"""

from src.response.interface import ResponseInterface
from src.response.profile_manager import UserProfileManager
from src.response.tone_adapter import ToneAdapter
from src.response.detail_adapter import DetailLevelAdapter
from src.response.visualizer import ThinkingChainVisualizer
from src.response.models import Interaction, RetrievalVisualization
# 从统一协议层重导出公共类型
from src.core.protocols import UserProfile, Response, ResponseTone, DetailLevel

__all__ = [
    "ResponseInterface",
    "UserProfileManager",
    "ToneAdapter",
    "DetailLevelAdapter",
    "ThinkingChainVisualizer",
    "UserProfile",
    "Response",
    "ResponseTone",
    "DetailLevel",
    "Interaction",
    "RetrievalVisualization",
]
