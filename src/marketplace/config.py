"""
NecoRAG 插件市场配置

提供插件市场的全局配置管理，包括：
- 存储路径配置
- 仓库源配置
- 沙箱和权限配置
- 搜索和更新配置
- GDI 评分权重配置
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
import json
import logging

from .models import PermissionLevel, ResourceQuota

logger = logging.getLogger(__name__)


@dataclass
class MarketplaceConfig:
    """
    插件市场配置
    
    管理插件市场的所有配置项，包括存储、仓库源、沙箱和评分等。
    """
    
    # ============== 存储配置 ==============
    db_path: str = ""  # 默认 ~/.necorag/marketplace/db/marketplace.db
    plugins_dir: str = ""  # 默认 ~/.necorag/marketplace/plugins/
    cache_dir: str = ""  # 默认 ~/.necorag/marketplace/cache/
    
    # ============== 仓库源配置 ==============
    # 每项格式: {"name": "official", "url": "...", "type": "local|github|gitee|http"}
    repo_sources: List[Dict[str, str]] = field(default_factory=list)
    
    # ============== 沙箱配置 ==============
    sandbox_enabled: bool = True
    default_permission_level: PermissionLevel = PermissionLevel.STANDARD
    default_resource_quota: ResourceQuota = field(default_factory=ResourceQuota)
    
    # ============== 搜索配置 ==============
    search_page_size: int = 20
    
    # ============== 自动更新配置 ==============
    auto_check_updates: bool = True
    auto_update_interval_hours: int = 24
    
    # ============== GDI 评分权重 ==============
    gdi_weights: Dict[str, float] = field(default_factory=lambda: {
        'code_quality': 0.20,
        'functionality': 0.15,
        'reliability': 0.25,
        'performance': 0.15,
        'user_experience': 0.10,
        'actual_usage': 0.15,
    })
    
    def __post_init__(self):
        """设置默认路径"""
        base = Path.home() / '.necorag' / 'marketplace'
        
        if not self.db_path:
            self.db_path = str(base / 'db' / 'marketplace.db')
        if not self.plugins_dir:
            self.plugins_dir = str(base / 'plugins')
        if not self.cache_dir:
            self.cache_dir = str(base / 'cache')
        
        # 确保 default_resource_quota 是 ResourceQuota 类型
        if isinstance(self.default_resource_quota, dict):
            self.default_resource_quota = ResourceQuota.from_dict(self.default_resource_quota)
        
        # 确保 default_permission_level 是 PermissionLevel 类型
        if isinstance(self.default_permission_level, str):
            self.default_permission_level = PermissionLevel(self.default_permission_level)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'db_path': self.db_path,
            'plugins_dir': self.plugins_dir,
            'cache_dir': self.cache_dir,
            'repo_sources': [src.copy() for src in self.repo_sources],
            'sandbox_enabled': self.sandbox_enabled,
            'default_permission_level': self.default_permission_level.value,
            'default_resource_quota': self.default_resource_quota.to_dict(),
            'search_page_size': self.search_page_size,
            'auto_check_updates': self.auto_check_updates,
            'auto_update_interval_hours': self.auto_update_interval_hours,
            'gdi_weights': self.gdi_weights.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketplaceConfig':
        """从字典创建"""
        # 处理 PermissionLevel 枚举
        permission_level = data.get('default_permission_level', 'standard')
        if isinstance(permission_level, str):
            permission_level = PermissionLevel(permission_level)
        
        # 处理 ResourceQuota
        quota_data = data.get('default_resource_quota', {})
        if isinstance(quota_data, dict):
            quota = ResourceQuota.from_dict(quota_data)
        else:
            quota = quota_data
        
        return cls(
            db_path=data.get('db_path', ''),
            plugins_dir=data.get('plugins_dir', ''),
            cache_dir=data.get('cache_dir', ''),
            repo_sources=data.get('repo_sources', []),
            sandbox_enabled=data.get('sandbox_enabled', True),
            default_permission_level=permission_level,
            default_resource_quota=quota,
            search_page_size=data.get('search_page_size', 20),
            auto_check_updates=data.get('auto_check_updates', True),
            auto_update_interval_hours=data.get('auto_update_interval_hours', 24),
            gdi_weights=data.get('gdi_weights', {
                'code_quality': 0.20,
                'functionality': 0.15,
                'reliability': 0.25,
                'performance': 0.15,
                'user_experience': 0.10,
                'actual_usage': 0.15,
            }),
        )
    
    def ensure_directories(self) -> None:
        """
        创建必要的目录
        
        确保数据库目录、插件目录和缓存目录存在。
        """
        directories = [
            Path(self.db_path).parent,
            Path(self.plugins_dir),
            Path(self.cache_dir),
        ]
        
        for dir_path in directories:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"确保目录存在: {dir_path}")
            except OSError as e:
                logger.error(f"创建目录失败 {dir_path}: {e}")
                raise
    
    def save(self, path: str) -> None:
        """
        保存配置到文件
        
        Args:
            path: 配置文件路径
        """
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"配置已保存到: {path}")
    
    @classmethod
    def load(cls, path: str) -> 'MarketplaceConfig':
        """
        从文件加载配置
        
        Args:
            path: 配置文件路径
            
        Returns:
            MarketplaceConfig: 配置对象
        """
        config_path = Path(path)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {path}，使用默认配置")
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"从文件加载配置: {path}")
        return cls.from_dict(data)
    
    def add_repo_source(
        self, 
        name: str, 
        url: str, 
        source_type: str = "http"
    ) -> None:
        """
        添加仓库源
        
        Args:
            name: 仓库源名称
            url: 仓库源 URL
            source_type: 仓库类型 (local|github|gitee|http)
        """
        # 检查是否已存在同名源
        for source in self.repo_sources:
            if source.get('name') == name:
                logger.warning(f"仓库源 '{name}' 已存在，将更新配置")
                source['url'] = url
                source['type'] = source_type
                return
        
        self.repo_sources.append({
            'name': name,
            'url': url,
            'type': source_type,
        })
        logger.info(f"添加仓库源: {name} ({source_type})")
    
    def remove_repo_source(self, name: str) -> bool:
        """
        移除仓库源
        
        Args:
            name: 仓库源名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, source in enumerate(self.repo_sources):
            if source.get('name') == name:
                self.repo_sources.pop(i)
                logger.info(f"移除仓库源: {name}")
                return True
        
        logger.warning(f"未找到仓库源: {name}")
        return False
    
    def get_repo_source(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取指定仓库源配置
        
        Args:
            name: 仓库源名称
            
        Returns:
            Optional[Dict[str, str]]: 仓库源配置，不存在则返回 None
        """
        for source in self.repo_sources:
            if source.get('name') == name:
                return source.copy()
        return None


def load_marketplace_config(
    config_path: Optional[str] = None,
    env_prefix: str = "NECORAG_MARKETPLACE"
) -> MarketplaceConfig:
    """
    加载插件市场配置
    
    优先级：环境变量 > 配置文件 > 默认值
    
    Args:
        config_path: 配置文件路径
        env_prefix: 环境变量前缀
        
    Returns:
        MarketplaceConfig: 配置对象
    """
    # 从配置文件加载或使用默认配置
    if config_path and Path(config_path).exists():
        config = MarketplaceConfig.load(config_path)
    else:
        config = MarketplaceConfig()
    
    # 从环境变量覆盖
    env_mappings = {
        f"{env_prefix}_DB_PATH": "db_path",
        f"{env_prefix}_PLUGINS_DIR": "plugins_dir",
        f"{env_prefix}_CACHE_DIR": "cache_dir",
        f"{env_prefix}_SANDBOX_ENABLED": "sandbox_enabled",
        f"{env_prefix}_SEARCH_PAGE_SIZE": "search_page_size",
        f"{env_prefix}_AUTO_CHECK_UPDATES": "auto_check_updates",
        f"{env_prefix}_AUTO_UPDATE_INTERVAL": "auto_update_interval_hours",
    }
    
    for env_key, attr_name in env_mappings.items():
        env_value = os.environ.get(env_key)
        if env_value is not None:
            # 类型转换
            if attr_name in ('sandbox_enabled', 'auto_check_updates'):
                value = env_value.lower() in ('true', '1', 'yes')
            elif attr_name in ('search_page_size', 'auto_update_interval_hours'):
                value = int(env_value)
            else:
                value = env_value
            
            setattr(config, attr_name, value)
            logger.debug(f"从环境变量 {env_key} 加载配置: {attr_name}={value}")
    
    return config
