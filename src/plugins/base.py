"""
插件基类定义
定义插件的标准接口和生命周期管理
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
import logging


class PluginType(Enum):
    """插件类型枚举"""
    PERCEPTION = "perception"      # 感知层插件
    MEMORY = "memory"             # 记忆层插件
    RETRIEVAL = "retrieval"       # 检索层插件
    REFINEMENT = "refinement"     # 巩固层插件
    RESPONSE = "response"         # 响应层插件
    CUSTOM = "custom"             # 自定义插件


class BasePlugin(ABC):
    """插件基类"""
    
    # ========== 市场元数据属性（带默认值，兼容现有子类）==========
    marketplace_id: str = ""               # 市场中的唯一 ID
    marketplace_version: str = "0.1.0"     # 版本号
    marketplace_author: str = ""            # 作者
    marketplace_category: str = "community" # 分类
    marketplace_tags: List[str] = []        # 标签
    marketplace_license: str = "MIT"
    marketplace_homepage: str = ""
    marketplace_repository: str = ""
    marketplace_min_necorag: str = "0.1.0"
    marketplace_max_necorag: Optional[str] = None
    marketplace_entry_point: str = ""
    
    # 权限声明
    required_permissions: List[str] = []    # 如 ["read_memory", "query_knowledge"]
    
    def __init__(self, plugin_id: str, name: str, version: str, plugin_type: PluginType):
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.plugin_type = plugin_type
        self.is_enabled = True
        self.config = {}
        self.logger = logging.getLogger(f"plugin.{plugin_id}")
        
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """依赖的其他插件列表"""
        pass
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化插件
        Args:
            config: 插件配置
        Returns:
            bool: 初始化是否成功
        """
        try:
            if config:
                self.config.update(config)
            
            self.logger.info(f"Initializing plugin: {self.name} v{self.version}")
            result = self._initialize()
            if result:
                self.logger.info(f"Plugin {self.name} initialized successfully")
            else:
                self.logger.error(f"Plugin {self.name} initialization failed")
            return result
        except Exception as e:
            self.logger.error(f"Plugin initialization error: {str(e)}")
            return False
    
    def cleanup(self) -> bool:
        """
        清理插件资源
        Returns:
            bool: 清理是否成功
        """
        try:
            self.logger.info(f"Cleaning up plugin: {self.name}")
            result = self._cleanup()
            if result:
                self.logger.info(f"Plugin {self.name} cleaned up successfully")
            else:
                self.logger.error(f"Plugin {self.name} cleanup failed")
            return result
        except Exception as e:
            self.logger.error(f"Plugin cleanup error: {str(e)}")
            return False
    
    def enable(self) -> bool:
        """启用插件"""
        if not self.is_enabled:
            try:
                result = self._enable()
                if result:
                    self.is_enabled = True
                    self.logger.info(f"Plugin {self.name} enabled")
                return result
            except Exception as e:
                self.logger.error(f"Failed to enable plugin {self.name}: {str(e)}")
                return False
        return True
    
    def disable(self) -> bool:
        """禁用插件"""
        if self.is_enabled:
            try:
                result = self._disable()
                if result:
                    self.is_enabled = False
                    self.logger.info(f"Plugin {self.name} disabled")
                return result
            except Exception as e:
                self.logger.error(f"Failed to disable plugin {self.name}: {str(e)}")
                return False
        return True
    
    @abstractmethod
    def _initialize(self) -> bool:
        """具体的初始化逻辑，由子类实现"""
        pass
    
    @abstractmethod
    def _cleanup(self) -> bool:
        """具体的清理逻辑，由子类实现"""
        pass
    
    def _enable(self) -> bool:
        """具体的启用逻辑，默认实现"""
        return True
    
    def _disable(self) -> bool:
        """具体的禁用逻辑，默认实现"""
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "type": self.plugin_type.value,
            "description": self.description,
            "enabled": self.is_enabled,
            "dependencies": self.dependencies
        }
    
    # ========== 市场集成方法 ==========
    
    @property
    def manifest(self) -> Optional[Any]:
        """
        生成与市场兼容的 PluginManifest 对象
        从现有 get_info() 和新增的 marketplace_* 属性构建
        使用 try-except 导入 marketplace.models，如果导入失败返回 None
        """
        try:
            from src.marketplace.models import PluginManifest, PluginType as MktPluginType, PluginCategory
            
            # 映射 PluginType
            type_mapping = {
                "perception": MktPluginType.PERCEPTION,
                "memory": MktPluginType.MEMORY,
                "retrieval": MktPluginType.RETRIEVAL,
                "refinement": MktPluginType.REFINEMENT,
                "response": MktPluginType.RESPONSE,
                "custom": MktPluginType.UTILITY,
            }
            mkt_type = type_mapping.get(self.plugin_type.value, MktPluginType.UTILITY)
            
            # 映射 PluginCategory
            category_mapping = {
                "official": PluginCategory.OFFICIAL,
                "certified": PluginCategory.CERTIFIED,
                "community": PluginCategory.COMMUNITY,
            }
            mkt_category = category_mapping.get(
                self.marketplace_category.lower(), 
                PluginCategory.COMMUNITY
            )
            
            return PluginManifest(
                plugin_id=self.marketplace_id or self.plugin_id,
                name=self.name,
                version=self.marketplace_version or self.version,
                author=self.marketplace_author,
                description=self.description,
                plugin_type=mkt_type,
                entry_point=self.marketplace_entry_point or f"{self.__class__.__module__}:{self.__class__.__name__}",
                category=mkt_category,
                tags=list(self.marketplace_tags) if self.marketplace_tags else [],
                license=self.marketplace_license,
                homepage=self.marketplace_homepage,
                repository=self.marketplace_repository,
                min_necorag_version=self.marketplace_min_necorag,
                max_necorag_version=self.marketplace_max_necorag,
                dependencies={},  # 转换为市场依赖格式
                permissions=[],   # 权限需要映射
            )
        except ImportError:
            self.logger.debug("marketplace.models not available, manifest property returns None")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to create manifest: {e}")
            return None
    
    def get_marketplace_info(self) -> Dict[str, Any]:
        """
        获取市场所需的元信息（纯字典格式，不依赖 marketplace 模块）
        合并 get_info() 和 marketplace_* 属性
        """
        base_info = self.get_info()
        marketplace_info = {
            "marketplace_id": self.marketplace_id or self.plugin_id,
            "marketplace_version": self.marketplace_version or self.version,
            "marketplace_author": self.marketplace_author,
            "marketplace_category": self.marketplace_category,
            "marketplace_tags": list(self.marketplace_tags) if self.marketplace_tags else [],
            "marketplace_license": self.marketplace_license,
            "marketplace_homepage": self.marketplace_homepage,
            "marketplace_repository": self.marketplace_repository,
            "marketplace_min_necorag": self.marketplace_min_necorag,
            "marketplace_max_necorag": self.marketplace_max_necorag,
            "marketplace_entry_point": self.marketplace_entry_point or f"{self.__class__.__module__}:{self.__class__.__name__}",
            "required_permissions": list(self.required_permissions) if self.required_permissions else [],
        }
        return {**base_info, **marketplace_info}
    
    # ========== 市场生命周期钩子（空实现，子类可覆盖）==========
    
    def on_marketplace_install(self, config: Optional[Dict] = None):
        """市场安装后回调"""
        pass
    
    def on_marketplace_uninstall(self):
        """市场卸载前回调"""
        pass
    
    def on_marketplace_upgrade(self, old_version: str, new_version: str):
        """市场升级后回调"""
        pass
    
    def on_marketplace_enable(self):
        """市场启用回调"""
        pass
    
    def on_marketplace_disable(self):
        """市场禁用回调"""
        pass


