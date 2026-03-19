"""
NecoRAG 插件市场模块

提供插件市场的核心功能，包括：
- 插件数据模型定义
- 市场配置管理
- 插件安装、搜索、评分等功能

使用示例:
    from src.marketplace import (
        PluginManifest,
        PluginType,
        PluginCategory,
        MarketplaceConfig,
    )
    
    # 创建插件清单
    manifest = PluginManifest(
        plugin_id="my-plugin",
        name="My Plugin",
        version="1.0.0",
        author="Author",
        description="A sample plugin",
        plugin_type=PluginType.UTILITY,
        entry_point="my_plugin.main",
    )
    
    # 加载市场配置
    config = MarketplaceConfig()
    config.ensure_directories()
"""

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
)

# 操作结果模型
from .models import (
    SearchResult,
    InstallResult,
    SyncResult,
)

# 依赖和版本管理模型
from .models import (
    UpgradePath,
    DependencyGraph,
    VersionConflict,
    CanaryDeployment,
)

# 配置类
from .config import (
    MarketplaceConfig,
    load_marketplace_config,
)

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
from .version_manager import (
    VersionConstraint,
    VersionManager,
)

# 依赖解析器
from .dependency_resolver import DependencyResolver

# 插件安装器
from .installer import (
    PluginInstaller,
    InstallHooks,
)

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

__all__ = [
    # 枚举类型
    'PluginType',
    'PluginCategory',
    'ReleaseStability',
    'InstallStatus',
    'PluginPermission',
    'SortStrategy',
    'PermissionLevel',
    # 核心数据模型
    'PluginManifest',
    'PluginRelease',
    'PluginRating',
    'PluginInstallation',
    'GDIScore',
    'ResourceQuota',
    # 操作结果模型
    'SearchResult',
    'InstallResult',
    'SyncResult',
    # 依赖和版本管理模型
    'UpgradePath',
    'DependencyGraph',
    'VersionConflict',
    'CanaryDeployment',
    # 配置类
    'MarketplaceConfig',
    'load_marketplace_config',
    # 存储层
    'MarketplaceStore',
    # 沙箱隔离系统
    'PluginSandbox',
    'ValidationResult',
    'ResourceUsage',
    'SandboxContext',
    'PERMISSION_LEVEL_GRANTS',
    'CATEGORY_DEFAULT_LEVEL',
    # 搜索发现引擎
    'DiscoveryEngine',
    # GDI 质量评估系统
    'GDIAssessor',
    # 版本管理器
    'VersionConstraint',
    'VersionManager',
    # 依赖解析器
    'DependencyResolver',
    # 插件安装器
    'PluginInstaller',
    'InstallHooks',
    # 仓库管理
    'BaseRepository',
    'LocalRepository',
    'RemoteRepository',
    'GitHubRepository',
    'RepositoryManager',
    # 统一入口客户端
    'MarketplaceClient',
]

__version__ = '0.1.0'
