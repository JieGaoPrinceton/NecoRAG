"""
NecoRAG 插件市场 - 仓库管理

管理本地和远程插件仓库，支持多源聚合、索引同步和插件包下载。
"""

import os
import json
import shutil
import hashlib
import logging
import urllib.request
import urllib.error
import tempfile
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from .models import (
    PluginManifest, PluginRelease, SyncResult, PluginType, PluginCategory,
    ReleaseStability
)
from .store import MarketplaceStore

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    仓库基类
    
    定义了仓库的通用接口，包括获取索引、获取版本列表、下载插件包等。
    """
    
    def __init__(self, name: str, url: str, config: Optional[Dict] = None):
        """
        初始化仓库
        
        Args:
            name: 仓库名称
            url: 仓库URL或路径
            config: 额外配置
        """
        self.name = name
        self.url = url
        self.config = config or {}
        self._lock = threading.Lock()
    
    @abstractmethod
    def fetch_index(self) -> List[PluginManifest]:
        """
        获取仓库中所有插件的元数据索引
        
        Returns:
            List[PluginManifest]: 插件清单列表
        """
        pass
    
    @abstractmethod
    def fetch_releases(self, plugin_id: str) -> List[PluginRelease]:
        """
        获取指定插件的所有版本
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[PluginRelease]: 版本发布列表
        """
        pass
    
    @abstractmethod
    def download_package(
        self, 
        plugin_id: str, 
        version: str, 
        dest_dir: Path
    ) -> Optional[Path]:
        """
        下载指定版本的插件包
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            dest_dir: 目标目录
            
        Returns:
            Optional[Path]: 下载的文件路径，失败返回 None
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查仓库是否可用
        
        Returns:
            bool: 是否可用
        """
        pass
    
    def verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """
        验证文件校验和
        
        Args:
            file_path: 文件路径
            expected_sha256: 期望的 SHA256 值
            
        Returns:
            bool: 校验是否通过
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            actual = sha256.hexdigest()
            return actual.lower() == expected_sha256.lower()
        except Exception as e:
            logger.error(f"校验和验证失败: {e}")
            return False


