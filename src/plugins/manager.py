"""
插件管理器
提供插件的生命周期管理、依赖解析和事件处理
"""

import logging
from typing import Dict, List, Set, Callable, Any, Optional
from collections import defaultdict, deque

from .base import BasePlugin, PluginType
from .registry import plugin_registry


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._plugin_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    def load_plugins(self, plugin_configs: Dict[str, Dict] = None) -> Dict[str, bool]:
        """
        批量加载插件
        Args:
            plugin_configs: 插件配置字典 {plugin_id: config}
        Returns:
            Dict[str, bool]: 每个插件的加载结果
        """
        if plugin_configs is None:
            plugin_configs = {}
        
        results = {}
        # 按依赖关系排序
        load_order = self._resolve_load_order(list(plugin_configs.keys()))
        
        for plugin_id in load_order:
            config = plugin_configs.get(plugin_id, {})
            plugin = plugin_registry.load_plugin(plugin_id, config)
            results[plugin_id] = plugin is not None
        
        return results
    
    def unload_plugins(self, plugin_ids: List[str] = None) -> Dict[str, bool]:
        """
        批量卸载插件
        Args:
            plugin_ids: 要卸载的插件ID列表，None表示卸载所有
        Returns:
            Dict[str, bool]: 每个插件的卸载结果
        """
        if plugin_ids is None:
            plugin_ids = list(plugin_registry._loaded_plugins.keys())
        
        results = {}
        # 按依赖关系逆序卸载
        unload_order = self._resolve_unload_order(plugin_ids)
        
        for plugin_id in unload_order:
            results[plugin_id] = plugin_registry.unload_plugin(plugin_id)
        
        return results
    
    def enable_plugins(self, plugin_ids: List[str]) -> Dict[str, bool]:
        """启用插件"""
        results = {}
        for plugin_id in plugin_ids:
            plugin = plugin_registry.get_plugin(plugin_id)
            if plugin:
                results[plugin_id] = plugin.enable()
            else:
                results[plugin_id] = False
        return results
    
    def disable_plugins(self, plugin_ids: List[str]) -> Dict[str, bool]:
        """禁用插件"""
        results = {}
        for plugin_id in plugin_ids:
            plugin = plugin_registry.get_plugin(plugin_id)
            if plugin:
                results[plugin_id] = plugin.disable()
            else:
                results[plugin_id] = False
        return results
    
    def register_event_handler(self, event_name: str, handler: Callable) -> None:
        """
        注册事件处理器
        Args:
            event_name: 事件名称
            handler: 处理器函数
        """
        self._event_handlers[event_name].append(handler)
        self.logger.debug(f"Registered event handler for {event_name}")
    
    def unregister_event_handler(self, event_name: str, handler: Callable) -> None:
        """
        注销事件处理器
        Args:
            event_name: 事件名称
            handler: 处理器函数
        """
        if event_name in self._event_handlers:
            try:
                self._event_handlers[event_name].remove(handler)
                self.logger.debug(f"Unregistered event handler for {event_name}")
            except ValueError:
                pass
    
    def emit_event(self, event_name: str, data: Any = None) -> List[Any]:
        """
        触发事件
        Args:
            event_name: 事件名称
            data: 事件数据
        Returns:
            List[Any]: 所有处理器的返回结果
        """
        results = []
        
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    result = handler(data)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Event handler error for {event_name}: {str(e)}")
        
        # 通知相关插件
        self._notify_plugins(event_name, data)
        
        return results
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        根据类型获取插件实例
        Args:
            plugin_type: 插件类型
        Returns:
            List[BasePlugin]: 插件实例列表
        """
        plugins = []
        for plugin_id, plugin in plugin_registry._loaded_plugins.items():
            if plugin.plugin_type == plugin_type:
                plugins.append(plugin)
        return plugins
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        获取插件详细信息
        Args:
            plugin_id: 插件ID
        Returns:
            Dict[str, Any]: 插件信息或None
        """
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin:
            info = plugin.get_info()
            info["dependencies"] = list(self._plugin_dependencies.get(plugin_id, set()))
            info["dependents"] = list(self._reverse_dependencies.get(plugin_id, set()))
            return info
        return None
    
    def discover_and_register_plugins(self, search_paths: List[str] = None) -> int:
        """
        发现并注册插件
        Args:
            search_paths: 搜索路径
        Returns:
            int: 发现的插件数量
        """
        count = plugin_registry.discover_plugins(search_paths)
        self.logger.info(f"Discovered {count} plugins")
        
        # 构建依赖关系图
        self._build_dependency_graph()
        
        return count
    
    def _resolve_load_order(self, plugin_ids: List[str]) -> List[str]:
        """解析加载顺序（拓扑排序）"""
        # 构建依赖图
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for plugin_id in plugin_ids:
            plugin_class = plugin_registry.get_plugin_class(plugin_id)
            if plugin_class:
                temp_plugin = plugin_class()
                deps = temp_plugin.dependencies
                for dep in deps:
                    if dep in plugin_ids:
                        graph[dep].append(plugin_id)
                        in_degree[plugin_id] += 1
        
        # 拓扑排序
        queue = deque([pid for pid in plugin_ids if in_degree[pid] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环依赖
        if len(result) != len(plugin_ids):
            self.logger.warning("Circular dependencies detected in plugin loading")
            # 返回原始顺序作为后备
            return plugin_ids
        
        return result
    
    def _resolve_unload_order(self, plugin_ids: List[str]) -> List[str]:
        """解析卸载顺序（依赖的逆序）"""
        # 构建反向依赖图
        reverse_graph = defaultdict(list)
        
        for plugin_id in plugin_ids:
            plugin_class = plugin_registry.get_plugin_class(plugin_id)
            if plugin_class:
                temp_plugin = plugin_class()
                deps = temp_plugin.dependencies
                for dep in deps:
                    if dep in plugin_ids:
                        reverse_graph[plugin_id].append(dep)
        
        # 拓扑排序（卸载顺序）
        in_degree = defaultdict(int)
        for plugin_id in plugin_ids:
            in_degree[plugin_id] = len(reverse_graph[plugin_id])
        
        queue = deque([pid for pid in plugin_ids if in_degree[pid] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for dependent in reverse_graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result
    
    def _build_dependency_graph(self) -> None:
        """构建插件依赖关系图"""
        self._plugin_dependencies.clear()
        self._reverse_dependencies.clear()
        
        for plugin_id, plugin_class in plugin_registry._plugins.items():
            try:
                temp_plugin = plugin_class()
                deps = temp_plugin.dependencies
                
                self._plugin_dependencies[plugin_id] = set(deps)
                for dep in deps:
                    self._reverse_dependencies[dep].add(plugin_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to build dependency graph for {plugin_id}: {str(e)}")
    
    def _notify_plugins(self, event_name: str, data: Any) -> None:
        """通知相关插件事件"""
        # 这里可以根据事件类型通知相应的插件
        # 例如：只通知感知层插件处理输入事件
        pass
    
    @property
    def loaded_plugins(self) -> List[str]:
        """已加载的插件ID列表"""
        return list(plugin_registry._loaded_plugins.keys())
    
    @property
    def registered_plugins(self) -> List[str]:
        """已注册的插件ID列表"""
        return list(plugin_registry._plugins.keys())


# 全局插件管理器实例
plugin_manager = PluginManager()