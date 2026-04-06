"""
NecoRAG 插件市场 - 依赖解析器

构建依赖有向无环图（DAG），支持拓扑排序、冲突检测和兼容版本求解。
"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict, deque

from .models import (
    DependencyGraph, VersionConflict, PluginManifest
)
from .store import MarketplaceStore
from .version_manager import VersionManager

logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    插件依赖解析器
    
    提供依赖图构建、拓扑排序、冲突检测和兼容版本求解等功能。
    """
    
    def __init__(
        self, 
        store: MarketplaceStore, 
        version_manager: Optional[VersionManager] = None
    ):
        """
        初始化依赖解析器
        
        Args:
            store: 市场存储实例
            version_manager: 版本管理器实例（可选）
        """
        self.store = store
        self.version_mgr = version_manager or VersionManager(store)
    
    # ==================== 依赖图构建 ====================
    
    def build_dependency_graph(
        self, 
        plugin_id: str, 
        version: Optional[str] = None
    ) -> DependencyGraph:
        """
        构建完整依赖图（递归解析所有传递依赖）
        
        Args:
            plugin_id: 插件ID
            version: 指定版本（None 则使用最新版本）
            
        Returns:
            DependencyGraph: 依赖图
        """
        try:
            # 获取目标插件的 manifest
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                logger.warning(f"插件不存在: {plugin_id}")
                return DependencyGraph(
                    nodes={plugin_id: version or "unknown"},
                    edges=[],
                    install_order=[plugin_id],
                    conflicts=[f"插件 {plugin_id} 不存在"]
                )
            
            # 确定版本
            if version is None:
                version = manifest.version
            
            # 初始化解析状态
            resolved: Dict[str, str] = {plugin_id: version}
            edges: List[Tuple[str, str]] = []
            visited: Set[str] = set()
            conflicts: List[str] = []
            
            # 递归解析依赖
            path = [plugin_id]
            self._resolve_recursive(
                plugin_id, version, resolved, edges, visited, path, conflicts
            )
            
            # 执行拓扑排序确定安装顺序
            install_order = self._topological_sort(resolved, edges)
            
            # 检查循环依赖
            cycles = self._detect_cycles_in_edges(edges)
            if cycles:
                for cycle in cycles:
                    cycle_str = " -> ".join(cycle + [cycle[0]])
                    conflicts.append(f"循环依赖: {cycle_str}")
            
            return DependencyGraph(
                nodes=resolved,
                edges=edges,
                install_order=install_order,
                conflicts=conflicts
            )
            
        except Exception as e:
            logger.error(f"构建依赖图失败: {e}")
            return DependencyGraph(
                nodes={plugin_id: version or "unknown"},
                edges=[],
                install_order=[plugin_id],
                conflicts=[f"构建依赖图失败: {str(e)}"]
            )
    
    def _resolve_recursive(
        self, 
        plugin_id: str, 
        constraint: str,
        resolved: Dict[str, str], 
        edges: List[Tuple[str, str]],
        visited: Set[str],
        path: List[str],
        conflicts: List[str]
    ) -> None:
        """
        递归解析依赖
        
        Args:
            plugin_id: 当前插件ID
            constraint: 版本约束
            resolved: 已解析的依赖 {plugin_id: version}
            edges: 依赖边列表 [(from, to)]
            visited: 已访问的插件集合
            path: 当前路径（用于检测循环）
            conflicts: 冲突列表
        """
        if plugin_id in visited:
            return
        
        visited.add(plugin_id)
        
        try:
            # 获取插件信息
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                conflicts.append(f"依赖的插件 {plugin_id} 不存在")
                return
            
            # 检查版本约束
            if plugin_id in resolved:
                # 已有解析版本，检查是否兼容新约束
                existing_version = resolved[plugin_id]
                if not self.version_mgr.is_compatible(existing_version, constraint):
                    conflicts.append(
                        f"版本冲突: {plugin_id} 已解析为 {existing_version}，"
                        f"但新约束要求 {constraint}"
                    )
                    return
            else:
                # 找到满足约束的版本
                releases = self.store.get_releases(plugin_id)
                available_versions = [r.version for r in releases]
                
                if not available_versions:
                    available_versions = [manifest.version]
                
                best_version = self.version_mgr.get_latest_compatible(
                    available_versions, constraint
                )
                
                if not best_version:
                    conflicts.append(
                        f"没有满足约束 {constraint} 的版本: {plugin_id}, "
                        f"可用版本: {available_versions}"
                    )
                    resolved[plugin_id] = manifest.version  # 使用默认版本
                else:
                    resolved[plugin_id] = best_version
            
            # 获取指定版本的 manifest（如果版本不同）
            # 注意：这里简化处理，假设依赖关系在各版本间相同
            dependencies = manifest.dependencies
            
            # 递归解析子依赖
            for dep_id, dep_constraint in dependencies.items():
                # 添加边
                edges.append((plugin_id, dep_id))
                
                # 检测循环
                if dep_id in path:
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    conflicts.append(f"循环依赖: {' -> '.join(cycle)}")
                    continue
                
                # 递归解析
                path.append(dep_id)
                self._resolve_recursive(
                    dep_id, dep_constraint, resolved, edges, 
                    visited, path, conflicts
                )
                path.pop()
                
        except Exception as e:
            logger.error(f"解析依赖 {plugin_id} 失败: {e}")
            conflicts.append(f"解析 {plugin_id} 失败: {str(e)}")
    
    # ==================== 拓扑排序 ====================
    
    def resolve_install_order(self, plugin_ids: List[str]) -> List[str]:
        """
        确定多个插件的安装顺序（拓扑排序）
        
        使用 Kahn 算法：
        1. 计算每个节点的入度
        2. 将入度为 0 的节点入队
        3. 依次出队并减少相邻节点的入度
        4. 如果队列清空后仍有未处理节点，则存在循环
        
        Args:
            plugin_ids: 要安装的插件ID列表
            
        Returns:
            List[str]: 安装顺序（被依赖的在前）
        """
        try:
            # 构建所有插件的依赖关系
            all_nodes: Dict[str, str] = {}
            all_edges: List[Tuple[str, str]] = []
            
            for plugin_id in plugin_ids:
                graph = self.build_dependency_graph(plugin_id)
                all_nodes.update(graph.nodes)
                for edge in graph.edges:
                    if edge not in all_edges:
                        all_edges.append(edge)
            
            return self._topological_sort(all_nodes, all_edges)
            
        except Exception as e:
            logger.error(f"解析安装顺序失败: {e}")
            return plugin_ids
    
    def _topological_sort(
        self, 
        nodes: Dict[str, str],
        edges: List[Tuple[str, str]]
    ) -> List[str]:
        """
        Kahn 算法拓扑排序
        
        Args:
            nodes: 节点字典 {plugin_id: version}
            edges: 边列表 [(from_plugin, to_plugin)]
            
        Returns:
            List[str]: 排序后的节点列表
        """
        if not nodes:
            return []
        
        # 构建邻接表和入度表
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {node: 0 for node in nodes}
        
        for from_node, to_node in edges:
            if from_node in nodes and to_node in nodes:
                adj[from_node].append(to_node)
                in_degree[to_node] = in_degree.get(to_node, 0) + 1
        
        # 初始化队列（入度为 0 的节点）
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result: List[str] = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环
        if len(result) != len(nodes):
            remaining = set(nodes.keys()) - set(result)
            logger.warning(f"检测到循环依赖，剩余节点: {remaining}")
            # 将剩余节点按原顺序追加
            for node in nodes:
                if node not in result:
                    result.append(node)
        
        # 反转结果，使被依赖的在前
        return list(reversed(result))
    
    # ==================== 冲突检测 ====================
    
    def detect_conflicts(
        self, 
        requirements: Dict[str, str]
    ) -> List[VersionConflict]:
        """
        检测版本冲突
        
        对于每个依赖：
        1. 收集所有请求方对该依赖的版本约束
        2. 检查是否存在满足所有约束的版本
        3. 如果不存在，报告冲突
        
        Args:
            requirements: 需求字典 {plugin_id: version_constraint}
            
        Returns:
            List[VersionConflict]: 冲突列表
        """
        conflicts: List[VersionConflict] = []
        
        try:
            # 收集所有传递依赖的约束
            all_constraints = self._collect_all_constraints(requirements)
            
            # 检查每个依赖是否有冲突
            for dep_id, requesters in all_constraints.items():
                # 获取该依赖的所有可用版本
                releases = self.store.get_releases(dep_id)
                available = [r.version for r in releases]
                
                if not available:
                    manifest = self.store.get_plugin(dep_id)
                    if manifest:
                        available = [manifest.version]
                
                # 检查是否存在满足所有约束的版本
                compatible_version = self._find_version_satisfying_all(
                    available, list(requesters.values())
                )
                
                if compatible_version is None:
                    # 存在冲突
                    conflict = VersionConflict(
                        plugin_id=dep_id,
                        required_by=requesters,
                        available_versions=available,
                        message=f"没有版本同时满足所有约束: {list(requesters.values())}"
                    )
                    conflicts.append(conflict)
                    
        except Exception as e:
            logger.error(f"检测冲突失败: {e}")
        
        return conflicts
    
    def _collect_all_constraints(
        self, 
        requirements: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        收集所有传递依赖的版本约束
        
        Args:
            requirements: 初始需求 {plugin_id: version_constraint}
            
        Returns:
            Dict[str, Dict[str, str]]: {dep_plugin_id: {requester_id: constraint}}
        """
        all_constraints: Dict[str, Dict[str, str]] = defaultdict(dict)
        visited: Set[str] = set()
        
        def collect_recursive(plugin_id: str, constraint: str, requester: str):
            """递归收集约束"""
            # 记录约束
            if plugin_id != requester:
                all_constraints[plugin_id][requester] = constraint
            
            if plugin_id in visited:
                return
            visited.add(plugin_id)
            
            # 获取该插件的依赖
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                return
            
            for dep_id, dep_constraint in manifest.dependencies.items():
                collect_recursive(dep_id, dep_constraint, plugin_id)
        
        # 从顶层需求开始收集
        for plugin_id, constraint in requirements.items():
            collect_recursive(plugin_id, constraint, "root")
        
        return dict(all_constraints)
    
    def _find_version_satisfying_all(
        self, 
        versions: List[str], 
        constraints: List[str]
    ) -> Optional[str]:
        """
        找到满足所有约束的版本
        
        Args:
            versions: 可用版本列表
            constraints: 约束列表
            
        Returns:
            Optional[str]: 满足所有约束的版本，没有则返回 None
        """
        for version in self.version_mgr.sort_versions(versions, reverse=True):
            satisfies_all = True
            for constraint in constraints:
                if not self.version_mgr.is_compatible(version, constraint):
                    satisfies_all = False
                    break
            if satisfies_all:
                return version
        return None
    
    # ==================== 兼容版本求解 ====================
    
    def find_compatible_set(
        self, 
        requirements: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """
        找到满足所有约束的兼容版本组合
        
        使用回溯算法：
        1. 对每个依赖，列出所有可用版本
        2. 按版本从高到低尝试
        3. 检查是否与已选定的版本兼容
        4. 如果兼容继续，否则回溯
        
        Args:
            requirements: 需求字典 {plugin_id: version_constraint}
            
        Returns:
            Optional[Dict[str, str]]: 兼容版本组合 {plugin_id: version}，无解则返回 None
        """
        try:
            # 收集所有依赖及其约束
            all_constraints = self._collect_all_constraints(requirements)
            
            # 添加顶层依赖
            for plugin_id, constraint in requirements.items():
                if plugin_id not in all_constraints:
                    all_constraints[plugin_id] = {}
                all_constraints[plugin_id]["root"] = constraint
            
            # 获取每个依赖的可用版本
            available: Dict[str, List[str]] = {}
            for dep_id in all_constraints:
                releases = self.store.get_releases(dep_id)
                versions = [r.version for r in releases]
                if not versions:
                    manifest = self.store.get_plugin(dep_id)
                    if manifest:
                        versions = [manifest.version]
                # 按版本降序排列（优先尝试高版本）
                available[dep_id] = self.version_mgr.sort_versions(
                    versions, reverse=True
                )
            
            # 转换为列表便于回溯
            deps = list(all_constraints.keys())
            
            if not deps:
                return {}
            
            # 回溯求解
            solution: Dict[str, str] = {}
            if self._backtrack_solve(deps, available, all_constraints, solution, 0):
                return solution
            
            return None
            
        except Exception as e:
            logger.error(f"兼容版本求解失败: {e}")
            return None
    
    def _backtrack_solve(
        self, 
        deps: List[str],
        available: Dict[str, List[str]],
        constraints: Dict[str, Dict[str, str]],
        solution: Dict[str, str],
        index: int
    ) -> bool:
        """
        回溯求解
        
        Args:
            deps: 依赖列表
            available: 每个依赖的可用版本
            constraints: 约束字典
            solution: 当前解
            index: 当前处理的依赖索引
            
        Returns:
            bool: 是否找到解
        """
        # 所有依赖都已解决
        if index >= len(deps):
            return True
        
        dep_id = deps[index]
        versions = available.get(dep_id, [])
        
        if not versions:
            logger.warning(f"依赖 {dep_id} 没有可用版本")
            return False
        
        # 尝试每个版本
        for version in versions:
            # 检查是否满足所有约束
            if self._is_version_valid(dep_id, version, constraints, solution):
                solution[dep_id] = version
                
                # 递归处理下一个依赖
                if self._backtrack_solve(
                    deps, available, constraints, solution, index + 1
                ):
                    return True
                
                # 回溯
                del solution[dep_id]
        
        return False
    
    def _is_version_valid(
        self, 
        plugin_id: str, 
        version: str,
        constraints: Dict[str, Dict[str, str]],
        solution: Dict[str, str]
    ) -> bool:
        """
        检查版本是否满足所有约束
        
        Args:
            plugin_id: 插件ID
            version: 候选版本
            constraints: 约束字典
            solution: 当前已解决的依赖
            
        Returns:
            bool: 是否有效
        """
        # 检查该依赖的所有约束
        dep_constraints = constraints.get(plugin_id, {})
        
        for requester, constraint in dep_constraints.items():
            # 如果请求方还没解决，跳过（后续会处理）
            if requester != "root" and requester not in solution:
                continue
            
            # 检查版本约束
            if not self.version_mgr.is_compatible(version, constraint):
                return False
        
        return True
    
    # ==================== 循环依赖检测 ====================
    
    def detect_cycles(self, graph: DependencyGraph) -> List[List[str]]:
        """
        使用 DFS 检测循环依赖
        
        Args:
            graph: 依赖图
            
        Returns:
            List[List[str]]: 所有发现的环路
        """
        return self._detect_cycles_in_edges(graph.edges)
    
    def _detect_cycles_in_edges(
        self, 
        edges: List[Tuple[str, str]]
    ) -> List[List[str]]:
        """
        在边列表中检测循环
        
        Args:
            edges: 边列表
            
        Returns:
            List[List[str]]: 环路列表
        """
        # 构建邻接表
        adj: Dict[str, List[str]] = defaultdict(list)
        nodes: Set[str] = set()
        
        for from_node, to_node in edges:
            adj[from_node].append(to_node)
            nodes.add(from_node)
            nodes.add(to_node)
        
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        for node in nodes:
            if node not in visited:
                path: List[str] = []
                self._dfs_cycles(node, adj, visited, rec_stack, path, cycles)
        
        return cycles
    
    def _dfs_cycles(
        self, 
        node: str, 
        adj: Dict[str, List[str]],
        visited: Set[str], 
        rec_stack: Set[str],
        path: List[str], 
        cycles: List[List[str]]
    ) -> None:
        """
        DFS 辅助函数检测循环
        
        Args:
            node: 当前节点
            adj: 邻接表
            visited: 已访问节点集合
            rec_stack: 递归栈（用于检测环）
            path: 当前路径
            cycles: 发现的环路列表
        """
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                self._dfs_cycles(
                    neighbor, adj, visited, rec_stack, path, cycles
                )
            elif neighbor in rec_stack:
                # 发现环
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:]
                # 避免重复记录相同的环
                normalized = self._normalize_cycle(cycle)
                if normalized not in [self._normalize_cycle(c) for c in cycles]:
                    cycles.append(cycle.copy())
        
        path.pop()
        rec_stack.remove(node)
    
    def _normalize_cycle(self, cycle: List[str]) -> Tuple[str, ...]:
        """
        规范化环路（使相同的环有相同的表示）
        
        Args:
            cycle: 环路
            
        Returns:
            Tuple[str, ...]: 规范化后的环路
        """
        if not cycle:
            return tuple()
        # 找到最小元素开始的位置
        min_idx = cycle.index(min(cycle))
        normalized = cycle[min_idx:] + cycle[:min_idx]
        return tuple(normalized)
    
    # ==================== 反向依赖 ====================
    
    def get_reverse_dependencies(self, plugin_id: str) -> List[str]:
        """
        获取依赖于指定插件的所有插件（反向依赖）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[str]: 依赖此插件的插件ID列表
        """
        dependents: List[str] = []
        
        try:
            # 获取所有已安装的插件
            installations = self.store.list_installations()
            
            for installation in installations:
                manifest = self.store.get_plugin(installation.plugin_id)
                if manifest and plugin_id in manifest.dependencies:
                    dependents.append(installation.plugin_id)
            
            # 也检查所有注册的插件
            plugins, _ = self.store.list_plugins(page_size=1000)
            for plugin in plugins:
                if plugin.plugin_id not in dependents:
                    if plugin_id in plugin.dependencies:
                        dependents.append(plugin.plugin_id)
                        
        except Exception as e:
            logger.error(f"获取反向依赖失败: {e}")
        
        return dependents
    
    def check_safe_to_uninstall(
        self, 
        plugin_id: str
    ) -> Tuple[bool, List[str]]:
        """
        检查是否可以安全卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Tuple[bool, List[str]]: (是否安全, 依赖此插件的已安装插件列表)
        """
        try:
            # 获取已安装的反向依赖
            installations = self.store.list_installations()
            installed_ids = {inst.plugin_id for inst in installations}
            
            # 获取所有依赖此插件的插件
            dependents = self.get_reverse_dependencies(plugin_id)
            
            # 过滤出已安装的
            installed_dependents = [
                dep for dep in dependents if dep in installed_ids
            ]
            
            is_safe = len(installed_dependents) == 0
            return is_safe, installed_dependents
            
        except Exception as e:
            logger.error(f"检查卸载安全性失败: {e}")
            return False, []
    
    def get_all_dependents_recursive(self, plugin_id: str) -> Set[str]:
        """
        递归获取所有直接和间接依赖此插件的插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Set[str]: 所有依赖者的集合
        """
        all_dependents: Set[str] = set()
        
        def collect_recursive(pid: str):
            dependents = self.get_reverse_dependencies(pid)
            for dep in dependents:
                if dep not in all_dependents:
                    all_dependents.add(dep)
                    collect_recursive(dep)
        
        collect_recursive(plugin_id)
        return all_dependents
    
    # ==================== 依赖树可视化 ====================
    
    def format_dependency_tree(
        self, 
        plugin_id: str, 
        version: Optional[str] = None,
        indent: int = 0
    ) -> str:
        """
        格式化依赖树为字符串（用于 CLI 显示）
        
        Args:
            plugin_id: 插件ID
            version: 版本（可选）
            indent: 缩进级别
            
        Returns:
            str: 格式化的依赖树字符串
        """
        try:
            lines: List[str] = []
            visited: Set[str] = set()
            
            self._format_tree_recursive(
                plugin_id, version, indent, lines, visited, is_last=True
            )
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"格式化依赖树失败: {e}")
            return f"{plugin_id}@{version or 'unknown'} (格式化失败)"
    
    def _format_tree_recursive(
        self, 
        plugin_id: str, 
        version: Optional[str],
        level: int, 
        lines: List[str], 
        visited: Set[str],
        is_last: bool = True,
        prefix: str = ""
    ) -> None:
        """
        递归格式化依赖树
        
        Args:
            plugin_id: 插件ID
            version: 版本
            level: 当前层级
            lines: 输出行列表
            visited: 已访问节点
            is_last: 是否为当前级别的最后一个节点
            prefix: 当前前缀
        """
        # 构建当前行
        if level == 0:
            connector = ""
            new_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            new_prefix = prefix + ("    " if is_last else "│   ")
        
        # 获取版本信息
        if version is None:
            manifest = self.store.get_plugin(plugin_id)
            version = manifest.version if manifest else "?"
        
        # 检查循环
        if plugin_id in visited:
            lines.append(f"{prefix}{connector}{plugin_id}@{version} (循环引用)")
            return
        
        visited.add(plugin_id)
        lines.append(f"{prefix}{connector}{plugin_id}@{version}")
        
        # 获取依赖
        manifest = self.store.get_plugin(plugin_id)
        if not manifest or not manifest.dependencies:
            return
        
        deps = list(manifest.dependencies.items())
        for i, (dep_id, constraint) in enumerate(deps):
            is_last_dep = (i == len(deps) - 1)
            
            # 解析满足约束的版本
            releases = self.store.get_releases(dep_id)
            available = [r.version for r in releases]
            dep_version = self.version_mgr.get_latest_compatible(
                available, constraint
            ) if available else None
            
            self._format_tree_recursive(
                dep_id, 
                dep_version, 
                level + 1, 
                lines, 
                visited.copy(),  # 使用副本以正确处理菱形依赖
                is_last_dep,
                new_prefix
            )
    
    # ==================== 辅助方法 ====================
    
    def get_dependency_depth(self, plugin_id: str) -> int:
        """
        获取依赖树的最大深度
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            int: 最大深度
        """
        def get_depth_recursive(pid: str, visited: Set[str]) -> int:
            if pid in visited:
                return 0
            visited.add(pid)
            
            manifest = self.store.get_plugin(pid)
            if not manifest or not manifest.dependencies:
                return 0
            
            max_child_depth = 0
            for dep_id in manifest.dependencies:
                depth = get_depth_recursive(dep_id, visited)
                max_child_depth = max(max_child_depth, depth)
            
            return max_child_depth + 1
        
        try:
            return get_depth_recursive(plugin_id, set())
        except Exception as e:
            logger.error(f"获取依赖深度失败: {e}")
            return 0
    
    def get_total_dependencies_count(self, plugin_id: str) -> int:
        """
        获取所有依赖（包括传递依赖）的总数
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            int: 依赖总数
        """
        try:
            graph = self.build_dependency_graph(plugin_id)
            # 排除自身
            return len(graph.nodes) - 1
        except Exception as e:
            logger.error(f"获取依赖总数失败: {e}")
            return 0
    
    def check_compatibility_matrix(
        self, 
        plugins: List[str]
    ) -> Dict[str, Dict[str, bool]]:
        """
        检查多个插件之间的兼容性矩阵
        
        Args:
            plugins: 插件ID列表
            
        Returns:
            Dict[str, Dict[str, bool]]: 兼容性矩阵 {plugin_a: {plugin_b: compatible}}
        """
        matrix: Dict[str, Dict[str, bool]] = {}
        
        for plugin_a in plugins:
            matrix[plugin_a] = {}
            for plugin_b in plugins:
                if plugin_a == plugin_b:
                    matrix[plugin_a][plugin_b] = True
                else:
                    # 检查两个插件是否可以同时安装
                    compatible = self._check_pair_compatibility(plugin_a, plugin_b)
                    matrix[plugin_a][plugin_b] = compatible
        
        return matrix
    
    def _check_pair_compatibility(self, plugin_a: str, plugin_b: str) -> bool:
        """
        检查两个插件是否兼容（可以同时安装）
        
        Args:
            plugin_a: 插件A
            plugin_b: 插件B
            
        Returns:
            bool: 是否兼容
        """
        try:
            manifest_a = self.store.get_plugin(plugin_a)
            manifest_b = self.store.get_plugin(plugin_b)
            
            if not manifest_a or not manifest_b:
                return False
            
            # 尝试找到兼容的版本组合
            requirements = {
                plugin_a: f"=={manifest_a.version}",
                plugin_b: f"=={manifest_b.version}"
            }
            
            conflicts = self.detect_conflicts(requirements)
            return len(conflicts) == 0
            
        except Exception as e:
            logger.error(f"检查兼容性失败: {e}")
            return False
