"""
NecoRAG 插件市场 - GDI 质量评估系统

借鉴 OpenClaw GDI（Global Desirability Index）评分体系，
为 NecoRAG 定制 6 维度质量评估系统。

GDI 综合评分公式:
GDI = 0.20 * 代码质量 + 0.15 * 功能完整性 + 0.25 * 可靠性
    + 0.15 * 性能 + 0.10 * 用户体验 + 0.15 * 实际使用数据
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .models import GDIScore, PluginManifest, PluginRating, ReleaseStability
from .store import MarketplaceStore

logger = logging.getLogger(__name__)

# GDI 默认权重配置
DEFAULT_GDI_WEIGHTS = {
    'code_quality': 0.20,
    'functionality': 0.15,
    'reliability': 0.25,
    'performance': 0.15,
    'user_experience': 0.10,
    'actual_usage': 0.15
}


class GDIAssessor:
    """GDI 全局期望指数评估器"""
    
    def __init__(self, store: MarketplaceStore, 
                 weights: Optional[Dict[str, float]] = None):
        """
        初始化 GDI 评估器
        
        Args:
            store: 插件市场存储层
            weights: 自定义权重配置
        """
        self.store = store
        self.weights = weights or DEFAULT_GDI_WEIGHTS.copy()
        
        logger.info("GDIAssessor 初始化完成")
    
    # === 综合评分 ===
    def calculate_gdi(self, plugin_id: str) -> Optional[GDIScore]:
        """
        计算插件的 GDI 综合评分
        
        流程:
        1. 分别计算 6 个维度的分数（0-100 分）
        2. 按权重加权求和得到综合分
        3. 保存评分到数据库
        4. 返回 GDIScore 对象
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[GDIScore]: GDI 评分，失败返回 None
        """
        try:
            # 检查插件是否存在
            plugin = self.store.get_plugin(plugin_id)
            if not plugin:
                logger.warning(f"插件不存在: {plugin_id}")
                return None
            
            # 计算各维度分数
            code_quality = self.assess_code_quality(plugin_id)
            functionality = self.assess_functionality(plugin_id)
            reliability = self.assess_reliability(plugin_id)
            performance = self.assess_performance(plugin_id)
            user_experience = self.assess_user_experience(plugin_id)
            actual_usage = self.assess_actual_usage(plugin_id)
            freshness = self.assess_freshness(plugin_id)
            
            # 按权重计算综合分
            overall_score = (
                self.weights['code_quality'] * code_quality +
                self.weights['functionality'] * functionality +
                self.weights['reliability'] * reliability +
                self.weights['performance'] * performance +
                self.weights['user_experience'] * user_experience +
                self.weights['actual_usage'] * actual_usage
            )
            
            # 创建 GDIScore 对象
            gdi_score = GDIScore(
                plugin_id=plugin_id,
                overall_score=round(overall_score, 2),
                code_quality=round(code_quality, 2),
                functionality=round(functionality, 2),
                reliability=round(reliability, 2),
                performance=round(performance, 2),
                user_experience=round(user_experience, 2),
                actual_usage=round(actual_usage, 2),
                freshness=round(freshness, 2),
                calculated_at=datetime.now()
            )
            
            # 保存到数据库
            self.store.save_gdi_score(gdi_score)
            
            logger.info(f"计算 GDI 评分: {plugin_id} = {overall_score:.2f}")
            return gdi_score
            
        except Exception as e:
            logger.error(f"计算 GDI 评分失败: {plugin_id}, {e}")
            return None
    
    # === 6 个维度评分 ===
    def assess_code_quality(self, plugin_id: str) -> float:
        """
        评估代码质量 (0-100)
        
        子维度:
        - 是否有完整的 entry_point（30%）
        - 依赖数量（越少越好，最佳 0-3 个）（25%）
        - 权限最小化（申请的权限越少越好）（25%）
        - 元数据完整度（homepage, repository, license 等）（20%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 代码质量分数 (0-100)
        """
        try:
            plugin = self.store.get_plugin(plugin_id)
            if not plugin:
                return 0.0
            
            score = 0.0
            
            # 1. entry_point 完整性 (30%)
            if plugin.entry_point and plugin.entry_point.strip():
                # 检查格式是否规范（模块.类名 或 模块.函数）
                if '.' in plugin.entry_point:
                    score += 30.0
                else:
                    score += 15.0  # 简单格式给部分分
            
            # 2. 依赖数量评估 (25%)
            dep_count = len(plugin.dependencies)
            if dep_count == 0:
                dep_score = 100.0
            elif dep_count <= 3:
                dep_score = 90.0
            elif dep_count <= 5:
                dep_score = 70.0
            elif dep_count <= 10:
                dep_score = 50.0
            else:
                dep_score = max(0.0, 30.0 - (dep_count - 10) * 2)
            score += 0.25 * dep_score
            
            # 3. 权限最小化 (25%)
            perm_count = len(plugin.permissions)
            if perm_count == 0:
                perm_score = 100.0
            elif perm_count <= 2:
                perm_score = 90.0
            elif perm_count <= 4:
                perm_score = 70.0
            elif perm_count <= 6:
                perm_score = 50.0
            else:
                perm_score = max(0.0, 30.0 - (perm_count - 6) * 5)
            score += 0.25 * perm_score
            
            # 4. 元数据完整度 (20%)
            metadata_fields = [
                plugin.homepage,
                plugin.repository,
                plugin.license,
                plugin.description,
                plugin.icon
            ]
            filled_count = sum(1 for f in metadata_fields if f and f.strip())
            metadata_score = (filled_count / len(metadata_fields)) * 100.0
            score += 0.20 * metadata_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估代码质量失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_functionality(self, plugin_id: str) -> float:
        """
        评估功能完整性 (0-100)
        
        子维度:
        - 版本发布数量（有多个版本说明持续迭代）（40%）
        - changelog 完整度（有 changelog 的版本比例）（30%）
        - 标签描述丰富度（标签数量 + 描述长度）（30%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 功能完整性分数 (0-100)
        """
        try:
            plugin = self.store.get_plugin(plugin_id)
            if not plugin:
                return 0.0
            
            releases = self.store.get_releases(plugin_id)
            score = 0.0
            
            # 1. 版本发布数量 (40%)
            release_count = len(releases)
            if release_count >= 10:
                version_score = 100.0
            elif release_count >= 5:
                version_score = 80.0
            elif release_count >= 3:
                version_score = 60.0
            elif release_count >= 1:
                version_score = 40.0
            else:
                version_score = 20.0  # 至少有基础版本
            score += 0.40 * version_score
            
            # 2. changelog 完整度 (30%)
            if releases:
                with_changelog = sum(1 for r in releases if r.changelog and r.changelog.strip())
                changelog_ratio = with_changelog / len(releases)
                changelog_score = changelog_ratio * 100.0
            else:
                changelog_score = 0.0
            score += 0.30 * changelog_score
            
            # 3. 标签描述丰富度 (30%)
            tag_count = len(plugin.tags)
            desc_length = len(plugin.description)
            
            # 标签分数：3-10 个最佳
            if 3 <= tag_count <= 10:
                tag_score = 100.0
            elif tag_count > 10:
                tag_score = 80.0
            elif tag_count >= 1:
                tag_score = tag_count * 30.0
            else:
                tag_score = 0.0
            
            # 描述分数：100-500 字符最佳
            if 100 <= desc_length <= 500:
                desc_score = 100.0
            elif desc_length > 500:
                desc_score = 90.0
            elif desc_length >= 50:
                desc_score = 70.0
            elif desc_length >= 20:
                desc_score = 50.0
            else:
                desc_score = max(0.0, desc_length * 2.5)
            
            richness_score = (tag_score + desc_score) / 2
            score += 0.30 * richness_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估功能完整性失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_reliability(self, plugin_id: str) -> float:
        """
        评估可靠性 (0-100)
        
        子维度:
        - 错误事件率（error 事件 / 总事件）（40%）
        - 卸载率（uninstall / install）（30%）
        - 稳定版本比例（stable 版本 / 总版本）（30%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 可靠性分数 (0-100)
        """
        try:
            score = 0.0
            
            # 1. 错误事件率 (40%)
            all_events = self.store.get_usage_stats(plugin_id, days=90)
            if all_events:
                error_events = [e for e in all_events if e.get('event_type') == 'error']
                error_rate = len(error_events) / len(all_events)
                # 错误率越低越好
                error_score = max(0.0, 100.0 - error_rate * 200.0)
            else:
                # 没有事件记录，给中等分数
                error_score = 50.0
            score += 0.40 * error_score
            
            # 2. 卸载率 (30%)
            install_events = self.store.get_usage_stats(plugin_id, event_type='install', days=90)
            uninstall_events = self.store.get_usage_stats(plugin_id, event_type='uninstall', days=90)
            
            if install_events:
                uninstall_rate = len(uninstall_events) / len(install_events)
                # 卸载率越低越好
                uninstall_score = max(0.0, 100.0 - uninstall_rate * 100.0)
            else:
                uninstall_score = 50.0
            score += 0.30 * uninstall_score
            
            # 3. 稳定版本比例 (30%)
            releases = self.store.get_releases(plugin_id)
            if releases:
                stable_releases = [r for r in releases if r.stability == ReleaseStability.STABLE]
                stable_ratio = len(stable_releases) / len(releases)
                stable_score = stable_ratio * 100.0
            else:
                stable_score = 50.0  # 没有发布记录
            score += 0.30 * stable_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估可靠性失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_performance(self, plugin_id: str) -> float:
        """
        评估性能 (0-100)
        
        子维度:
        - 包大小效率（越小越好，基准 10MB）（40%）
        - 依赖数量（越少启动越快）（30%）
        - 无性能相关错误事件（30%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 性能分数 (0-100)
        """
        try:
            plugin = self.store.get_plugin(plugin_id)
            if not plugin:
                return 0.0
            
            score = 0.0
            
            # 1. 包大小效率 (40%)
            latest_release = self.store.get_latest_release(plugin_id)
            if latest_release and latest_release.size_bytes > 0:
                size_mb = latest_release.size_bytes / (1024 * 1024)
                # 10MB 以下满分，超过线性衰减
                if size_mb <= 1:
                    size_score = 100.0
                elif size_mb <= 5:
                    size_score = 90.0
                elif size_mb <= 10:
                    size_score = 80.0
                elif size_mb <= 50:
                    size_score = 60.0 - (size_mb - 10) * 0.5
                else:
                    size_score = max(20.0, 40.0 - (size_mb - 50) * 0.2)
            else:
                size_score = 70.0  # 未知大小给中等偏上分数
            score += 0.40 * size_score
            
            # 2. 依赖数量 (30%)
            dep_count = len(plugin.dependencies)
            if dep_count == 0:
                dep_score = 100.0
            elif dep_count <= 3:
                dep_score = 90.0
            elif dep_count <= 5:
                dep_score = 70.0
            elif dep_count <= 10:
                dep_score = 50.0
            else:
                dep_score = max(20.0, 40.0 - (dep_count - 10) * 2)
            score += 0.30 * dep_score
            
            # 3. 无性能相关错误 (30%)
            all_events = self.store.get_usage_stats(plugin_id, days=30)
            perf_error_keywords = ['timeout', 'slow', 'memory', 'performance', 'oom']
            
            perf_errors = 0
            for event in all_events:
                event_data = event.get('event_data', {})
                if isinstance(event_data, str):
                    event_data_lower = event_data.lower()
                else:
                    event_data_lower = str(event_data).lower()
                
                if any(kw in event_data_lower for kw in perf_error_keywords):
                    perf_errors += 1
            
            if all_events:
                perf_error_rate = perf_errors / len(all_events)
                perf_score = max(0.0, 100.0 - perf_error_rate * 300.0)
            else:
                perf_score = 70.0
            score += 0.30 * perf_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估性能失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_user_experience(self, plugin_id: str) -> float:
        """
        评估用户体验 (0-100)
        
        子维度:
        - 用户评分平均分（直接映射到 0-100）（50%）
        - 评分数量（参与评价的用户越多说明体验可评）（25%）
        - 评价中的维度评分（如果有 dimensions）（25%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 用户体验分数 (0-100)
        """
        try:
            score = 0.0
            
            # 获取评分数据
            avg_rating, rating_count = self.store.get_average_rating(plugin_id)
            ratings, _ = self.store.get_ratings(plugin_id, page=1, page_size=100)
            
            # 1. 用户评分平均分 (50%)
            # 评分范围 1-5，映射到 0-100
            if rating_count > 0:
                rating_score = (avg_rating - 1) / 4 * 100.0
            else:
                rating_score = 50.0  # 无评分给中等分
            score += 0.50 * rating_score
            
            # 2. 评分数量 (25%)
            # 使用对数标准化
            count_score = self._normalize_log(rating_count, base_value=50)
            score += 0.25 * count_score
            
            # 3. 维度评分丰富度 (25%)
            if ratings:
                with_dimensions = sum(1 for r in ratings if r.dimensions)
                dimension_ratio = with_dimensions / len(ratings)
                
                # 收集所有维度评分
                all_dimension_scores: List[float] = []
                for rating in ratings:
                    if rating.dimensions:
                        all_dimension_scores.extend(rating.dimensions.values())
                
                if all_dimension_scores:
                    # 维度评分的平均值
                    avg_dim = sum(all_dimension_scores) / len(all_dimension_scores)
                    dim_score = (avg_dim - 1) / 4 * 100.0 if avg_dim > 1 else 0.0
                else:
                    dim_score = dimension_ratio * 50.0  # 有维度但没分数
            else:
                dim_score = 50.0
            score += 0.25 * dim_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估用户体验失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_actual_usage(self, plugin_id: str) -> float:
        """
        评估实际使用数据 (0-100)
        
        子维度:
        - 活跃安装数（对数标准化）（40%）
        - 总下载量（对数标准化）（25%）
        - 最近 30 天事件活跃度（35%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 实际使用数据分数 (0-100)
        """
        try:
            score = 0.0
            
            # 1. 活跃安装数 (40%)
            active_installs = self.store.get_active_install_count(plugin_id)
            install_score = self._normalize_log(active_installs, base_value=100)
            score += 0.40 * install_score
            
            # 2. 总下载量 (25%)
            releases = self.store.get_releases(plugin_id)
            total_downloads = sum(r.download_count for r in releases)
            download_score = self._normalize_log(total_downloads, base_value=1000)
            score += 0.25 * download_score
            
            # 3. 最近 30 天事件活跃度 (35%)
            recent_events = self.store.get_usage_stats(plugin_id, days=30)
            event_count = len(recent_events)
            activity_score = self._normalize_log(event_count, base_value=100)
            score += 0.35 * activity_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估实际使用数据失败: {plugin_id}, {e}")
            return 0.0
    
    def assess_freshness(self, plugin_id: str) -> float:
        """
        评估新鲜度 (0-100) - 虽然不在主权重中，但作为附加维度
        
        子维度:
        - 最近更新时间（越近越好）（50%）
        - 更新频率（版本数 / 存活月数）（30%）
        - 是否在持续维护（最近 90 天有更新）（20%）
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            float: 新鲜度分数 (0-100)
        """
        try:
            plugin = self.store.get_plugin(plugin_id)
            if not plugin:
                return 0.0
            
            releases = self.store.get_releases(plugin_id)
            score = 0.0
            
            # 1. 最近更新时间 (50%)
            days_since_update = self._days_since(plugin.updated_at)
            if days_since_update <= 7:
                recency_score = 100.0
            elif days_since_update <= 30:
                recency_score = 90.0
            elif days_since_update <= 90:
                recency_score = 70.0
            elif days_since_update <= 180:
                recency_score = 50.0
            elif days_since_update <= 365:
                recency_score = 30.0
            else:
                recency_score = max(10.0, 20.0 - (days_since_update - 365) / 30)
            score += 0.50 * recency_score
            
            # 2. 更新频率 (30%)
            days_alive = max(1, self._days_since(plugin.created_at))
            months_alive = days_alive / 30.0
            release_count = len(releases)
            
            if months_alive > 0:
                releases_per_month = release_count / months_alive
                # 每月 0.5-2 次更新最佳
                if 0.5 <= releases_per_month <= 2:
                    frequency_score = 100.0
                elif releases_per_month > 2:
                    frequency_score = 90.0  # 更新太频繁也还行
                elif releases_per_month >= 0.1:
                    frequency_score = releases_per_month * 150.0
                else:
                    frequency_score = 20.0
            else:
                frequency_score = 50.0
            score += 0.30 * frequency_score
            
            # 3. 是否持续维护 (20%)
            if days_since_update <= 90:
                maintenance_score = 100.0
            elif days_since_update <= 180:
                maintenance_score = 50.0
            else:
                maintenance_score = 0.0
            score += 0.20 * maintenance_score
            
            return self._clamp(score)
            
        except Exception as e:
            logger.error(f"评估新鲜度失败: {plugin_id}, {e}")
            return 0.0
    
    # === 批量操作 ===
    def refresh_all_scores(self) -> Dict[str, GDIScore]:
        """
        批量刷新所有插件的 GDI 评分
        
        Returns:
            Dict[str, GDIScore]: 插件ID -> GDI评分的映射
        """
        try:
            plugins, _ = self.store.list_plugins(page=1, page_size=10000)
            results: Dict[str, GDIScore] = {}
            
            for plugin in plugins:
                gdi_score = self.calculate_gdi(plugin.plugin_id)
                if gdi_score:
                    results[plugin.plugin_id] = gdi_score
            
            logger.info(f"批量刷新 GDI 评分完成: {len(results)} 个插件")
            return results
            
        except Exception as e:
            logger.error(f"批量刷新 GDI 评分失败: {e}")
            return {}
    
    def refresh_score(self, plugin_id: str) -> Optional[GDIScore]:
        """
        刷新单个插件评分
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[GDIScore]: 更新后的 GDI 评分
        """
        return self.calculate_gdi(plugin_id)
    
    # === 排行榜 ===
    def get_leaderboard(self, dimension: Optional[str] = None,
                        limit: int = 50) -> List[GDIScore]:
        """
        获取排行榜
        
        Args:
            dimension: 排序维度，None 表示综合评分
                可选: "code_quality", "functionality", "reliability",
                      "performance", "user_experience", "actual_usage", "freshness"
            limit: 返回数量
            
        Returns:
            List[GDIScore]: GDI 评分列表
        """
        try:
            # 获取所有评分
            leaderboard = self.store.get_gdi_leaderboard(limit=limit * 2)
            
            if dimension is None:
                # 综合评分排序（已经按 overall_score 排序）
                return leaderboard[:limit]
            
            # 按特定维度排序
            valid_dimensions = [
                'code_quality', 'functionality', 'reliability',
                'performance', 'user_experience', 'actual_usage', 'freshness'
            ]
            
            if dimension not in valid_dimensions:
                logger.warning(f"无效的维度: {dimension}")
                return leaderboard[:limit]
            
            # 按指定维度排序
            sorted_scores = sorted(
                leaderboard,
                key=lambda s: getattr(s, dimension, 0.0),
                reverse=True
            )
            
            return sorted_scores[:limit]
            
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}")
            return []
    
    def get_score_distribution(self) -> Dict[str, int]:
        """
        获取评分分布
        
        Returns:
            Dict[str, int]: 评分区间 -> 插件数量
        """
        try:
            leaderboard = self.store.get_gdi_leaderboard(limit=10000)
            
            distribution = {
                "0-20": 0,
                "20-40": 0,
                "40-60": 0,
                "60-80": 0,
                "80-100": 0
            }
            
            for score in leaderboard:
                overall = score.overall_score
                if overall < 20:
                    distribution["0-20"] += 1
                elif overall < 40:
                    distribution["20-40"] += 1
                elif overall < 60:
                    distribution["40-60"] += 1
                elif overall < 80:
                    distribution["60-80"] += 1
                else:
                    distribution["80-100"] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"获取评分分布失败: {e}")
            return {}
    
    # === 工具方法 ===
    def _normalize_log(self, value: float, base_value: float = 100) -> float:
        """
        对数标准化: 将 value 通过对数函数映射到 0-100
        适用于下载量、安装数等长尾分布数据
        
        Args:
            value: 原始值
            base_value: 基准值（达到此值时分数约为 100）
            
        Returns:
            float: 标准化后的分数 (0-100)
        """
        if value <= 0:
            return 0.0
        return min(100.0, (math.log(value + 1) / math.log(base_value + 1)) * 100)
    
    def _clamp(self, value: float, min_val: float = 0.0, 
               max_val: float = 100.0) -> float:
        """
        将值限制在范围内
        
        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            float: 限制后的值
        """
        return max(min_val, min(max_val, value))
    
    def _days_since(self, dt: datetime) -> int:
        """
        计算距今天数
        
        Args:
            dt: 日期时间
            
        Returns:
            int: 天数
        """
        return (datetime.now() - dt).days
