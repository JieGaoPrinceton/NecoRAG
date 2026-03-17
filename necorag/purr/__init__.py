"""
Purr Interface - 呼噜交互接口
交互层核心组件，情境自适应生成与可解释性输出
"""

from necorag.purr.interface import PurrInterface
from necorag.purr.profile_manager import UserProfileManager
from necorag.purr.tone_adapter import ToneAdapter
from necorag.purr.detail_adapter import DetailLevelAdapter
from necorag.purr.visualizer import ThinkingChainVisualizer
from necorag.purr.models import UserProfile, Response, Interaction

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
