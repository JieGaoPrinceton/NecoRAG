"""
NecoRAG 插件市场 - 插件安装器

管理插件的完整生命周期：安装、卸载、升级、回滚和批量操作。
"""

import os
import json
import shutil
import hashlib
import zipfile
import tarfile
import tempfile
import logging
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from .models import (
    PluginManifest, PluginRelease, PluginInstallation, InstallResult,
    InstallStatus, PluginCategory, ResourceQuota, ReleaseStability
)
from .store import MarketplaceStore
from .version_manager import VersionManager
from .dependency_resolver import DependencyResolver
from .sandbox import PluginSandbox

logger = logging.getLogger(__name__)


def _safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    """安全解压 tar 文件，防止目录遍历攻击"""
    base = os.path.abspath(str(dest))
    for member in tf.getmembers():
        member_path = os.path.abspath(os.path.join(base, member.name))
        if not member_path.startswith(base + os.sep) and member_path != base:
            raise ValueError(f"检测到不安全的 tar 成员路径: {member.name}")
        # 额外检查：禁止绝对路径和 .. 组件
        if member.name.startswith('/') or '..' in member.name.split('/'):
            raise ValueError(f"检测到不安全的 tar 成员路径: {member.name}")
    tf.extractall(dest)


def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    """安全解压 zip 文件，防止目录遍历攻击"""
    base = os.path.abspath(str(dest))
    for name in zf.namelist():
        member_path = os.path.abspath(os.path.join(base, name))
        if not member_path.startswith(base + os.sep) and member_path != base:
            raise ValueError(f"检测到不安全的 zip 成员路径: {name}")
        if name.startswith('/') or '..' in name.split('/'):
            raise ValueError(f"检测到不安全的 zip 成员路径: {name}")
    zf.extractall(dest)


class InstallHooks:
    """安装钩子回调管理"""
    
    def __init__(self):
        """初始化钩子列表"""
        self.pre_install: List[Callable] = []
        self.post_install: List[Callable] = []
        self.pre_uninstall: List[Callable] = []
        self.post_uninstall: List[Callable] = []
        self.pre_upgrade: List[Callable] = []
        self.post_upgrade: List[Callable] = []
        self.on_error: List[Callable] = []
    
    def add_hook(self, hook_type: str, callback: Callable) -> bool:
        """
        添加钩子回调
        
        Args:
            hook_type: 钩子类型 (pre_install, post_install, pre_uninstall, 
                       post_uninstall, pre_upgrade, post_upgrade, on_error)
            callback: 回调函数
            
        Returns:
            bool: 是否添加成功
        """
        try:
            hook_list = getattr(self, hook_type, None)
            if hook_list is not None and isinstance(hook_list, list):
                hook_list.append(callback)
                logger.debug(f"添加钩子: {hook_type}")
                return True
            logger.warning(f"未知的钩子类型: {hook_type}")
            return False
        except Exception as e:
            logger.error(f"添加钩子失败: {e}")
            return False
    
    def remove_hook(self, hook_type: str, callback: Callable) -> bool:
        """
        移除钩子回调
        
        Args:
            hook_type: 钩子类型
            callback: 要移除的回调函数
            
        Returns:
            bool: 是否移除成功
        """
        try:
            hook_list = getattr(self, hook_type, None)
            if hook_list is not None and isinstance(hook_list, list):
                if callback in hook_list:
                    hook_list.remove(callback)
                    return True
            return False
        except Exception as e:
            logger.error(f"移除钩子失败: {e}")
            return False
    
    def _run_hooks(self, hook_type: str, **kwargs) -> bool:
        """
        运行指定类型的钩子
        
        Args:
            hook_type: 钩子类型
            **kwargs: 传递给钩子的参数
            
        Returns:
            bool: 所有钩子是否执行成功
        """
        try:
            hook_list = getattr(self, hook_type, None)
            if hook_list is None:
                return True
            
            for callback in hook_list:
                try:
                    result = callback(**kwargs)
                    # 如果钩子返回 False，中止执行
                    if result is False:
                        logger.warning(f"钩子 {hook_type} 返回 False，中止执行")
                        return False
                except Exception as e:
                    logger.error(f"钩子 {hook_type} 执行失败: {e}")
                    # 调用错误钩子
                    if hook_type != 'on_error':
                        self._run_hooks('on_error', error=e, hook_type=hook_type, **kwargs)
                    return False
            
            return True
        except Exception as e:
            logger.error(f"运行钩子失败: {e}")
            return False


