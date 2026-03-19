"""
NecoRAG 插件市场 - 语义版本管理

提供版本约束解析、兼容性检查、升级路径规划和灰度升级支持。
"""

import logging
import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier

from .models import (
    UpgradePath, CanaryDeployment, PluginManifest, ReleaseStability
)
from .store import MarketplaceStore

logger = logging.getLogger(__name__)


class VersionConstraint:
    """
    版本约束解析器 - 支持多种约束语法
    
    支持的约束格式：
    - "*" 或 "" -> 任意版本
    - "1.2.3" -> 精确版本 ==1.2.3
    - "^1.2.3" -> 主版本兼容 >=1.2.3,<2.0.0
    - "~1.2.3" -> 小版本兼容 >=1.2.3,<1.3.0
    - ">=1.0.0,<2.0.0" -> 范围约束
    - ">=1.0.0" -> 单边约束
    """
    
    # 版本号正则表达式
    VERSION_PATTERN = re.compile(
        r'^(?P<prefix>[\^~])?'  # 可选前缀 ^ 或 ~
        r'(?P<major>\d+)'       # 主版本号
        r'(?:\.(?P<minor>\d+)'  # 可选小版本号
        r'(?:\.(?P<patch>\d+))?)?'  # 可选补丁版本号
        r'(?P<prerelease>-[a-zA-Z0-9.]+)?'  # 可选预发布标识
        r'(?P<build>\+[a-zA-Z0-9.]+)?$'     # 可选构建元数据
    )
    
    def __init__(self, constraint_str: str):
        """
        解析版本约束字符串
        
        Args:
            constraint_str: 版本约束字符串
        """
        self.original = constraint_str.strip() if constraint_str else ""
        self._specifier: Optional[SpecifierSet] = None
        self._is_any = False
        
        try:
            self._specifier = self._parse(self.original)
        except Exception as e:
            logger.warning(f"版本约束解析失败: {constraint_str}, 错误: {e}")
            # 解析失败时默认为任意版本
            self._is_any = True
            self._specifier = SpecifierSet()
    
    def _parse(self, constraint: str) -> SpecifierSet:
        """
        将各种约束格式转换为 packaging.SpecifierSet
        
        Args:
            constraint: 版本约束字符串
            
        Returns:
            SpecifierSet: 解析后的约束规范
        """
        # 空字符串或 * 表示任意版本
        if not constraint or constraint == "*":
            self._is_any = True
            return SpecifierSet()
        
        # 已经是标准格式（包含操作符），直接解析
        if any(op in constraint for op in ['>=', '<=', '>', '<', '==', '!=', '~=']):
            return SpecifierSet(constraint)
        
        # 尝试匹配自定义格式
        match = self.VERSION_PATTERN.match(constraint)
        if not match:
            # 如果不匹配，尝试作为精确版本处理
            try:
                Version(constraint)
                return SpecifierSet(f"=={constraint}")
            except InvalidVersion:
                logger.warning(f"无效的版本约束格式: {constraint}")
                self._is_any = True
                return SpecifierSet()
        
        prefix = match.group('prefix')
        major = int(match.group('major'))
        minor = int(match.group('minor')) if match.group('minor') else 0
        patch = int(match.group('patch')) if match.group('patch') else 0
        prerelease = match.group('prerelease') or ""
        
        version_str = f"{major}.{minor}.{patch}{prerelease}"
        
        if prefix == '^':
            # Caret (^) - 主版本兼容
            # ^1.2.3 -> >=1.2.3,<2.0.0
            # ^0.2.3 -> >=0.2.3,<0.3.0 (0.x 版本特殊处理)
            # ^0.0.3 -> >=0.0.3,<0.0.4 (0.0.x 版本特殊处理)
            if major == 0:
                if minor == 0:
                    # ^0.0.x -> 只允许补丁版本变化
                    upper = f"0.0.{patch + 1}"
                else:
                    # ^0.x.y -> 允许到下一个小版本
                    upper = f"0.{minor + 1}.0"
            else:
                # ^x.y.z -> 允许到下一个主版本
                upper = f"{major + 1}.0.0"
            
            return SpecifierSet(f">={version_str},<{upper}")
        
        elif prefix == '~':
            # Tilde (~) - 小版本兼容
            # ~1.2.3 -> >=1.2.3,<1.3.0
            upper = f"{major}.{minor + 1}.0"
            return SpecifierSet(f">={version_str},<{upper}")
        
        else:
            # 无前缀 - 精确版本
            return SpecifierSet(f"=={version_str}")
    
    def matches(self, version: str) -> bool:
        """
        检查版本是否满足约束
        
        Args:
            version: 要检查的版本字符串
            
        Returns:
            bool: 是否满足约束
        """
        if self._is_any:
            return True
        
        try:
            v = Version(version)
            return v in self._specifier
        except InvalidVersion:
            logger.warning(f"无效的版本号: {version}")
            return False
    
    @property
    def specifier(self) -> SpecifierSet:
        """获取内部的 SpecifierSet"""
        return self._specifier
    
    @property
    def is_any_version(self) -> bool:
        """是否接受任意版本"""
        return self._is_any
    
    def __str__(self) -> str:
        if self._is_any:
            return "*"
        return self.original or str(self._specifier)
    
    def __repr__(self) -> str:
        return f"VersionConstraint({self.original!r})"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, VersionConstraint):
            return self.original == other.original
        return False
    
    def __hash__(self) -> int:
        return hash(self.original)


