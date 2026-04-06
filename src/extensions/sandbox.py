"""
NecoRAG 插件市场 - 沙箱隔离系统

提供插件权限声明验证、运行时权限强制执行和资源配额管理。
支持 4 级权限级别：MINIMAL / STANDARD / ELEVATED / FULL。
"""

import os
import sys
import time
import threading
import logging
import platform
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager

from .models import (
    PluginManifest, PluginPermission, PermissionLevel,
    ResourceQuota, PluginCategory, _datetime_to_str, _enum_to_value
)

logger = logging.getLogger(__name__)

# 平台检测
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'
IS_WINDOWS = platform.system() == 'Windows'

# 尝试导入 resource 模块（Unix 系统）
try:
    import resource as sys_resource
    HAS_RESOURCE_MODULE = True
except ImportError:
    HAS_RESOURCE_MODULE = False
    logger.debug("resource 模块不可用，资源限制功能将受限")

# 尝试导入 psutil 用于更精确的资源监控
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.debug("psutil 模块不可用，资源监控将使用基础方法")


# ============== 权限级别定义 ==============

# 各权限级别允许的权限集合
PERMISSION_LEVEL_GRANTS: Dict[PermissionLevel, Set[PluginPermission]] = {
    PermissionLevel.MINIMAL: {
        PluginPermission.QUERY_KNOWLEDGE,
        PluginPermission.READ_FILES,
    },
    PermissionLevel.STANDARD: {
        PluginPermission.READ_MEMORY,
        PluginPermission.QUERY_KNOWLEDGE,
        PluginPermission.READ_FILES,
        PluginPermission.CALL_LLM,
        PluginPermission.NETWORK_REQUEST,
    },
    PermissionLevel.ELEVATED: {
        PluginPermission.READ_MEMORY,
        PluginPermission.WRITE_MEMORY,
        PluginPermission.QUERY_KNOWLEDGE,
        PluginPermission.MANAGE_INDEX,
        PluginPermission.CONFIG_RAG,
        PluginPermission.CALL_LLM,
        PluginPermission.NETWORK_REQUEST,
        PluginPermission.READ_FILES,
        PluginPermission.WRITE_FILES,
        PluginPermission.WEBHOOK,
    },
    PermissionLevel.FULL: set(PluginPermission),  # 所有权限
}

# 插件分类到默认权限级别的映射
CATEGORY_DEFAULT_LEVEL: Dict[PluginCategory, PermissionLevel] = {
    PluginCategory.OFFICIAL: PermissionLevel.FULL,
    PluginCategory.CERTIFIED: PermissionLevel.ELEVATED,
    PluginCategory.COMMUNITY: PermissionLevel.STANDARD,
}

# 敏感权限及其警告信息
SENSITIVE_PERMISSIONS: Dict[PluginPermission, str] = {
    PluginPermission.DELETE_MEMORY: "插件请求了删除记忆的权限，可能导致数据丢失",
    PluginPermission.MANAGE_USERS: "插件请求了用户管理权限，可能影响系统安全",
    PluginPermission.MANAGE_PLUGINS: "插件请求了插件管理权限，可能导致系统不稳定",
    PluginPermission.WRITE_FILES: "插件请求了文件写入权限，请确认其用途",
    PluginPermission.CONFIG_RAG: "插件请求了修改 RAG 配置的权限，可能影响系统行为",
}


# ============== 数据模型 ==============

@dataclass
class ValidationResult:
    """权限验证结果"""
    valid: bool
    plugin_id: str
    requested_permissions: List[PluginPermission] = field(default_factory=list)
    granted_permissions: List[PluginPermission] = field(default_factory=list)
    denied_permissions: List[PluginPermission] = field(default_factory=list)
    permission_level: PermissionLevel = PermissionLevel.STANDARD
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'valid': self.valid,
            'plugin_id': self.plugin_id,
            'requested_permissions': [_enum_to_value(p) for p in self.requested_permissions],
            'granted_permissions': [_enum_to_value(p) for p in self.granted_permissions],
            'denied_permissions': [_enum_to_value(p) for p in self.denied_permissions],
            'permission_level': _enum_to_value(self.permission_level),
            'warnings': self.warnings.copy(),
            'errors': self.errors.copy(),
        }


