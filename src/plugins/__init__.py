"""
NecoRAG 插件扩展模块
提供插件注册、加载、管理和卸载功能

市场集成：
- BasePlugin 新增 marketplace_* 属性用于市场元数据
- BasePlugin 新增 required_permissions 属性用于权限声明
- BasePlugin 新增 manifest 属性和 get_marketplace_info() 方法
- BasePlugin 新增 on_marketplace_* 生命周期钩子
- PluginManager 新增 marketplace 集成方法
- PluginRegistry 新增版本索引和市场元数据缓存
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Plugin Team"

from .base import (
    BasePlugin, 
    PluginType,
    PerceptionPlugin,
    MemoryPlugin,
    RetrievalPlugin,
    RefinementPlugin,
    ResponsePlugin,
)
from .registry import PluginRegistry, plugin_registry
from .manager import PluginManager, plugin_manager

__all__ = [
    # 基础类
    "BasePlugin",
    "PluginType",
    # 层级插件基类
    "PerceptionPlugin",
    "MemoryPlugin",
    "RetrievalPlugin",
    "RefinementPlugin",
    "ResponsePlugin",
    # 管理器
    "PluginManager",
    "PluginRegistry",
    # 全局实例
    "plugin_registry",
    "plugin_manager",
]