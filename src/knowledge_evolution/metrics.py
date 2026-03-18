"""
Knowledge Metrics Calculator - 知识库量化指标计算器

持续计算知识库的健康度指标，提供综合评分和维度报告。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import math

from .models import KnowledgeMetrics, HealthReport, QueryRecord, GrowthTrend
from .config import KnowledgeEvolutionConfig


logger = logging.getLogger(__name__)


class KnowledgeMetricsCalculator:
    """
    知识库量化指标计算器
    
    持续计算知识库的健康度指标，提供综合评分和维度报告。
    
    Knowledge base metrics calculator that continuously computes
    health indicators and provides comprehensive reports.
    """
    
    def __init__(
        self,
        config: Optional[KnowledgeEvolutionConfig] = None,
        memory_manager: Any = None
    ):
        """
        初始化指标计算器
        
        Args:
            config: 知识演化配置
            memory_manager: 记忆管理器实例
        """
        self.config = config or KnowledgeEvolutionConfig.default()
        self.memory_manager = memory_manager
        
        # 查询日志（用于统计）
        self._query_log: List[QueryRecord] = []
        
        # 指标历史
        self._metrics_history: List[KnowledgeMetrics] = []
        
        # 增长趋势数据
        self._daily_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total_entries": 0,
            "new_entries": 0,
            "deleted_entries": 0,
        })
        
        # 缓存
        self._cached_metrics: Optional[KnowledgeMetrics] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl: int = 60  # 缓存有效期（秒）
        
        logger.info("KnowledgeMetricsCalculator initialized")
    
    def calculate_metrics(self, force_refresh: bool = False) -> KnowledgeMetrics:
        """
        计算当前知识库量化指标
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            KnowledgeMetrics: 计算后的指标
        """
        # 检查缓存
        if not force_refresh and self._cached_metrics and self._cache_time:
            if (datetime.now() - self._cache_time).total_seconds() < self._cache_ttl:
                return self._cached_metrics
        
        metrics = KnowledgeMetrics()
        
        # 计算规模指标
        metrics.total_entries = self._count_total_entries()
        metrics.l1_entries = self._count_l1()
        metrics.l2_entries = self._count_l2()
        metrics.l3_entities = self._count_l3_entities()
        metrics.l3_relations = self._count_l3_relations()
        metrics.vector_coverage = self._calc_vector_coverage()
        
        # 计算新鲜度指标
        metrics.avg_knowledge_age_days = self._calc_avg_age()
        metrics.recent_update_rate = self._calc_recent_update_rate()
        age_stats = self._calc_age_stats()
        metrics.oldest_entry_days = age_stats.get("oldest_days", 0.0)
        metrics.newest_entry_days = age_stats.get("newest_days", 0.0)
        
        # 计算质量指标
        metrics.retrieval_hit_rate = self._calc_hit_rate()
        metrics.fragmentation_rate = self._calc_fragmentation()
        metrics.avg_relevance_score = self._calc_avg_relevance()
        
        # 计算健康度指标
        metrics.decay_distribution = self._calc_decay_distribution()
        metrics.redundancy_rate = self._calc_redundancy()
        
        # 计算更新指标
        today = datetime.now().strftime("%Y-%m-%d")
        metrics.total_updates_today = self._daily_stats[today].get("new_entries", 0)
        metrics.realtime_updates_today = self._count_realtime_updates_today()
        metrics.batch_updates_today = self._count_batch_updates_today()
        metrics.pending_candidates = self._count_pending_candidates()
        
        # 计算查询统计
        query_stats = self._calc_query_stats_today()
        metrics.total_queries_today = query_stats["total"]
        metrics.queries_with_hits = query_stats["with_hits"]
        metrics.queries_without_hits = query_stats["without_hits"]
        
        # 计算综合健康分
        metrics.health_score = self._calc_health_score(metrics)
        
        metrics.calculated_at = datetime.now()
        
        # 更新缓存
        self._cached_metrics = metrics
        self._cache_time = datetime.now()
        
        # 保存到历史
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self.config.metrics_history_limit:
            self._metrics_history = self._metrics_history[-self.config.metrics_history_limit:]
        
        return metrics
    
    def _count_total_entries(self) -> int:
        """统计总条目数"""
        if self.memory_manager is None:
            return 0
        
        try:
            # 尝试调用 memory_manager 的 count 方法
            if hasattr(self.memory_manager, 'count'):
                return self.memory_manager.count()
            if hasattr(self.memory_manager, '_memory_store'):
                return len(self.memory_manager._memory_store)
        except Exception as e:
            logger.debug(f"Error counting entries: {e}")
        
        return 0
    
    def _count_l1(self) -> int:
        """统计 L1 工作记忆条目数"""
        if self.memory_manager is None:
            return 0
        
        try:
            if hasattr(self.memory_manager, 'working_memory'):
                wm = self.memory_manager.working_memory
                if hasattr(wm, 'size'):
                    return wm.size()
                if hasattr(wm, '_items'):
                    return len(wm._items)
        except Exception as e:
            logger.debug(f"Error counting L1: {e}")
        
        return 0
    
    def _count_l2(self) -> int:
        """统计 L2 语义记忆条目数"""
        if self.memory_manager is None:
            return 0
        
        try:
            if hasattr(self.memory_manager, 'semantic_memory'):
                sm = self.memory_manager.semantic_memory
                if hasattr(sm, 'count'):
                    return sm.count()
                if hasattr(sm, '_vectors'):
                    return len(sm._vectors)
        except Exception as e:
            logger.debug(f"Error counting L2: {e}")
        
        return self._count_total_entries()
    
    def _count_l3_entities(self) -> int:
        """统计 L3 图谱实体数"""
        if self.memory_manager is None:
            return 0
        
        try:
            if hasattr(self.memory_manager, 'episodic_graph'):
                eg = self.memory_manager.episodic_graph
                if hasattr(eg, 'entity_count'):
                    return eg.entity_count()
                if hasattr(eg, '_entities'):
                    return len(eg._entities)
        except Exception as e:
            logger.debug(f"Error counting L3 entities: {e}")
        
        return 0
    
    def _count_l3_relations(self) -> int:
        """统计 L3 图谱关系数"""
        if self.memory_manager is None:
            return 0
        
        try:
            if hasattr(self.memory_manager, 'episodic_graph'):
                eg = self.memory_manager.episodic_graph
                if hasattr(eg, 'relation_count'):
                    return eg.relation_count()
                if hasattr(eg, '_relations'):
                    return len(eg._relations)
        except Exception as e:
            logger.debug(f"Error counting L3 relations: {e}")
        
        return 0
    
    def _calc_vector_coverage(self) -> float:
        """计算向量覆盖率"""
        total = self._count_total_entries()
        if total == 0:
            return 1.0  # 空知识库视为完全覆盖
        
        l2_count = self._count_l2()
        return min(l2_count / total, 1.0)
    
    def _calc_avg_age(self) -> float:
        """计算平均知识年龄（天）"""
        if self.memory_manager is None:
            return 0.0
        
        try:
            if hasattr(self.memory_manager, '_memory_store'):
                memories = list(self.memory_manager._memory_store.values())
                if not memories:
                    return 0.0
                
                now = datetime.now()
                total_age = 0.0
                for memory in memories:
                    if hasattr(memory, 'created_at'):
                        age = (now - memory.created_at).total_seconds() / 86400
                        total_age += age
                
                return total_age / len(memories)
        except Exception as e:
            logger.debug(f"Error calculating avg age: {e}")
        
        return 0.0
    
    def _calc_recent_update_rate(self) -> float:
        """计算近7天更新率"""
        total = self._count_total_entries()
        if total == 0:
            return 0.0
        
        # 统计近7天新增
        recent_count = 0
        cutoff = datetime.now() - timedelta(days=7)
        
        for date_str, stats in self._daily_stats.items():
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if date >= cutoff:
                    recent_count += stats.get("new_entries", 0)
            except ValueError:
                continue
        
        return min(recent_count / max(total, 1), 1.0)
    
    def _calc_age_stats(self) -> Dict[str, float]:
        """计算年龄统计（最旧/最新）"""
        result = {"oldest_days": 0.0, "newest_days": 0.0}
        
        if self.memory_manager is None:
            return result
        
        try:
            if hasattr(self.memory_manager, '_memory_store'):
                memories = list(self.memory_manager._memory_store.values())
                if not memories:
                    return result
                
                now = datetime.now()
                ages = []
                for memory in memories:
                    if hasattr(memory, 'created_at'):
                        age = (now - memory.created_at).total_seconds() / 86400
                        ages.append(age)
                
                if ages:
                    result["oldest_days"] = max(ages)
                    result["newest_days"] = min(ages)
        except Exception as e:
            logger.debug(f"Error calculating age stats: {e}")
        
        return result
    
    def _calc_hit_rate(self) -> float:
        """计算检索命中率"""
        if not self._query_log:
            return 0.0
        
        hits = sum(1 for q in self._query_log if q.hit)
        return hits / len(self._query_log)
    
    def _calc_fragmentation(self) -> float:
        """计算碎片率（孤立节点比例）"""
        entities = self._count_l3_entities()
        relations = self._count_l3_relations()
        
        if entities == 0:
            return 0.0
        
        # 简化计算：假设每个关系连接2个实体
        # 孤立节点 = 总实体 - 有关系连接的实体
        connected_estimate = min(relations * 2, entities)
        isolated = max(entities - connected_estimate, 0)
        
        return isolated / entities
    
    def _calc_avg_relevance(self) -> float:
        """计算平均相关性评分"""
        if not self._query_log:
            return 0.0
        
        scores = [q.confidence for q in self._query_log if q.confidence > 0]
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    def _calc_decay_distribution(self) -> Dict[str, int]:
        """计算权重区间分布"""
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
            "1.0+": 0,
        }
        
        if self.memory_manager is None:
            return distribution
        
        try:
            if hasattr(self.memory_manager, '_memory_store'):
                for memory in self.memory_manager._memory_store.values():
                    weight = getattr(memory, 'weight', 1.0)
                    if weight < 0.2:
                        distribution["0.0-0.2"] += 1
                    elif weight < 0.4:
                        distribution["0.2-0.4"] += 1
                    elif weight < 0.6:
                        distribution["0.4-0.6"] += 1
                    elif weight < 0.8:
                        distribution["0.6-0.8"] += 1
                    elif weight <= 1.0:
                        distribution["0.8-1.0"] += 1
                    else:
                        distribution["1.0+"] += 1
        except Exception as e:
            logger.debug(f"Error calculating decay distribution: {e}")
        
        return distribution
    
    def _calc_redundancy(self) -> float:
        """计算冗余度"""
        # 简化实现：基于内容相似度估算
        # 实际实现可以使用向量聚类或哈希去重
        return 0.0
    
    def _count_realtime_updates_today(self) -> int:
        """统计今日实时更新数"""
        # 这个值应该从 updater 获取
        return 0
    
    def _count_batch_updates_today(self) -> int:
        """统计今日批量更新数"""
        # 这个值应该从 updater 获取
        return 0
    
    def _count_pending_candidates(self) -> int:
        """统计待审核候选数"""
        # 这个值应该从 updater 获取
        return 0
    
    def _calc_query_stats_today(self) -> Dict[str, int]:
        """计算今日查询统计"""
        today = datetime.now().date()
        
        total = 0
        with_hits = 0
        without_hits = 0
        
        for query in self._query_log:
            if query.timestamp.date() == today:
                total += 1
                if query.hit:
                    with_hits += 1
                else:
                    without_hits += 1
        
        return {
            "total": total,
            "with_hits": with_hits,
            "without_hits": without_hits,
        }
    
    def _calc_health_score(self, metrics: KnowledgeMetrics) -> float:
        """
        计算综合健康分（0-100）
        
        公式：health = Σ(weight_i × score_i)
        各维度分数归一化到 0-100
        
        Args:
            metrics: 已计算的指标
            
        Returns:
            float: 综合健康分
        """
        # 规模评分 (0-100)
        scale_score = self._calc_scale_score(metrics)
        
        # 新鲜度评分 (0-100)
        freshness_score = self._calc_freshness_score(metrics)
        
        # 质量评分 (0-100)
        quality_score = self._calc_quality_score(metrics)
        
        # 连通性评分 (0-100)
        connectivity_score = self._calc_connectivity_score(metrics)
        
        # 加权平均
        health_score = (
            self.config.scale_weight * scale_score +
            self.config.freshness_weight * freshness_score +
            self.config.quality_weight * quality_score +
            self.config.connectivity_weight * connectivity_score
        )
        
        return round(health_score, 2)
    
    def _calc_scale_score(self, metrics: KnowledgeMetrics) -> float:
        """计算规模评分"""
        # 基于总条目数和各层分布
        total = metrics.total_entries
        
        if total == 0:
            return 50.0  # 空知识库给中等分数
        
        # 假设理想分布：L1 < 10%, L2 > 80%, L3实体 > 10%
        l2_ratio = metrics.l2_entries / max(total, 1)
        
        score = 50.0
        
        # 规模加成（对数增长）
        if total > 0:
            score += min(math.log10(total + 1) * 10, 30)
        
        # L2 覆盖加成
        score += l2_ratio * 20
        
        return min(score, 100.0)
    
    def _calc_freshness_score(self, metrics: KnowledgeMetrics) -> float:
        """计算新鲜度评分"""
        score = 100.0
        
        # 平均年龄惩罚
        if metrics.avg_knowledge_age_days > 0:
            age_penalty = min(metrics.avg_knowledge_age_days / 365 * 30, 30)
            score -= age_penalty
        
        # 更新活跃度加成
        score += metrics.recent_update_rate * 30
        
        return max(min(score, 100.0), 0.0)
    
    def _calc_quality_score(self, metrics: KnowledgeMetrics) -> float:
        """计算质量评分"""
        score = 50.0
        
        # 命中率加成
        score += metrics.retrieval_hit_rate * 40
        
        # 相关性加成
        score += metrics.avg_relevance_score * 10
        
        return min(score, 100.0)
    
    def _calc_connectivity_score(self, metrics: KnowledgeMetrics) -> float:
        """计算连通性评分"""
        score = 100.0
        
        # 碎片率惩罚
        score -= metrics.fragmentation_rate * 50
        
        # 冗余度惩罚
        score -= metrics.redundancy_rate * 30
        
        return max(score, 0.0)
    
    def generate_health_report(self) -> HealthReport:
        """
        生成知识库健康报告
        
        Returns:
            HealthReport: 健康报告
        """
        metrics = self.calculate_metrics()
        
        warnings = []
        recommendations = []
        
        # 根据健康分确定级别
        if metrics.health_score >= self.config.health_warning_threshold:
            level = "healthy"
        elif metrics.health_score >= self.config.health_critical_threshold:
            level = "warning"
        else:
            level = "critical"
        
        # 生成警告
        if metrics.health_score < self.config.health_warning_threshold:
            warnings.append("知识库健康度低于预警阈值")
        
        if metrics.recent_update_rate < 0.01:
            warnings.append("知识库近期更新活跃度低")
            recommendations.append("建议增加知识入库频率或启用查询驱动知识积累")
        
        if metrics.fragmentation_rate > 0.3:
            warnings.append("知识碎片率偏高")
            recommendations.append("建议执行图谱关系维护任务")
        
        if metrics.redundancy_rate > 0.2:
            warnings.append("知识冗余度偏高")
            recommendations.append("建议执行知识去重任务")
        
        if metrics.retrieval_hit_rate < 0.5:
            warnings.append("检索命中率较低")
            recommendations.append("建议补充知识缺口或优化检索策略")
        
        if metrics.avg_knowledge_age_days > 180:
            warnings.append("知识平均年龄较大")
            recommendations.append("建议更新过时知识")
        
        if metrics.total_entries == 0:
            warnings.append("知识库为空")
            recommendations.append("建议导入文档或启用知识积累功能")
        
        # 计算各维度评分
        scale_score = self._calc_scale_score(metrics)
        freshness_score = self._calc_freshness_score(metrics)
        quality_score = self._calc_quality_score(metrics)
        connectivity_score = self._calc_connectivity_score(metrics)
        
        return HealthReport(
            health_score=metrics.health_score,
            level=level,
            metrics=metrics,
            scale_score=scale_score,
            freshness_score=freshness_score,
            quality_score=quality_score,
            connectivity_score=connectivity_score,
            warnings=warnings,
            recommendations=recommendations,
        )
    
    def record_query(
        self,
        query: str,
        hit: bool,
        confidence: float = 0.0,
        latency_ms: float = 0.0
    ):
        """
        记录查询用于统计
        
        Args:
            query: 查询文本
            hit: 是否命中
            confidence: 置信度
            latency_ms: 延迟（毫秒）
        """
        record = QueryRecord(
            query=query,
            hit=hit,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        
        self._query_log.append(record)
        
        # 限制日志大小
        if len(self._query_log) > self.config.query_log_max_entries:
            self._query_log = self._query_log[-self.config.query_log_max_entries:]
    
    def record_update(self, operation: str, count: int = 1):
        """
        记录更新操作用于增长趋势
        
        Args:
            operation: 操作类型 (insert/delete)
            count: 数量
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        if operation == "insert":
            self._daily_stats[today]["new_entries"] += count
            # 更新总数
            yesterday_total = 0
            for date_str in sorted(self._daily_stats.keys(), reverse=True):
                if date_str < today:
                    yesterday_total = self._daily_stats[date_str].get("total_entries", 0)
                    break
            self._daily_stats[today]["total_entries"] = yesterday_total + count
        elif operation == "delete":
            self._daily_stats[today]["deleted_entries"] += count
    
    def get_metrics_history(self, limit: int = 30) -> List[KnowledgeMetrics]:
        """
        获取历史指标
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[KnowledgeMetrics]: 历史指标列表
        """
        return self._metrics_history[-limit:]
    
    def get_growth_trend(self, days: int = 30) -> List[GrowthTrend]:
        """
        获取知识增长趋势
        
        Args:
            days: 统计天数
            
        Returns:
            List[GrowthTrend]: 增长趋势数据
        """
        trends = []
        
        # 生成日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            stats = self._daily_stats.get(date_str, {})
            
            trend = GrowthTrend(
                date=date_str,
                total_entries=stats.get("total_entries", 0),
                new_entries=stats.get("new_entries", 0),
                deleted_entries=stats.get("deleted_entries", 0),
                net_growth=stats.get("new_entries", 0) - stats.get("deleted_entries", 0),
            )
            trends.append(trend)
            
            current_date += timedelta(days=1)
        
        return trends
    
    def get_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取查询统计
        
        Args:
            hours: 统计小时数
            
        Returns:
            Dict: 查询统计
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_queries = [q for q in self._query_log if q.timestamp >= cutoff]
        
        if not recent_queries:
            return {
                "total_queries": 0,
                "hit_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_latency_ms": 0.0,
            }
        
        hits = sum(1 for q in recent_queries if q.hit)
        confidences = [q.confidence for q in recent_queries if q.confidence > 0]
        latencies = [q.latency_ms for q in recent_queries if q.latency_ms > 0]
        
        return {
            "total_queries": len(recent_queries),
            "hit_rate": hits / len(recent_queries) if recent_queries else 0.0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        }
    
    def set_updater_stats(
        self,
        realtime_updates: int = 0,
        batch_updates: int = 0,
        pending_candidates: int = 0
    ):
        """
        设置来自 updater 的统计数据
        
        用于在计算指标时获取更新相关的数据。
        
        Args:
            realtime_updates: 今日实时更新数
            batch_updates: 今日批量更新数
            pending_candidates: 待审核候选数
        """
        self._updater_stats = {
            "realtime_updates": realtime_updates,
            "batch_updates": batch_updates,
            "pending_candidates": pending_candidates,
        }
