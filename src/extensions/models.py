"""
NecoRAG 插件市场数据模型

定义插件市场中使用的所有数据结构，包括：
- 枚举类型定义
- 插件清单、发布、评分等核心模型
- 安装记录、GDI评分等运行时模型
- 依赖图、版本冲突等辅助模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


# ============== 枚举类型定义 ==============

class PluginType(Enum):
    """插件类型枚举"""
    PERCEPTION = "perception"      # 感知层插件
    MEMORY = "memory"              # 记忆层插件
    RETRIEVAL = "retrieval"        # 检索层插件
    REFINEMENT = "refinement"      # 巩固层插件
    RESPONSE = "response"          # 响应层插件
    UTILITY = "utility"            # 工具类插件


class PluginCategory(Enum):
    """插件分类枚举"""
    OFFICIAL = "official"      # 官方插件
    CERTIFIED = "certified"    # 认证插件
    COMMUNITY = "community"    # 社区插件


class ReleaseStability(Enum):
    """发布稳定性枚举"""
    ALPHA = "alpha"    # Alpha 测试版
    BETA = "beta"      # Beta 测试版
    RC = "rc"          # 候选发布版
    STABLE = "stable"  # 稳定版


class InstallStatus(Enum):
    """安装状态枚举"""
    ACTIVE = "active"              # 激活状态
    DISABLED = "disabled"          # 已禁用
    FAILED = "failed"              # 安装失败
    OUTDATED = "outdated"          # 版本过期
    INSTALLING = "installing"      # 安装中
    UNINSTALLING = "uninstalling"  # 卸载中


class PluginPermission(Enum):
    """插件权限枚举"""
    READ_MEMORY = "read_memory"         # 读取记忆
    WRITE_MEMORY = "write_memory"       # 写入记忆
    DELETE_MEMORY = "delete_memory"     # 删除记忆
    QUERY_KNOWLEDGE = "query_knowledge" # 查询知识库
    MANAGE_INDEX = "manage_index"       # 管理索引
    CONFIG_RAG = "config_rag"           # 配置RAG
    CALL_LLM = "call_llm"               # 调用LLM
    NETWORK_REQUEST = "network_request" # 网络请求
    READ_FILES = "read_files"           # 读取文件
    WRITE_FILES = "write_files"         # 写入文件
    MANAGE_USERS = "manage_users"       # 管理用户
    MANAGE_PLUGINS = "manage_plugins"   # 管理插件
    WEBHOOK = "webhook"                 # Webhook回调


class SortStrategy(Enum):
    """排序策略枚举"""
    RELEVANCE = "relevance"    # 相关性排序
    GDI_SCORE = "gdi_score"    # GDI评分排序
    RATING = "rating"          # 用户评分排序
    TRENDING = "trending"      # 热度排序
    DOWNLOADS = "downloads"    # 下载量排序
    NEWEST = "newest"          # 最新发布排序
    NAME = "name"              # 名称排序


class PermissionLevel(Enum):
    """权限等级枚举"""
    MINIMAL = "minimal"      # 最小权限
    STANDARD = "standard"    # 标准权限
    ELEVATED = "elevated"    # 提升权限
    FULL = "full"            # 完全权限


# ============== 辅助函数 ==============

def _datetime_to_str(dt: datetime) -> str:
    """将 datetime 转换为 ISO 格式字符串"""
    return dt.isoformat() if dt else None


def _str_to_datetime(s: str) -> Optional[datetime]:
    """将 ISO 格式字符串转换为 datetime"""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _enum_to_value(e: Enum) -> str:
    """将枚举转换为值"""
    return e.value if e else None


def _convert_to_dict(obj: Any) -> Any:
    """递归转换对象为可序列化的字典"""
    if obj is None:
        return None
    if isinstance(obj, datetime):
        return _datetime_to_str(obj)
    if isinstance(obj, Enum):
        return _enum_to_value(obj)
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: _convert_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_to_dict(item) for item in obj]
    return obj


# ============== 数据模型定义 ==============

@dataclass
class PluginManifest:
    """
    插件清单
    
    描述插件的核心元数据，包括标识、版本、依赖和权限等信息。
    """
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    entry_point: str
    category: PluginCategory = PluginCategory.COMMUNITY
    tags: List[str] = field(default_factory=list)
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    min_necorag_version: str = "0.1.0"
    max_necorag_version: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    permissions: List[PluginPermission] = field(default_factory=list)
    python_requires: str = ">=3.9"
    icon: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'plugin_type': _enum_to_value(self.plugin_type),
            'entry_point': self.entry_point,
            'category': _enum_to_value(self.category),
            'tags': self.tags.copy(),
            'license': self.license,
            'homepage': self.homepage,
            'repository': self.repository,
            'min_necorag_version': self.min_necorag_version,
            'max_necorag_version': self.max_necorag_version,
            'dependencies': self.dependencies.copy(),
            'permissions': [_enum_to_value(p) for p in self.permissions],
            'python_requires': self.python_requires,
            'icon': self.icon,
            'created_at': _datetime_to_str(self.created_at),
            'updated_at': _datetime_to_str(self.updated_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        """从字典创建"""
        return cls(
            plugin_id=data['plugin_id'],
            name=data['name'],
            version=data['version'],
            author=data['author'],
            description=data['description'],
            plugin_type=PluginType(data['plugin_type']),
            entry_point=data['entry_point'],
            category=PluginCategory(data.get('category', 'community')),
            tags=data.get('tags', []),
            license=data.get('license', 'MIT'),
            homepage=data.get('homepage', ''),
            repository=data.get('repository', ''),
            min_necorag_version=data.get('min_necorag_version', '0.1.0'),
            max_necorag_version=data.get('max_necorag_version'),
            dependencies=data.get('dependencies', {}),
            permissions=[PluginPermission(p) for p in data.get('permissions', [])],
            python_requires=data.get('python_requires', '>=3.9'),
            icon=data.get('icon', ''),
            created_at=_str_to_datetime(data.get('created_at')) or datetime.now(),
            updated_at=_str_to_datetime(data.get('updated_at')) or datetime.now(),
        )
    
    def validate(self) -> bool:
        """
        验证清单数据有效性
        
        Returns:
            bool: 验证是否通过
        """
        if not self.plugin_id or not self.plugin_id.strip():
            logger.warning("插件ID不能为空")
            return False
        if not self.name or not self.name.strip():
            logger.warning("插件名称不能为空")
            return False
        if not self.version or not self.version.strip():
            logger.warning("版本号不能为空")
            return False
        if not self.entry_point or not self.entry_point.strip():
            logger.warning("入口点不能为空")
            return False
        return True


@dataclass
class PluginRelease:
    """
    版本发布记录
    
    记录插件的每次发布信息，包括下载地址、校验和等。
    """
    plugin_id: str
    version: str
    release_id: str = field(default_factory=lambda: str(uuid4()))
    download_url: str = ""
    checksum_sha256: str = ""
    size_bytes: int = 0
    changelog: str = ""
    stability: ReleaseStability = ReleaseStability.STABLE
    published_at: datetime = field(default_factory=datetime.now)
    download_count: int = 0
    min_necorag_version: str = "0.1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'release_id': self.release_id,
            'plugin_id': self.plugin_id,
            'version': self.version,
            'download_url': self.download_url,
            'checksum_sha256': self.checksum_sha256,
            'size_bytes': self.size_bytes,
            'changelog': self.changelog,
            'stability': _enum_to_value(self.stability),
            'published_at': _datetime_to_str(self.published_at),
            'download_count': self.download_count,
            'min_necorag_version': self.min_necorag_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginRelease':
        """从字典创建"""
        return cls(
            release_id=data.get('release_id', str(uuid4())),
            plugin_id=data['plugin_id'],
            version=data['version'],
            download_url=data.get('download_url', ''),
            checksum_sha256=data.get('checksum_sha256', ''),
            size_bytes=data.get('size_bytes', 0),
            changelog=data.get('changelog', ''),
            stability=ReleaseStability(data.get('stability', 'stable')),
            published_at=_str_to_datetime(data.get('published_at')) or datetime.now(),
            download_count=data.get('download_count', 0),
            min_necorag_version=data.get('min_necorag_version', '0.1.0'),
        )


@dataclass
class PluginRating:
    """
    用户评分
    
    用户对插件的评分和评价，支持多维度评分。
    """
    plugin_id: str
    user_id: str
    score: float
    rating_id: str = field(default_factory=lambda: str(uuid4()))
    comment: str = ""
    dimensions: Dict[str, float] = field(default_factory=dict)
    helpful_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rating_id': self.rating_id,
            'plugin_id': self.plugin_id,
            'user_id': self.user_id,
            'score': self.score,
            'comment': self.comment,
            'dimensions': self.dimensions.copy(),
            'helpful_count': self.helpful_count,
            'created_at': _datetime_to_str(self.created_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginRating':
        """从字典创建"""
        return cls(
            rating_id=data.get('rating_id', str(uuid4())),
            plugin_id=data['plugin_id'],
            user_id=data['user_id'],
            score=float(data['score']),
            comment=data.get('comment', ''),
            dimensions=data.get('dimensions', {}),
            helpful_count=data.get('helpful_count', 0),
            created_at=_str_to_datetime(data.get('created_at')) or datetime.now(),
        )
    
    def validate(self) -> bool:
        """
        验证评分数据有效性
        
        Returns:
            bool: 验证是否通过（评分在1.0-5.0范围内）
        """
        if self.score < 1.0 or self.score > 5.0:
            logger.warning(f"评分 {self.score} 超出有效范围 [1.0, 5.0]")
            return False
        return True


@dataclass
class PluginInstallation:
    """
    安装记录
    
    记录插件的安装信息，包括路径、状态和配置。
    """
    plugin_id: str
    version: str
    installation_id: str = field(default_factory=lambda: str(uuid4()))
    install_path: str = ""
    status: InstallStatus = InstallStatus.ACTIVE
    config: Dict[str, Any] = field(default_factory=dict)
    installed_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'installation_id': self.installation_id,
            'plugin_id': self.plugin_id,
            'version': self.version,
            'install_path': self.install_path,
            'status': _enum_to_value(self.status),
            'config': _convert_to_dict(self.config),
            'installed_at': _datetime_to_str(self.installed_at),
            'updated_at': _datetime_to_str(self.updated_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginInstallation':
        """从字典创建"""
        return cls(
            installation_id=data.get('installation_id', str(uuid4())),
            plugin_id=data['plugin_id'],
            version=data['version'],
            install_path=data.get('install_path', ''),
            status=InstallStatus(data.get('status', 'active')),
            config=data.get('config', {}),
            installed_at=_str_to_datetime(data.get('installed_at')) or datetime.now(),
            updated_at=_str_to_datetime(data.get('updated_at')) or datetime.now(),
        )


@dataclass
class GDIScore:
    """
    GDI 全局期望指数
    
    综合评估插件质量的多维度评分系统。
    """
    plugin_id: str
    overall_score: float = 0.0
    code_quality: float = 0.0
    functionality: float = 0.0
    reliability: float = 0.0
    performance: float = 0.0
    user_experience: float = 0.0
    actual_usage: float = 0.0
    freshness: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'overall_score': self.overall_score,
            'code_quality': self.code_quality,
            'functionality': self.functionality,
            'reliability': self.reliability,
            'performance': self.performance,
            'user_experience': self.user_experience,
            'actual_usage': self.actual_usage,
            'freshness': self.freshness,
            'calculated_at': _datetime_to_str(self.calculated_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GDIScore':
        """从字典创建"""
        return cls(
            plugin_id=data['plugin_id'],
            overall_score=float(data.get('overall_score', 0.0)),
            code_quality=float(data.get('code_quality', 0.0)),
            functionality=float(data.get('functionality', 0.0)),
            reliability=float(data.get('reliability', 0.0)),
            performance=float(data.get('performance', 0.0)),
            user_experience=float(data.get('user_experience', 0.0)),
            actual_usage=float(data.get('actual_usage', 0.0)),
            freshness=float(data.get('freshness', 0.0)),
            calculated_at=_str_to_datetime(data.get('calculated_at')) or datetime.now(),
        )
    
    def calculate_overall(self) -> float:
        """
        按权重计算综合评分
        
        权重分配：
        - code_quality: 0.20
        - functionality: 0.15
        - reliability: 0.25
        - performance: 0.15
        - user_experience: 0.10
        - actual_usage: 0.15
        
        Returns:
            float: 综合评分
        """
        self.overall_score = (
            0.20 * self.code_quality +
            0.15 * self.functionality +
            0.25 * self.reliability +
            0.15 * self.performance +
            0.10 * self.user_experience +
            0.15 * self.actual_usage
        )
        self.calculated_at = datetime.now()
        return self.overall_score


@dataclass
class ResourceQuota:
    """
    资源配额
    
    定义插件可使用的系统资源限制。
    """
    memory_mb: int = 256
    cpu_percent: float = 50.0
    disk_mb: int = 100
    network_enabled: bool = True
    max_execution_time: int = 300  # 秒
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'memory_mb': self.memory_mb,
            'cpu_percent': self.cpu_percent,
            'disk_mb': self.disk_mb,
            'network_enabled': self.network_enabled,
            'max_execution_time': self.max_execution_time,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceQuota':
        """从字典创建"""
        return cls(
            memory_mb=data.get('memory_mb', 256),
            cpu_percent=float(data.get('cpu_percent', 50.0)),
            disk_mb=data.get('disk_mb', 100),
            network_enabled=data.get('network_enabled', True),
            max_execution_time=data.get('max_execution_time', 300),
        )


@dataclass
class SearchResult:
    """
    搜索结果
    
    插件市场搜索返回的结果集。
    """
    plugins: List[PluginManifest]
    total_count: int
    page: int
    page_size: int
    query: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugins': [p.to_dict() for p in self.plugins],
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'query': self.query,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """从字典创建"""
        return cls(
            plugins=[PluginManifest.from_dict(p) for p in data.get('plugins', [])],
            total_count=data.get('total_count', 0),
            page=data.get('page', 1),
            page_size=data.get('page_size', 20),
            query=data.get('query', ''),
        )


@dataclass
class InstallResult:
    """
    安装结果
    
    插件安装操作的返回结果。
    """
    success: bool
    plugin_id: str
    version: str
    message: str = ""
    installation: Optional[PluginInstallation] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'plugin_id': self.plugin_id,
            'version': self.version,
            'message': self.message,
            'installation': self.installation.to_dict() if self.installation else None,
            'errors': self.errors.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstallResult':
        """从字典创建"""
        installation_data = data.get('installation')
        return cls(
            success=data.get('success', False),
            plugin_id=data['plugin_id'],
            version=data['version'],
            message=data.get('message', ''),
            installation=PluginInstallation.from_dict(installation_data) if installation_data else None,
            errors=data.get('errors', []),
        )


@dataclass
class UpgradePath:
    """
    升级路径
    
    描述从当前版本到目标版本的升级路径。
    """
    plugin_id: str
    current_version: str
    target_version: str
    steps: List[str] = field(default_factory=list)
    is_compatible: bool = True
    breaking_changes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'current_version': self.current_version,
            'target_version': self.target_version,
            'steps': self.steps.copy(),
            'is_compatible': self.is_compatible,
            'breaking_changes': self.breaking_changes.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpgradePath':
        """从字典创建"""
        return cls(
            plugin_id=data['plugin_id'],
            current_version=data['current_version'],
            target_version=data['target_version'],
            steps=data.get('steps', []),
            is_compatible=data.get('is_compatible', True),
            breaking_changes=data.get('breaking_changes', []),
        )


@dataclass
class DependencyGraph:
    """
    依赖图
    
    表示插件之间的依赖关系。
    """
    nodes: Dict[str, str] = field(default_factory=dict)  # plugin_id -> version
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from_plugin, to_plugin)
    install_order: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'nodes': self.nodes.copy(),
            'edges': [list(edge) for edge in self.edges],
            'install_order': self.install_order.copy(),
            'conflicts': self.conflicts.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencyGraph':
        """从字典创建"""
        return cls(
            nodes=data.get('nodes', {}),
            edges=[tuple(edge) for edge in data.get('edges', [])],
            install_order=data.get('install_order', []),
            conflicts=data.get('conflicts', []),
        )


@dataclass
class VersionConflict:
    """
    版本冲突
    
    描述插件版本冲突的详细信息。
    """
    plugin_id: str
    required_by: Dict[str, str] = field(default_factory=dict)  # requester -> version_constraint
    available_versions: List[str] = field(default_factory=list)
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'required_by': self.required_by.copy(),
            'available_versions': self.available_versions.copy(),
            'message': self.message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionConflict':
        """从字典创建"""
        return cls(
            plugin_id=data['plugin_id'],
            required_by=data.get('required_by', {}),
            available_versions=data.get('available_versions', []),
            message=data.get('message', ''),
        )


@dataclass
class CanaryDeployment:
    """
    灰度部署
    
    描述插件的灰度发布配置和状态。
    """
    plugin_id: str
    current_version: str
    new_version: str
    deployment_id: str = field(default_factory=lambda: str(uuid4()))
    percentage: float = 0.1
    status: str = "pending"  # pending, running, promoted, rolled_back
    metrics: Dict[str, float] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'deployment_id': self.deployment_id,
            'plugin_id': self.plugin_id,
            'current_version': self.current_version,
            'new_version': self.new_version,
            'percentage': self.percentage,
            'status': self.status,
            'metrics': self.metrics.copy(),
            'started_at': _datetime_to_str(self.started_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanaryDeployment':
        """从字典创建"""
        return cls(
            deployment_id=data.get('deployment_id', str(uuid4())),
            plugin_id=data['plugin_id'],
            current_version=data['current_version'],
            new_version=data['new_version'],
            percentage=float(data.get('percentage', 0.1)),
            status=data.get('status', 'pending'),
            metrics=data.get('metrics', {}),
            started_at=_str_to_datetime(data.get('started_at')) or datetime.now(),
        )


@dataclass
class SyncResult:
    """
    同步结果
    
    插件仓库同步操作的返回结果。
    """
    success: bool
    source_name: str = ""
    new_plugins: int = 0
    updated_plugins: int = 0
    errors: List[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'source_name': self.source_name,
            'new_plugins': self.new_plugins,
            'updated_plugins': self.updated_plugins,
            'errors': self.errors.copy(),
            'synced_at': _datetime_to_str(self.synced_at),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncResult':
        """从字典创建"""
        return cls(
            success=data.get('success', False),
            source_name=data.get('source_name', ''),
            new_plugins=data.get('new_plugins', 0),
            updated_plugins=data.get('updated_plugins', 0),
            errors=data.get('errors', []),
            synced_at=_str_to_datetime(data.get('synced_at')) or datetime.now(),
        )
