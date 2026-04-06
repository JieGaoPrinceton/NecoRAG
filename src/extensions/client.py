"""
NecoRAG 插件市场 - 统一入口客户端

MarketplaceClient 是插件市场的统一入口，组合所有子系统提供简洁的高级 API。
类似于 NecoRAG 主类的设计模式，对外提供一站式的插件管理能力。

用法:
    from src.marketplace import MarketplaceClient, MarketplaceConfig
    
    config = MarketplaceConfig()
    client = MarketplaceClient(config)
    
    # 搜索插件
    results = client.search("pdf parser")
    
    # 安装插件
    result = client.install("necorag-perception-pdf")
    
    # 查看推荐
    recommendations = client.get_recommendations()
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    PluginManifest, PluginRelease, PluginRating, PluginInstallation,
    GDIScore, SearchResult, InstallResult, SyncResult, UpgradePath,
    DependencyGraph, CanaryDeployment, PluginType, PluginCategory,
    SortStrategy, PluginPermission, InstallStatus, PermissionLevel
)
from .config import MarketplaceConfig
from .store import MarketplaceStore
from .version_manager import VersionManager
from .dependency_resolver import DependencyResolver
from .installer import PluginInstaller
from .discovery import DiscoveryEngine
from .quality import GDIAssessor
from .sandbox import PluginSandbox, ValidationResult
from .repository import RepositoryManager, LocalRepository

logger = logging.getLogger(__name__)


class MarketplaceClient:
    """
    插件市场统一入口客户端
    
    组合所有子系统:
    - Store: 数据持久化
    - VersionManager: 版本管理
    - DependencyResolver: 依赖解析
    - PluginInstaller: 安装/卸载/升级
    - DiscoveryEngine: 搜索/推荐
    - GDIAssessor: 质量评估
    - PluginSandbox: 安全沙箱
    - RepositoryManager: 仓库管理
    """
    
    def __init__(self, config: Optional[MarketplaceConfig] = None):
        """
        初始化市场客户端
        
        1. 加载或使用默认配置
        2. 确保所有必要目录存在
        3. 初始化所有子系统（按依赖顺序）
        4. 记录初始化日志
        """
        self.config = config or MarketplaceConfig()
        self.config.ensure_directories()
        
        # 初始化子系统（按依赖顺序）
        self.store = MarketplaceStore(self.config.db_path)
        self.version_manager = VersionManager(self.store)
        self.dependency_resolver = DependencyResolver(self.store, self.version_manager)
        self.sandbox = PluginSandbox(
            enabled=self.config.sandbox_enabled,
            default_level=self.config.default_permission_level,
            default_quota=self.config.default_resource_quota
        )
        self.installer = PluginInstaller(
            store=self.store,
            version_manager=self.version_manager,
            dependency_resolver=self.dependency_resolver,
            sandbox=self.sandbox,
            plugins_dir=self.config.plugins_dir,
            cache_dir=self.config.cache_dir
        )
        self.discovery = DiscoveryEngine(
            store=self.store,
            page_size=self.config.search_page_size
        )
        self.quality = GDIAssessor(
            store=self.store,
            weights=self.config.gdi_weights
        )
        self.repository = RepositoryManager(
            store=self.store
        )
        
        self._initialized = True
        logger.info("插件市场客户端初始化完成")
    
    # ========================================
    # 搜索和发现
    # ========================================
    
    def search(self, query: str = "",
               category: Optional[str] = None,
               plugin_type: Optional[str] = None,
               sort_by: str = "relevance",
               tags: Optional[List[str]] = None,
               min_rating: Optional[float] = None,
               page: int = 1,
               page_size: Optional[int] = None) -> SearchResult:
        """
        搜索插件
        
        Args:
            query: 搜索关键词
            category: 分类过滤 ("official", "certified", "community")
            plugin_type: 类型过滤 ("perception", "memory", "retrieval", "refinement", "response", "utility")
            sort_by: 排序方式 ("relevance", "gdi_score", "rating", "trending", "downloads", "newest", "name")
            tags: 标签过滤
            min_rating: 最低评分过滤
            page: 页码
            page_size: 每页大小
        
        Returns:
            SearchResult 包含匹配的插件列表和分页信息
        """
        try:
            category_enum = self._to_category_enum(category)
            type_enum = self._to_type_enum(plugin_type)
            sort_enum = self._to_sort_enum(sort_by)
            
            return self.discovery.search(
                query=query,
                category=category_enum,
                plugin_type=type_enum,
                sort_by=sort_enum,
                tags=tags,
                min_rating=min_rating,
                page=page,
                page_size=page_size
            )
        except Exception as e:
            logger.error(f"搜索插件失败: {e}")
            return SearchResult(
                plugins=[],
                total_count=0,
                page=page,
                page_size=page_size or self.config.search_page_size,
                query=query
            )
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        获取插件详细信息
        
        聚合返回：
        - manifest: 插件基本信息
        - releases: 版本列表
        - installation: 安装状态（如果已安装）
        - gdi_score: GDI 评分
        - rating: 平均评分和评分数
        - dependencies: 依赖图
        """
        try:
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                return None
            
            releases = self.store.get_releases(plugin_id)
            installation = self.store.get_installation(plugin_id)
            gdi_score = self.store.get_gdi_score(plugin_id)
            avg_rating, rating_count = self.store.get_average_rating(plugin_id)
            
            # 构建依赖图
            dep_graph = self.dependency_resolver.build_dependency_graph(plugin_id)
            
            return {
                'manifest': manifest.to_dict(),
                'releases': [r.to_dict() for r in releases],
                'installation': installation.to_dict() if installation else None,
                'gdi_score': gdi_score.to_dict() if gdi_score else None,
                'rating': {
                    'average': avg_rating,
                    'count': rating_count
                },
                'dependencies': dep_graph.to_dict()
            }
        except Exception as e:
            logger.error(f"获取插件信息失败 {plugin_id}: {e}")
            return None
    
    def get_plugin_versions(self, plugin_id: str) -> List[PluginRelease]:
        """获取插件所有版本"""
        try:
            return self.store.get_releases(plugin_id)
        except Exception as e:
            logger.error(f"获取插件版本失败 {plugin_id}: {e}")
            return []
    
    def get_recommendations(self, limit: int = 10) -> List[PluginManifest]:
        """
        获取推荐插件（基于已安装插件）
        """
        try:
            # 获取已安装插件 ID
            installations = self.store.list_installations()
            installed_ids = [inst.plugin_id for inst in installations]
            
            return self.discovery.recommend(
                installed_plugin_ids=installed_ids,
                limit=limit
            )
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []
    
    def get_trending(self, time_window: str = "weekly",
                     limit: int = 20) -> List[PluginManifest]:
        """获取热门趋势插件"""
        try:
            return self.discovery.get_trending(
                time_window=time_window,
                limit=limit
            )
        except Exception as e:
            logger.error(f"获取趋势插件失败: {e}")
            return []
    
    def get_categories(self) -> List[Dict]:
        """获取分类概览"""
        try:
            return self.discovery.get_categories_overview()
        except Exception as e:
            logger.error(f"获取分类概览失败: {e}")
            return []
    
    def get_popular_tags(self, limit: int = 30) -> List[Dict]:
        """获取热门标签"""
        try:
            tags = self.discovery.get_popular_tags(limit=limit)
            return [{"tag": tag, "count": count} for tag, count in tags]
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return []
    
    def find_similar(self, plugin_id: str, limit: int = 5) -> List[PluginManifest]:
        """查找相似插件"""
        try:
            return self.discovery.find_similar(plugin_id, limit=limit)
        except Exception as e:
            logger.error(f"查找相似插件失败: {e}")
            return []
    
    # ========================================
    # 安装管理
    # ========================================
    
    def install(self, plugin_id: str, version: Optional[str] = None,
                force: bool = False) -> InstallResult:
        """
        安装插件
        
        完整流程封装：权限检查 -> 依赖解析 -> 下载 -> 安装 -> 刷新GDI
        """
        try:
            result = self.installer.install(
                plugin_id=plugin_id,
                version=version,
                force=force
            )
            
            # 安装成功后刷新 GDI
            if result.success:
                self.quality.calculate_gdi(plugin_id)
                logger.info(f"安装插件成功: {plugin_id}@{result.version}")
            
            return result
        except Exception as e:
            logger.error(f"安装插件失败 {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=version or "unknown",
                message=f"安装失败: {str(e)}",
                errors=[str(e)]
            )
    
    def uninstall(self, plugin_id: str, force: bool = False) -> InstallResult:
        """卸载插件"""
        try:
            result = self.installer.uninstall(plugin_id=plugin_id, force=force)
            if result.success:
                logger.info(f"卸载插件成功: {plugin_id}")
            return result
        except Exception as e:
            logger.error(f"卸载插件失败 {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version="unknown",
                message=f"卸载失败: {str(e)}",
                errors=[str(e)]
            )
    
    def upgrade(self, plugin_id: str, 
                target_version: Optional[str] = None) -> InstallResult:
        """升级插件"""
        try:
            result = self.installer.upgrade(
                plugin_id=plugin_id,
                target_version=target_version
            )
            
            # 升级成功后刷新 GDI
            if result.success:
                self.quality.calculate_gdi(plugin_id)
                logger.info(f"升级插件成功: {plugin_id}@{result.version}")
            
            return result
        except Exception as e:
            logger.error(f"升级插件失败 {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=target_version or "unknown",
                message=f"升级失败: {str(e)}",
                errors=[str(e)]
            )
    
    def upgrade_all(self) -> List[InstallResult]:
        """升级所有已安装插件"""
        try:
            results = self.installer.upgrade_all()
            
            # 刷新升级成功的插件的 GDI
            for result in results:
                if result.success:
                    self.quality.calculate_gdi(result.plugin_id)
            
            return results
        except Exception as e:
            logger.error(f"批量升级失败: {e}")
            return [InstallResult(
                success=False,
                plugin_id="upgrade_all",
                version="unknown",
                message=f"批量升级失败: {str(e)}",
                errors=[str(e)]
            )]
    
    def rollback(self, plugin_id: str, to_version: str) -> InstallResult:
        """回滚到指定版本"""
        try:
            result = self.installer.rollback(plugin_id=plugin_id, to_version=to_version)
            if result.success:
                logger.info(f"回滚插件成功: {plugin_id}@{to_version}")
            return result
        except Exception as e:
            logger.error(f"回滚插件失败 {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=to_version,
                message=f"回滚失败: {str(e)}",
                errors=[str(e)]
            )
    
    def check_updates(self) -> List[Dict]:
        """检查可用更新"""
        try:
            return self.installer.check_updates()
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return []
    
    def list_installed(self, status: Optional[str] = None) -> List[PluginInstallation]:
        """
        列出已安装插件
        status: "active", "disabled", "failed", "outdated" 或 None (全部)
        """
        try:
            status_enum = None
            if status:
                try:
                    status_enum = InstallStatus(status)
                except ValueError:
                    logger.warning(f"无效的状态值: {status}")
            
            return self.store.list_installations(status=status_enum)
        except Exception as e:
            logger.error(f"列出已安装插件失败: {e}")
            return []
    
    def get_install_info(self, plugin_id: str) -> Optional[PluginInstallation]:
        """获取插件安装信息"""
        try:
            return self.store.get_installation(plugin_id)
        except Exception as e:
            logger.error(f"获取安装信息失败 {plugin_id}: {e}")
            return None
    
    # ========================================
    # 评分和评价
    # ========================================
    
    def rate(self, plugin_id: str, score: float, 
             comment: str = "",
             user_id: str = "default",
             dimensions: Optional[Dict[str, float]] = None) -> Optional[PluginRating]:
        """
        为插件评分
        
        1. 验证评分范围 (1.0-5.0)
        2. 保存评分
        3. 触发 GDI 重新计算
        """
        try:
            # 验证评分范围
            if score < 1.0 or score > 5.0:
                logger.warning(f"评分 {score} 超出有效范围 [1.0, 5.0]")
                score = max(1.0, min(5.0, score))
            
            rating = PluginRating(
                plugin_id=plugin_id,
                user_id=user_id,
                score=score,
                comment=comment,
                dimensions=dimensions or {}
            )
            
            if self.store.add_rating(rating):
                # 重新计算 GDI
                self.quality.calculate_gdi(plugin_id)
                logger.info(f"为插件 {plugin_id} 评分: {score}")
                return rating
            
            return None
        except Exception as e:
            logger.error(f"评分失败 {plugin_id}: {e}")
            return None
    
    def get_ratings(self, plugin_id: str, page: int = 1,
                    page_size: int = 20) -> Dict:
        """
        获取插件评分
        返回: {"ratings": list, "total": int, "average": float, "count": int}
        """
        try:
            ratings, total = self.store.get_ratings(plugin_id, page=page, page_size=page_size)
            avg_rating, rating_count = self.store.get_average_rating(plugin_id)
            
            return {
                "ratings": [r.to_dict() for r in ratings],
                "total": total,
                "average": avg_rating,
                "count": rating_count
            }
        except Exception as e:
            logger.error(f"获取评分失败 {plugin_id}: {e}")
            return {"ratings": [], "total": 0, "average": 0.0, "count": 0}
    
    # ========================================
    # 质量评估 (GDI)
    # ========================================
    
    def get_gdi_score(self, plugin_id: str) -> Optional[GDIScore]:
        """获取插件 GDI 评分"""
        try:
            return self.store.get_gdi_score(plugin_id)
        except Exception as e:
            logger.error(f"获取 GDI 评分失败 {plugin_id}: {e}")
            return None
    
    def refresh_gdi(self, plugin_id: Optional[str] = None) -> Dict:
        """
        刷新 GDI 评分
        plugin_id=None 时刷新所有插件
        返回: {"refreshed": int, "scores": dict}
        """
        try:
            if plugin_id:
                score = self.quality.calculate_gdi(plugin_id)
                return {
                    "refreshed": 1 if score else 0,
                    "scores": {plugin_id: score.to_dict()} if score else {}
                }
            else:
                scores = self.quality.refresh_all_scores()
                return {
                    "refreshed": len(scores),
                    "scores": {pid: s.to_dict() for pid, s in scores.items()}
                }
        except Exception as e:
            logger.error(f"刷新 GDI 评分失败: {e}")
            return {"refreshed": 0, "scores": {}}
    
    def get_leaderboard(self, dimension: Optional[str] = None,
                        limit: int = 50) -> List[GDIScore]:
        """获取 GDI 排行榜"""
        try:
            return self.quality.get_leaderboard(dimension=dimension, limit=limit)
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}")
            return []
    
    # ========================================
    # 仓库管理
    # ========================================
    
    def add_repository(self, name: str, url: str, repo_type: str,
                       priority: int = 0, config: Optional[Dict] = None) -> bool:
        """添加仓库源"""
        try:
            return self.repository.add_source(
                name=name,
                url=url,
                repo_type=repo_type,
                priority=priority,
                config=config
            )
        except Exception as e:
            logger.error(f"添加仓库失败 {name}: {e}")
            return False
    
    def remove_repository(self, name: str) -> bool:
        """移除仓库源"""
        try:
            return self.repository.remove_source(name)
        except Exception as e:
            logger.error(f"移除仓库失败 {name}: {e}")
            return False
    
    def list_repositories(self) -> List[Dict]:
        """列出所有仓库源"""
        try:
            return self.repository.list_sources()
        except Exception as e:
            logger.error(f"列出仓库失败: {e}")
            return []
    
    def sync_repositories(self, source_name: Optional[str] = None) -> List[SyncResult]:
        """
        同步仓库
        source_name=None 时同步所有源
        """
        try:
            if source_name:
                result = self.repository.sync_source(source_name)
                return [result]
            else:
                return self.repository.sync_all()
        except Exception as e:
            logger.error(f"同步仓库失败: {e}")
            return [SyncResult(
                success=False,
                source_name=source_name or "all",
                errors=[str(e)]
            )]
    
    # ========================================
    # 版本和依赖
    # ========================================
    
    def check_compatibility(self, plugin_id: str, 
                            version: str) -> Dict:
        """
        检查插件版本兼容性
        返回: {"compatible": bool, "necorag_compatible": bool, "dep_conflicts": list}
        """
        try:
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                return {
                    "compatible": False,
                    "necorag_compatible": False,
                    "dep_conflicts": ["插件不存在"]
                }
            
            # 检查 NecoRAG 兼容性
            # 假设当前 NecoRAG 版本为 0.1.0
            necorag_version = "0.1.0"
            necorag_compatible = self.version_manager.check_necorag_compatibility(
                manifest, necorag_version
            )
            
            # 检查依赖冲突
            requirements = {plugin_id: version}
            conflicts = self.dependency_resolver.detect_conflicts(requirements)
            conflict_msgs = [c.message for c in conflicts]
            
            return {
                "compatible": necorag_compatible and len(conflicts) == 0,
                "necorag_compatible": necorag_compatible,
                "dep_conflicts": conflict_msgs
            }
        except Exception as e:
            logger.error(f"检查兼容性失败 {plugin_id}: {e}")
            return {
                "compatible": False,
                "necorag_compatible": False,
                "dep_conflicts": [str(e)]
            }
    
    def get_dependency_tree(self, plugin_id: str,
                            version: Optional[str] = None) -> Dict:
        """
        获取依赖树
        返回: {"graph": DependencyGraph, "tree_text": str}
        """
        try:
            graph = self.dependency_resolver.build_dependency_graph(plugin_id, version)
            tree_text = self.dependency_resolver.format_dependency_tree(plugin_id, version)
            
            return {
                "graph": graph.to_dict(),
                "tree_text": tree_text
            }
        except Exception as e:
            logger.error(f"获取依赖树失败 {plugin_id}: {e}")
            return {
                "graph": DependencyGraph(
                    nodes={plugin_id: version or "unknown"},
                    edges=[],
                    install_order=[plugin_id],
                    conflicts=[str(e)]
                ).to_dict(),
                "tree_text": f"{plugin_id}@{version or 'unknown'} (获取失败)"
            }
    
    def plan_upgrade_path(self, plugin_id: str,
                          target_version: Optional[str] = None) -> Optional[UpgradePath]:
        """获取升级路径"""
        try:
            installation = self.store.get_installation(plugin_id)
            if not installation:
                logger.warning(f"插件 {plugin_id} 未安装")
                return None
            
            return self.version_manager.plan_upgrade(
                plugin_id=plugin_id,
                current_version=installation.version,
                target_version=target_version
            )
        except Exception as e:
            logger.error(f"规划升级路径失败 {plugin_id}: {e}")
            return None
    
    # ========================================
    # 灰度部署
    # ========================================
    
    def create_canary_deployment(self, plugin_id: str, new_version: str,
                                  percentage: float = 0.1) -> Optional[CanaryDeployment]:
        """创建灰度部署"""
        try:
            installation = self.store.get_installation(plugin_id)
            if not installation:
                logger.warning(f"插件 {plugin_id} 未安装，无法创建灰度部署")
                return None
            
            return self.version_manager.create_canary(
                plugin_id=plugin_id,
                current_version=installation.version,
                new_version=new_version,
                percentage=percentage
            )
        except Exception as e:
            logger.error(f"创建灰度部署失败 {plugin_id}: {e}")
            return None
    
    def evaluate_canary(self, deployment_id: str) -> Dict:
        """评估灰度部署"""
        try:
            return self.version_manager.evaluate_canary(deployment_id)
        except Exception as e:
            logger.error(f"评估灰度部署失败 {deployment_id}: {e}")
            return {
                "action": "continue",
                "reason": f"评估出错: {str(e)}",
                "metrics": {}
            }
    
    def promote_canary(self, deployment_id: str) -> bool:
        """推广灰度部署"""
        try:
            return self.version_manager.promote_canary(deployment_id)
        except Exception as e:
            logger.error(f"推广灰度部署失败 {deployment_id}: {e}")
            return False
    
    def rollback_canary(self, deployment_id: str) -> bool:
        """回滚灰度部署"""
        try:
            return self.version_manager.rollback_canary(deployment_id)
        except Exception as e:
            logger.error(f"回滚灰度部署失败 {deployment_id}: {e}")
            return False
    
    # ========================================
    # 安全
    # ========================================
    
    def validate_plugin_permissions(self, plugin_id: str) -> Optional[ValidationResult]:
        """验证插件权限"""
        try:
            manifest = self.store.get_plugin(plugin_id)
            if not manifest:
                return None
            
            return self.sandbox.validate_permissions(manifest)
        except Exception as e:
            logger.error(f"验证插件权限失败 {plugin_id}: {e}")
            return None
    
    def get_security_report(self) -> Dict:
        """获取安全报告"""
        try:
            return self.sandbox.get_security_report()
        except Exception as e:
            logger.error(f"获取安全报告失败: {e}")
            return {"error": str(e)}
    
    def set_plugin_permission_level(self, plugin_id: str, level: str) -> bool:
        """设置插件权限级别"""
        try:
            try:
                level_enum = PermissionLevel(level)
            except ValueError:
                logger.warning(f"无效的权限级别: {level}")
                return False
            
            return self.sandbox.set_permission_level(plugin_id, level_enum)
        except Exception as e:
            logger.error(f"设置权限级别失败 {plugin_id}: {e}")
            return False
    
    # ========================================
    # 统计和管理
    # ========================================
    
    def get_marketplace_stats(self) -> Dict:
        """
        获取市场总体统计
        聚合: store 统计 + 仓库统计 + 安装统计 + GDI 分布
        """
        try:
            store_stats = self.store.get_statistics()
            repo_stats = self.repository.get_statistics()
            gdi_distribution = self.quality.get_score_distribution()
            
            return {
                "plugins": {
                    "total": store_stats.get("total_plugins", 0),
                    "by_type": store_stats.get("plugins_by_type", {}),
                    "by_category": store_stats.get("plugins_by_category", {})
                },
                "releases": {
                    "total": store_stats.get("total_releases", 0)
                },
                "installations": {
                    "total": store_stats.get("total_installations", 0),
                    "active": store_stats.get("active_installations", 0)
                },
                "ratings": {
                    "total": store_stats.get("total_ratings", 0)
                },
                "repositories": {
                    "total": repo_stats.get("total_sources", 0),
                    "available": repo_stats.get("available_sources", 0),
                    "local": repo_stats.get("local_sources", 0),
                    "remote": repo_stats.get("remote_sources", 0)
                },
                "gdi_distribution": gdi_distribution
            }
        except Exception as e:
            logger.error(f"获取市场统计失败: {e}")
            return {}
    
    def publish_plugin(self, manifest: PluginManifest,
                       package_path: Optional[str] = None) -> bool:
        """
        发布插件到市场
        1. 注册插件元数据到 store
        2. 创建版本发布记录
        3. 如果有 package_path，发布到本地仓库
        4. 计算初始 GDI 评分
        """
        try:
            # 验证 manifest
            if not manifest.validate():
                logger.warning("插件清单验证失败")
                return False
            
            # 注册到 store
            existing = self.store.get_plugin(manifest.plugin_id)
            if existing:
                if not self.store.update_plugin(manifest):
                    return False
            else:
                if not self.store.add_plugin(manifest):
                    return False
            
            # 创建版本发布记录
            release = PluginRelease(
                plugin_id=manifest.plugin_id,
                version=manifest.version,
                download_url=package_path or "",
                changelog="Initial release",
                published_at=datetime.now()
            )
            self.store.add_release(release)
            
            # 发布到本地仓库（如果有包）
            if package_path:
                pkg_path = Path(package_path)
                if pkg_path.exists():
                    self.repository.publish_to_local(manifest, pkg_path)
            
            # 计算初始 GDI
            self.quality.calculate_gdi(manifest.plugin_id)
            
            logger.info(f"发布插件成功: {manifest.plugin_id}@{manifest.version}")
            return True
            
        except Exception as e:
            logger.error(f"发布插件失败 {manifest.plugin_id}: {e}")
            return False
    
    def register_plugin(self, manifest: PluginManifest) -> bool:
        """仅注册插件元数据（不安装）"""
        try:
            if not manifest.validate():
                logger.warning("插件清单验证失败")
                return False
            
            existing = self.store.get_plugin(manifest.plugin_id)
            if existing:
                return self.store.update_plugin(manifest)
            else:
                return self.store.add_plugin(manifest)
        except Exception as e:
            logger.error(f"注册插件失败 {manifest.plugin_id}: {e}")
            return False
    
    def clear_cache(self) -> Dict:
        """清理缓存"""
        try:
            cleared_bytes = self.installer.clear_cache()
            return {
                "cleared_bytes": cleared_bytes,
                "cleared_mb": round(cleared_bytes / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return {"cleared_bytes": 0, "cleared_mb": 0.0}
    
    # ========================================
    # 生命周期
    # ========================================
    
    def close(self):
        """关闭客户端，释放资源"""
        try:
            if hasattr(self, 'store'):
                self.store.close()
            if hasattr(self, 'sandbox'):
                self.sandbox.cleanup()
            self._initialized = False
            logger.info("插件市场客户端已关闭")
        except Exception as e:
            logger.error(f"关闭客户端失败: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ========================================
    # 内部工具方法
    # ========================================
    
    def _to_category_enum(self, category: Optional[str]) -> Optional[PluginCategory]:
        """字符串转 PluginCategory 枚举"""
        if not category:
            return None
        try:
            return PluginCategory(category.lower())
        except ValueError:
            logger.warning(f"无效的分类值: {category}")
            return None
    
    def _to_type_enum(self, plugin_type: Optional[str]) -> Optional[PluginType]:
        """字符串转 PluginType 枚举"""
        if not plugin_type:
            return None
        try:
            return PluginType(plugin_type.lower())
        except ValueError:
            logger.warning(f"无效的类型值: {plugin_type}")
            return None
    
    def _to_sort_enum(self, sort_by: str) -> SortStrategy:
        """字符串转 SortStrategy 枚举"""
        if not sort_by:
            return SortStrategy.RELEVANCE
        try:
            return SortStrategy(sort_by.lower())
        except ValueError:
            logger.warning(f"无效的排序值: {sort_by}，使用默认值 relevance")
            return SortStrategy.RELEVANCE