# 感知层插件基类
class PerceptionPlugin(BasePlugin):
    """感知层插件基类"""
    
    def __init__(self, plugin_id: str, name: str, version: str):
        super().__init__(plugin_id, name, version, PluginType.PERCEPTION)
    
    @abstractmethod
    def process_input(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        处理输入数据
        Args:
            data: 输入数据
            context: 上下文信息
        Returns:
            处理后的数据
        """
        pass


# 记忆层插件基类
class MemoryPlugin(BasePlugin):
    """记忆层插件基类"""
    
    def __init__(self, plugin_id: str, name: str, version: str):
        super().__init__(plugin_id, name, version, PluginType.MEMORY)
    
    @abstractmethod
    def store(self, data: Any, metadata: Dict[str, Any]) -> str:
        """
        存储数据到记忆层
        Args:
            data: 要存储的数据
            metadata: 元数据
        Returns:
            存储标识符
        """
        pass
    
    @abstractmethod
    def retrieve(self, query: Any, **kwargs) -> List[Any]:
        """
        从记忆层检索数据
        Args:
            query: 查询条件
            **kwargs: 其他参数
        Returns:
            检索结果列表
        """
        pass


# 检索层插件基类
class RetrievalPlugin(BasePlugin):
    """检索层插件基类"""
    
    def __init__(self, plugin_id: str, name: str, version: str):
        super().__init__(plugin_id, name, version, PluginType.RETRIEVAL)
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        执行检索操作
        Args:
            query: 查询字符串
            **kwargs: 检索参数
        Returns:
            检索结果列表
        """
        pass


# 巩固层插件基类
class RefinementPlugin(BasePlugin):
    """巩固层插件基类"""
    
    def __init__(self, plugin_id: str, name: str, version: str):
        super().__init__(plugin_id, name, version, PluginType.REFINEMENT)
    
    @abstractmethod
    def refine(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        精炼/巩固数据
        Args:
            data: 待精炼的数据
            context: 上下文信息
        Returns:
            精炼后的数据
        """
        pass


# 响应层插件基类
class ResponsePlugin(BasePlugin):
    """响应层插件基类"""
    
    def __init__(self, plugin_id: str, name: str, version: str):
        super().__init__(plugin_id, name, version, PluginType.RESPONSE)
    
    @abstractmethod
    def generate_response(self, data: Any, context: Dict[str, Any]) -> Any:
        """
        生成响应
        Args:
            data: 处理后的数据
            context: 上下文信息
        Returns:
            生成的响应
        """
        pass