class LocalRepository(BaseRepository):
    """
    本地文件系统仓库
    
    目录结构:
    repo_path/
      index.json          # 插件索引
      packages/
        plugin-id/
          1.0.0/
            plugin.json   # manifest
            package.tar.gz or package.zip  # 插件包
    """
    
    def __init__(self, name: str, path: str, config: Optional[Dict] = None):
        """
        初始化本地仓库
        
        Args:
            name: 仓库名称
            path: 本地路径
            config: 额外配置
        """
        super().__init__(name, path, config)
        self.repo_path = Path(path)
        
        # 确保目录结构存在
        self._ensure_structure()
    
    def _ensure_structure(self):
        """确保仓库目录结构存在"""
        try:
            self.repo_path.mkdir(parents=True, exist_ok=True)
            (self.repo_path / 'packages').mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"创建仓库目录结构失败: {e}")
    
    def fetch_index(self) -> List[PluginManifest]:
        """
        读取本地 index.json 或扫描 packages 目录
        
        Returns:
            List[PluginManifest]: 插件清单列表
        """
        manifests = []
        
        try:
            # 尝试读取 index.json
            index_path = self.repo_path / 'index.json'
            if index_path.exists():
                index_data = self._read_index()
                for item in index_data:
                    try:
                        manifest = PluginManifest.from_dict(item)
                        manifests.append(manifest)
                    except Exception as e:
                        logger.warning(f"解析插件清单失败: {e}")
                return manifests
            
            # 扫描 packages 目录
            packages_dir = self.repo_path / 'packages'
            if packages_dir.exists():
                for plugin_dir in packages_dir.iterdir():
                    if plugin_dir.is_dir():
                        # 找到最新版本的 manifest
                        latest_manifest = self._find_latest_manifest(plugin_dir)
                        if latest_manifest:
                            manifests.append(latest_manifest)
            
        except Exception as e:
            logger.error(f"获取本地仓库索引失败: {e}")
        
        return manifests
    
    def _find_latest_manifest(self, plugin_dir: Path) -> Optional[PluginManifest]:
        """找到插件目录中最新版本的 manifest"""
        try:
            versions = []
            for version_dir in plugin_dir.iterdir():
                if version_dir.is_dir():
                    manifest_path = version_dir / 'plugin.json'
                    if manifest_path.exists():
                        versions.append(version_dir.name)
            
            if not versions:
                return None
            
            # 简单的版本排序（按字符串）
            versions.sort(reverse=True)
            latest_version = versions[0]
            
            manifest_path = plugin_dir / latest_version / 'plugin.json'
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PluginManifest.from_dict(data)
                
        except Exception as e:
            logger.warning(f"读取 manifest 失败 {plugin_dir}: {e}")
            return None
    
    def fetch_releases(self, plugin_id: str) -> List[PluginRelease]:
        """
        扫描插件目录下的版本
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[PluginRelease]: 版本发布列表
        """
        releases = []
        
        try:
            plugin_dir = self.repo_path / 'packages' / plugin_id
            if not plugin_dir.exists():
                return releases
            
            for version_dir in plugin_dir.iterdir():
                if version_dir.is_dir():
                    version = version_dir.name
                    
                    # 查找插件包
                    package_path = self._find_package(version_dir)
                    
                    release = PluginRelease(
                        plugin_id=plugin_id,
                        version=version,
                        download_url=str(package_path) if package_path else "",
                        checksum_sha256=self._calculate_checksum(package_path) if package_path else "",
                        size_bytes=package_path.stat().st_size if package_path else 0,
                        stability=ReleaseStability.STABLE,
                        published_at=datetime.fromtimestamp(
                            version_dir.stat().st_mtime
                        ) if version_dir.exists() else datetime.now()
                    )
                    releases.append(release)
            
        except Exception as e:
            logger.error(f"获取本地仓库版本列表失败: {e}")
        
        return releases
    
    def _find_package(self, version_dir: Path) -> Optional[Path]:
        """在版本目录中查找插件包"""
        for ext in ['package.tar.gz', 'package.zip', '*.tar.gz', '*.zip']:
            if '*' in ext:
                for f in version_dir.glob(ext):
                    return f
            else:
                path = version_dir / ext
                if path.exists():
                    return path
        return None
    
    def _calculate_checksum(self, file_path: Optional[Path]) -> str:
        """计算文件 SHA256"""
        if not file_path or not file_path.exists():
            return ""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""
    
    def download_package(
        self, 
        plugin_id: str, 
        version: str,
        dest_dir: Path
    ) -> Optional[Path]:
        """
        复制本地插件包到目标目录
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            dest_dir: 目标目录
            
        Returns:
            Optional[Path]: 复制后的文件路径
        """
        try:
            version_dir = self.repo_path / 'packages' / plugin_id / version
            package_path = self._find_package(version_dir)
            
            if not package_path:
                logger.warning(f"本地仓库中未找到插件包: {plugin_id}@{version}")
                return None
            
            # 确保目标目录存在
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            dest_path = dest_dir / package_path.name
            shutil.copy2(package_path, dest_path)
            
            logger.debug(f"复制本地插件包: {package_path} -> {dest_path}")
            return dest_path
            
        except Exception as e:
            logger.error(f"复制本地插件包失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        检查路径是否存在
        
        Returns:
            bool: 是否可用
        """
        return self.repo_path.exists()
    
    # ==================== 本地仓库特有方法 ====================
    
    def publish_plugin(
        self, 
        manifest: PluginManifest, 
        package_path: Path
    ) -> bool:
        """
        发布插件到本地仓库
        
        Args:
            manifest: 插件清单
            package_path: 插件包路径
            
        Returns:
            bool: 是否发布成功
        """
        try:
            with self._lock:
                # 创建版本目录
                version_dir = self.repo_path / 'packages' / manifest.plugin_id / manifest.version
                version_dir.mkdir(parents=True, exist_ok=True)
                
                # 复制插件包
                dest_package = version_dir / package_path.name
                shutil.copy2(package_path, dest_package)
                
                # 写入 manifest
                manifest_path = version_dir / 'plugin.json'
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    dir=version_dir, 
                    suffix='.json', 
                    delete=False,
                    encoding='utf-8'
                ) as tmp:
                    json.dump(manifest.to_dict(), tmp, indent=2, ensure_ascii=False)
                shutil.move(tmp.name, manifest_path)
                
                # 更新索引
                self._update_index(manifest)
                
                logger.info(f"发布插件到本地仓库: {manifest.plugin_id}@{manifest.version}")
                return True
                
        except Exception as e:
            logger.error(f"发布插件失败: {e}")
            return False
    
    def remove_plugin(
        self, 
        plugin_id: str, 
        version: Optional[str] = None
    ) -> bool:
        """
        从本地仓库移除插件
        
        Args:
            plugin_id: 插件ID
            version: 版本号（None 则移除所有版本）
            
        Returns:
            bool: 是否移除成功
        """
        try:
            with self._lock:
                plugin_dir = self.repo_path / 'packages' / plugin_id
                
                if not plugin_dir.exists():
                    return False
                
                if version:
                    # 移除指定版本
                    version_dir = plugin_dir / version
                    if version_dir.exists():
                        shutil.rmtree(version_dir)
                        
                    # 如果没有其他版本，删除插件目录
                    if not any(plugin_dir.iterdir()):
                        plugin_dir.rmdir()
                else:
                    # 移除所有版本
                    shutil.rmtree(plugin_dir)
                
                # 重建索引
                self.rebuild_index()
                
                logger.info(f"从本地仓库移除插件: {plugin_id}@{version or 'all'}")
                return True
                
        except Exception as e:
            logger.error(f"移除插件失败: {e}")
            return False
    
    def rebuild_index(self) -> int:
        """
        重建索引文件
        
        Returns:
            int: 索引的插件数
        """
        try:
            with self._lock:
                manifests = self.fetch_index()
                index_data = [m.to_dict() for m in manifests]
                self._write_index(index_data)
                
                logger.info(f"重建索引完成，共 {len(manifests)} 个插件")
                return len(manifests)
                
        except Exception as e:
            logger.error(f"重建索引失败: {e}")
            return 0
    
    def _update_index(self, manifest: PluginManifest):
        """更新索引文件"""
        try:
            index_data = self._read_index()
            
            # 更新或添加
            found = False
            for i, item in enumerate(index_data):
                if item.get('plugin_id') == manifest.plugin_id:
                    index_data[i] = manifest.to_dict()
                    found = True
                    break
            
            if not found:
                index_data.append(manifest.to_dict())
            
            self._write_index(index_data)
            
        except Exception as e:
            logger.error(f"更新索引失败: {e}")
    
    def _read_index(self) -> List[Dict]:
        """读取索引文件"""
        try:
            index_path = self.repo_path / 'index.json'
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.warning(f"读取索引失败: {e}")
            return []
    
    def _write_index(self, index_data: List[Dict]):
        """写入索引文件"""
        try:
            index_path = self.repo_path / 'index.json'
            
            # 原子写入
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=self.repo_path, 
                suffix='.json', 
                delete=False,
                encoding='utf-8'
            ) as tmp:
                json.dump(index_data, tmp, indent=2, ensure_ascii=False)
            
            shutil.move(tmp.name, index_path)
            
        except Exception as e:
            logger.error(f"写入索引失败: {e}")


class RemoteRepository(BaseRepository):
    """
    远程 HTTP 仓库
    
    期望远程端点:
    - GET {url}/index.json -> 插件索引列表
    - GET {url}/plugins/{plugin_id}/releases.json -> 版本列表
    - GET {url}/plugins/{plugin_id}/{version}/package.tar.gz -> 插件包
    """
    
    def __init__(self, name: str, url: str, config: Optional[Dict] = None):
        """
        初始化远程仓库
        
        Args:
            name: 仓库名称
            url: 仓库URL
            config: 额外配置（可包含 timeout, headers 等）
        """
        super().__init__(name, url, config)
        self.timeout = config.get('timeout', 30) if config else 30
        self.headers = config.get('headers', {}) if config else {}
        
        # 确保 URL 没有尾部斜杠
        self.url = url.rstrip('/')
    
    def fetch_index(self) -> List[PluginManifest]:
        """
        从远程拉取索引
        
        Returns:
            List[PluginManifest]: 插件清单列表
        """
        manifests = []
        
        try:
            index_url = f"{self.url}/index.json"
            data = self._fetch_json(index_url)
            
            if data and isinstance(data, list):
                for item in data:
                    try:
                        manifest = PluginManifest.from_dict(item)
                        manifests.append(manifest)
                    except Exception as e:
                        logger.warning(f"解析远程插件清单失败: {e}")
            
        except Exception as e:
            logger.error(f"获取远程仓库索引失败: {e}")
        
        return manifests
    
    def fetch_releases(self, plugin_id: str) -> List[PluginRelease]:
        """
        从远程获取版本列表
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[PluginRelease]: 版本发布列表
        """
        releases = []
        
        try:
            releases_url = f"{self.url}/plugins/{plugin_id}/releases.json"
            data = self._fetch_json(releases_url)
            
            if data and isinstance(data, list):
                for item in data:
                    try:
                        release = PluginRelease.from_dict(item)
                        releases.append(release)
                    except Exception as e:
                        logger.warning(f"解析远程版本信息失败: {e}")
            
        except Exception as e:
            logger.error(f"获取远程版本列表失败: {e}")
        
        return releases
    
    def download_package(
        self, 
        plugin_id: str, 
        version: str,
        dest_dir: Path
    ) -> Optional[Path]:
        """
        从远程下载插件包
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            dest_dir: 目标目录
            
        Returns:
            Optional[Path]: 下载的文件路径
        """
        try:
            # 尝试多种包格式
            for ext in ['package.tar.gz', 'package.zip']:
                package_url = f"{self.url}/plugins/{plugin_id}/{version}/{ext}"
                dest_path = dest_dir / f"{plugin_id}-{version}.{ext.split('.')[-1]}"
                
                if ext.endswith('.tar.gz'):
                    dest_path = dest_dir / f"{plugin_id}-{version}.tar.gz"
                
                if self._download_file(package_url, dest_path):
                    logger.info(f"下载插件包成功: {package_url}")
                    return dest_path
            
            logger.warning(f"远程仓库中未找到插件包: {plugin_id}@{version}")
            return None
            
        except Exception as e:
            logger.error(f"下载远程插件包失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        检查远程可达性
        
        Returns:
            bool: 是否可用
        """
        try:
            req = urllib.request.Request(
                f"{self.url}/index.json",
                method='HEAD',
                headers=self.headers
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def _fetch_json(self, url: str) -> Optional[Any]:
        """
        获取远程 JSON 数据
        
        Args:
            url: URL
            
        Returns:
            Optional[Any]: JSON 数据
        """
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                logger.warning(f"HTTP 错误 {e.code}: {url}")
            return None
        except Exception as e:
            logger.error(f"获取远程 JSON 失败 {url}: {e}")
            return None
    
    def _download_file(self, url: str, dest: Path) -> bool:
        """
        下载文件到指定路径
        
        Args:
            url: 下载URL
            dest: 目标路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标目录存在
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            req = urllib.request.Request(url, headers=self.headers)
            
            # 使用临时文件下载
            with tempfile.NamedTemporaryFile(delete=False, dir=dest.parent) as tmp:
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        shutil.copyfileobj(response, tmp)
                    tmp.flush()
                    
                    # 原子移动
                    shutil.move(tmp.name, dest)
                    return True
                    
                except Exception:
                    # 清理临时文件
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                    raise
                    
        except urllib.error.HTTPError as e:
            if e.code != 404:
                logger.warning(f"HTTP 下载错误 {e.code}: {url}")
            return False
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {e}")
            return False


class GitHubRepository(RemoteRepository):
    """
    GitHub Releases 仓库
    
    使用 GitHub API 获取插件索引和版本：
    - 每个 repo 的 releases 对应插件版本
    - release assets 对应插件包
    """
    
    def __init__(self, name: str, url: str, config: Optional[Dict] = None):
        """
        初始化 GitHub 仓库
        
        Args:
            name: 仓库名称
            url: GitHub URL (如 https://github.com/owner/repo 或 owner/repo)
            config: 额外配置（可包含 api_token）
        """
        super().__init__(name, url, config)
        self.api_token = config.get('api_token', '') if config else ''
        self._api_base = "https://api.github.com"
        
        # 解析 GitHub URL
        self._parse_github_url()
    
    def _parse_github_url(self):
        """解析 GitHub URL 提取 owner 和 repo"""
        url = self.url
        
        # 移除协议和域名
        if url.startswith('https://github.com/'):
            url = url.replace('https://github.com/', '')
        elif url.startswith('http://github.com/'):
            url = url.replace('http://github.com/', '')
        elif url.startswith('github.com/'):
            url = url.replace('github.com/', '')
        
        # 解析 owner/repo
        parts = url.strip('/').split('/')
        if len(parts) >= 2:
            self.owner = parts[0]
            self.repo = parts[1].replace('.git', '')
        else:
            self.owner = ""
            self.repo = url
        
        logger.debug(f"GitHub 仓库解析: owner={self.owner}, repo={self.repo}")
    
    def _get_api_headers(self) -> Dict[str, str]:
        """获取 API 请求头"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NecoRAG-Marketplace'
        }
        if self.api_token:
            headers['Authorization'] = f'token {self.api_token}'
        return headers
    
    def fetch_index(self) -> List[PluginManifest]:
        """
        通过 GitHub API 获取 releases 作为插件索引
        
        每个 release 的 tag_name 作为版本号，body 中可能包含 manifest 信息。
        
        Returns:
            List[PluginManifest]: 插件清单列表
        """
        manifests = []
        
        try:
            releases_url = f"{self._api_base}/repos/{self.owner}/{self.repo}/releases"
            self.headers = self._get_api_headers()
            data = self._fetch_json(releases_url)
            
            if not data or not isinstance(data, list):
                return manifests
            
            # 尝试从最新的 release 获取 manifest
            if data:
                latest = data[0]
                
                # 尝试下载 manifest 文件
                manifest = self._fetch_manifest_from_release(latest)
                if manifest:
                    manifests.append(manifest)
                else:
                    # 从 release 信息构建基本 manifest
                    manifest = PluginManifest(
                        plugin_id=self.repo,
                        name=self.repo,
                        version=latest.get('tag_name', '').lstrip('v'),
                        author=self.owner,
                        description=latest.get('body', '')[:200] if latest.get('body') else "",
                        plugin_type=PluginType.UTILITY,
                        entry_point=f"{self.repo}.main",
                        homepage=f"https://github.com/{self.owner}/{self.repo}"
                    )
                    manifests.append(manifest)
            
        except Exception as e:
            logger.error(f"获取 GitHub 仓库索引失败: {e}")
        
        return manifests
    
    def _fetch_manifest_from_release(self, release: Dict) -> Optional[PluginManifest]:
        """从 release assets 中获取 manifest"""
        try:
            assets = release.get('assets', [])
            for asset in assets:
                name = asset.get('name', '')
                if name in ['plugin.json', 'manifest.json']:
                    download_url = asset.get('browser_download_url')
                    if download_url:
                        data = self._fetch_json(download_url)
                        if data:
                            return PluginManifest.from_dict(data)
            return None
        except Exception as e:
            logger.debug(f"获取 manifest 失败: {e}")
            return None
    
    def fetch_releases(self, plugin_id: str) -> List[PluginRelease]:
        """
        获取 GitHub releases
        
        Args:
            plugin_id: 插件ID（通常是 repo 名）
            
        Returns:
            List[PluginRelease]: 版本发布列表
        """
        releases = []
        
        try:
            releases_url = f"{self._api_base}/repos/{self.owner}/{self.repo}/releases"
            self.headers = self._get_api_headers()
            data = self._fetch_json(releases_url)
            
            if not data or not isinstance(data, list):
                return releases
            
            for item in data:
                version = item.get('tag_name', '').lstrip('v')
                if not version:
                    continue
                
                # 查找插件包 asset
                download_url = ""
                size_bytes = 0
                checksum = ""
                
                assets = item.get('assets', [])
                for asset in assets:
                    name = asset.get('name', '')
                    if name.endswith('.tar.gz') or name.endswith('.zip'):
                        download_url = asset.get('browser_download_url', '')
                        size_bytes = asset.get('size', 0)
                        break
                
                # 如果没有 asset，使用 tarball
                if not download_url:
                    download_url = item.get('tarball_url', '')
                
                release = PluginRelease(
                    plugin_id=plugin_id,
                    version=version,
                    download_url=download_url,
                    checksum_sha256=checksum,
                    size_bytes=size_bytes,
                    changelog=item.get('body', ''),
                    stability=self._parse_stability(item.get('prerelease', False)),
                    published_at=self._parse_datetime(item.get('published_at', ''))
                )
                releases.append(release)
            
        except Exception as e:
            logger.error(f"获取 GitHub releases 失败: {e}")
        
        return releases
    
    def _parse_stability(self, prerelease: bool) -> ReleaseStability:
        """根据 prerelease 标志判断稳定性"""
        return ReleaseStability.BETA if prerelease else ReleaseStability.STABLE
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析 GitHub 日期时间字符串"""
        try:
            if dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            pass
        return datetime.now()
    
    def download_package(
        self, 
        plugin_id: str, 
        version: str,
        dest_dir: Path
    ) -> Optional[Path]:
        """
        下载 GitHub release asset
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            dest_dir: 目标目录
            
        Returns:
            Optional[Path]: 下载的文件路径
        """
        try:
            # 获取 releases 找到对应版本
            releases = self.fetch_releases(plugin_id)
            
            for release in releases:
                if release.version == version and release.download_url:
                    dest_path = dest_dir / f"{plugin_id}-{version}.tar.gz"
                    
                    if self._download_file(release.download_url, dest_path):
                        return dest_path
            
            # 尝试直接下载 tarball
            tarball_url = f"https://github.com/{self.owner}/{self.repo}/archive/refs/tags/v{version}.tar.gz"
            dest_path = dest_dir / f"{plugin_id}-{version}.tar.gz"
            
            if self._download_file(tarball_url, dest_path):
                return dest_path
            
            # 尝试不带 v 前缀
            tarball_url = f"https://github.com/{self.owner}/{self.repo}/archive/refs/tags/{version}.tar.gz"
            if self._download_file(tarball_url, dest_path):
                return dest_path
            
            return None
            
        except Exception as e:
            logger.error(f"下载 GitHub 插件包失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        检查 GitHub 仓库是否可访问
        
        Returns:
            bool: 是否可用
        """
        try:
            repo_url = f"{self._api_base}/repos/{self.owner}/{self.repo}"
            self.headers = self._get_api_headers()
            data = self._fetch_json(repo_url)
            return data is not None and 'id' in data
        except Exception:
            return False


class RepositoryManager:
    """
    仓库管理器 - 多源聚合
    
    管理多个插件仓库源，支持同步、搜索和下载等操作。
    
    使用示例:
        repo_mgr = RepositoryManager(store)
        
        # 添加仓库源
        repo_mgr.add_source("official", "https://plugins.necorag.io", "http")
        repo_mgr.add_source("local", "/path/to/repo", "local")
        
        # 同步所有源
        results = repo_mgr.sync_all()
        
        # 查找插件
        source, manifest = repo_mgr.find_plugin("my-plugin")
        
        # 下载插件
        path = repo_mgr.download_plugin("my-plugin", "1.0.0", dest_dir)
    """
    
    def __init__(
        self, 
        store: MarketplaceStore,
        default_local_path: Optional[str] = None
    ):
        """
        初始化仓库管理器
        
        Args:
            store: 市场存储实例
            default_local_path: 默认本地仓库路径
        """
        self.store = store
        self.default_local_path = Path(
            default_local_path or Path.home() / '.necorag' / 'marketplace' / 'repository'
        )
        self._repositories: Dict[str, BaseRepository] = {}
        self._lock = threading.Lock()
        
        # 初始化默认本地仓库
        self._init_default_repo()
        
        logger.info(f"RepositoryManager 初始化完成")
    
    def _init_default_repo(self):
        """初始化默认本地仓库"""
        try:
            self.default_local_path.mkdir(parents=True, exist_ok=True)
            
            default_repo = LocalRepository(
                name="local",
                path=str(self.default_local_path)
            )
            self._repositories["local"] = default_repo
            
            # 确保存储中有记录
            self.store.add_repository_source(
                name="local",
                url=str(self.default_local_path),
                repo_type="local",
                priority=100  # 高优先级
            )
            
        except Exception as e:
            logger.warning(f"初始化默认本地仓库失败: {e}")
    
    def _create_repository(
        self, 
        name: str, 
        url: str, 
        repo_type: str, 
        config: Optional[Dict] = None
    ) -> BaseRepository:
        """
        根据类型创建仓库实例
        
        Args:
            name: 仓库名称
            url: 仓库URL或路径
            repo_type: 仓库类型 (local, http, github)
            config: 额外配置
            
        Returns:
            BaseRepository: 仓库实例
        """
        if repo_type == "local":
            return LocalRepository(name, url, config)
        elif repo_type == "github":
            return GitHubRepository(name, url, config)
        else:  # http 或其他
            return RemoteRepository(name, url, config)
    
    # ==================== 仓库源管理 ====================
    
    def add_source(
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
            name: 仓库名称
            url: 仓库URL或路径
            repo_type: 仓库类型 (local, http, github)
            priority: 优先级（数值越大优先级越高）
            config: 额外配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            with self._lock:
                # 创建仓库实例
                repo = self._create_repository(name, url, repo_type, config)
                self._repositories[name] = repo
                
                # 保存到存储
                self.store.add_repository_source(
                    name=name,
                    url=url,
                    repo_type=repo_type,
                    priority=priority,
                    config=config
                )
                
                logger.info(f"添加仓库源: {name} ({repo_type})")
                return True
                
        except Exception as e:
            logger.error(f"添加仓库源失败: {e}")
            return False
    
    def remove_source(self, name: str) -> bool:
        """
        移除仓库源
        
        Args:
            name: 仓库名称
            
        Returns:
            bool: 是否移除成功
        """
        try:
            with self._lock:
                if name in self._repositories:
                    del self._repositories[name]
                
                self.store.remove_repository_source(name)
                
                logger.info(f"移除仓库源: {name}")
                return True
                
        except Exception as e:
            logger.error(f"移除仓库源失败: {e}")
            return False
    
    def list_sources(self) -> List[Dict]:
        """
        列出所有仓库源
        
        Returns:
            List[Dict]: 仓库源列表
        """
        try:
            sources = self.store.get_repository_sources()
            
            # 添加可用性状态
            for source in sources:
                name = source.get('name')
                if name in self._repositories:
                    source['available'] = self._repositories[name].is_available()
                else:
                    source['available'] = False
            
            return sources
            
        except Exception as e:
            logger.error(f"列出仓库源失败: {e}")
            return []
    
    def get_repository(self, name: str) -> Optional[BaseRepository]:
        """
        获取仓库实例
        
        Args:
            name: 仓库名称
            
        Returns:
            Optional[BaseRepository]: 仓库实例
        """
        with self._lock:
            # 如果内存中没有，尝试从存储加载
            if name not in self._repositories:
                sources = self.store.get_repository_sources()
                for source in sources:
                    if source.get('name') == name:
                        repo = self._create_repository(
                            name=source['name'],
                            url=source['url'],
                            repo_type=source['type'],
                            config=source.get('config')
                        )
                        self._repositories[name] = repo
                        break
            
            return self._repositories.get(name)
    
    # ==================== 同步操作 ====================
    
    def sync_source(self, name: str) -> SyncResult:
        """
        同步单个仓库源
        
        1. 拉取远程索引
        2. 对比本地数据，更新新增/变更的插件
        3. 同步版本信息
        4. 更新同步时间
        
        Args:
            name: 仓库名称
            
        Returns:
            SyncResult: 同步结果
        """
        new_count = 0
        updated_count = 0
        errors = []
        
        try:
            repo = self.get_repository(name)
            if not repo:
                return SyncResult(
                    success=False,
                    source_name=name,
                    errors=[f"仓库 {name} 不存在"]
                )
            
            if not repo.is_available():
                return SyncResult(
                    success=False,
                    source_name=name,
                    errors=[f"仓库 {name} 不可用"]
                )
            
            # 拉取索引
            manifests = repo.fetch_index()
            
            for manifest in manifests:
                try:
                    # 检查是否已存在
                    existing = self.store.get_plugin(manifest.plugin_id)
                    
                    if existing:
                        # 更新
                        self.store.update_plugin(manifest)
                        updated_count += 1
                    else:
                        # 新增
                        self.store.add_plugin(manifest)
                        new_count += 1
                    
                    # 同步版本信息
                    releases = repo.fetch_releases(manifest.plugin_id)
                    for release in releases:
                        existing_release = self.store.get_release(
                            manifest.plugin_id, release.version
                        )
                        if not existing_release:
                            self.store.add_release(release)
                            
                except Exception as e:
                    errors.append(f"同步插件 {manifest.plugin_id} 失败: {str(e)}")
            
            # 更新同步时间
            self.store.update_sync_time(name)
            
            logger.info(f"仓库 {name} 同步完成: 新增 {new_count}, 更新 {updated_count}")
            
            return SyncResult(
                success=True,
                source_name=name,
                new_plugins=new_count,
                updated_plugins=updated_count,
                errors=errors,
                synced_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"同步仓库 {name} 失败: {e}")
            return SyncResult(
                success=False,
                source_name=name,
                errors=[str(e)]
            )
    
    def sync_all(self) -> List[SyncResult]:
        """
        同步所有启用的仓库源
        
        Returns:
            List[SyncResult]: 同步结果列表
        """
        results = []
        
        try:
            sources = self.store.get_repository_sources()
            
            for source in sources:
                if source.get('enabled', True):
                    result = self.sync_source(source['name'])
                    results.append(result)
            
        except Exception as e:
            logger.error(f"同步所有仓库失败: {e}")
            results.append(SyncResult(
                success=False,
                source_name="all",
                errors=[str(e)]
            ))
        
        return results
    
    # ==================== 插件查找 ====================
    
    def find_plugin(
        self, 
        plugin_id: str
    ) -> Optional[Tuple[str, PluginManifest]]:
        """
        在所有仓库中查找插件
        
        按优先级顺序搜索。
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[Tuple[str, PluginManifest]]: (source_name, manifest) 或 None
        """
        try:
            # 按优先级排序的仓库源
            sources = sorted(
                self.store.get_repository_sources(),
                key=lambda x: x.get('priority', 0),
                reverse=True
            )
            
            for source in sources:
                if not source.get('enabled', True):
                    continue
                
                repo = self.get_repository(source['name'])
                if not repo or not repo.is_available():
                    continue
                
                # 获取索引
                manifests = repo.fetch_index()
                for manifest in manifests:
                    if manifest.plugin_id == plugin_id:
                        return (source['name'], manifest)
            
            return None
            
        except Exception as e:
            logger.error(f"查找插件 {plugin_id} 失败: {e}")
            return None
    
    def find_release(
        self, 
        plugin_id: str, 
        version: str
    ) -> Optional[Tuple[str, PluginRelease]]:
        """
        在所有仓库中查找指定版本
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            
        Returns:
            Optional[Tuple[str, PluginRelease]]: (source_name, release) 或 None
        """
        try:
            sources = sorted(
                self.store.get_repository_sources(),
                key=lambda x: x.get('priority', 0),
                reverse=True
            )
            
            for source in sources:
                if not source.get('enabled', True):
                    continue
                
                repo = self.get_repository(source['name'])
                if not repo or not repo.is_available():
                    continue
                
                releases = repo.fetch_releases(plugin_id)
                for release in releases:
                    if release.version == version:
                        return (source['name'], release)
            
            return None
            
        except Exception as e:
            logger.error(f"查找版本 {plugin_id}@{version} 失败: {e}")
            return None
    
    # ==================== 下载 ====================
    
    def download_plugin(
        self, 
        plugin_id: str, 
        version: str,
        dest_dir: Path
    ) -> Optional[Path]:
        """
        从仓库下载插件包
        
        按优先级尝试各源。
        
        Args:
            plugin_id: 插件ID
            version: 版本号
            dest_dir: 目标目录
            
        Returns:
            Optional[Path]: 下载的文件路径
        """
        try:
            sources = sorted(
                self.store.get_repository_sources(),
                key=lambda x: x.get('priority', 0),
                reverse=True
            )
            
            for source in sources:
                if not source.get('enabled', True):
                    continue
                
                repo = self.get_repository(source['name'])
                if not repo or not repo.is_available():
                    continue
                
                result = repo.download_package(plugin_id, version, dest_dir)
                if result:
                    logger.info(f"从仓库 {source['name']} 下载插件: {plugin_id}@{version}")
                    return result
            
            logger.warning(f"所有仓库中都未找到插件包: {plugin_id}@{version}")
            return None
            
        except Exception as e:
            logger.error(f"下载插件 {plugin_id}@{version} 失败: {e}")
            return None
    
    # ==================== 本地仓库发布 ====================
    
    def publish_to_local(
        self, 
        manifest: PluginManifest,
        package_path: Path
    ) -> bool:
        """
        发布插件到默认本地仓库
        
        Args:
            manifest: 插件清单
            package_path: 插件包路径
            
        Returns:
            bool: 是否发布成功
        """
        try:
            local_repo = self.get_repository("local")
            if not local_repo or not isinstance(local_repo, LocalRepository):
                logger.error("默认本地仓库不可用")
                return False
            
            return local_repo.publish_plugin(manifest, package_path)
            
        except Exception as e:
            logger.error(f"发布到本地仓库失败: {e}")
            return False
    
    # ==================== 状态 ====================
    
    def check_sources_health(self) -> Dict[str, bool]:
        """
        检查所有仓库源的可用性
        
        Returns:
            Dict[str, bool]: {source_name: is_available}
        """
        health = {}
        
        try:
            sources = self.store.get_repository_sources()
            
            for source in sources:
                name = source['name']
                repo = self.get_repository(name)
                health[name] = repo.is_available() if repo else False
            
        except Exception as e:
            logger.error(f"检查仓库健康状态失败: {e}")
        
        return health
    
    def get_statistics(self) -> Dict:
        """
        获取仓库统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            'total_sources': 0,
            'available_sources': 0,
            'local_sources': 0,
            'remote_sources': 0,
            'sources': []
        }
        
        try:
            sources = self.store.get_repository_sources()
            stats['total_sources'] = len(sources)
            
            for source in sources:
                name = source['name']
                repo = self.get_repository(name)
                
                source_info = {
                    'name': name,
                    'type': source.get('type'),
                    'url': source.get('url'),
                    'priority': source.get('priority', 0),
                    'enabled': source.get('enabled', True),
                    'available': repo.is_available() if repo else False,
                    'last_synced': source.get('last_synced')
                }
                
                if source_info['available']:
                    stats['available_sources'] += 1
                
                if source.get('type') == 'local':
                    stats['local_sources'] += 1
                else:
                    stats['remote_sources'] += 1
                
                stats['sources'].append(source_info)
            
        except Exception as e:
            logger.error(f"获取仓库统计信息失败: {e}")
        
        return stats
