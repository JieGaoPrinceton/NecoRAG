"""
NecoRAG 插件市场 SQLite 存储层

基于 SQLite 的轻量级本地存储，提供：
- 插件元数据的增删改查
- FTS5 全文搜索
- 版本发布管理
- 安装记录管理
- 评分和统计功能
- GDI 评分存储
- 灰度部署管理
- 仓库源管理
"""

import sqlite3
import json
import logging
import threading
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .models import (
    PluginManifest,
    PluginRelease,
    PluginRating,
    PluginInstallation,
    GDIScore,
    CanaryDeployment,
    PluginType,
    PluginCategory,
    ReleaseStability,
    InstallStatus,
    PluginPermission,
)

logger = logging.getLogger(__name__)


class MarketplaceStore:
    """
    插件市场 SQLite 存储层
    
    基于 SQLite 的轻量级本地存储，支持：
    - WAL 模式提升并发性能
    - FTS5 全文搜索
    - 线程安全的数据库连接
    """
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._local = threading.local()
        
        # 确保数据库目录存在
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建表
        self._create_tables()
        
        logger.info(f"MarketplaceStore 初始化完成: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        获取线程安全的数据库连接
        
        Returns:
            sqlite3.Connection: 当前线程的数据库连接
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # 启用 WAL 模式
            conn.execute("PRAGMA journal_mode=WAL")
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return self._local.connection
    
    def _create_tables(self):
        """创建所有表和索引"""
        conn = self._get_connection()
        
        # 插件元数据表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                plugin_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                author TEXT NOT NULL,
                description TEXT DEFAULT '',
                plugin_type TEXT NOT NULL,
                category TEXT DEFAULT 'community',
                tags TEXT DEFAULT '[]',
                license TEXT DEFAULT 'MIT',
                homepage TEXT DEFAULT '',
                repository TEXT DEFAULT '',
                entry_point TEXT NOT NULL,
                min_necorag_version TEXT DEFAULT '0.1.0',
                max_necorag_version TEXT,
                dependencies TEXT DEFAULT '{}',
                permissions TEXT DEFAULT '[]',
                python_requires TEXT DEFAULT '>=3.9',
                icon TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 版本发布表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                release_id TEXT PRIMARY KEY,
                plugin_id TEXT NOT NULL,
                version TEXT NOT NULL,
                download_url TEXT DEFAULT '',
                checksum_sha256 TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                changelog TEXT DEFAULT '',
                stability TEXT DEFAULT 'stable',
                published_at TEXT NOT NULL,
                download_count INTEGER DEFAULT 0,
                min_necorag_version TEXT DEFAULT '0.1.0',
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id),
                UNIQUE(plugin_id, version)
            )
        """)
        
        # 安装记录表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS installations (
                installation_id TEXT PRIMARY KEY,
                plugin_id TEXT NOT NULL,
                version TEXT NOT NULL,
                install_path TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                config TEXT DEFAULT '{}',
                installed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
            )
        """)
        
        # 评分表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id TEXT PRIMARY KEY,
                plugin_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                score REAL NOT NULL CHECK(score >= 1.0 AND score <= 5.0),
                comment TEXT DEFAULT '',
                dimensions TEXT DEFAULT '{}',
                helpful_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id),
                UNIQUE(plugin_id, user_id)
            )
        """)
        
        # 使用统计表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
            )
        """)
        
        # GDI 评分表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gdi_scores (
                plugin_id TEXT PRIMARY KEY,
                overall_score REAL DEFAULT 0.0,
                code_quality REAL DEFAULT 0.0,
                functionality REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.0,
                performance REAL DEFAULT 0.0,
                user_experience REAL DEFAULT 0.0,
                actual_usage REAL DEFAULT 0.0,
                freshness REAL DEFAULT 0.0,
                calculated_at TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
            )
        """)
        
        # 灰度部署表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS canary_deployments (
                deployment_id TEXT PRIMARY KEY,
                plugin_id TEXT NOT NULL,
                current_version TEXT NOT NULL,
                new_version TEXT NOT NULL,
                percentage REAL DEFAULT 0.1,
                status TEXT DEFAULT 'pending',
                metrics TEXT DEFAULT '{}',
                started_at TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
            )
        """)
        
        # 仓库源表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repository_sources (
                name TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                last_synced TEXT,
                config TEXT DEFAULT '{}'
            )
        """)
        
        # FTS5 全文搜索虚拟表（不使用 content 同步模式，手动管理）
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS plugins_fts USING fts5(
                plugin_id,
                name,
                description,
                tags,
                author
            )
        """)
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_type ON plugins(plugin_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_category ON plugins(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_releases_plugin ON releases(plugin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_installations_plugin ON installations(plugin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ratings_plugin ON ratings(plugin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_plugin ON usage_stats(plugin_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_stats(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_canary_plugin ON canary_deployments(plugin_id)")
        
        conn.commit()
        logger.debug("数据库表和索引创建完成")
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("数据库连接已关闭")
    
    # ============== 插件 CRUD ==============
    
    def add_plugin(self, manifest: PluginManifest) -> bool:
        """
        添加插件元数据
        
        Args:
            manifest: 插件清单
            
        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            now = datetime.now().isoformat()
            
            conn.execute("""
                INSERT INTO plugins (
                    plugin_id, name, version, author, description,
                    plugin_type, category, tags, license, homepage,
                    repository, entry_point, min_necorag_version,
                    max_necorag_version, dependencies, permissions,
                    python_requires, icon, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                manifest.plugin_id,
                manifest.name,
                manifest.version,
                manifest.author,
                manifest.description,
                manifest.plugin_type.value,
                manifest.category.value,
                json.dumps(manifest.tags),
                manifest.license,
                manifest.homepage,
                manifest.repository,
                manifest.entry_point,
                manifest.min_necorag_version,
                manifest.max_necorag_version,
                json.dumps(manifest.dependencies),
                json.dumps([p.value for p in manifest.permissions]),
                manifest.python_requires,
                manifest.icon,
                manifest.created_at.isoformat() if manifest.created_at else now,
                manifest.updated_at.isoformat() if manifest.updated_at else now,
            ))
            
            # 更新 FTS 索引
            self._update_fts_index(manifest.plugin_id, manifest)
            
            conn.commit()
            logger.info(f"添加插件: {manifest.plugin_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"插件已存在: {manifest.plugin_id}, {e}")
            return False
        except Exception as e:
            logger.error(f"添加插件失败: {e}")
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """
        获取插件信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[PluginManifest]: 插件清单，不存在则返回 None
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM plugins WHERE plugin_id = ?",
                (plugin_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_manifest(row)
            return None
            
        except Exception as e:
            logger.error(f"获取插件失败: {plugin_id}, {e}")
            return None
    
    def update_plugin(self, manifest: PluginManifest) -> bool:
        """
        更新插件信息
        
        Args:
            manifest: 插件清单
            
        Returns:
            bool: 是否成功更新
        """
        try:
            conn = self._get_connection()
            now = datetime.now().isoformat()
            
            cursor = conn.execute("""
                UPDATE plugins SET
                    name = ?, version = ?, author = ?, description = ?,
                    plugin_type = ?, category = ?, tags = ?, license = ?,
                    homepage = ?, repository = ?, entry_point = ?,
                    min_necorag_version = ?, max_necorag_version = ?,
                    dependencies = ?, permissions = ?, python_requires = ?,
                    icon = ?, updated_at = ?
                WHERE plugin_id = ?
            """, (
                manifest.name,
                manifest.version,
                manifest.author,
                manifest.description,
                manifest.plugin_type.value,
                manifest.category.value,
                json.dumps(manifest.tags),
                manifest.license,
                manifest.homepage,
                manifest.repository,
                manifest.entry_point,
                manifest.min_necorag_version,
                manifest.max_necorag_version,
                json.dumps(manifest.dependencies),
                json.dumps([p.value for p in manifest.permissions]),
                manifest.python_requires,
                manifest.icon,
                now,
                manifest.plugin_id,
            ))
            
            if cursor.rowcount > 0:
                # 更新 FTS 索引
                self._update_fts_index(manifest.plugin_id, manifest)
                conn.commit()
                logger.info(f"更新插件: {manifest.plugin_id}")
                return True
            
            logger.warning(f"插件不存在: {manifest.plugin_id}")
            return False
            
        except Exception as e:
            logger.error(f"更新插件失败: {e}")
            return False
    
    def delete_plugin(self, plugin_id: str) -> bool:
        """
        删除插件（级联删除相关记录）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            conn = self._get_connection()
            
            # 删除 FTS 索引
            self._delete_fts_index(plugin_id)
            
            # 级联删除相关记录
            conn.execute("DELETE FROM releases WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM installations WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM ratings WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM usage_stats WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM gdi_scores WHERE plugin_id = ?", (plugin_id,))
            conn.execute("DELETE FROM canary_deployments WHERE plugin_id = ?", (plugin_id,))
            
            # 删除插件
            cursor = conn.execute("DELETE FROM plugins WHERE plugin_id = ?", (plugin_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"删除插件: {plugin_id}")
                return True
            
            logger.warning(f"插件不存在: {plugin_id}")
            return False
            
        except Exception as e:
            logger.error(f"删除插件失败: {e}")
            return False
    
    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        category: Optional[PluginCategory] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PluginManifest], int]:
        """
        列出插件（带分页和过滤）
        
        Args:
            plugin_type: 插件类型过滤
            category: 分类过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[PluginManifest], int]: 插件列表和总数
        """
        try:
            conn = self._get_connection()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if plugin_type:
                conditions.append("plugin_type = ?")
                params.append(plugin_type.value)
            if category:
                conditions.append("category = ?")
                params.append(category.value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) FROM plugins WHERE {where_clause}"
            total = conn.execute(count_sql, params).fetchone()[0]
            
            # 查询数据
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT * FROM plugins WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(query_sql, params + [page_size, offset])
            
            plugins = [self._row_to_manifest(row) for row in cursor.fetchall()]
            return plugins, total
            
        except Exception as e:
            logger.error(f"列出插件失败: {e}")
            return [], 0
    
    def search_plugins(
        self,
        query: str,
        plugin_type: Optional[PluginType] = None,
        category: Optional[PluginCategory] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PluginManifest], int]:
        """
        全文搜索插件（使用 FTS5）
        
        Args:
            query: 搜索关键词
            plugin_type: 插件类型过滤
            category: 分类过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[PluginManifest], int]: 插件列表和总数
        """
        try:
            conn = self._get_connection()
            
            # FTS5 搜索
            fts_query = query.replace('"', '""')
            
            # 构建额外过滤条件
            extra_conditions = []
            params = []
            
            if plugin_type:
                extra_conditions.append("p.plugin_type = ?")
                params.append(plugin_type.value)
            if category:
                extra_conditions.append("p.category = ?")
                params.append(category.value)
            
            extra_where = " AND " + " AND ".join(extra_conditions) if extra_conditions else ""
            
            # 查询匹配的插件ID
            count_sql = f"""
                SELECT COUNT(DISTINCT p.plugin_id)
                FROM plugins p
                JOIN plugins_fts fts ON p.plugin_id = fts.plugin_id
                WHERE plugins_fts MATCH ?{extra_where}
            """
            total = conn.execute(count_sql, [fts_query] + params).fetchone()[0]
            
            # 查询数据
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT p.*
                FROM plugins p
                JOIN plugins_fts fts ON p.plugin_id = fts.plugin_id
                WHERE plugins_fts MATCH ?{extra_where}
                ORDER BY rank
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(query_sql, [fts_query] + params + [page_size, offset])
            
            plugins = [self._row_to_manifest(row) for row in cursor.fetchall()]
            return plugins, total
            
        except Exception as e:
            logger.error(f"搜索插件失败: {e}")
            return [], 0
    
    def plugin_exists(self, plugin_id: str) -> bool:
        """
        检查插件是否存在
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否存在
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT 1 FROM plugins WHERE plugin_id = ?",
                (plugin_id,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查插件存在性失败: {e}")
            return False
    
    # ============== FTS 索引管理 ==============
    
    def _update_fts_index(self, plugin_id: str, manifest: PluginManifest):
        """更新 FTS 索引"""
        conn = self._get_connection()
        
        # 先删除旧索引
        conn.execute(
            "DELETE FROM plugins_fts WHERE plugin_id = ?",
            (plugin_id,)
        )
        
        # 插入新索引
        conn.execute("""
            INSERT INTO plugins_fts (plugin_id, name, description, tags, author)
            VALUES (?, ?, ?, ?, ?)
        """, (
            plugin_id,
            manifest.name,
            manifest.description,
            json.dumps(manifest.tags),
            manifest.author,
        ))
    
    def _delete_fts_index(self, plugin_id: str):
        """删除 FTS 索引"""
        conn = self._get_connection()
        conn.execute(
            "DELETE FROM plugins_fts WHERE plugin_id = ?",
            (plugin_id,)
        )
    
    # ============== 版本/发布 CRUD ==============
    
    def add_release(self, release: PluginRelease) -> bool:
        """
        添加版本发布
        
        Args:
            release: 版本发布记录
            
        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT INTO releases (
                    release_id, plugin_id, version, download_url,
                    checksum_sha256, size_bytes, changelog, stability,
                    published_at, download_count, min_necorag_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                release.release_id,
                release.plugin_id,
                release.version,
                release.download_url,
                release.checksum_sha256,
                release.size_bytes,
                release.changelog,
                release.stability.value,
                release.published_at.isoformat(),
                release.download_count,
                release.min_necorag_version,
            ))
            
            conn.commit()
            logger.info(f"添加版本发布: {release.plugin_id}@{release.version}")
            return True
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"版本已存在: {release.plugin_id}@{release.version}, {e}")
            return False
        except Exception as e:
            logger.error(f"添加版本发布失败: {e}")
            return False
    
    def get_releases(self, plugin_id: str) -> List[PluginRelease]:
        """
        获取插件的所有版本
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[PluginRelease]: 版本列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM releases WHERE plugin_id = ? ORDER BY published_at DESC",
                (plugin_id,)
            )
            return [self._row_to_release(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取版本列表失败: {e}")
            return []
    
    def get_release(self, plugin_id: str, version: str) -> Optional[PluginRelease]:
        """
        获取特定版本
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            Optional[PluginRelease]: 版本发布记录
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM releases WHERE plugin_id = ? AND version = ?",
                (plugin_id, version)
            )
            row = cursor.fetchone()
            return self._row_to_release(row) if row else None
        except Exception as e:
            logger.error(f"获取版本失败: {e}")
            return None
    
    def get_latest_release(
        self,
        plugin_id: str,
        stability: Optional[ReleaseStability] = None
    ) -> Optional[PluginRelease]:
        """
        获取最新版本
        
        Args:
            plugin_id: 插件ID
            stability: 稳定性过滤
            
        Returns:
            Optional[PluginRelease]: 最新版本发布记录
        """
        try:
            conn = self._get_connection()
            
            if stability:
                cursor = conn.execute("""
                    SELECT * FROM releases 
                    WHERE plugin_id = ? AND stability = ?
                    ORDER BY published_at DESC LIMIT 1
                """, (plugin_id, stability.value))
            else:
                cursor = conn.execute("""
                    SELECT * FROM releases 
                    WHERE plugin_id = ?
                    ORDER BY published_at DESC LIMIT 1
                """, (plugin_id,))
            
            row = cursor.fetchone()
            return self._row_to_release(row) if row else None
        except Exception as e:
            logger.error(f"获取最新版本失败: {e}")
            return None
    
    def increment_download_count(self, plugin_id: str, version: str) -> bool:
        """
        增加下载计数
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                UPDATE releases SET download_count = download_count + 1
                WHERE plugin_id = ? AND version = ?
            """, (plugin_id, version))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"增加下载计数失败: {e}")
            return False
    
    # ============== 安装记录 CRUD ==============
    
    def add_installation(self, installation: PluginInstallation) -> bool:
        """
        添加安装记录
        
        Args:
            installation: 安装记录
            
        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            now = datetime.now().isoformat()
            
            conn.execute("""
                INSERT INTO installations (
                    installation_id, plugin_id, version, install_path,
                    status, config, installed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                installation.installation_id,
                installation.plugin_id,
                installation.version,
                installation.install_path,
                installation.status.value,
                json.dumps(installation.config),
                installation.installed_at.isoformat() if installation.installed_at else now,
                installation.updated_at.isoformat() if installation.updated_at else now,
            ))
            
            conn.commit()
            logger.info(f"添加安装记录: {installation.plugin_id}@{installation.version}")
            return True
            
        except Exception as e:
            logger.error(f"添加安装记录失败: {e}")
            return False
    
    def get_installation(self, plugin_id: str) -> Optional[PluginInstallation]:
        """
        获取安装记录
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[PluginInstallation]: 安装记录
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM installations WHERE plugin_id = ? ORDER BY installed_at DESC LIMIT 1",
                (plugin_id,)
            )
            row = cursor.fetchone()
            return self._row_to_installation(row) if row else None
        except Exception as e:
            logger.error(f"获取安装记录失败: {e}")
            return None
    
    def update_installation(self, installation: PluginInstallation) -> bool:
        """
        更新安装记录
        
        Args:
            installation: 安装记录
            
        Returns:
            bool: 是否成功更新
        """
        try:
            conn = self._get_connection()
            now = datetime.now().isoformat()
            
            cursor = conn.execute("""
                UPDATE installations SET
                    version = ?, install_path = ?, status = ?,
                    config = ?, updated_at = ?
                WHERE installation_id = ?
            """, (
                installation.version,
                installation.install_path,
                installation.status.value,
                json.dumps(installation.config),
                now,
                installation.installation_id,
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新安装记录失败: {e}")
            return False
    
    def remove_installation(self, plugin_id: str) -> bool:
        """
        删除安装记录
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM installations WHERE plugin_id = ?",
                (plugin_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除安装记录失败: {e}")
            return False
    
    def list_installations(
        self,
        status: Optional[InstallStatus] = None
    ) -> List[PluginInstallation]:
        """
        列出已安装插件
        
        Args:
            status: 状态过滤
            
        Returns:
            List[PluginInstallation]: 安装记录列表
        """
        try:
            conn = self._get_connection()
            
            if status:
                cursor = conn.execute(
                    "SELECT * FROM installations WHERE status = ? ORDER BY installed_at DESC",
                    (status.value,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM installations ORDER BY installed_at DESC"
                )
            
            return [self._row_to_installation(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"列出安装记录失败: {e}")
            return []
    
    # ============== 评分 CRUD ==============
    
    def add_rating(self, rating: PluginRating) -> bool:
        """
        添加评分（同一用户覆盖旧评分）
        
        Args:
            rating: 评分记录
            
        Returns:
            bool: 是否成功添加
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT OR REPLACE INTO ratings (
                    rating_id, plugin_id, user_id, score, comment,
                    dimensions, helpful_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rating.rating_id,
                rating.plugin_id,
                rating.user_id,
                rating.score,
                rating.comment,
                json.dumps(rating.dimensions),
                rating.helpful_count,
                rating.created_at.isoformat(),
            ))
            
            conn.commit()
            logger.info(f"添加评分: {rating.plugin_id} by {rating.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加评分失败: {e}")
            return False
    
    def get_ratings(
        self,
        plugin_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[PluginRating], int]:
        """
        获取插件评分列表
        
        Args:
            plugin_id: 插件ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[PluginRating], int]: 评分列表和总数
        """
        try:
            conn = self._get_connection()
            
            # 查询总数
            total = conn.execute(
                "SELECT COUNT(*) FROM ratings WHERE plugin_id = ?",
                (plugin_id,)
            ).fetchone()[0]
            
            # 查询数据
            offset = (page - 1) * page_size
            cursor = conn.execute("""
                SELECT * FROM ratings WHERE plugin_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (plugin_id, page_size, offset))
            
            ratings = [self._row_to_rating(row) for row in cursor.fetchall()]
            return ratings, total
            
        except Exception as e:
            logger.error(f"获取评分列表失败: {e}")
            return [], 0
    
    def get_average_rating(self, plugin_id: str) -> Tuple[float, int]:
        """
        获取平均评分和评分数
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Tuple[float, int]: 平均评分和评分数
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT AVG(score) as avg_score, COUNT(*) as count
                FROM ratings WHERE plugin_id = ?
            """, (plugin_id,))
            row = cursor.fetchone()
            
            avg_score = row['avg_score'] if row['avg_score'] else 0.0
            count = row['count'] if row['count'] else 0
            return avg_score, count
            
        except Exception as e:
            logger.error(f"获取平均评分失败: {e}")
            return 0.0, 0
    
    def increment_helpful(self, rating_id: str) -> bool:
        """
        增加有用计数
        
        Args:
            rating_id: 评分ID
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                UPDATE ratings SET helpful_count = helpful_count + 1
                WHERE rating_id = ?
            """, (rating_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"增加有用计数失败: {e}")
            return False
    
    # ============== 使用统计 ==============
    
    def record_usage_event(
        self,
        plugin_id: str,
        event_type: str,
        event_data: Optional[Dict] = None
    ) -> bool:
        """
        记录使用事件
        
        Args:
            plugin_id: 插件ID
            event_type: 事件类型 (install, uninstall, activate, error, query)
            event_data: 事件数据
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT INTO usage_stats (plugin_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                plugin_id,
                event_type,
                json.dumps(event_data or {}),
                datetime.now().isoformat(),
            ))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"记录使用事件失败: {e}")
            return False
    
    def get_usage_stats(
        self,
        plugin_id: str,
        event_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        获取使用统计
        
        Args:
            plugin_id: 插件ID
            event_type: 事件类型过滤
            days: 统计天数
            
        Returns:
            List[Dict]: 使用统计列表
        """
        try:
            conn = self._get_connection()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            if event_type:
                cursor = conn.execute("""
                    SELECT * FROM usage_stats
                    WHERE plugin_id = ? AND event_type = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (plugin_id, event_type, since))
            else:
                cursor = conn.execute("""
                    SELECT * FROM usage_stats
                    WHERE plugin_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (plugin_id, since))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取使用统计失败: {e}")
            return []
    
    def get_active_install_count(self, plugin_id: str) -> int:
        """
        获取活跃安装数
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            int: 活跃安装数
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT COUNT(*) FROM installations
                WHERE plugin_id = ? AND status = 'active'
            """, (plugin_id,))
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取活跃安装数失败: {e}")
            return 0
    
    def get_trending_plugins(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Tuple[str, int]]:
        """
        获取热门插件（基于事件数）
        
        Args:
            days: 统计天数
            limit: 返回数量
            
        Returns:
            List[Tuple[str, int]]: (plugin_id, event_count) 列表
        """
        try:
            conn = self._get_connection()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor = conn.execute("""
                SELECT plugin_id, COUNT(*) as event_count
                FROM usage_stats
                WHERE timestamp >= ?
                GROUP BY plugin_id
                ORDER BY event_count DESC
                LIMIT ?
            """, (since, limit))
            
            return [(row['plugin_id'], row['event_count']) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取热门插件失败: {e}")
            return []
    
    # ============== GDI 评分 ==============
    
    def save_gdi_score(self, score: GDIScore) -> bool:
        """
        保存 GDI 评分
        
        Args:
            score: GDI 评分
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT OR REPLACE INTO gdi_scores (
                    plugin_id, overall_score, code_quality, functionality,
                    reliability, performance, user_experience, actual_usage,
                    freshness, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                score.plugin_id,
                score.overall_score,
                score.code_quality,
                score.functionality,
                score.reliability,
                score.performance,
                score.user_experience,
                score.actual_usage,
                score.freshness,
                score.calculated_at.isoformat(),
            ))
            
            conn.commit()
            logger.info(f"保存 GDI 评分: {score.plugin_id}")
            return True
        except Exception as e:
            logger.error(f"保存 GDI 评分失败: {e}")
            return False
    
    def get_gdi_score(self, plugin_id: str) -> Optional[GDIScore]:
        """
        获取 GDI 评分
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[GDIScore]: GDI 评分
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM gdi_scores WHERE plugin_id = ?",
                (plugin_id,)
            )
            row = cursor.fetchone()
            return self._row_to_gdi_score(row) if row else None
        except Exception as e:
            logger.error(f"获取 GDI 评分失败: {e}")
            return None
    
    def get_gdi_leaderboard(self, limit: int = 50) -> List[GDIScore]:
        """
        获取 GDI 排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            List[GDIScore]: GDI 评分列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM gdi_scores
                ORDER BY overall_score DESC
                LIMIT ?
            """, (limit,))
            return [self._row_to_gdi_score(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取 GDI 排行榜失败: {e}")
            return []
    
    # ============== 灰度部署 ==============
    
    def save_canary_deployment(self, deployment: CanaryDeployment) -> bool:
        """
        保存灰度部署记录
        
        Args:
            deployment: 灰度部署记录
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT OR REPLACE INTO canary_deployments (
                    deployment_id, plugin_id, current_version, new_version,
                    percentage, status, metrics, started_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deployment.deployment_id,
                deployment.plugin_id,
                deployment.current_version,
                deployment.new_version,
                deployment.percentage,
                deployment.status,
                json.dumps(deployment.metrics),
                deployment.started_at.isoformat(),
            ))
            
            conn.commit()
            logger.info(f"保存灰度部署: {deployment.deployment_id}")
            return True
        except Exception as e:
            logger.error(f"保存灰度部署失败: {e}")
            return False
    
    def get_canary_deployment(self, deployment_id: str) -> Optional[CanaryDeployment]:
        """
        获取灰度部署记录
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Optional[CanaryDeployment]: 灰度部署记录
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT * FROM canary_deployments WHERE deployment_id = ?",
                (deployment_id,)
            )
            row = cursor.fetchone()
            return self._row_to_canary(row) if row else None
        except Exception as e:
            logger.error(f"获取灰度部署失败: {e}")
            return None
    
    def get_active_canary(self, plugin_id: str) -> Optional[CanaryDeployment]:
        """
        获取插件的活跃灰度部署
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[CanaryDeployment]: 活跃的灰度部署记录
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM canary_deployments
                WHERE plugin_id = ? AND status IN ('pending', 'running')
                ORDER BY started_at DESC LIMIT 1
            """, (plugin_id,))
            row = cursor.fetchone()
            return self._row_to_canary(row) if row else None
        except Exception as e:
            logger.error(f"获取活跃灰度部署失败: {e}")
            return None
    
    def update_canary_status(
        self,
        deployment_id: str,
        status: str,
        metrics: Optional[Dict] = None
    ) -> bool:
        """
        更新灰度部署状态
        
        Args:
            deployment_id: 部署ID
            status: 新状态
            metrics: 更新的指标
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            
            if metrics:
                cursor = conn.execute("""
                    UPDATE canary_deployments
                    SET status = ?, metrics = ?
                    WHERE deployment_id = ?
                """, (status, json.dumps(metrics), deployment_id))
            else:
                cursor = conn.execute("""
                    UPDATE canary_deployments
                    SET status = ?
                    WHERE deployment_id = ?
                """, (status, deployment_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新灰度部署状态失败: {e}")
            return False
    
    # ============== 仓库源 ==============
    
    def add_repository_source(
        self,
        name: str,
        url: str,
        repo_type: str,
        priority: int = 0,
        config: Optional[Dict] = None
    ) -> bool:
        """
        添加仓库源
        
        Args:
            name: 仓库源名称
            url: 仓库URL
            repo_type: 仓库类型 (local, github, gitee, http)
            priority: 优先级
            config: 额外配置
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            
            conn.execute("""
                INSERT OR REPLACE INTO repository_sources (
                    name, url, type, enabled, priority, config
                ) VALUES (?, ?, ?, 1, ?, ?)
            """, (name, url, repo_type, priority, json.dumps(config or {})))
            
            conn.commit()
            logger.info(f"添加仓库源: {name}")
            return True
        except Exception as e:
            logger.error(f"添加仓库源失败: {e}")
            return False
    
    def get_repository_sources(self) -> List[Dict]:
        """
        获取所有仓库源
        
        Returns:
            List[Dict]: 仓库源列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT * FROM repository_sources
                WHERE enabled = 1
                ORDER BY priority DESC
            """)
            
            sources = []
            for row in cursor.fetchall():
                source = dict(row)
                source['config'] = json.loads(source.get('config', '{}'))
                sources.append(source)
            return sources
        except Exception as e:
            logger.error(f"获取仓库源失败: {e}")
            return []
    
    def remove_repository_source(self, name: str) -> bool:
        """
        删除仓库源
        
        Args:
            name: 仓库源名称
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM repository_sources WHERE name = ?",
                (name,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除仓库源失败: {e}")
            return False
    
    def update_sync_time(self, name: str) -> bool:
        """
        更新仓库同步时间
        
        Args:
            name: 仓库源名称
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                UPDATE repository_sources
                SET last_synced = ?
                WHERE name = ?
            """, (datetime.now().isoformat(), name))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新同步时间失败: {e}")
            return False
    
    # ============== 数据库工具 ==============
    
    def get_statistics(self) -> Dict:
        """
        获取市场统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            conn = self._get_connection()
            
            stats = {
                'total_plugins': 0,
                'total_releases': 0,
                'total_installations': 0,
                'active_installations': 0,
                'total_ratings': 0,
                'plugins_by_type': {},
                'plugins_by_category': {},
            }
            
            # 总插件数
            stats['total_plugins'] = conn.execute(
                "SELECT COUNT(*) FROM plugins"
            ).fetchone()[0]
            
            # 总发布数
            stats['total_releases'] = conn.execute(
                "SELECT COUNT(*) FROM releases"
            ).fetchone()[0]
            
            # 总安装数
            stats['total_installations'] = conn.execute(
                "SELECT COUNT(*) FROM installations"
            ).fetchone()[0]
            
            # 活跃安装数
            stats['active_installations'] = conn.execute(
                "SELECT COUNT(*) FROM installations WHERE status = 'active'"
            ).fetchone()[0]
            
            # 总评分数
            stats['total_ratings'] = conn.execute(
                "SELECT COUNT(*) FROM ratings"
            ).fetchone()[0]
            
            # 按类型统计
            cursor = conn.execute("""
                SELECT plugin_type, COUNT(*) as count
                FROM plugins GROUP BY plugin_type
            """)
            stats['plugins_by_type'] = {row['plugin_type']: row['count'] for row in cursor}
            
            # 按分类统计
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM plugins GROUP BY category
            """)
            stats['plugins_by_category'] = {row['category']: row['count'] for row in cursor}
            
            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def vacuum(self):
        """压缩数据库"""
        try:
            conn = self._get_connection()
            conn.execute("VACUUM")
            logger.info("数据库压缩完成")
        except Exception as e:
            logger.error(f"数据库压缩失败: {e}")
    
    def backup(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保备份目录存在
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 关闭当前连接以确保数据完整性
            self.close()
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            
            # WAL 文件也需要备份（如果存在）
            wal_path = self.db_path + "-wal"
            if Path(wal_path).exists():
                shutil.copy2(wal_path, backup_path + "-wal")
            
            logger.info(f"数据库备份完成: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False
    
    # ============== 行转换辅助方法 ==============
    
    def _row_to_manifest(self, row: sqlite3.Row) -> PluginManifest:
        """将数据库行转换为 PluginManifest"""
        return PluginManifest(
            plugin_id=row['plugin_id'],
            name=row['name'],
            version=row['version'],
            author=row['author'],
            description=row['description'],
            plugin_type=PluginType(row['plugin_type']),
            entry_point=row['entry_point'],
            category=PluginCategory(row['category']),
            tags=json.loads(row['tags']),
            license=row['license'],
            homepage=row['homepage'],
            repository=row['repository'],
            min_necorag_version=row['min_necorag_version'],
            max_necorag_version=row['max_necorag_version'],
            dependencies=json.loads(row['dependencies']),
            permissions=[PluginPermission(p) for p in json.loads(row['permissions'])],
            python_requires=row['python_requires'],
            icon=row['icon'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now(),
        )
    
    def _row_to_release(self, row: sqlite3.Row) -> PluginRelease:
        """将数据库行转换为 PluginRelease"""
        return PluginRelease(
            release_id=row['release_id'],
            plugin_id=row['plugin_id'],
            version=row['version'],
            download_url=row['download_url'],
            checksum_sha256=row['checksum_sha256'],
            size_bytes=row['size_bytes'],
            changelog=row['changelog'],
            stability=ReleaseStability(row['stability']),
            published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else datetime.now(),
            download_count=row['download_count'],
            min_necorag_version=row['min_necorag_version'],
        )
    
    def _row_to_installation(self, row: sqlite3.Row) -> PluginInstallation:
        """将数据库行转换为 PluginInstallation"""
        return PluginInstallation(
            installation_id=row['installation_id'],
            plugin_id=row['plugin_id'],
            version=row['version'],
            install_path=row['install_path'],
            status=InstallStatus(row['status']),
            config=json.loads(row['config']),
            installed_at=datetime.fromisoformat(row['installed_at']) if row['installed_at'] else datetime.now(),
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.now(),
        )
    
    def _row_to_rating(self, row: sqlite3.Row) -> PluginRating:
        """将数据库行转换为 PluginRating"""
        return PluginRating(
            rating_id=row['rating_id'],
            plugin_id=row['plugin_id'],
            user_id=row['user_id'],
            score=row['score'],
            comment=row['comment'],
            dimensions=json.loads(row['dimensions']),
            helpful_count=row['helpful_count'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
        )
    
    def _row_to_gdi_score(self, row: sqlite3.Row) -> GDIScore:
        """将数据库行转换为 GDIScore"""
        return GDIScore(
            plugin_id=row['plugin_id'],
            overall_score=row['overall_score'],
            code_quality=row['code_quality'],
            functionality=row['functionality'],
            reliability=row['reliability'],
            performance=row['performance'],
            user_experience=row['user_experience'],
            actual_usage=row['actual_usage'],
            freshness=row['freshness'],
            calculated_at=datetime.fromisoformat(row['calculated_at']) if row['calculated_at'] else datetime.now(),
        )
    
    def _row_to_canary(self, row: sqlite3.Row) -> CanaryDeployment:
        """将数据库行转换为 CanaryDeployment"""
        return CanaryDeployment(
            deployment_id=row['deployment_id'],
            plugin_id=row['plugin_id'],
            current_version=row['current_version'],
            new_version=row['new_version'],
            percentage=row['percentage'],
            status=row['status'],
            metrics=json.loads(row['metrics']),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else datetime.now(),
        )