@dataclass
class ResourceUsage:
    """资源使用情况"""
    plugin_id: str
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    disk_mb: float = 0.0
    execution_time_seconds: float = 0.0
    within_quota: bool = True
    violations: List[str] = field(default_factory=list)
    measured_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'memory_mb': self.memory_mb,
            'cpu_percent': self.cpu_percent,
            'disk_mb': self.disk_mb,
            'execution_time_seconds': self.execution_time_seconds,
            'within_quota': self.within_quota,
            'violations': self.violations.copy(),
            'measured_at': _datetime_to_str(self.measured_at),
        }


@dataclass
class SandboxContext:
    """沙箱执行上下文"""
    plugin_id: str
    permission_level: PermissionLevel
    granted_permissions: Set[PluginPermission]
    resource_quota: ResourceQuota
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    start_time: float = field(default_factory=time.time)
    
    def has_permission(self, permission: PluginPermission) -> bool:
        """
        检查是否有指定权限
        
        Args:
            permission: 要检查的权限
            
        Returns:
            bool: 是否拥有该权限
        """
        return permission in self.granted_permissions
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'permission_level': _enum_to_value(self.permission_level),
            'granted_permissions': [_enum_to_value(p) for p in self.granted_permissions],
            'resource_quota': self.resource_quota.to_dict(),
            'created_at': _datetime_to_str(self.created_at),
            'is_active': self.is_active,
        }


# ============== 沙箱主类 ==============

