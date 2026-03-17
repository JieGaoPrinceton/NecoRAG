"""
Purr Interface - 呼噜交互接口
交互层核心组件，情境自适应生成与可解释性输出
"""

from src.purr.interface import PurrInterface
from src.purr.profile_manager import UserProfileManager
from src.purr.tone_adapter import ToneAdapter
from src.purr.detail_adapter import DetailLevelAdapter
from src.purr.visualizer import ThinkingChainVisualizer
from src.purr.models import UserProfile, Response, Interaction

__all__ = [
    "PurrInterface",
    "UserProfileManager",
    "ToneAdapter",
    "DetailLevelAdapter",
    "ThinkingChainVisualizer",
    "UserProfile",
    "Response",
    "Interaction",
]