class PluginInstaller:
    """
    插件安装器
    
    管理插件的完整生命周期，包括安装、卸载、升级、回滚和批量操作。
    
    使用示例:
        installer = PluginInstaller(store, version_mgr, dep_resolver)
        
        # 安装插件
        result = installer.install("my-plugin", version="1.0.0")
        if result.success:
            print(f"安装成功: {result.installation.install_path}")
        
        # 升级插件
        result = installer.upgrade("my-plugin")
        
        # 卸载插件
        result = installer.uninstall("my-plugin")
    """
    
    def __init__(
        self,
        store: MarketplaceStore,
        version_manager: VersionManager,
        dependency_resolver: DependencyResolver,
        sandbox: Optional[PluginSandbox] = None,
        plugins_dir: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        初始化插件安装器
        
        Args:
            store: 市场存储实例
            version_manager: 版本管理器实例
            dependency_resolver: 依赖解析器实例
            sandbox: 沙箱隔离实例（可选）
            plugins_dir: 插件安装目录（可选）
            cache_dir: 下载缓存目录（可选）
        """
        self.store = store
        self.version_mgr = version_manager
        self.dep_resolver = dependency_resolver
        self.sandbox = sandbox
        
        # 设置目录路径
        base = Path.home() / '.necorag' / 'marketplace'
        self.plugins_dir = Path(plugins_dir) if plugins_dir else base / 'plugins'
        self.cache_dir = Path(cache_dir) if cache_dir else base / 'cache'
        
        # 安装钩子
        self.hooks = InstallHooks()
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 确保目录存在
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"PluginInstaller 初始化完成，插件目录: {self.plugins_dir}")
    
    # ==================== 安装 ====================
    
    def install(
        self,
        plugin_id: str,
        version: Optional[str] = None,
        source: Optional[str] = None,
        skip_deps: bool = False,
        force: bool = False
    ) -> InstallResult:
        """
        安装插件
        
        完整流程：
        1. 检查是否已安装（如果已安装且不是 force，返回错误）
        2. 从 store 获取插件信息和指定版本
        3. 如果没有指定版本，获取最新稳定版
        4. 沙箱权限验证
        5. 解析依赖（如果不 skip_deps）
        6. 按拓扑排序安装所有依赖
        7. 下载/复制插件包到安装目录
        8. 校验 checksum
        9. 解压并安装
        10. 创建安装记录
        11. 记录使用事件
        12. 运行 post_install 钩子
        
        Args:
            plugin_id: 插件ID
            version: 指定版本（None 则安装最新稳定版）
            source: 安装来源（本地路径或远程URL）
            skip_deps: 是否跳过依赖安装
            force: 是否强制重新安装
            
        Returns:
            InstallResult: 安装结果
        """
        errors: List[str] = []
        
        try:
            with self._lock:
                # 1. 检查是否已安装
                existing = self.store.get_installation(plugin_id)
                if existing and not force:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=existing.version,
                        message=f"插件 {plugin_id} 已安装 (版本 {existing.version})，使用 force=True 强制重新安装",
                        errors=[f"插件已存在"]
                    )
                
                # 2. 获取插件信息
                manifest = self.store.get_plugin(plugin_id)
                if not manifest:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=version or "unknown",
                        message=f"插件 {plugin_id} 不存在",
                        errors=["插件未注册"]
                    )
                
                # 3. 确定版本
                if version is None:
                    release = self.store.get_latest_release(plugin_id, ReleaseStability.STABLE)
                    if release:
                        version = release.version
                    else:
                        version = manifest.version
                
                # 获取发布信息
                release = self.store.get_release(plugin_id, version)
                
                # 4. 沙箱权限验证
                if self.sandbox and self.sandbox.enabled:
                    validation = self.sandbox.validate_permissions(manifest)
                    if not validation.valid:
                        return InstallResult(
                            success=False,
                            plugin_id=plugin_id,
                            version=version,
                            message="权限验证失败",
                            errors=validation.errors
                        )
                
                # 运行 pre_install 钩子
                if not self.hooks._run_hooks('pre_install', plugin_id=plugin_id, version=version):
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=version,
                        message="pre_install 钩子执行失败",
                        errors=["钩子中止安装"]
                    )
                
                # 5. 解析并安装依赖
                if not skip_deps and manifest.dependencies:
                    dep_result = self._install_dependencies(manifest, force)
                    if dep_result:
                        errors.extend(dep_result)
                
                # 6. 下载插件包
                package_path = None
                if source:
                    # 从指定来源安装
                    source_path = Path(source)
                    if source_path.exists():
                        package_path = source_path
                    else:
                        errors.append(f"指定的安装来源不存在: {source}")
                elif release and release.download_url:
                    package_path = self._download_plugin(release)
                    if not package_path:
                        errors.append("插件包下载失败")
                
                # 7. 校验 checksum
                if package_path and release and release.checksum_sha256:
                    if not self._verify_checksum(package_path, release.checksum_sha256):
                        errors.append("校验和验证失败，文件可能已损坏")
                        package_path = None
                
                # 8. 解压并安装
                install_dir = None
                if package_path:
                    install_dir = self._extract_package(package_path, plugin_id, version)
                else:
                    # 如果没有包，只创建安装目录
                    install_dir = self._create_plugin_dir(plugin_id, version)
                
                # 写入 manifest
                if install_dir:
                    self._write_manifest(manifest, install_dir)
                
                # 9. 创建安装记录
                installation = PluginInstallation(
                    plugin_id=plugin_id,
                    version=version,
                    install_path=str(install_dir) if install_dir else "",
                    status=InstallStatus.ACTIVE,
                    config={},
                    installed_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 如果已存在安装记录，先删除
                if existing:
                    self.store.remove_installation(plugin_id)
                
                self.store.add_installation(installation)
                
                # 10. 记录使用事件
                self.store.record_usage_event(
                    plugin_id,
                    'install',
                    {'version': version, 'source': source or 'marketplace'}
                )
                
                # 11. 运行 post_install 钩子
                self.hooks._run_hooks(
                    'post_install',
                    plugin_id=plugin_id,
                    version=version,
                    installation=installation
                )
                
                logger.info(f"插件安装成功: {plugin_id}@{version}")
                
                return InstallResult(
                    success=True,
                    plugin_id=plugin_id,
                    version=version,
                    message="安装成功",
                    installation=installation,
                    errors=errors if errors else []
                )
                
        except Exception as e:
            logger.error(f"安装插件失败 {plugin_id}: {e}")
            self.hooks._run_hooks('on_error', error=e, operation='install', plugin_id=plugin_id)
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=version or "unknown",
                message=f"安装失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _install_dependencies(
        self, 
        manifest: PluginManifest, 
        force: bool = False
    ) -> List[str]:
        """
        安装插件依赖
        
        Args:
            manifest: 插件清单
            force: 是否强制安装
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        try:
            # 构建依赖图
            graph = self.dep_resolver.build_dependency_graph(
                manifest.plugin_id, manifest.version
            )
            
            if graph.conflicts:
                errors.extend(graph.conflicts)
                logger.warning(f"依赖解析存在冲突: {graph.conflicts}")
            
            # 按拓扑排序安装依赖（排除自身）
            for dep_id in graph.install_order:
                if dep_id == manifest.plugin_id:
                    continue
                
                # 检查是否已安装
                if self.is_installed(dep_id) and not force:
                    continue
                
                # 获取依赖版本
                dep_version = graph.nodes.get(dep_id)
                
                # 安装依赖
                dep_result = self.install(
                    dep_id, 
                    version=dep_version, 
                    skip_deps=True,  # 避免递归
                    force=force
                )
                
                if not dep_result.success:
                    errors.append(f"依赖 {dep_id} 安装失败: {dep_result.message}")
                    
        except Exception as e:
            errors.append(f"依赖安装过程出错: {str(e)}")
            logger.error(f"安装依赖失败: {e}")
        
        return errors
    
    def _download_plugin(self, release: PluginRelease) -> Optional[Path]:
        """
        下载插件包到缓存目录
        
        如果是本地源，直接复制。
        如果缓存中已有且 checksum 匹配，直接使用缓存。
        
        Args:
            release: 版本发布记录
            
        Returns:
            Optional[Path]: 下载的文件路径，失败返回 None
        """
        try:
            if not release.download_url:
                logger.warning(f"插件 {release.plugin_id} 没有下载地址")
                return None
            
            # 确定缓存文件名
            cache_filename = f"{release.plugin_id}-{release.version}"
            if release.download_url.endswith('.tar.gz'):
                cache_filename += '.tar.gz'
            elif release.download_url.endswith('.zip'):
                cache_filename += '.zip'
            else:
                cache_filename += '.tar.gz'
            
            cache_path = self.cache_dir / cache_filename
            
            # 检查缓存
            if cache_path.exists():
                if release.checksum_sha256:
                    if self._verify_checksum(cache_path, release.checksum_sha256):
                        logger.debug(f"使用缓存: {cache_path}")
                        return cache_path
                    else:
                        # 缓存文件损坏，删除
                        cache_path.unlink()
                else:
                    return cache_path
            
            # 本地路径
            if release.download_url.startswith('/') or release.download_url.startswith('file://'):
                local_path = release.download_url.replace('file://', '')
                local_path = Path(local_path)
                if local_path.exists():
                    shutil.copy2(local_path, cache_path)
                    logger.info(f"从本地复制插件包: {local_path}")
                    return cache_path
                else:
                    logger.error(f"本地文件不存在: {local_path}")
                    return None
            
            # 远程下载
            import urllib.request
            import urllib.error
            
            logger.info(f"下载插件包: {release.download_url}")
            
            # 使用临时文件下载，然后原子移动
            with tempfile.NamedTemporaryFile(delete=False, dir=self.cache_dir) as tmp:
                try:
                    with urllib.request.urlopen(release.download_url, timeout=60) as response:
                        shutil.copyfileobj(response, tmp)
                    tmp.flush()
                    
                    # 原子移动到目标位置
                    shutil.move(tmp.name, cache_path)
                    logger.info(f"插件包下载完成: {cache_path}")
                    return cache_path
                    
                except Exception as e:
                    # 清理临时文件
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                    raise
                    
        except Exception as e:
            logger.error(f"下载插件包失败: {e}")
            return None
    
    def _verify_checksum(self, file_path: Path, expected: str) -> bool:
        """
        验证文件 SHA256 校验和
        
        Args:
            file_path: 文件路径
            expected: 期望的校验和
            
        Returns:
            bool: 校验是否通过
        """
        try:
            actual = self._calculate_sha256(file_path)
            if actual.lower() == expected.lower():
                return True
            logger.warning(f"校验和不匹配: 期望 {expected}, 实际 {actual}")
            return False
        except Exception as e:
            logger.error(f"校验和验证失败: {e}")
            return False
    
    def _extract_package(
        self, 
        package_path: Path, 
        plugin_id: str, 
        version: str
    ) -> Path:
        """
        解压插件包到安装目录
        
        支持 .zip 和 .tar.gz 格式。
        安装到: plugins_dir / plugin_id / version /
        
        Args:
            package_path: 插件包路径
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            Path: 安装目录路径
        """
        install_dir = self._create_plugin_dir(plugin_id, version)
        
        try:
            if package_path.suffix == '.zip' or str(package_path).endswith('.zip'):
                with zipfile.ZipFile(package_path, 'r') as zf:
                    _safe_extract_zip(zf, install_dir)
                logger.debug(f"解压 ZIP 包到: {install_dir}")
                    
            elif package_path.suffix == '.gz' or str(package_path).endswith('.tar.gz'):
                with tarfile.open(package_path, 'r:gz') as tf:
                    _safe_extract_tar(tf, install_dir)
                logger.debug(f"解压 TAR.GZ 包到: {install_dir}")
                    
            else:
                # 尝试作为 tar.gz 处理
                try:
                    with tarfile.open(package_path, 'r:gz') as tf:
                        _safe_extract_tar(tf, install_dir)
                except tarfile.TarError:
                    # 尝试作为 zip 处理
                    with zipfile.ZipFile(package_path, 'r') as zf:
                        _safe_extract_zip(zf, install_dir)
            
            return install_dir
            
        except Exception as e:
            logger.error(f"解压插件包失败: {e}")
            return install_dir
    
    def _create_plugin_dir(self, plugin_id: str, version: str) -> Path:
        """
        创建插件安装目录
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            Path: 安装目录路径
        """
        install_dir = self.plugins_dir / plugin_id / version
        install_dir.mkdir(parents=True, exist_ok=True)
        return install_dir
    
    def _write_manifest(self, manifest: PluginManifest, install_dir: Path):
        """
        将 manifest 写入安装目录的 plugin.json
        
        使用原子写入确保文件完整性。
        
        Args:
            manifest: 插件清单
            install_dir: 安装目录
        """
        try:
            manifest_path = install_dir / 'plugin.json'
            
            # 使用临时文件原子写入
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=install_dir, 
                suffix='.json', 
                delete=False,
                encoding='utf-8'
            ) as tmp:
                json.dump(manifest.to_dict(), tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
            
            # 原子移动
            shutil.move(tmp.name, manifest_path)
            logger.debug(f"写入 manifest: {manifest_path}")
            
        except Exception as e:
            logger.error(f"写入 manifest 失败: {e}")
    
    # ==================== 卸载 ====================
    
    def uninstall(self, plugin_id: str, force: bool = False) -> InstallResult:
        """
        卸载插件
        
        流程：
        1. 检查是否已安装
        2. 检查反向依赖（如果有其他插件依赖此插件且不是 force，拒绝卸载）
        3. 运行 pre_uninstall 钩子
        4. 清理安装目录
        5. 移除安装记录
        6. 记录使用事件
        7. 运行 post_uninstall 钩子
        
        Args:
            plugin_id: 插件ID
            force: 是否强制卸载（忽略反向依赖）
            
        Returns:
            InstallResult: 卸载结果
        """
        try:
            with self._lock:
                # 1. 检查是否已安装
                installation = self.store.get_installation(plugin_id)
                if not installation:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version="unknown",
                        message=f"插件 {plugin_id} 未安装",
                        errors=["插件未安装"]
                    )
                
                version = installation.version
                
                # 2. 检查反向依赖
                if not force:
                    is_safe, dependents = self.dep_resolver.check_safe_to_uninstall(plugin_id)
                    if not is_safe:
                        return InstallResult(
                            success=False,
                            plugin_id=plugin_id,
                            version=version,
                            message=f"有其他插件依赖此插件: {dependents}",
                            errors=[f"被依赖: {', '.join(dependents)}"]
                        )
                
                # 3. 运行 pre_uninstall 钩子
                if not self.hooks._run_hooks('pre_uninstall', plugin_id=plugin_id, version=version):
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=version,
                        message="pre_uninstall 钩子执行失败",
                        errors=["钩子中止卸载"]
                    )
                
                # 清理沙箱状态
                if self.sandbox:
                    self.sandbox.cleanup_plugin(plugin_id)
                
                # 4. 清理安装目录
                self._cleanup_plugin_dir(plugin_id)
                
                # 5. 移除安装记录
                self.store.remove_installation(plugin_id)
                
                # 6. 记录使用事件
                self.store.record_usage_event(
                    plugin_id,
                    'uninstall',
                    {'version': version}
                )
                
                # 7. 运行 post_uninstall 钩子
                self.hooks._run_hooks('post_uninstall', plugin_id=plugin_id, version=version)
                
                logger.info(f"插件卸载成功: {plugin_id}@{version}")
                
                return InstallResult(
                    success=True,
                    plugin_id=plugin_id,
                    version=version,
                    message="卸载成功"
                )
                
        except Exception as e:
            logger.error(f"卸载插件失败 {plugin_id}: {e}")
            self.hooks._run_hooks('on_error', error=e, operation='uninstall', plugin_id=plugin_id)
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version="unknown",
                message=f"卸载失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _cleanup_plugin_dir(
        self, 
        plugin_id: str, 
        version: Optional[str] = None
    ):
        """
        清理插件安装目录
        
        Args:
            plugin_id: 插件ID
            version: 指定版本（None 则清理所有版本）
        """
        try:
            plugin_dir = self.plugins_dir / plugin_id
            
            if version:
                # 只清理指定版本
                version_dir = plugin_dir / version
                if version_dir.exists():
                    shutil.rmtree(version_dir)
                    logger.debug(f"清理版本目录: {version_dir}")
                    
                # 如果插件目录为空，也删除
                if plugin_dir.exists() and not any(plugin_dir.iterdir()):
                    plugin_dir.rmdir()
            else:
                # 清理所有版本
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir)
                    logger.debug(f"清理插件目录: {plugin_dir}")
                    
        except Exception as e:
            logger.error(f"清理插件目录失败: {e}")
    
    # ==================== 升级 ====================
    
    def upgrade(
        self, 
        plugin_id: str, 
        target_version: Optional[str] = None,
        force: bool = False
    ) -> InstallResult:
        """
        升级插件
        
        流程：
        1. 检查当前安装状态
        2. 规划升级路径（version_manager.plan_upgrade）
        3. 兼容性验证
        4. 备份当前配置
        5. 安装新版本（到新的版本目录）
        6. 迁移配置
        7. 更新安装记录
        8. 清理旧版本目录（保留一个版本用于回滚）
        9. 记录使用事件
        
        Args:
            plugin_id: 插件ID
            target_version: 目标版本（None 则升级到最新稳定版）
            force: 是否强制升级
            
        Returns:
            InstallResult: 升级结果
        """
        try:
            with self._lock:
                # 1. 检查当前安装状态
                installation = self.store.get_installation(plugin_id)
                if not installation:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=target_version or "unknown",
                        message=f"插件 {plugin_id} 未安装，无法升级",
                        errors=["插件未安装"]
                    )
                
                current_version = installation.version
                
                # 2. 规划升级路径
                upgrade_path = self.version_mgr.plan_upgrade(
                    plugin_id, current_version, target_version
                )
                
                if not upgrade_path.steps:
                    return InstallResult(
                        success=True,
                        plugin_id=plugin_id,
                        version=current_version,
                        message="已是最新版本，无需升级",
                        installation=installation
                    )
                
                final_version = upgrade_path.target_version
                
                # 3. 兼容性验证
                if not upgrade_path.is_compatible and not force:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=final_version,
                        message="检测到不兼容的主版本升级，使用 force=True 强制升级",
                        errors=upgrade_path.breaking_changes
                    )
                
                # 运行 pre_upgrade 钩子
                if not self.hooks._run_hooks(
                    'pre_upgrade',
                    plugin_id=plugin_id,
                    from_version=current_version,
                    to_version=final_version
                ):
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=final_version,
                        message="pre_upgrade 钩子执行失败",
                        errors=["钩子中止升级"]
                    )
                
                # 4. 备份当前配置
                old_config = self._backup_config(plugin_id, current_version)
                
                # 5. 安装新版本
                result = self.install(
                    plugin_id,
                    version=final_version,
                    skip_deps=False,
                    force=True  # 升级时强制安装
                )
                
                if not result.success:
                    return result
                
                # 6. 迁移配置
                if old_config and result.installation:
                    new_config = self._migrate_config(
                        old_config, current_version, final_version
                    )
                    result.installation.config = new_config
                    self.store.update_installation(result.installation)
                
                # 7. 清理旧版本目录（保留用于回滚）
                # 只保留当前版本和上一个版本
                self._cleanup_old_versions(plugin_id, keep_versions=[final_version, current_version])
                
                # 8. 记录使用事件
                self.store.record_usage_event(
                    plugin_id,
                    'upgrade',
                    {'from_version': current_version, 'to_version': final_version}
                )
                
                # 运行 post_upgrade 钩子
                self.hooks._run_hooks(
                    'post_upgrade',
                    plugin_id=plugin_id,
                    from_version=current_version,
                    to_version=final_version,
                    installation=result.installation
                )
                
                logger.info(f"插件升级成功: {plugin_id} {current_version} -> {final_version}")
                
                return InstallResult(
                    success=True,
                    plugin_id=plugin_id,
                    version=final_version,
                    message=f"升级成功: {current_version} -> {final_version}",
                    installation=result.installation
                )
                
        except Exception as e:
            logger.error(f"升级插件失败 {plugin_id}: {e}")
            self.hooks._run_hooks('on_error', error=e, operation='upgrade', plugin_id=plugin_id)
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=target_version or "unknown",
                message=f"升级失败: {str(e)}",
                errors=[str(e)]
            )
    
    def _backup_config(self, plugin_id: str, version: str) -> Optional[Dict]:
        """
        备份插件配置
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            Optional[Dict]: 配置字典，没有则返回 None
        """
        try:
            installation = self.store.get_installation(plugin_id)
            if installation and installation.config:
                return installation.config.copy()
            
            # 尝试从安装目录读取配置
            config_path = self.plugins_dir / plugin_id / version / 'config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
        except Exception as e:
            logger.warning(f"备份配置失败: {e}")
            return None
    
    def _migrate_config(
        self, 
        old_config: Dict, 
        old_version: str,
        new_version: str
    ) -> Dict:
        """
        迁移配置（简单合并策略）
        
        Args:
            old_config: 旧配置
            old_version: 旧版本
            new_version: 新版本
            
        Returns:
            Dict: 迁移后的配置
        """
        try:
            # 简单策略：保留旧配置，添加版本迁移标记
            migrated = old_config.copy()
            migrated['_migrated_from'] = old_version
            migrated['_migrated_to'] = new_version
            migrated['_migrated_at'] = datetime.now().isoformat()
            return migrated
        except Exception as e:
            logger.warning(f"配置迁移失败: {e}")
            return old_config
    
    def _cleanup_old_versions(
        self, 
        plugin_id: str, 
        keep_versions: List[str]
    ):
        """
        清理旧版本目录
        
        Args:
            plugin_id: 插件ID
            keep_versions: 要保留的版本列表
        """
        try:
            plugin_dir = self.plugins_dir / plugin_id
            if not plugin_dir.exists():
                return
            
            for version_dir in plugin_dir.iterdir():
                if version_dir.is_dir() and version_dir.name not in keep_versions:
                    shutil.rmtree(version_dir)
                    logger.debug(f"清理旧版本: {version_dir}")
                    
        except Exception as e:
            logger.warning(f"清理旧版本失败: {e}")
    
    # ==================== 回滚 ====================
    
    def rollback(self, plugin_id: str, to_version: str) -> InstallResult:
        """
        回滚到指定版本
        
        1. 检查目标版本目录是否还存在
        2. 如果不存在，尝试重新安装该版本
        3. 更新安装记录
        
        Args:
            plugin_id: 插件ID
            to_version: 目标版本
            
        Returns:
            InstallResult: 回滚结果
        """
        try:
            with self._lock:
                # 检查当前安装状态
                installation = self.store.get_installation(plugin_id)
                if not installation:
                    return InstallResult(
                        success=False,
                        plugin_id=plugin_id,
                        version=to_version,
                        message="插件未安装",
                        errors=["插件未安装，无法回滚"]
                    )
                
                current_version = installation.version
                
                if current_version == to_version:
                    return InstallResult(
                        success=True,
                        plugin_id=plugin_id,
                        version=to_version,
                        message="已是目标版本",
                        installation=installation
                    )
                
                # 检查目标版本目录是否存在
                target_dir = self.plugins_dir / plugin_id / to_version
                
                if target_dir.exists():
                    # 目标版本目录存在，直接更新安装记录
                    installation.version = to_version
                    installation.install_path = str(target_dir)
                    installation.updated_at = datetime.now()
                    self.store.update_installation(installation)
                    
                    # 记录使用事件
                    self.store.record_usage_event(
                        plugin_id,
                        'rollback',
                        {'from_version': current_version, 'to_version': to_version}
                    )
                    
                    logger.info(f"插件回滚成功: {plugin_id} {current_version} -> {to_version}")
                    
                    return InstallResult(
                        success=True,
                        plugin_id=plugin_id,
                        version=to_version,
                        message=f"回滚成功: {current_version} -> {to_version}",
                        installation=installation
                    )
                else:
                    # 目标版本目录不存在，尝试重新安装
                    logger.info(f"目标版本目录不存在，尝试重新安装: {plugin_id}@{to_version}")
                    return self.install(plugin_id, version=to_version, force=True)
                    
        except Exception as e:
            logger.error(f"回滚插件失败 {plugin_id}: {e}")
            return InstallResult(
                success=False,
                plugin_id=plugin_id,
                version=to_version,
                message=f"回滚失败: {str(e)}",
                errors=[str(e)]
            )
    
    # ==================== 批量操作 ====================
    
    def batch_install(
        self, 
        plugin_specs: List[Dict[str, str]]
    ) -> List[InstallResult]:
        """
        批量安装插件
        
        先解析所有依赖，检测冲突，然后按拓扑排序依次安装。
        
        Args:
            plugin_specs: 插件规格列表 [{"plugin_id": "xxx", "version": "1.0.0"}, ...]
            
        Returns:
            List[InstallResult]: 安装结果列表
        """
        results: List[InstallResult] = []
        
        try:
            # 构建需求字典
            requirements = {}
            for spec in plugin_specs:
                plugin_id = spec.get('plugin_id')
                version = spec.get('version', '*')
                if plugin_id:
                    requirements[plugin_id] = version
            
            # 检测冲突
            conflicts = self.dep_resolver.detect_conflicts(requirements)
            if conflicts:
                for conflict in conflicts:
                    results.append(InstallResult(
                        success=False,
                        plugin_id=conflict.plugin_id,
                        version="conflict",
                        message=conflict.message,
                        errors=[f"版本冲突: {conflict.required_by}"]
                    ))
                return results
            
            # 解析安装顺序
            install_order = self.dep_resolver.resolve_install_order(
                list(requirements.keys())
            )
            
            # 按顺序安装
            for plugin_id in install_order:
                version = requirements.get(plugin_id)
                if version == '*':
                    version = None
                
                result = self.install(
                    plugin_id, 
                    version=version, 
                    skip_deps=True,  # 已经解析过依赖
                    force=False
                )
                results.append(result)
                
                # 如果安装失败，记录但继续安装其他插件
                if not result.success:
                    logger.warning(f"批量安装中 {plugin_id} 安装失败: {result.message}")
            
        except Exception as e:
            logger.error(f"批量安装失败: {e}")
            results.append(InstallResult(
                success=False,
                plugin_id="batch",
                version="unknown",
                message=f"批量安装失败: {str(e)}",
                errors=[str(e)]
            ))
        
        return results
    
    def upgrade_all(self) -> List[InstallResult]:
        """
        升级所有已安装且有更新的插件
        
        Returns:
            List[InstallResult]: 升级结果列表
        """
        results: List[InstallResult] = []
        
        try:
            updates = self.check_updates()
            
            for update in updates:
                plugin_id = update['plugin_id']
                latest = update['latest']
                
                result = self.upgrade(plugin_id, target_version=latest)
                results.append(result)
                
        except Exception as e:
            logger.error(f"批量升级失败: {e}")
            results.append(InstallResult(
                success=False,
                plugin_id="upgrade_all",
                version="unknown",
                message=f"批量升级失败: {str(e)}",
                errors=[str(e)]
            ))
        
        return results
    
    def check_updates(self) -> List[Dict]:
        """
        检查所有已安装插件的更新
        
        Returns:
            List[Dict]: 更新信息列表
                [{"plugin_id": str, "current": str, "latest": str, "is_major": bool}, ...]
        """
        updates = []
        
        try:
            installations = self.store.list_installations()
            
            for installation in installations:
                plugin_id = installation.plugin_id
                current = installation.version
                
                # 获取最新版本
                latest_release = self.store.get_latest_release(
                    plugin_id, ReleaseStability.STABLE
                )
                
                if not latest_release:
                    continue
                
                latest = latest_release.version
                
                # 比较版本
                cmp = self.version_mgr.compare_versions(latest, current)
                if cmp > 0:
                    is_major = self.version_mgr.is_major_upgrade(current, latest)
                    updates.append({
                        'plugin_id': plugin_id,
                        'current': current,
                        'latest': latest,
                        'is_major': is_major
                    })
                    
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
        
        return updates
    
    # ==================== 插件信息 ====================
    
    def get_install_path(
        self, 
        plugin_id: str, 
        version: Optional[str] = None
    ) -> Optional[Path]:
        """
        获取插件安装路径
        
        Args:
            plugin_id: 插件ID
            version: 版本号（None 则返回当前安装版本）
            
        Returns:
            Optional[Path]: 安装路径，不存在返回 None
        """
        try:
            if version is None:
                installation = self.store.get_installation(plugin_id)
                if installation:
                    return Path(installation.install_path) if installation.install_path else None
                return None
            
            path = self.plugins_dir / plugin_id / version
            return path if path.exists() else None
            
        except Exception as e:
            logger.error(f"获取安装路径失败: {e}")
            return None
    
    def is_installed(self, plugin_id: str) -> bool:
        """
        检查插件是否已安装
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否已安装
        """
        installation = self.store.get_installation(plugin_id)
        return installation is not None
    
    def get_installed_version(self, plugin_id: str) -> Optional[str]:
        """
        获取已安装的版本
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[str]: 已安装版本，未安装返回 None
        """
        installation = self.store.get_installation(plugin_id)
        return installation.version if installation else None
    
    def list_installed(self) -> List[PluginInstallation]:
        """
        列出所有已安装插件
        
        Returns:
            List[PluginInstallation]: 安装记录列表
        """
        return self.store.list_installations()
    
    # ==================== 缓存管理 ====================
    
    def clear_cache(self) -> int:
        """
        清理下载缓存
        
        Returns:
            int: 清理的字节数
        """
        cleared_bytes = 0
        
        try:
            for cache_file in self.cache_dir.iterdir():
                if cache_file.is_file():
                    cleared_bytes += cache_file.stat().st_size
                    cache_file.unlink()
                    
            logger.info(f"缓存清理完成，释放 {cleared_bytes / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
        
        return cleared_bytes
    
    def get_cache_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            int: 缓存大小（字节）
        """
        try:
            total_size = 0
            for cache_file in self.cache_dir.iterdir():
                if cache_file.is_file():
                    total_size += cache_file.stat().st_size
            return total_size
        except Exception as e:
            logger.error(f"获取缓存大小失败: {e}")
            return 0
    
    # ==================== 工具方法 ====================
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """
        计算文件 SHA256
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: SHA256 哈希值（十六进制）
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
