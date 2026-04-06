"""
NecoRAG - Extensions (扩展组件)
基于认知科学的神经符号 RAG 框架

扩展组件层提供可插拔的增强功能：
- 插件系统：动态扩展系统能力
- 安全机制：权限控制与数据保护
- 监控告警：系统健康状态监测
- 市场生态：插件发现与管理
"""

# ========== 插件系统 ==========
from .base import BasePlugin, PluginLifecycle
from .manager import PluginManager
from .registry import PluginRegistry

# ========== 安全机制 ==========
from .auth import AuthenticationManager, TokenManager
from .permission import PermissionChecker, AccessControlList
from .protection import DataProtection, AuditLogger
from .storage import SecureStorage
from .models import (
    SecurityContext,
    AuthToken,
    PermissionScope,
    AuditEntry,
)

# ========== 监控告警 ==========
from .health import HealthChecker, SystemHealth
from .metrics import MetricsCollector, MetricType
from .alerts import AlertManager, AlertLevel, AlertRule
from .service import MonitoringService
from .dashboard import MonitoringDashboard

# ========== 市场生态 ==========
# 枚举类型
from .models import (
    PluginType,
    PluginCategory,
    ReleaseStability,
    InstallStatus,
    PluginPermission,
    SortStrategy,
    PermissionLevel,
)

# 核心数据模型
from .models import (
    PluginManifest,
    PluginRelease,
    PluginRating,
    PluginInstallation,
    GDIScore,
    ResourceQuota,
    SearchResult,
    InstallResult,
    SyncResult,
    UpgradePath,
    DependencyGraph,
    VersionConflict,
    CanaryDeployment,
)

# 配置类
from .config import MarketplaceConfig, load_marketplace_config

# 存储层
from .store import MarketplaceStore

# 沙箱隔离系统
from .sandbox import (
    PluginSandbox,
    ValidationResult,
    ResourceUsage,
    SandboxContext,
    PERMISSION_LEVEL_GRANTS,
    CATEGORY_DEFAULT_LEVEL,
)

# 搜索发现引擎
from .discovery import DiscoveryEngine

# GDI 质量评估系统
from .quality import GDIAssessor

# 版本管理器
from .version_manager import VersionConstraint, VersionManager

# 依赖解析器
from .dependency_resolver import DependencyResolver

# 插件安装器
from .installer import PluginInstaller, InstallHooks

# 仓库管理
from .repository import (
    BaseRepository,
    LocalRepository,
    RemoteRepository,
    GitHubRepository,
    RepositoryManager,
)

# 统一入口客户端
from .client import MarketplaceClient

# REST API 端点
from .api import marketplace_router, get_client, set_client


__all__ = [
    # 插件系统
    "BasePlugin",
    "PluginLifecycle",
    "PluginManager",
    "PluginRegistry",
    
    # 安全机制
    "AuthenticationManager",
    "TokenManager",
    "PermissionChecker",
    "AccessControlList",
    "DataProtection",
    "AuditLogger",
    "SecureStorage",
    "SecurityContext",
    "AuthToken",
    "PermissionScope",
    "AuditEntry",
    
    # 监控告警
    "HealthChecker",
    "SystemHealth",
    "MetricsCollector",
    "MetricType",
    "AlertManager",
    "AlertLevel",
    "AlertRule",
    "MonitoringService",
    "MonitoringDashboard",
    
    # 市场生态
    "PluginType",
    "PluginCategory",
    "ReleaseStability",
    "InstallStatus",
    "PluginPermission",
    "SortStrategy",
    "PermissionLevel",
    "PluginManifest",
    "PluginRelease",
    "PluginRating",
    "PluginInstallation",
    "GDIScore",
    "ResourceQuota",
    "SearchResult",
    "InstallResult",
    "SyncResult",
    "UpgradePath",
    "DependencyGraph",
    "VersionConflict",
    "CanaryDeployment",
    "MarketplaceConfig",
    "load_marketplace_config",
    "MarketplaceStore",
    "PluginSandbox",
    "ValidationResult",
    "ResourceUsage",
    "SandboxContext",
    "PERMISSION_LEVEL_GRANTS",
    "CATEGORY_DEFAULT_LEVEL",
    "DiscoveryEngine",
    "GDIAssessor",
    "VersionConstraint",
    "VersionManager",
    "DependencyResolver",
    "PluginInstaller",
    "InstallHooks",
    "BaseRepository",
    "LocalRepository",
    "RemoteRepository",
    "GitHubRepository",
    "RepositoryManager",
    "MarketplaceClient",
    "marketplace_router",
    "get_client",
    "set_client",
]

__version__ = '0.1.0'