class VersionManager:
    """
    语义版本管理器
    
    提供版本解析、比较、兼容性检查、升级路径规划等功能。
    """
    
    def __init__(self, store: Optional[MarketplaceStore] = None):
        """
        初始化版本管理器
        
        Args:
            store: 市场存储实例（可选）
        """
        self.store = store
        self._canary_deployments: Dict[str, CanaryDeployment] = {}
    
    # ==================== 版本解析 ====================
    
    def parse_version(self, version_str: str) -> Optional[Version]:
        """
        安全解析版本号
        
        Args:
            version_str: 版本字符串
            
        Returns:
            Optional[Version]: 解析后的版本对象，失败返回 None
        """
        try:
            return Version(version_str)
        except InvalidVersion:
            logger.warning(f"无效的版本号: {version_str}")
            return None
    
    def parse_constraint(self, constraint: str) -> VersionConstraint:
        """
        解析版本约束
        
        Args:
            constraint: 约束字符串
            
        Returns:
            VersionConstraint: 版本约束对象
        """
        return VersionConstraint(constraint)
    
    def is_compatible(self, version: str, constraint: str) -> bool:
        """
        检查版本是否满足约束
        
        Args:
            version: 版本号
            constraint: 版本约束
            
        Returns:
            bool: 是否兼容
        """
        try:
            vc = VersionConstraint(constraint)
            return vc.matches(version)
        except Exception as e:
            logger.error(f"版本兼容性检查失败: {e}")
            return False
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        比较两个版本
        
        Args:
            v1: 第一个版本
            v2: 第二个版本
            
        Returns:
            int: -1(v1<v2), 0(相等), 1(v1>v2)
        """
        try:
            ver1 = Version(v1)
            ver2 = Version(v2)
            
            if ver1 < ver2:
                return -1
            elif ver1 > ver2:
                return 1
            else:
                return 0
        except InvalidVersion as e:
            logger.error(f"版本比较失败: {e}")
            # 无法比较时按字符串比较
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            return 0
    
    def sort_versions(self, versions: List[str], reverse: bool = False) -> List[str]:
        """
        排序版本列表
        
        Args:
            versions: 版本列表
            reverse: 是否降序排列
            
        Returns:
            List[str]: 排序后的版本列表
        """
        try:
            # 解析所有版本
            parsed = []
            invalid = []
            
            for v in versions:
                try:
                    parsed.append((Version(v), v))
                except InvalidVersion:
                    invalid.append(v)
            
            # 排序有效版本
            parsed.sort(key=lambda x: x[0], reverse=reverse)
            result = [v[1] for v in parsed]
            
            # 无效版本追加到末尾
            if invalid:
                invalid.sort(reverse=reverse)
                result.extend(invalid)
            
            return result
        except Exception as e:
            logger.error(f"版本排序失败: {e}")
            return sorted(versions, reverse=reverse)
    
    def get_latest_compatible(self, versions: List[str], constraint: str) -> Optional[str]:
        """
        从版本列表中找到满足约束的最新版本
        
        Args:
            versions: 版本列表
            constraint: 版本约束
            
        Returns:
            Optional[str]: 满足约束的最新版本，没有则返回 None
        """
        vc = VersionConstraint(constraint)
        
        # 过滤出满足约束的版本
        compatible = [v for v in versions if vc.matches(v)]
        
        if not compatible:
            return None
        
        # 返回最新版本
        sorted_versions = self.sort_versions(compatible, reverse=True)
        return sorted_versions[0] if sorted_versions else None
    
    # ==================== NecoRAG 兼容性 ====================
    
    def check_necorag_compatibility(
        self, 
        manifest: PluginManifest, 
        necorag_version: str
    ) -> bool:
        """
        检查插件与 NecoRAG 版本的兼容性
        
        Args:
            manifest: 插件清单
            necorag_version: 当前 NecoRAG 版本
            
        Returns:
            bool: 是否兼容
        """
        try:
            neco_ver = self.parse_version(necorag_version)
            if not neco_ver:
                return False
            
            # 检查最低版本要求
            if manifest.min_necorag_version:
                min_ver = self.parse_version(manifest.min_necorag_version)
                if min_ver and neco_ver < min_ver:
                    logger.info(
                        f"NecoRAG 版本 {necorag_version} 低于插件最低要求 "
                        f"{manifest.min_necorag_version}"
                    )
                    return False
            
            # 检查最高版本限制
            if manifest.max_necorag_version:
                max_ver = self.parse_version(manifest.max_necorag_version)
                if max_ver and neco_ver > max_ver:
                    logger.info(
                        f"NecoRAG 版本 {necorag_version} 高于插件最高支持 "
                        f"{manifest.max_necorag_version}"
                    )
                    return False
            
            return True
        except Exception as e:
            logger.error(f"NecoRAG 兼容性检查失败: {e}")
            return False
    
    # ==================== 升级路径 ====================
    
    def plan_upgrade(
        self, 
        plugin_id: str, 
        current_version: str,
        target_version: Optional[str] = None
    ) -> UpgradePath:
        """
        规划升级路径
        
        Args:
            plugin_id: 插件ID
            current_version: 当前版本
            target_version: 目标版本（None 则升级到最新稳定版）
            
        Returns:
            UpgradePath: 升级路径信息
        """
        try:
            # 获取可用版本列表
            available = self.find_available_upgrades(plugin_id, current_version)
            
            if not available:
                return UpgradePath(
                    plugin_id=plugin_id,
                    current_version=current_version,
                    target_version=current_version,
                    steps=[],
                    is_compatible=True,
                    breaking_changes=[]
                )
            
            # 确定目标版本
            if target_version is None:
                # 默认升级到最新稳定版
                if self.store:
                    latest = self.store.get_latest_release(
                        plugin_id, ReleaseStability.STABLE
                    )
                    target_version = latest.version if latest else available[-1]
                else:
                    target_version = available[-1]
            
            # 检查目标版本是否可用
            if target_version not in available and target_version != current_version:
                cmp = self.compare_versions(target_version, current_version)
                if cmp <= 0:
                    # 目标版本不高于当前版本
                    return UpgradePath(
                        plugin_id=plugin_id,
                        current_version=current_version,
                        target_version=current_version,
                        steps=[],
                        is_compatible=True,
                        breaking_changes=["目标版本不高于当前版本"]
                    )
            
            # 检查是否为主版本升级
            is_major = self.is_major_upgrade(current_version, target_version)
            breaking_changes = []
            
            if is_major:
                breaking_changes.append(
                    f"主版本升级 ({current_version} -> {target_version})，"
                    "可能存在不兼容变更"
                )
            
            # 构建升级步骤
            steps = self._build_upgrade_steps(
                current_version, target_version, available
            )
            
            return UpgradePath(
                plugin_id=plugin_id,
                current_version=current_version,
                target_version=target_version,
                steps=steps,
                is_compatible=not is_major,
                breaking_changes=breaking_changes
            )
            
        except Exception as e:
            logger.error(f"升级路径规划失败: {e}")
            return UpgradePath(
                plugin_id=plugin_id,
                current_version=current_version,
                target_version=target_version or current_version,
                steps=[],
                is_compatible=False,
                breaking_changes=[f"升级路径规划失败: {str(e)}"]
            )
    
    def _build_upgrade_steps(
        self, 
        current: str, 
        target: str, 
        available: List[str]
    ) -> List[str]:
        """
        构建升级步骤列表
        
        对于主版本升级，需要经过每个主版本的最后一个版本。
        例如: 1.5.0 -> 3.2.0 需要经过 1.x.x 最新版 -> 2.x.x 最新版 -> 3.2.0
        
        Args:
            current: 当前版本
            target: 目标版本
            available: 可用版本列表
            
        Returns:
            List[str]: 升级步骤版本列表
        """
        try:
            current_ver = Version(current)
            target_ver = Version(target)
            
            # 如果版本相同或目标更低，无需升级
            if target_ver <= current_ver:
                return []
            
            # 获取主版本跨度
            current_major = current_ver.major
            target_major = target_ver.major
            
            # 如果只是小版本或补丁升级，直接升级
            if current_major == target_major:
                return [target]
            
            # 主版本升级，需要分步
            steps = []
            sorted_available = self.sort_versions(available)
            
            # 对每个中间主版本，找到该主版本的最新版本
            for major in range(current_major + 1, target_major + 1):
                # 找到该主版本的最新版本
                major_versions = [
                    v for v in sorted_available
                    if self._get_major_version(v) == major
                ]
                
                if major_versions:
                    latest_in_major = self.sort_versions(
                        major_versions, reverse=True
                    )[0]
                    
                    # 如果是目标主版本，使用目标版本
                    if major == target_major:
                        steps.append(target)
                    else:
                        steps.append(latest_in_major)
            
            return steps if steps else [target]
            
        except Exception as e:
            logger.warning(f"构建升级步骤失败: {e}")
            return [target]
    
    def _get_major_version(self, version: str) -> int:
        """获取版本的主版本号"""
        try:
            return Version(version).major
        except InvalidVersion:
            return 0
    
    def find_available_upgrades(
        self, 
        plugin_id: str, 
        current_version: str
    ) -> List[str]:
        """
        查找所有可用的升级版本
        
        Args:
            plugin_id: 插件ID
            current_version: 当前版本
            
        Returns:
            List[str]: 可用升级版本列表（已排序）
        """
        try:
            if not self.store:
                return []
            
            # 获取所有发布版本
            releases = self.store.get_releases(plugin_id)
            all_versions = [r.version for r in releases]
            
            # 过滤出高于当前版本的版本
            upgrades = []
            for v in all_versions:
                if self.compare_versions(v, current_version) > 0:
                    upgrades.append(v)
            
            return self.sort_versions(upgrades)
            
        except Exception as e:
            logger.error(f"查找可用升级失败: {e}")
            return []
    
    # ==================== 灰度升级 ====================
    
    def create_canary(
        self, 
        plugin_id: str, 
        current_version: str,
        new_version: str, 
        percentage: float = 0.1
    ) -> CanaryDeployment:
        """
        创建灰度部署
        
        Args:
            plugin_id: 插件ID
            current_version: 当前版本
            new_version: 新版本
            percentage: 初始流量比例（0.0-1.0）
            
        Returns:
            CanaryDeployment: 灰度部署信息
        """
        # 验证参数
        percentage = max(0.0, min(1.0, percentage))
        
        deployment = CanaryDeployment(
            plugin_id=plugin_id,
            current_version=current_version,
            new_version=new_version,
            percentage=percentage,
            status="running",
            metrics={
                "requests": 0,
                "errors": 0,
                "error_rate": 0.0,
                "avg_latency": 0.0,
                "p99_latency": 0.0
            },
            started_at=datetime.now()
        )
        
        # 保存到存储
        if self.store:
            self.store.save_canary_deployment(deployment)
        
        # 缓存到内存
        self._canary_deployments[deployment.deployment_id] = deployment
        
        logger.info(
            f"创建灰度部署: {plugin_id} {current_version} -> {new_version}, "
            f"流量比例: {percentage:.1%}"
        )
        
        return deployment
    
    def evaluate_canary(
        self, 
        deployment_id: str,
        error_threshold: float = 0.05,
        latency_threshold: float = 2.0
    ) -> Dict:
        """
        评估灰度部署
        
        Args:
            deployment_id: 部署ID
            error_threshold: 错误率阈值（默认5%）
            latency_threshold: 延迟阈值（秒，默认2.0）
            
        Returns:
            Dict: 评估结果 {"action": str, "reason": str, "metrics": dict}
        """
        try:
            # 获取部署信息
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                return {
                    "action": "rollback",
                    "reason": "灰度部署不存在",
                    "metrics": {}
                }
            
            metrics = deployment.metrics
            
            # 检查样本量是否足够
            min_requests = 100
            requests = metrics.get("requests", 0)
            
            if requests < min_requests:
                return {
                    "action": "continue",
                    "reason": f"样本量不足（{requests}/{min_requests}），继续观察",
                    "metrics": metrics
                }
            
            # 检查错误率
            error_rate = metrics.get("error_rate", 0.0)
            if error_rate > error_threshold:
                return {
                    "action": "rollback",
                    "reason": f"错误率 {error_rate:.2%} 超过阈值 {error_threshold:.2%}",
                    "metrics": metrics
                }
            
            # 检查延迟
            avg_latency = metrics.get("avg_latency", 0.0)
            if avg_latency > latency_threshold:
                return {
                    "action": "rollback",
                    "reason": f"平均延迟 {avg_latency:.2f}s 超过阈值 {latency_threshold:.2f}s",
                    "metrics": metrics
                }
            
            # 检查 P99 延迟
            p99_latency = metrics.get("p99_latency", 0.0)
            if p99_latency > latency_threshold * 3:
                return {
                    "action": "rollback",
                    "reason": f"P99延迟 {p99_latency:.2f}s 过高",
                    "metrics": metrics
                }
            
            # 指标正常，可以推广
            return {
                "action": "promote",
                "reason": "所有指标正常，可以推广",
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"灰度评估失败: {e}")
            return {
                "action": "continue",
                "reason": f"评估出错: {str(e)}",
                "metrics": {}
            }
    
    def promote_canary(self, deployment_id: str) -> bool:
        """
        推广灰度部署（100% 流量）
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            bool: 是否成功
        """
        try:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                logger.warning(f"灰度部署不存在: {deployment_id}")
                return False
            
            # 更新状态
            deployment.status = "promoted"
            deployment.percentage = 1.0
            
            # 保存到存储
            if self.store:
                self.store.update_canary_status(
                    deployment_id, "promoted", deployment.metrics
                )
            
            logger.info(f"灰度部署已推广: {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"推广灰度部署失败: {e}")
            return False
    
    def rollback_canary(self, deployment_id: str) -> bool:
        """
        回滚灰度部署
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            bool: 是否成功
        """
        try:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                logger.warning(f"灰度部署不存在: {deployment_id}")
                return False
            
            # 更新状态
            deployment.status = "rolled_back"
            deployment.percentage = 0.0
            
            # 保存到存储
            if self.store:
                self.store.update_canary_status(
                    deployment_id, "rolled_back", deployment.metrics
                )
            
            logger.info(f"灰度部署已回滚: {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"回滚灰度部署失败: {e}")
            return False
    
    def _get_deployment(self, deployment_id: str) -> Optional[CanaryDeployment]:
        """获取灰度部署（先查缓存，再查存储）"""
        # 先查内存缓存
        if deployment_id in self._canary_deployments:
            return self._canary_deployments[deployment_id]
        
        # 再查存储
        if self.store:
            deployment = self.store.get_canary_deployment(deployment_id)
            if deployment:
                self._canary_deployments[deployment_id] = deployment
                return deployment
        
        return None
    
    def update_canary_metrics(
        self, 
        deployment_id: str, 
        metrics: Dict[str, float]
    ) -> bool:
        """
        更新灰度部署指标
        
        Args:
            deployment_id: 部署ID
            metrics: 新指标数据
            
        Returns:
            bool: 是否成功
        """
        try:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                return False
            
            # 合并指标
            deployment.metrics.update(metrics)
            
            # 计算错误率
            requests = deployment.metrics.get("requests", 0)
            errors = deployment.metrics.get("errors", 0)
            if requests > 0:
                deployment.metrics["error_rate"] = errors / requests
            
            # 保存到存储
            if self.store:
                self.store.update_canary_status(
                    deployment_id, deployment.status, deployment.metrics
                )
            
            return True
            
        except Exception as e:
            logger.error(f"更新灰度指标失败: {e}")
            return False
    
    # ==================== 工具方法 ====================
    
    def is_major_upgrade(self, from_version: str, to_version: str) -> bool:
        """
        是否为主版本升级（可能有 breaking changes）
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            bool: 是否为主版本升级
        """
        try:
            from_ver = Version(from_version)
            to_ver = Version(to_version)
            return to_ver.major > from_ver.major
        except InvalidVersion:
            return False
    
    def is_prerelease(self, version: str) -> bool:
        """
        是否为预发布版本
        
        Args:
            version: 版本字符串
            
        Returns:
            bool: 是否为预发布版本
        """
        try:
            ver = Version(version)
            return ver.is_prerelease
        except InvalidVersion:
            return False
    
    def get_next_version(self, current: str, bump: str = "patch") -> str:
        """
        获取下一个版本号
        
        Args:
            current: 当前版本
            bump: 版本升级类型 ("major", "minor", "patch")
            
        Returns:
            str: 下一个版本号
        """
        try:
            ver = Version(current)
            major = ver.major
            minor = ver.minor
            micro = ver.micro
            
            if bump == "major":
                return f"{major + 1}.0.0"
            elif bump == "minor":
                return f"{major}.{minor + 1}.0"
            else:  # patch
                return f"{major}.{minor}.{micro + 1}"
                
        except InvalidVersion:
            logger.warning(f"无法解析版本号: {current}")
            return current
    
    def normalize_version(self, version: str) -> str:
        """
        规范化版本号
        
        Args:
            version: 版本字符串
            
        Returns:
            str: 规范化后的版本号
        """
        try:
            return str(Version(version))
        except InvalidVersion:
            return version
    
    def get_version_info(self, version: str) -> Dict:
        """
        获取版本详细信息
        
        Args:
            version: 版本字符串
            
        Returns:
            Dict: 版本信息字典
        """
        try:
            ver = Version(version)
            return {
                "version": str(ver),
                "major": ver.major,
                "minor": ver.minor,
                "micro": ver.micro,
                "is_prerelease": ver.is_prerelease,
                "is_postrelease": ver.is_postrelease,
                "is_devrelease": ver.is_devrelease,
                "pre": ver.pre,
                "post": ver.post,
                "dev": ver.dev,
                "local": ver.local
            }
        except InvalidVersion:
            return {
                "version": version,
                "major": 0,
                "minor": 0,
                "micro": 0,
                "is_prerelease": False,
                "is_postrelease": False,
                "is_devrelease": False,
                "pre": None,
                "post": None,
                "dev": None,
                "local": None
            }
