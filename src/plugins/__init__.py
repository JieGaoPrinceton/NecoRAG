"""
NecoRAG 插件扩展模块
提供插件注册、加载、管理和卸载功能
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Plugin Team"

from .manager import PluginManager
from .base import BasePlugin, PluginType
from .registry import PluginRegistry

__all__ = [
    "PluginManager",
    "BasePlugin", 
    "PluginType",
    "PluginRegistry"
]