class PluginSandbox:
    """
    插件沙箱隔离系统
    
    提供插件权限验证、运行时权限检查和资源配额管理功能。
    支持四级权限模型：MINIMAL、STANDARD、ELEVATED、FULL。
    
    使用示例:
        sandbox = PluginSandbox(enabled=True)
        
        # 验证插件权限
        result = sandbox.validate_permissions(manifest)
        if result.valid:
            # 创建沙箱上下文
            with sandbox.sandbox_scope(manifest) as ctx:
                if ctx.has_permission(PluginPermission.READ_MEMORY):
                    # 执行需要权限的操作
                    pass
    """
    
    def __init__(
        self,
        enabled: bool = True,
        default_level: PermissionLevel = PermissionLevel.STANDARD,
        default_quota: Optional[ResourceQuota] = None
    ):
        """
        初始化沙箱系统
        
        Args:
            enabled: 是否启用沙箱隔离
            default_level: 默认权限级别
            default_quota: 默认资源配额
        """
        self.enabled = enabled
        self.default_level = default_level
        self.default_quota = default_quota or ResourceQuota()
        
        # 运行时状态管理
        self._active_contexts: Dict[str, SandboxContext] = {}
        self._resource_usage: Dict[str, ResourceUsage] = {}
        self._permission_overrides: Dict[str, PermissionLevel] = {}
        self._quota_overrides: Dict[str, ResourceQuota] = {}
        self._lock = threading.Lock()
        
        logger.info(f"沙箱系统初始化完成，状态: {'启用' if enabled else '禁用'}")
    
    # ============== 权限验证 ==============
    
    def validate_permissions(
        self,
        manifest: PluginManifest,
        override_level: Optional[PermissionLevel] = None
    ) -> ValidationResult:
        """
        验证插件权限声明
        
        流程:
        1. 确定插件的权限级别（override > 自定义覆盖 > 分类默认）
        2. 获取该级别允许的权限集合
        3. 对比插件请求的权限
        4. 标记被拒绝的权限
        5. 生成警告（如请求敏感权限）
        
        Args:
            manifest: 插件清单
            override_level: 强制使用的权限级别（可选）
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            plugin_id = manifest.plugin_id
            
            # 获取有效权限级别
            level = self._get_permission_level(manifest, override_level)
            
            # 获取该级别允许的权限
            allowed_permissions = PERMISSION_LEVEL_GRANTS.get(level, set())
            
            # 分析请求的权限
            requested = list(manifest.permissions)
            granted = []
            denied = []
            
            for perm in requested:
                if perm in allowed_permissions:
                    granted.append(perm)
                else:
                    denied.append(perm)
            
            # 检查敏感权限生成警告
            warnings = self._check_sensitive_permissions(requested)
            
            # 生成错误信息
            errors = []
            if denied:
                denied_names = [p.value for p in denied]
                errors.append(f"以下权限被拒绝: {', '.join(denied_names)}")
            
            # 验证是否通过（没有被拒绝的权限，或沙箱未启用）
            valid = len(denied) == 0 or not self.enabled
            
            result = ValidationResult(
                valid=valid,
                plugin_id=plugin_id,
                requested_permissions=requested,
                granted_permissions=granted,
                denied_permissions=denied,
                permission_level=level,
                warnings=warnings,
                errors=errors,
            )
            
            if denied:
                logger.warning(
                    f"插件 {plugin_id} 权限验证: "
                    f"请求 {len(requested)} 项, 授予 {len(granted)} 项, "
                    f"拒绝 {len(denied)} 项"
                )
            else:
                logger.debug(f"插件 {plugin_id} 权限验证通过，授予 {len(granted)} 项权限")
            
            return result
            
        except Exception as e:
            logger.error(f"权限验证失败: {e}")
            return ValidationResult(
                valid=False,
                plugin_id=manifest.plugin_id if manifest else "unknown",
                errors=[f"验证过程出错: {str(e)}"],
            )
    
    def _get_permission_level(
        self,
        manifest: PluginManifest,
        override: Optional[PermissionLevel] = None
    ) -> PermissionLevel:
        """
        获取插件的有效权限级别
        
        优先级: override参数 > 自定义覆盖 > 分类默认 > 系统默认
        
        Args:
            manifest: 插件清单
            override: 强制覆盖的权限级别
            
        Returns:
            PermissionLevel: 有效的权限级别
        """
        # 优先使用传入的覆盖值
        if override is not None:
            return override
        
        # 检查是否有自定义覆盖
        with self._lock:
            if manifest.plugin_id in self._permission_overrides:
                return self._permission_overrides[manifest.plugin_id]
        
        # 根据插件分类确定默认级别
        category_level = CATEGORY_DEFAULT_LEVEL.get(manifest.category)
        if category_level is not None:
            return category_level
        
        # 返回系统默认级别
        return self.default_level
    
    def _check_sensitive_permissions(
        self,
        permissions: List[PluginPermission]
    ) -> List[str]:
        """
        检查敏感权限并生成警告
        
        Args:
            permissions: 权限列表
            
        Returns:
            List[str]: 警告信息列表
        """
        warnings = []
        for perm in permissions:
            if perm in SENSITIVE_PERMISSIONS:
                warnings.append(SENSITIVE_PERMISSIONS[perm])
        return warnings
    
    # ============== 运行时权限检查 ==============
    
    def check_permission(
        self,
        plugin_id: str,
        permission: PluginPermission
    ) -> bool:
        """
        运行时检查插件是否有执行特定操作的权限
        
        Args:
            plugin_id: 插件ID
            permission: 要检查的权限
            
        Returns:
            bool: 是否有权限（沙箱未启用时始终返回 True）
        """
        if not self.enabled:
            return True
        
        with self._lock:
            context = self._active_contexts.get(plugin_id)
            if context is None:
                logger.warning(f"插件 {plugin_id} 没有活跃的沙箱上下文")
                return False
            
            has_perm = context.has_permission(permission)
            
            if not has_perm:
                logger.warning(
                    f"权限拒绝: 插件 {plugin_id} 尝试使用权限 {permission.value}"
                )
            
            return has_perm
    
    def check_permissions(
        self,
        plugin_id: str,
        permissions: List[PluginPermission]
    ) -> Dict[PluginPermission, bool]:
        """
        批量检查权限
        
        Args:
            plugin_id: 插件ID
            permissions: 要检查的权限列表
            
        Returns:
            Dict[PluginPermission, bool]: 每个权限的检查结果
        """
        return {
            perm: self.check_permission(plugin_id, perm)
            for perm in permissions
        }
    
    # ============== 资源配额管理 ==============
    
    def set_quota(self, plugin_id: str, quota: ResourceQuota) -> bool:
        """
        为插件设置自定义资源配额
        
        Args:
            plugin_id: 插件ID
            quota: 资源配额
            
        Returns:
            bool: 是否设置成功
        """
        try:
            with self._lock:
                self._quota_overrides[plugin_id] = quota
            logger.info(f"已为插件 {plugin_id} 设置自定义资源配额")
            return True
        except Exception as e:
            logger.error(f"设置资源配额失败: {e}")
            return False
    
    def get_quota(self, plugin_id: str) -> ResourceQuota:
        """
        获取插件的资源配额
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            ResourceQuota: 自定义配额或默认配额
        """
        with self._lock:
            return self._quota_overrides.get(plugin_id, self.default_quota)
    
    def monitor_usage(self, plugin_id: str) -> ResourceUsage:
        """
        监控插件资源使用情况
        
        检测:
        - 内存使用
        - CPU 占用
        - 磁盘使用
        - 执行时间
        - 是否超出配额
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            ResourceUsage: 资源使用情况
        """
        usage = ResourceUsage(
            plugin_id=plugin_id,
            measured_at=datetime.now()
        )
        
        try:
            with self._lock:
                context = self._active_contexts.get(plugin_id)
            
            # 计算执行时间
            if context:
                usage.execution_time_seconds = time.time() - context.start_time
            
            # 获取内存和 CPU 使用（使用 psutil 如果可用）
            if HAS_PSUTIL:
                try:
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    usage.memory_mb = memory_info.rss / (1024 * 1024)
                    usage.cpu_percent = process.cpu_percent(interval=0.1)
                except Exception as e:
                    logger.debug(f"psutil 获取资源信息失败: {e}")
            elif HAS_RESOURCE_MODULE and not IS_WINDOWS:
                try:
                    # 使用 resource 模块获取内存使用（Unix 系统）
                    rusage = sys_resource.getrusage(sys_resource.RUSAGE_SELF)
                    # macOS 上 ru_maxrss 单位是字节，Linux 上是 KB
                    if IS_MACOS:
                        usage.memory_mb = rusage.ru_maxrss / (1024 * 1024)
                    else:
                        usage.memory_mb = rusage.ru_maxrss / 1024
                except Exception as e:
                    logger.debug(f"resource 模块获取资源信息失败: {e}")
            
            # 检查配额违规
            quota = self.get_quota(plugin_id)
            violations = self.check_quota_violation(plugin_id, usage)
            usage.violations = violations
            usage.within_quota = len(violations) == 0
            
            # 更新资源使用记录
            with self._lock:
                self._resource_usage[plugin_id] = usage
            
        except Exception as e:
            logger.error(f"监控资源使用失败: {e}")
            usage.violations.append(f"监控失败: {str(e)}")
            usage.within_quota = False
        
        return usage
    
    def check_quota_violation(
        self,
        plugin_id: str,
        usage: ResourceUsage
    ) -> List[str]:
        """
        检查资源使用是否违反配额
        
        Args:
            plugin_id: 插件ID
            usage: 资源使用情况
            
        Returns:
            List[str]: 违规信息列表
        """
        violations = []
        quota = self.get_quota(plugin_id)
        
        # 检查内存限制
        if usage.memory_mb > quota.memory_mb:
            violations.append(
                f"内存使用超限: {usage.memory_mb:.1f}MB > {quota.memory_mb}MB"
            )
            logger.warning(f"插件 {plugin_id} 内存使用超限")
        
        # 检查 CPU 限制
        if usage.cpu_percent > quota.cpu_percent:
            violations.append(
                f"CPU 使用超限: {usage.cpu_percent:.1f}% > {quota.cpu_percent}%"
            )
            logger.warning(f"插件 {plugin_id} CPU 使用超限")
        
        # 检查磁盘限制
        if usage.disk_mb > quota.disk_mb:
            violations.append(
                f"磁盘使用超限: {usage.disk_mb:.1f}MB > {quota.disk_mb}MB"
            )
            logger.warning(f"插件 {plugin_id} 磁盘使用超限")
        
        # 检查执行时间限制
        if usage.execution_time_seconds > quota.max_execution_time:
            violations.append(
                f"执行时间超限: {usage.execution_time_seconds:.1f}s > {quota.max_execution_time}s"
            )
            logger.warning(f"插件 {plugin_id} 执行时间超限")
        
        return violations
    
    # ============== 沙箱上下文管理 ==============
    
    def create_context(self, manifest: PluginManifest) -> SandboxContext:
        """
        为插件创建沙箱执行上下文
        
        1. 验证权限
        2. 分配资源配额
        3. 注册到活跃上下文
        
        Args:
            manifest: 插件清单
            
        Returns:
            SandboxContext: 沙箱上下文
        """
        plugin_id = manifest.plugin_id
        
        # 验证权限
        validation = self.validate_permissions(manifest)
        
        # 获取资源配额
        quota = self.get_quota(plugin_id)
        
        # 创建上下文
        context = SandboxContext(
            plugin_id=plugin_id,
            permission_level=validation.permission_level,
            granted_permissions=set(validation.granted_permissions),
            resource_quota=quota,
            created_at=datetime.now(),
            is_active=True,
            start_time=time.time(),
        )
        
        # 注册上下文
        with self._lock:
            self._active_contexts[plugin_id] = context
        
        logger.info(
            f"为插件 {plugin_id} 创建沙箱上下文，"
            f"权限级别: {validation.permission_level.value}，"
            f"授予权限数: {len(context.granted_permissions)}"
        )
        
        return context
    
    def get_context(self, plugin_id: str) -> Optional[SandboxContext]:
        """
        获取插件的沙箱上下文
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[SandboxContext]: 沙箱上下文，不存在则返回 None
        """
        with self._lock:
            return self._active_contexts.get(plugin_id)
    
    def destroy_context(self, plugin_id: str) -> bool:
        """
        销毁插件的沙箱上下文
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否销毁成功
        """
        try:
            with self._lock:
                if plugin_id in self._active_contexts:
                    context = self._active_contexts.pop(plugin_id)
                    context.is_active = False
                    logger.info(f"销毁插件 {plugin_id} 的沙箱上下文")
                    return True
                else:
                    logger.debug(f"插件 {plugin_id} 没有活跃的沙箱上下文")
                    return False
        except Exception as e:
            logger.error(f"销毁沙箱上下文失败: {e}")
            return False
    
    @contextmanager
    def sandbox_scope(self, manifest: PluginManifest):
        """
        上下文管理器：在沙箱范围内执行插件代码
        
        自动创建和销毁沙箱上下文，确保资源清理。
        
        Args:
            manifest: 插件清单
            
        Yields:
            SandboxContext: 沙箱上下文
            
        使用示例:
            with sandbox.sandbox_scope(manifest) as ctx:
                if ctx.has_permission(PluginPermission.READ_MEMORY):
                    # 在沙箱环境中执行
                    pass
        """
        plugin_id = manifest.plugin_id
        context = None
        
        try:
            # 创建沙箱上下文
            context = self.create_context(manifest)
            yield context
            
        except Exception as e:
            logger.error(f"沙箱执行过程出错: {e}")
            raise
            
        finally:
            # 确保清理上下文
            if context is not None:
                # 记录最终资源使用情况
                try:
                    self.monitor_usage(plugin_id)
                except Exception as e:
                    logger.debug(f"最终资源监控失败: {e}")
                
                # 销毁上下文
                self.destroy_context(plugin_id)
    
    # ============== 权限级别管理 ==============
    
    def set_permission_level(
        self,
        plugin_id: str,
        level: PermissionLevel
    ) -> bool:
        """
        设置插件的权限级别覆盖
        
        Args:
            plugin_id: 插件ID
            level: 权限级别
            
        Returns:
            bool: 是否设置成功
        """
        try:
            with self._lock:
                self._permission_overrides[plugin_id] = level
            logger.info(f"设置插件 {plugin_id} 权限级别为 {level.value}")
            return True
        except Exception as e:
            logger.error(f"设置权限级别失败: {e}")
            return False
    
    def get_permission_level(self, plugin_id: str) -> PermissionLevel:
        """
        获取插件的当前权限级别
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            PermissionLevel: 当前权限级别
        """
        with self._lock:
            return self._permission_overrides.get(plugin_id, self.default_level)
    
    def reset_permission_level(self, plugin_id: str) -> bool:
        """
        重置为默认权限级别
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否重置成功
        """
        try:
            with self._lock:
                if plugin_id in self._permission_overrides:
                    del self._permission_overrides[plugin_id]
                    logger.info(f"重置插件 {plugin_id} 权限级别为默认值")
                    return True
                return False
        except Exception as e:
            logger.error(f"重置权限级别失败: {e}")
            return False
    
    # ============== 安全审计 ==============
    
    def get_active_contexts(self) -> Dict[str, SandboxContext]:
        """
        获取所有活跃的沙箱上下文
        
        Returns:
            Dict[str, SandboxContext]: 插件ID到上下文的映射
        """
        with self._lock:
            return self._active_contexts.copy()
    
    def get_all_resource_usage(self) -> Dict[str, ResourceUsage]:
        """
        获取所有插件的资源使用情况
        
        Returns:
            Dict[str, ResourceUsage]: 插件ID到资源使用的映射
        """
        with self._lock:
            return self._resource_usage.copy()
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        生成安全报告
        
        Returns:
            dict: 安全报告，包含:
                - total_active: 活跃上下文数量
                - by_level: 各权限级别的插件数量
                - quota_violations: 配额违规列表
                - sensitive_permissions_granted: 已授予敏感权限的插件列表
        """
        report: Dict[str, Any] = {
            'total_active': 0,
            'by_level': {level.value: 0 for level in PermissionLevel},
            'quota_violations': [],
            'sensitive_permissions_granted': [],
            'generated_at': _datetime_to_str(datetime.now()),
        }
        
        try:
            with self._lock:
                contexts = self._active_contexts.copy()
                usage_records = self._resource_usage.copy()
            
            report['total_active'] = len(contexts)
            
            for plugin_id, context in contexts.items():
                # 统计权限级别分布
                level_key = context.permission_level.value
                report['by_level'][level_key] = report['by_level'].get(level_key, 0) + 1
                
                # 检查敏感权限
                for perm in context.granted_permissions:
                    if perm in SENSITIVE_PERMISSIONS:
                        report['sensitive_permissions_granted'].append({
                            'plugin_id': plugin_id,
                            'permission': perm.value,
                            'warning': SENSITIVE_PERMISSIONS[perm],
                        })
            
            # 收集配额违规
            for plugin_id, usage in usage_records.items():
                if not usage.within_quota:
                    report['quota_violations'].append({
                        'plugin_id': plugin_id,
                        'violations': usage.violations,
                        'measured_at': _datetime_to_str(usage.measured_at),
                    })
            
        except Exception as e:
            logger.error(f"生成安全报告失败: {e}")
            report['error'] = str(e)
        
        return report
    
    # ============== 清理 ==============
    
    def cleanup(self) -> None:
        """
        清理所有沙箱上下文和资源
        """
        try:
            with self._lock:
                # 标记所有上下文为非活跃
                for context in self._active_contexts.values():
                    context.is_active = False
                
                count = len(self._active_contexts)
                
                # 清空所有状态
                self._active_contexts.clear()
                self._resource_usage.clear()
                self._permission_overrides.clear()
                self._quota_overrides.clear()
            
            logger.info(f"沙箱系统清理完成，已销毁 {count} 个上下文")
            
        except Exception as e:
            logger.error(f"清理沙箱系统失败: {e}")
    
    def cleanup_plugin(self, plugin_id: str) -> None:
        """
        清理特定插件的沙箱状态
        
        Args:
            plugin_id: 插件ID
        """
        try:
            with self._lock:
                # 销毁上下文
                if plugin_id in self._active_contexts:
                    self._active_contexts[plugin_id].is_active = False
                    del self._active_contexts[plugin_id]
                
                # 清理资源使用记录
                if plugin_id in self._resource_usage:
                    del self._resource_usage[plugin_id]
                
                # 清理权限覆盖
                if plugin_id in self._permission_overrides:
                    del self._permission_overrides[plugin_id]
                
                # 清理配额覆盖
                if plugin_id in self._quota_overrides:
                    del self._quota_overrides[plugin_id]
            
            logger.info(f"已清理插件 {plugin_id} 的沙箱状态")
            
        except Exception as e:
            logger.error(f"清理插件 {plugin_id} 沙箱状态失败: {e}")
