"""
NecoRAG - Layer 5: Interaction Layer (交互层)
基于认知科学的神经符号 RAG 框架

交互层负责情境自适应生成与可解释性输出，模拟人脑的决策与表达机制：
- 响应接口：统一的响应生成与管理
- 用户画像：个性化交互适配
- 语调适配器：根据场景调整表达风格
- 细节适配器：动态调整信息密度
- 思维链可视化：提供可解释的推理过程
"""

from .interface import ResponseInterface
from .profile_manager import UserProfileManager
from .tone_adapter import ToneAdapter
from .detail_adapter import DetailLevelAdapter
from .visualizer import ThinkingChainVisualizer
from .models import Interaction, RetrievalVisualization
# 从统一协议层重导出公共类型
from ..core.protocols import UserProfile, Response, ResponseTone, DetailLevel

__all__ = [
    # 核心接口
    "ResponseInterface",
    # 适配组件
    "UserProfileManager",
    "ToneAdapter",
    "DetailLevelAdapter",
    "ThinkingChainVisualizer",
    # 数据模型
    "Interaction",
    "RetrievalVisualization",
    # 协议类型
    "UserProfile",
    "Response",
    "ResponseTone",
    "DetailLevel",
]
