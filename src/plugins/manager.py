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
        # 市场集成
        self._marketplace_client = None  # 延迟初始化
        self._marketplace_plugins: Dict[str, Dict] = {}  # 市场安装的插件信息
    
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
    
    # ========== 市场集成方法 ==========
    
    def set_marketplace_client(self, client) -> None:
        """
        设置市场客户端（延迟注入，避免循环依赖）
        
        Args:
            client: MarketplaceClient 实例
        """
        self._marketplace_client = client
        self.logger.info("Marketplace client set")
    
    def install_from_marketplace(self, plugin_id: str, 
                                  version: Optional[str] = None) -> bool:
        """
        从市场安装并加载插件
        
        流程:
        1. 调用 marketplace_client.install()
        2. 从安装路径加载插件模块
        3. 注册到 PluginManager
        4. 调用 on_marketplace_install 钩子
        
        Args:
            plugin_id: 插件 ID
            version: 可选的目标版本
        
        Returns:
            bool: 安装是否成功
        """
        if not self._marketplace_client:
            self.logger.error("Marketplace client not set")
            return False
        
        try:
            # 1. 通过市场客户端安装
            result = self._marketplace_client.install(plugin_id, version=version)
            if not result.success:
                self.logger.error(f"Failed to install plugin from marketplace: {result.message}")
                return False
            
            installed_version = result.version
            install_path = result.installation.install_path if result.installation else None
            
            # 2. 尝试加载插件模块（如果有安装路径）
            plugin_loaded = False
            if install_path:
                try:
                    import importlib.util
                    import sys
                    from pathlib import Path
                    
                    install_path_obj = Path(install_path)
                    if install_path_obj.exists():
                        # 查找入口点文件
                        for py_file in install_path_obj.glob("*.py"):
                            if py_file.name.startswith("_"):
                                continue
                            
                            module_name = f"marketplace_plugins.{plugin_id}"
                            spec = importlib.util.spec_from_file_location(module_name, py_file)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = module
                                spec.loader.exec_module(module)
                                
                                # 查找 BasePlugin 子类
                                for attr_name in dir(module):
                                    attr = getattr(module, attr_name)
                                    if (isinstance(attr, type) and 
                                        hasattr(attr, '_initialize') and
                                        attr_name != 'BasePlugin'):
                                        # 将市场 ID 设置到类上
                                        attr.marketplace_id = plugin_id
                                        plugin_registry.register_plugin(attr)
                                        plugin_loaded = True
                                        break
                            if plugin_loaded:
                                break
                except Exception as e:
                    self.logger.warning(f"Failed to load plugin module: {e}")
            
            # 3. 记录市场插件信息
            self._marketplace_plugins[plugin_id] = {
                "version": installed_version,
                "install_path": install_path,
                "loaded": plugin_loaded,
                "installed_at": result.installation.installed_at.isoformat() if result.installation and result.installation.installed_at else None
            }
            
            # 4. 调用 on_marketplace_install 钩子
            plugin = plugin_registry.get_plugin_by_marketplace_id(plugin_id) if hasattr(plugin_registry, 'get_plugin_by_marketplace_id') else plugin_registry.get_plugin(plugin_id)
            if plugin and hasattr(plugin, 'on_marketplace_install'):
                try:
                    plugin.on_marketplace_install(config=None)
                except Exception as e:
                    self.logger.warning(f"on_marketplace_install hook failed: {e}")
            
            self.logger.info(f"Successfully installed plugin from marketplace: {plugin_id}@{installed_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install plugin from marketplace: {str(e)}")
            return False
    
    def uninstall_marketplace_plugin(self, plugin_id: str) -> bool:
        """
        卸载市场插件
        
        流程:
        1. 调用 on_marketplace_uninstall 钩子
        2. 从 PluginManager 注销
        3. 调用 marketplace_client.uninstall()
        
        Args:
            plugin_id: 插件 ID
        
        Returns:
            bool: 卸载是否成功
        """
        if not self._marketplace_client:
            self.logger.error("Marketplace client not set")
            return False
        
        try:
            # 1. 调用 on_marketplace_uninstall 钩子
            plugin = plugin_registry.get_plugin_by_marketplace_id(plugin_id) if hasattr(plugin_registry, 'get_plugin_by_marketplace_id') else plugin_registry.get_plugin(plugin_id)
            if plugin and hasattr(plugin, 'on_marketplace_uninstall'):
                try:
                    plugin.on_marketplace_uninstall()
                except Exception as e:
                    self.logger.warning(f"on_marketplace_uninstall hook failed: {e}")
            
            # 2. 从 PluginManager 注销
            plugin_registry.unload_plugin(plugin_id)
            plugin_registry.unregister_plugin(plugin_id)
            
            # 3. 调用 marketplace_client.uninstall()
            result = self._marketplace_client.uninstall(plugin_id)
            if not result.success:
                self.logger.warning(f"Marketplace uninstall returned failure: {result.message}")
            
            # 4. 清理市场插件记录
            if plugin_id in self._marketplace_plugins:
                del self._marketplace_plugins[plugin_id]
            
            self.logger.info(f"Successfully uninstalled marketplace plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall marketplace plugin: {str(e)}")
            return False
    
    def upgrade_marketplace_plugin(self, plugin_id: str,
                                    target_version: Optional[str] = None) -> bool:
        """
        升级市场插件
        
        流程:
        1. 记录旧版本
        2. 调用 marketplace_client.upgrade()
        3. 重新加载插件模块
        4. 调用 on_marketplace_upgrade 钩子
        
        Args:
            plugin_id: 插件 ID
            target_version: 可选的目标版本
        
        Returns:
            bool: 升级是否成功
        """
        if not self._marketplace_client:
            self.logger.error("Marketplace client not set")
            return False
        
        try:
            # 1. 记录旧版本
            old_version = None
            if plugin_id in self._marketplace_plugins:
                old_version = self._marketplace_plugins[plugin_id].get("version")
            
            if not old_version:
                # 尝试从已加载插件获取
                plugin = plugin_registry.get_plugin(plugin_id)
                if plugin:
                    old_version = plugin.version
            
            # 2. 调用 marketplace_client.upgrade()
            result = self._marketplace_client.upgrade(plugin_id, target_version=target_version)
            if not result.success:
                self.logger.error(f"Failed to upgrade plugin: {result.message}")
                return False
            
            new_version = result.version
            
            # 3. 更新市场插件记录
            if plugin_id in self._marketplace_plugins:
                self._marketplace_plugins[plugin_id]["version"] = new_version
            else:
                self._marketplace_plugins[plugin_id] = {
                    "version": new_version,
                    "install_path": result.installation.install_path if result.installation else None,
                    "loaded": True
                }
            
            # 4. 调用 on_marketplace_upgrade 钩子
            plugin = plugin_registry.get_plugin_by_marketplace_id(plugin_id) if hasattr(plugin_registry, 'get_plugin_by_marketplace_id') else plugin_registry.get_plugin(plugin_id)
            if plugin and hasattr(plugin, 'on_marketplace_upgrade'):
                try:
                    plugin.on_marketplace_upgrade(old_version or "unknown", new_version)
                except Exception as e:
                    self.logger.warning(f"on_marketplace_upgrade hook failed: {e}")
            
            self.logger.info(f"Successfully upgraded plugin: {plugin_id} from {old_version} to {new_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upgrade marketplace plugin: {str(e)}")
            return False
    
    def get_marketplace_plugins(self) -> List[Dict]:
        """
        获取所有市场安装的插件信息
        
        Returns:
            List[Dict]: 市场插件信息列表
        """
        result = []
        for plugin_id, info in self._marketplace_plugins.items():
            plugin_info = {
                "plugin_id": plugin_id,
                **info
            }
            # 补充加载状态
            plugin = plugin_registry.get_plugin(plugin_id)
            if plugin:
                plugin_info["loaded"] = True
                plugin_info["enabled"] = plugin.is_enabled
            else:
                plugin_info["loaded"] = False
                plugin_info["enabled"] = False
            
            result.append(plugin_info)
        
        return result
    
    def sync_with_marketplace(self) -> Dict[str, Any]:
        """
        同步 PluginManager 和市场的状态
        确保已安装的市场插件都已加载
        
        Returns:
            Dict: 同步结果 {"synced": int, "failed": int, "details": list}
        """
        if not self._marketplace_client:
            self.logger.warning("Marketplace client not set, skipping sync")
            return {"synced": 0, "failed": 0, "details": []}
        
        synced = 0
        failed = 0
        details = []
        
        try:
            # 获取市场已安装的插件列表
            installed = self._marketplace_client.list_installed()
            
            for installation in installed:
                plugin_id = installation.plugin_id
                version = installation.version
                
                # 检查是否已在 PluginManager 中
                if plugin_id not in self._marketplace_plugins:
                    self._marketplace_plugins[plugin_id] = {
                        "version": version,
                        "install_path": installation.install_path,
                        "loaded": False
                    }
                    details.append({"plugin_id": plugin_id, "action": "registered"})
                    synced += 1
                
                # 检查版本是否一致
                elif self._marketplace_plugins[plugin_id].get("version") != version:
                    self._marketplace_plugins[plugin_id]["version"] = version
                    details.append({"plugin_id": plugin_id, "action": "version_updated"})
                    synced += 1
            
            self.logger.info(f"Marketplace sync completed: {synced} synced, {failed} failed")
            
        except Exception as e:
            self.logger.error(f"Failed to sync with marketplace: {str(e)}")
            failed += 1
            details.append({"error": str(e)})
        
        return {"synced": synced, "failed": failed, "details": details}


# 全局插件管理器实例
plugin_manager = PluginManager()