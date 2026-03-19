"""
NecoRAG 插件市场 - 搜索发现与推荐引擎

提供多维度搜索、智能推荐、趋势排行和场景匹配。
"""

import logging
from typing import List, Optional, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime

from .models import (
    PluginManifest, PluginType, PluginCategory, SortStrategy,
    SearchResult, GDIScore
)
from .store import MarketplaceStore

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """插件搜索发现与推荐引擎"""
    
    def __init__(self, store: MarketplaceStore, page_size: int = 20):
        """
        初始化搜索发现引擎
        
        Args:
            store: 插件市场存储层
            page_size: 默认分页大小
        """
        self.store = store
        self.page_size = page_size
        
        # 场景到插件类型/标签的映射
        self._use_case_mappings: Dict[str, Dict] = {
            "document_processing": {
                "types": [PluginType.PERCEPTION],
                "tags": ["pdf", "docx", "parser", "document", "文档处理"],
                "description": "文档处理与解析"
            },
            "search_enhancement": {
                "types": [PluginType.RETRIEVAL],
                "tags": ["search", "rerank", "retrieval", "搜索增强"],
                "description": "搜索增强与重排序"
            },
            "memory_optimization": {
                "types": [PluginType.MEMORY],
                "tags": ["cache", "memory", "storage", "记忆优化"],
                "description": "记忆系统优化"
            },
            "quality_control": {
                "types": [PluginType.REFINEMENT],
                "tags": ["hallucination", "verification", "quality", "质量控制"],
                "description": "质量控制与幻觉检测"
            },
            "response_formatting": {
                "types": [PluginType.RESPONSE],
                "tags": ["format", "template", "visualization", "响应格式化"],
                "description": "响应格式化与模板"
            },
            "data_analysis": {
                "types": [PluginType.UTILITY],
                "tags": ["analytics", "statistics", "monitoring", "数据分析"],
                "description": "数据分析与监控"
            }
        }
        
        logger.info("DiscoveryEngine 初始化完成")
    
    # === 核心搜索 ===
    def search(self, query: str = "",
               category: Optional[PluginCategory] = None,
               plugin_type: Optional[PluginType] = None,
               sort_by: SortStrategy = SortStrategy.RELEVANCE,
               tags: Optional[List[str]] = None,
               min_rating: Optional[float] = None,
               page: int = 1,
               page_size: Optional[int] = None) -> SearchResult:
        """
        多维度插件搜索
        
        流程：
        1. 使用 FTS5 全文搜索（如果有 query）
        2. 按 category 和 plugin_type 过滤
        3. 按 tags 过滤（标签匹配）
        4. 按 min_rating 过滤
        5. 按 sort_by 排序
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            plugin_type: 插件类型过滤
            sort_by: 排序策略
            tags: 标签过滤
            min_rating: 最低评分过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            SearchResult: 搜索结果
        """
        try:
            actual_page_size = page_size or self.page_size
            
            # 获取原始结果
            if query and query.strip():
                # 使用 FTS5 全文搜索
                plugins, total = self.store.search_plugins(
                    query=query,
                    plugin_type=plugin_type,
                    category=category,
                    page=1,  # 先获取全部用于后续过滤
                    page_size=10000
                )
            else:
                # 列出所有插件
                plugins, total = self.store.list_plugins(
                    plugin_type=plugin_type,
                    category=category,
                    page=1,
                    page_size=10000
                )
            
            # 按标签过滤
            if tags:
                plugins = self._filter_by_tags(plugins, tags)
            
            # 按最低评分过滤
            if min_rating is not None:
                plugins = self._filter_by_rating(plugins, min_rating)
            
            # 应用排序
            plugins = self._apply_sort(plugins, sort_by)
            
            # 分页
            total_count = len(plugins)
            start = (page - 1) * actual_page_size
            end = start + actual_page_size
            paginated_plugins = plugins[start:end]
            
            logger.debug(f"搜索完成: query='{query}', 结果数={total_count}")
            
            return SearchResult(
                plugins=paginated_plugins,
                total_count=total_count,
                page=page,
                page_size=actual_page_size,
                query=query
            )
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return SearchResult(
                plugins=[],
                total_count=0,
                page=page,
                page_size=page_size or self.page_size,
                query=query
            )
    
    def _apply_sort(self, plugins: List[PluginManifest], 
                    sort_by: SortStrategy) -> List[PluginManifest]:
        """
        应用排序策略
        
        Args:
            plugins: 插件列表
            sort_by: 排序策略
            
        Returns:
            List[PluginManifest]: 排序后的插件列表
        """
        try:
            if sort_by == SortStrategy.NAME:
                return sorted(plugins, key=lambda p: p.name.lower())
            
            elif sort_by == SortStrategy.NEWEST:
                return sorted(plugins, key=lambda p: p.created_at, reverse=True)
            
            elif sort_by == SortStrategy.GDI_SCORE:
                # 按 GDI 评分排序
                def get_gdi(p: PluginManifest) -> float:
                    score = self.store.get_gdi_score(p.plugin_id)
                    return score.overall_score if score else 0.0
                return sorted(plugins, key=get_gdi, reverse=True)
            
            elif sort_by == SortStrategy.RATING:
                # 按用户评分排序
                def get_rating(p: PluginManifest) -> float:
                    avg, _ = self.store.get_average_rating(p.plugin_id)
                    return avg
                return sorted(plugins, key=get_rating, reverse=True)
            
            elif sort_by == SortStrategy.TRENDING:
                # 按热度（最近事件数）排序
                trending = dict(self.store.get_trending_plugins(days=7, limit=1000))
                return sorted(
                    plugins,
                    key=lambda p: trending.get(p.plugin_id, 0),
                    reverse=True
                )
            
            elif sort_by == SortStrategy.DOWNLOADS:
                # 按总下载量排序
                def get_downloads(p: PluginManifest) -> int:
                    releases = self.store.get_releases(p.plugin_id)
                    return sum(r.download_count for r in releases)
                return sorted(plugins, key=get_downloads, reverse=True)
            
            else:  # RELEVANCE 或默认
                # FTS5 搜索已经按相关性排序，保持原顺序
                return plugins
                
        except Exception as e:
            logger.error(f"排序失败: {e}")
            return plugins
    
    def _filter_by_tags(self, plugins: List[PluginManifest],
                        tags: List[str]) -> List[PluginManifest]:
        """
        按标签过滤
        
        Args:
            plugins: 插件列表
            tags: 标签列表（任意匹配）
            
        Returns:
            List[PluginManifest]: 过滤后的插件列表
        """
        if not tags:
            return plugins
        
        tags_lower = [t.lower() for t in tags]
        result = []
        
        for plugin in plugins:
            plugin_tags_lower = [t.lower() for t in plugin.tags]
            # 任意标签匹配即可
            if any(tag in plugin_tags_lower for tag in tags_lower):
                result.append(plugin)
        
        return result
    
    def _filter_by_rating(self, plugins: List[PluginManifest],
                          min_rating: float) -> List[PluginManifest]:
        """
        按最低评分过滤
        
        Args:
            plugins: 插件列表
            min_rating: 最低评分
            
        Returns:
            List[PluginManifest]: 过滤后的插件列表
        """
        result = []
        
        for plugin in plugins:
            avg_rating, count = self.store.get_average_rating(plugin.plugin_id)
            if avg_rating >= min_rating:
                result.append(plugin)
        
        return result
    
    # === 推荐系统 ===
    def recommend(self, installed_plugin_ids: Optional[List[str]] = None,
                  user_preferences: Optional[Dict] = None,
                  limit: int = 10) -> List[PluginManifest]:
        """
        智能推荐
        
        算法:
        1. 基于已安装插件的类型分布，推荐互补插件
        2. 基于用户偏好（如常用类型、标签）推荐相关插件
        3. 排除已安装的插件
        4. 按 GDI 评分和新鲜度加权排序
        5. 保证多样性（不全推荐同一类型）
        
        Args:
            installed_plugin_ids: 已安装的插件ID列表
            user_preferences: 用户偏好（preferred_types, preferred_tags）
            limit: 返回数量
            
        Returns:
            List[PluginManifest]: 推荐的插件列表
        """
        try:
            installed_ids = set(installed_plugin_ids or [])
            user_prefs = user_preferences or {}
            
            # 获取所有插件
            all_plugins, _ = self.store.list_plugins(page=1, page_size=10000)
            
            # 排除已安装的插件
            candidates = [p for p in all_plugins if p.plugin_id not in installed_ids]
            
            if not candidates:
                return []
            
            # 分析已安装插件的类型分布
            installed_types: Dict[PluginType, int] = Counter()
            for pid in installed_ids:
                plugin = self.store.get_plugin(pid)
                if plugin:
                    installed_types[plugin.plugin_type] += 1
            
            # 计算每个候选插件的推荐分数
            scored_plugins: List[Tuple[PluginManifest, float]] = []
            for plugin in candidates:
                score = self._score_recommendation(plugin, installed_types, user_prefs)
                scored_plugins.append((plugin, score))
            
            # 按分数排序
            scored_plugins.sort(key=lambda x: x[1], reverse=True)
            
            # 保证多样性：每种类型最多推荐 limit // 2 个
            type_counts: Dict[PluginType, int] = Counter()
            max_per_type = max(2, limit // 2)
            result = []
            
            for plugin, score in scored_plugins:
                if len(result) >= limit:
                    break
                if type_counts[plugin.plugin_type] < max_per_type:
                    result.append(plugin)
                    type_counts[plugin.plugin_type] += 1
            
            logger.info(f"推荐完成: 返回 {len(result)} 个插件")
            return result
            
        except Exception as e:
            logger.error(f"推荐失败: {e}")
            return []
    
    def _find_complementary_plugins(self, installed_types: Dict[PluginType, int],
                                     all_plugins: List[PluginManifest]) -> List[PluginManifest]:
        """
        找到互补插件（安装较少的类型）
        
        Args:
            installed_types: 已安装插件的类型分布
            all_plugins: 所有插件列表
            
        Returns:
            List[PluginManifest]: 互补插件列表
        """
        # 找出安装较少的类型
        all_types = list(PluginType)
        type_priority = []
        
        for ptype in all_types:
            count = installed_types.get(ptype, 0)
            type_priority.append((ptype, count))
        
        # 按安装数升序（少的优先）
        type_priority.sort(key=lambda x: x[1])
        
        # 收集互补类型的插件
        result = []
        for ptype, _ in type_priority[:3]:  # 取安装最少的 3 种类型
            for plugin in all_plugins:
                if plugin.plugin_type == ptype:
                    result.append(plugin)
        
        return result
    
    def _score_recommendation(self, plugin: PluginManifest,
                               installed_types: Dict[PluginType, int],
                               user_prefs: Optional[Dict]) -> float:
        """
        计算推荐分数
        
        Args:
            plugin: 插件
            installed_types: 已安装插件的类型分布
            user_prefs: 用户偏好
            
        Returns:
            float: 推荐分数
        """
        score = 0.0
        
        # 1. GDI 评分权重 (40%)
        gdi = self.store.get_gdi_score(plugin.plugin_id)
        if gdi:
            score += 0.4 * (gdi.overall_score / 100.0)
        
        # 2. 互补性权重 (25%)
        # 如果该类型安装较少，分数更高
        type_count = installed_types.get(plugin.plugin_type, 0)
        total_installed = sum(installed_types.values()) or 1
        complementary_score = 1.0 - (type_count / total_installed)
        score += 0.25 * complementary_score
        
        # 3. 用户偏好匹配 (20%)
        if user_prefs:
            # 类型偏好
            preferred_types = user_prefs.get('preferred_types', [])
            if plugin.plugin_type.value in preferred_types:
                score += 0.1
            
            # 标签偏好
            preferred_tags = set(t.lower() for t in user_prefs.get('preferred_tags', []))
            plugin_tags = set(t.lower() for t in plugin.tags)
            if preferred_tags & plugin_tags:
                score += 0.1
        
        # 4. 新鲜度权重 (15%)
        days_old = (datetime.now() - plugin.updated_at).days
        freshness = max(0, 1.0 - (days_old / 365.0))  # 一年内线性衰减
        score += 0.15 * freshness
        
        return score
    
    # === 趋势排行 ===
    def get_trending(self, time_window: str = "weekly",
                     category: Optional[PluginCategory] = None,
                     limit: int = 20) -> List[PluginManifest]:
        """
        获取热门趋势插件
        
        Args:
            time_window: 时间窗口 ("daily", "weekly", "monthly")
            category: 分类过滤
            limit: 返回数量
            
        Returns:
            List[PluginManifest]: 热门插件列表
        """
        try:
            # 时间窗口映射
            days_map = {
                "daily": 1,
                "weekly": 7,
                "monthly": 30
            }
            days = days_map.get(time_window, 7)
            
            # 获取热门插件ID和事件数
            trending = self.store.get_trending_plugins(days=days, limit=limit * 2)
            
            result = []
            for plugin_id, event_count in trending:
                plugin = self.store.get_plugin(plugin_id)
                if plugin:
                    # 分类过滤
                    if category and plugin.category != category:
                        continue
                    result.append(plugin)
                    if len(result) >= limit:
                        break
            
            logger.debug(f"获取趋势插件: window={time_window}, 结果数={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"获取趋势插件失败: {e}")
            return []
    
    # === 场景推荐 ===
    def get_by_use_case(self, use_case: str,
                        limit: int = 10) -> List[PluginManifest]:
        """
        按使用场景推荐插件
        
        Args:
            use_case: 场景名称或自然语言描述
            limit: 返回数量
            
        Returns:
            List[PluginManifest]: 推荐的插件列表
        """
        try:
            # 检查是否是预定义场景
            use_case_lower = use_case.lower().replace(" ", "_")
            mapping = self._use_case_mappings.get(use_case_lower)
            
            if mapping:
                # 使用预定义映射
                types = mapping.get("types", [])
                tags = mapping.get("tags", [])
            else:
                # 自然语言匹配：尝试在所有场景中查找相关的
                types = []
                tags = [use_case]  # 用关键词作为标签搜索
                
                # 检查是否包含某个场景的关键词
                for scene_name, scene_mapping in self._use_case_mappings.items():
                    desc = scene_mapping.get("description", "")
                    if use_case in desc or any(t in use_case for t in scene_mapping.get("tags", [])):
                        types.extend(scene_mapping.get("types", []))
                        tags.extend(scene_mapping.get("tags", []))
            
            # 获取所有插件
            all_plugins, _ = self.store.list_plugins(page=1, page_size=10000)
            
            # 过滤匹配的插件
            matched = []
            for plugin in all_plugins:
                # 类型匹配
                if types and plugin.plugin_type in types:
                    matched.append((plugin, 2))  # 类型匹配权重 2
                    continue
                
                # 标签匹配
                plugin_tags_lower = [t.lower() for t in plugin.tags]
                for tag in tags:
                    if tag.lower() in plugin_tags_lower:
                        matched.append((plugin, 1))  # 标签匹配权重 1
                        break
            
            # 按匹配权重和 GDI 评分排序
            def sort_key(item):
                plugin, match_weight = item
                gdi = self.store.get_gdi_score(plugin.plugin_id)
                gdi_score = gdi.overall_score if gdi else 0.0
                return (match_weight, gdi_score)
            
            matched.sort(key=sort_key, reverse=True)
            
            result = [p for p, _ in matched[:limit]]
            logger.debug(f"场景推荐: use_case='{use_case}', 结果数={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"场景推荐失败: {e}")
            return []
    
    def get_available_use_cases(self) -> List[Dict[str, str]]:
        """
        获取所有可用的使用场景
        
        Returns:
            List[Dict[str, str]]: 场景列表
        """
        return [
            {
                "name": name,
                "description": mapping.get("description", ""),
                "tags": mapping.get("tags", [])
            }
            for name, mapping in self._use_case_mappings.items()
        ]
    
    # === 分类浏览 ===
    def browse_by_category(self, category: PluginCategory,
                           sort_by: SortStrategy = SortStrategy.GDI_SCORE,
                           page: int = 1,
                           page_size: Optional[int] = None) -> SearchResult:
        """
        按分类浏览插件
        
        Args:
            category: 插件分类
            sort_by: 排序策略
            page: 页码
            page_size: 每页数量
            
        Returns:
            SearchResult: 搜索结果
        """
        return self.search(
            query="",
            category=category,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
    
    def browse_by_type(self, plugin_type: PluginType,
                       sort_by: SortStrategy = SortStrategy.GDI_SCORE,
                       page: int = 1,
                       page_size: Optional[int] = None) -> SearchResult:
        """
        按插件类型浏览
        
        Args:
            plugin_type: 插件类型
            sort_by: 排序策略
            page: 页码
            page_size: 每页数量
            
        Returns:
            SearchResult: 搜索结果
        """
        return self.search(
            query="",
            plugin_type=plugin_type,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
    
    # === 统计和洞察 ===
    def get_categories_overview(self) -> List[Dict]:
        """
        获取分类概览
        
        Returns:
            List[Dict]: 分类统计信息
        """
        try:
            result = []
            
            for category in PluginCategory:
                plugins, total = self.store.list_plugins(
                    category=category,
                    page=1,
                    page_size=10000
                )
                
                # 计算平均评分
                total_rating = 0.0
                rated_count = 0
                for plugin in plugins:
                    avg, count = self.store.get_average_rating(plugin.plugin_id)
                    if count > 0:
                        total_rating += avg
                        rated_count += 1
                
                avg_rating = total_rating / rated_count if rated_count > 0 else 0.0
                
                result.append({
                    "category": category.value,
                    "count": total,
                    "avg_rating": round(avg_rating, 2)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取分类概览失败: {e}")
            return []
    
    def get_types_overview(self) -> List[Dict]:
        """
        获取类型概览
        
        Returns:
            List[Dict]: 类型统计信息
        """
        try:
            result = []
            
            for ptype in PluginType:
                plugins, total = self.store.list_plugins(
                    plugin_type=ptype,
                    page=1,
                    page_size=10000
                )
                
                # 收集所有标签
                all_tags: List[str] = []
                total_gdi = 0.0
                gdi_count = 0
                
                for plugin in plugins:
                    all_tags.extend(plugin.tags)
                    gdi = self.store.get_gdi_score(plugin.plugin_id)
                    if gdi:
                        total_gdi += gdi.overall_score
                        gdi_count += 1
                
                # 统计热门标签
                tag_counter = Counter(all_tags)
                popular_tags = [tag for tag, _ in tag_counter.most_common(5)]
                
                avg_gdi = total_gdi / gdi_count if gdi_count > 0 else 0.0
                
                result.append({
                    "type": ptype.value,
                    "count": total,
                    "popular_tags": popular_tags,
                    "avg_gdi": round(avg_gdi, 2)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取类型概览失败: {e}")
            return []
    
    def get_popular_tags(self, limit: int = 30) -> List[Tuple[str, int]]:
        """
        获取热门标签和对应的插件数
        
        Args:
            limit: 返回数量
            
        Returns:
            List[Tuple[str, int]]: (标签, 插件数) 列表
        """
        try:
            plugins, _ = self.store.list_plugins(page=1, page_size=10000)
            
            tag_counter: Counter = Counter()
            for plugin in plugins:
                for tag in plugin.tags:
                    tag_counter[tag] += 1
            
            return tag_counter.most_common(limit)
            
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return []
    
    # === 相似插件 ===
    def find_similar(self, plugin_id: str, limit: int = 5) -> List[PluginManifest]:
        """
        找到相似插件（基于类型、标签、描述关键词匹配）
        
        Args:
            plugin_id: 源插件ID
            limit: 返回数量
            
        Returns:
            List[PluginManifest]: 相似插件列表
        """
        try:
            # 获取源插件
            source = self.store.get_plugin(plugin_id)
            if not source:
                logger.warning(f"源插件不存在: {plugin_id}")
                return []
            
            # 获取所有插件
            all_plugins, _ = self.store.list_plugins(page=1, page_size=10000)
            
            # 计算相似度分数
            scored: List[Tuple[PluginManifest, float]] = []
            source_tags = set(t.lower() for t in source.tags)
            source_words = set(source.description.lower().split())
            
            for plugin in all_plugins:
                if plugin.plugin_id == plugin_id:
                    continue
                
                score = 0.0
                
                # 类型相同 (权重 0.4)
                if plugin.plugin_type == source.plugin_type:
                    score += 0.4
                
                # 标签重叠 (权重 0.35)
                plugin_tags = set(t.lower() for t in plugin.tags)
                if source_tags and plugin_tags:
                    overlap = len(source_tags & plugin_tags)
                    tag_similarity = overlap / max(len(source_tags), len(plugin_tags))
                    score += 0.35 * tag_similarity
                
                # 描述词重叠 (权重 0.15)
                plugin_words = set(plugin.description.lower().split())
                if source_words and plugin_words:
                    word_overlap = len(source_words & plugin_words)
                    word_similarity = word_overlap / max(len(source_words), len(plugin_words))
                    score += 0.15 * word_similarity
                
                # 同作者 (权重 0.1)
                if plugin.author == source.author:
                    score += 0.1
                
                if score > 0:
                    scored.append((plugin, score))
            
            # 按分数排序
            scored.sort(key=lambda x: x[1], reverse=True)
            
            result = [p for p, _ in scored[:limit]]
            logger.debug(f"找到相似插件: source={plugin_id}, 结果数={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"查找相似插件失败: {e}")
            return []
