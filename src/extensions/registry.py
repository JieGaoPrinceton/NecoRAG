"""
插件注册表
管理插件的注册、发现和元数据
"""

import importlib
import pkgutil
import logging
from typing import Dict, List, Type, Optional, Set, Any
from pathlib import Path

from .base import BasePlugin, PluginType


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._loaded_plugins: Dict[str, BasePlugin] = {}
        self._plugin_paths: Set[str] = set()
        self.logger = logging.getLogger(__name__)
        # 市场集成
        self._version_index: Dict[str, Dict[str, type]] = {}  # plugin_id -> {version -> plugin_class}
        self._marketplace_metadata: Dict[str, Dict] = {}  # plugin_id -> marketplace metadata cache
        self._marketplace_id_map: Dict[str, str] = {}  # marketplace_plugin_id -> registry_key
    
    def register_plugin(self, plugin_class: Type[BasePlugin]) -> bool:
        """
        注册插件类
        Args:
            plugin_class: 插件类
        Returns:
            bool: 注册是否成功
        """
        try:
            plugin_id = plugin_class.__name__
            
            if plugin_id in self._plugins:
                self.logger.warning(f"Plugin {plugin_id} already registered")
                return False
            
            # 验证插件类
            if not self._validate_plugin_class(plugin_class):
                self.logger.error(f"Invalid plugin class: {plugin_id}")
                return False
            
            self._plugins[plugin_id] = plugin_class
            self.logger.info(f"Plugin registered: {plugin_id}")
            
            # 建立 marketplace_id 映射
            marketplace_id = getattr(plugin_class, 'marketplace_id', '')
            if marketplace_id:
                self._marketplace_id_map[marketplace_id] = plugin_id
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register plugin: {str(e)}")
            return False
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        注销插件
        Args:
            plugin_id: 插件ID
        Returns:
            bool: 注销是否成功
        """
        if plugin_id in self._plugins:
            # 如果插件已加载，先卸载
            if plugin_id in self._loaded_plugins:
                self.unload_plugin(plugin_id)
            
            del self._plugins[plugin_id]
            self.logger.info(f"Plugin unregistered: {plugin_id}")
            return True
        return False
    
    def load_plugin(self, plugin_id: str, config: Dict = None) -> Optional[BasePlugin]:
        """
        加载插件实例
        Args:
            plugin_id: 插件ID
            config: 插件配置
        Returns:
            BasePlugin: 插件实例或None
        """
        try:
            if plugin_id not in self._plugins:
                self.logger.error(f"Plugin not registered: {plugin_id}")
                return None
            
            if plugin_id in self._loaded_plugins:
                self.logger.info(f"Plugin already loaded: {plugin_id}")
                return self._loaded_plugins[plugin_id]
            
            plugin_class = self._plugins[plugin_id]
            plugin_instance = plugin_class()
            
            if plugin_instance.initialize(config):
                self._loaded_plugins[plugin_id] = plugin_instance
                self.logger.info(f"Plugin loaded: {plugin_id}")
                return plugin_instance
            else:
                self.logger.error(f"Failed to initialize plugin: {plugin_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_id}: {str(e)}")
            return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件实例
        Args:
            plugin_id: 插件ID
        Returns:
            bool: 卸载是否成功
        """
        if plugin_id in self._loaded_plugins:
            try:
                plugin_instance = self._loaded_plugins[plugin_id]
                plugin_instance.cleanup()
                del self._loaded_plugins[plugin_id]
                self.logger.info(f"Plugin unloaded: {plugin_id}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to unload plugin {plugin_id}: {str(e)}")
                return False
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """
        获取已加载的插件实例
        Args:
            plugin_id: 插件ID
        Returns:
            BasePlugin: 插件实例或None
        """
        return self._loaded_plugins.get(plugin_id)
    
    def get_plugin_by_marketplace_id(self, marketplace_id: str) -> Optional[BasePlugin]:
        """
        通过市场 ID 获取插件实例
        Args:
            marketplace_id: 市场插件ID
        Returns:
            BasePlugin: 插件实例或None
        """
        registry_key = self._marketplace_id_map.get(marketplace_id)
        if registry_key:
            return self._loaded_plugins.get(registry_key)
        # 降级：直接尝试用 marketplace_id 作为 key 查找
        return self._loaded_plugins.get(marketplace_id)
    
    def get_plugin_class(self, plugin_id: str) -> Optional[Type[BasePlugin]]:
        """
        获取插件类
        Args:
            plugin_id: 插件ID
        Returns:
            Type[BasePlugin]: 插件类或None
        """
        return self._plugins.get(plugin_id)
    
    def list_plugins(self, plugin_type: PluginType = None) -> List[Dict[str, Any]]:
        """
        列出所有插件
        Args:
            plugin_type: 插件类型过滤
        Returns:
            List[Dict]: 插件信息列表
        """
        plugins_info = []
        
        for plugin_id, plugin_class in self._plugins.items():
            try:
                # 创建临时实例获取信息
                temp_plugin = plugin_class()
                info = temp_plugin.get_info()
                info["loaded"] = plugin_id in self._loaded_plugins
                info["class"] = plugin_class.__name__
                
                if plugin_type is None or info["type"] == plugin_type.value:
                    plugins_info.append(info)
            except Exception as e:
                self.logger.error(f"Failed to get info for plugin {plugin_id}: {str(e)}")
        
        return plugins_info
    
    def discover_plugins(self, search_paths: List[str] = None) -> int:
        """
        发现插件
        Args:
            search_paths: 搜索路径列表
        Returns:
            int: 发现的插件数量
        """
        if search_paths is None:
            search_paths = []
        
        # 添加默认插件目录
        default_plugin_dir = Path(__file__).parent.parent / "plugins"
        if default_plugin_dir.exists():
            search_paths.append(str(default_plugin_dir))
        
        discovered_count = 0
        
        for search_path in search_paths:
            if search_path not in self._plugin_paths:
                count = self._discover_from_path(search_path)
                discovered_count += count
                self._plugin_paths.add(search_path)
        
        return discovered_count
    
    def _discover_from_path(self, path: str) -> int:
        """从指定路径发现插件"""
        discovered_count = 0
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return 0
            
            # 遍历路径下的所有Python模块
            for module_info in pkgutil.iter_modules([str(path_obj)]):
                try:
                    module = importlib.import_module(f"plugins.{module_info.name}")
                    
                    # 查找BasePlugin的子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BasePlugin) and 
                            attr != BasePlugin):
                            
                            if self.register_plugin(attr):
                                discovered_count += 1
                                
                except Exception as e:
                    self.logger.warning(f"Failed to import module {module_info.name}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Failed to discover plugins from {path}: {str(e)}")
        
        return discovered_count
    
    def _validate_plugin_class(self, plugin_class: Type[BasePlugin]) -> bool:
        """验证插件类的有效性"""
        try:
            # 检查必需的方法
            required_methods = ['_initialize', '_cleanup', 'description', 'dependencies']
            for method in required_methods:
                if not hasattr(plugin_class, method):
                    self.logger.error(f"Plugin class missing required method: {method}")
                    return False
            
            # 尝试创建实例验证
            plugin_instance = plugin_class()
            plugin_instance.get_info()  # 验证基本信息可获取
            
            return True
        except Exception as e:
            self.logger.error(f"Plugin class validation failed: {str(e)}")
            return False
    
    @property
    def registered_count(self) -> int:
        """已注册的插件数量"""
        return len(self._plugins)
    
    @property
    def loaded_count(self) -> int:
        """已加载的插件数量"""
        return len(self._loaded_plugins)
    
    # ========== 市场集成方法 ==========
    
    def register_version(self, plugin_id: str, version: str, 
                         plugin_class: type) -> bool:
        """
        注册插件的特定版本
        
        Args:
            plugin_id: 插件 ID
            version: 版本号
            plugin_class: 插件类
        
        Returns:
            bool: 注册是否成功
        """
        try:
            if plugin_id not in self._version_index:
                self._version_index[plugin_id] = {}
            
            if version in self._version_index[plugin_id]:
                self.logger.warning(f"Version {version} of plugin {plugin_id} already registered")
                return False
            
            self._version_index[plugin_id][version] = plugin_class
            self.logger.debug(f"Registered version {version} for plugin {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register version: {str(e)}")
            return False
    
    def get_version(self, plugin_id: str, version: str) -> Optional[type]:
        """
        获取插件的特定版本
        
        Args:
            plugin_id: 插件 ID
            version: 版本号
        
        Returns:
            Optional[type]: 插件类或 None
        """
        if plugin_id in self._version_index:
            return self._version_index[plugin_id].get(version)
        return None
    
    def get_versions(self, plugin_id: str) -> List[str]:
        """
        获取插件所有已注册的版本
        
        Args:
            plugin_id: 插件 ID
        
        Returns:
            List[str]: 版本号列表
        """
        if plugin_id in self._version_index:
            return list(self._version_index[plugin_id].keys())
        return []
    
    def set_marketplace_metadata(self, plugin_id: str, metadata: Dict) -> None:
        """
        缓存市场元数据
        
        Args:
            plugin_id: 插件 ID
            metadata: 元数据字典
        """
        self._marketplace_metadata[plugin_id] = metadata
        self.logger.debug(f"Cached marketplace metadata for plugin {plugin_id}")
    
    def get_marketplace_metadata(self, plugin_id: str) -> Optional[Dict]:
        """
        获取缓存的市场元数据
        
        Args:
            plugin_id: 插件 ID
        
        Returns:
            Optional[Dict]: 元数据字典或 None
        """
        return self._marketplace_metadata.get(plugin_id)
    
    def list_marketplace_plugins(self) -> List[Dict]:
        """
        列出所有有市场元数据的插件
        
        Returns:
            List[Dict]: 插件信息列表，包含 plugin_id 和元数据
        """
        result = []
        for plugin_id, metadata in self._marketplace_metadata.items():
            plugin_info = {
                "plugin_id": plugin_id,
                "metadata": metadata,
                "registered": plugin_id in self._plugins,
                "loaded": plugin_id in self._loaded_plugins,
                "versions": self.get_versions(plugin_id)
            }
            result.append(plugin_info)
        return result


# 全局插件注册表实例
plugin_registry = PluginRegistry()