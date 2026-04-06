"""
Knowledge Visualizer - 知识库可视化数据接口

为 Dashboard 提供可视化所需的数据格式。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .models import KnowledgeMetrics, HealthReport, GrowthTrend, ChangeLogEntry
from .config import KnowledgeEvolutionConfig


logger = logging.getLogger(__name__)


class KnowledgeVisualizer:
    """
    知识库可视化数据接口
    
    为 Dashboard 提供可视化所需的数据格式，
    包括健康度仪表盘、增长曲线、热力图等。
    
    Knowledge base visualization data interface that provides
    data formats needed for dashboard visualization.
    """
    
    def __init__(
        self,
        metrics_calculator: Any = None,
        updater: Any = None,
        config: Optional[KnowledgeEvolutionConfig] = None
    ):
        """
        初始化可视化接口
        
        Args:
            metrics_calculator: 指标计算器实例
            updater: 知识更新管理器实例
            config: 知识演化配置
        """
        self.metrics_calculator = metrics_calculator
        self.updater = updater
        self.config = config or KnowledgeEvolutionConfig.default()
        
        logger.info("KnowledgeVisualizer initialized")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表盘完整数据
        
        Returns:
            Dict: 包含所有仪表盘组件数据的字典
        """
        return {
            "health": self.get_health_gauge(),
            "summary": self.get_summary(),
            "growth_trend": self.get_growth_chart_data(),
            "layer_distribution": self.get_layer_distribution(),
            "decay_radar": self.get_decay_radar_data(),
            "update_timeline": self.get_update_timeline(),
            "metrics": self.get_current_metrics(),
            "quality_trend": self.get_quality_trend(),
            "generated_at": datetime.now().isoformat(),
        }
    
    def get_health_gauge(self) -> Dict[str, Any]:
        """
        获取健康度仪表盘数据
        
        Returns:
            Dict: 健康度仪表盘数据
        """
        if self.metrics_calculator is None:
            return self._default_health_gauge()
        
        try:
            report = self.metrics_calculator.generate_health_report()
            
            # 确定颜色
            if report.health_score >= 80:
                color = "#4CAF50"  # 绿色
                level_text = "健康"
            elif report.health_score >= 60:
                color = "#FFC107"  # 黄色
                level_text = "一般"
            elif report.health_score >= 40:
                color = "#FF9800"  # 橙色
                level_text = "预警"
            else:
                color = "#F44336"  # 红色
                level_text = "严重"
            
            return {
                "score": report.health_score,
                "level": report.level,
                "level_text": level_text,
                "color": color,
                "description": self._get_health_description(report.health_score),
                "dimensions": {
                    "scale": report.scale_score,
                    "freshness": report.freshness_score,
                    "quality": report.quality_score,
                    "connectivity": report.connectivity_score,
                },
                "warnings": report.warnings,
                "recommendations": report.recommendations,
            }
        except Exception as e:
            logger.error(f"Error getting health gauge: {e}")
            return self._default_health_gauge()
    
    def _default_health_gauge(self) -> Dict[str, Any]:
        """返回默认健康度数据"""
        return {
            "score": 0,
            "level": "unknown",
            "level_text": "未知",
            "color": "#9E9E9E",
            "description": "暂无数据",
            "dimensions": {
                "scale": 0,
                "freshness": 0,
                "quality": 0,
                "connectivity": 0,
            },
            "warnings": [],
            "recommendations": ["请先导入数据或启用知识积累功能"],
        }
    
    def _get_health_description(self, score: float) -> str:
        """根据分数获取健康描述"""
        if score >= 80:
            return "知识库状态良好，各项指标正常"
        elif score >= 60:
            return "知识库状态一般，部分指标需要关注"
        elif score >= 40:
            return "知识库健康度偏低，建议进行维护"
        else:
            return "知识库状态严重，需要立即处理"
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取摘要数据
        
        Returns:
            Dict: 摘要数据
        """
        if self.metrics_calculator is None:
            return self._default_summary()
        
        try:
            metrics = self.metrics_calculator.calculate_metrics()
            
            return {
                "total_entries": metrics.total_entries,
                "total_updates_today": metrics.total_updates_today,
                "pending_candidates": metrics.pending_candidates,
                "health_score": metrics.health_score,
                "retrieval_hit_rate": f"{metrics.retrieval_hit_rate * 100:.1f}%",
                "avg_age_days": f"{metrics.avg_knowledge_age_days:.1f}",
            }
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return self._default_summary()
    
    def _default_summary(self) -> Dict[str, Any]:
        """返回默认摘要数据"""
        return {
            "total_entries": 0,
            "total_updates_today": 0,
            "pending_candidates": 0,
            "health_score": 0,
            "retrieval_hit_rate": "0%",
            "avg_age_days": "0",
        }
    
    def get_growth_chart_data(self, days: int = 30) -> Dict[str, Any]:
        """
        获取知识增长曲线数据
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 增长曲线数据
        """
        if self.metrics_calculator is None:
            return self._default_growth_chart(days)
        
        try:
            trends = self.metrics_calculator.get_growth_trend(days)
            
            return {
                "dates": [t.date for t in trends],
                "total_entries": [t.total_entries for t in trends],
                "new_entries": [t.new_entries for t in trends],
                "deleted_entries": [t.deleted_entries for t in trends],
                "net_growth": [t.net_growth for t in trends],
            }
        except Exception as e:
            logger.error(f"Error getting growth chart: {e}")
            return self._default_growth_chart(days)
    
    def _default_growth_chart(self, days: int) -> Dict[str, Any]:
        """返回默认增长曲线数据"""
        dates = []
        end_date = datetime.now().date()
        for i in range(days - 1, -1, -1):
            date = end_date - timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        
        return {
            "dates": dates,
            "total_entries": [0] * days,
            "new_entries": [0] * days,
            "deleted_entries": [0] * days,
            "net_growth": [0] * days,
        }
    
    def get_layer_distribution(self) -> Dict[str, Any]:
        """
        获取层级分布数据（饼图）
        
        Returns:
            Dict: 层级分布数据
        """
        if self.metrics_calculator is None:
            return self._default_layer_distribution()
        
        try:
            metrics = self.metrics_calculator.calculate_metrics()
            
            return {
                "labels": ["L1 工作记忆", "L2 语义记忆", "L3 实体", "L3 关系"],
                "values": [
                    metrics.l1_entries,
                    metrics.l2_entries,
                    metrics.l3_entities,
                    metrics.l3_relations,
                ],
                "colors": ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"],
            }
        except Exception as e:
            logger.error(f"Error getting layer distribution: {e}")
            return self._default_layer_distribution()
    
    def _default_layer_distribution(self) -> Dict[str, Any]:
        """返回默认层级分布数据"""
        return {
            "labels": ["L1 工作记忆", "L2 语义记忆", "L3 实体", "L3 关系"],
            "values": [0, 0, 0, 0],
            "colors": ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"],
        }
    
    def get_decay_radar_data(self) -> Dict[str, Any]:
        """
        获取衰减雷达图数据
        
        展示知识库的多维度健康状态。
        
        Returns:
            Dict: 雷达图数据
        """
        if self.metrics_calculator is None:
            return self._default_decay_radar()
        
        try:
            report = self.metrics_calculator.generate_health_report()
            
            return {
                "dimensions": ["规模", "新鲜度", "质量", "连通性", "活跃度"],
                "values": [
                    report.scale_score,
                    report.freshness_score,
                    report.quality_score,
                    report.connectivity_score,
                    self._calc_activity_score(),
                ],
                "max_value": 100,
            }
        except Exception as e:
            logger.error(f"Error getting decay radar: {e}")
            return self._default_decay_radar()
    
    def _default_decay_radar(self) -> Dict[str, Any]:
        """返回默认雷达图数据"""
        return {
            "dimensions": ["规模", "新鲜度", "质量", "连通性", "活跃度"],
            "values": [0, 0, 0, 0, 0],
            "max_value": 100,
        }
    
    def _calc_activity_score(self) -> float:
        """计算活跃度评分"""
        if self.metrics_calculator is None:
            return 0.0
        
        try:
            metrics = self.metrics_calculator.calculate_metrics()
            # 基于今日更新数计算
            activity = min(metrics.total_updates_today * 10, 100)
            return activity
        except Exception:
            return 0.0
    
    def get_update_timeline(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取更新时间线数据
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 时间线数据
        """
        if self.updater is None:
            return []
        
        try:
            logs = self.updater.get_change_log(limit=limit)
            
            timeline = []
            for log in logs:
                timeline.append({
                    "time": log.timestamp.isoformat(),
                    "time_text": self._format_time(log.timestamp),
                    "type": log.operation,
                    "type_text": self._get_operation_text(log.operation),
                    "layer": log.layer,
                    "description": log.content_summary,
                    "icon": self._get_operation_icon(log.operation),
                    "color": self._get_operation_color(log.operation),
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting update timeline: {e}")
            return []
    
    def _format_time(self, dt: datetime) -> str:
        """格式化时间显示"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}小时前"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}分钟前"
        else:
            return "刚刚"
    
    def _get_operation_text(self, operation: str) -> str:
        """获取操作类型文本"""
        texts = {
            "insert": "新增",
            "update": "更新",
            "delete": "删除",
            "archive": "归档",
            "rollback": "回滚",
        }
        return texts.get(operation, operation)
    
    def _get_operation_icon(self, operation: str) -> str:
        """获取操作类型图标"""
        icons = {
            "insert": "add",
            "update": "edit",
            "delete": "delete",
            "archive": "archive",
            "rollback": "undo",
        }
        return icons.get(operation, "info")
    
    def _get_operation_color(self, operation: str) -> str:
        """获取操作类型颜色"""
        colors = {
            "insert": "#4CAF50",
            "update": "#2196F3",
            "delete": "#F44336",
            "archive": "#9E9E9E",
            "rollback": "#FF9800",
        }
        return colors.get(operation, "#9E9E9E")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        获取当前指标数据
        
        Returns:
            Dict: 当前指标
        """
        if self.metrics_calculator is None:
            return {}
        
        try:
            metrics = self.metrics_calculator.calculate_metrics()
            return metrics.to_dict()
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {}
    
    def get_quality_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        获取质量趋势数据
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 质量趋势数据
        """
        if self.metrics_calculator is None:
            return self._default_quality_trend(days)
        
        try:
            history = self.metrics_calculator.get_metrics_history(limit=days * 24)
            
            # 按天聚合
            daily_quality = {}
            for metrics in history:
                date = metrics.calculated_at.strftime("%Y-%m-%d")
                if date not in daily_quality:
                    daily_quality[date] = []
                daily_quality[date].append(metrics.health_score)
            
            dates = sorted(daily_quality.keys())[-days:]
            scores = [sum(daily_quality[d]) / len(daily_quality[d]) for d in dates]
            
            return {
                "dates": dates,
                "health_scores": scores,
            }
        except Exception as e:
            logger.error(f"Error getting quality trend: {e}")
            return self._default_quality_trend(days)
    
    def _default_quality_trend(self, days: int) -> Dict[str, Any]:
        """返回默认质量趋势数据"""
        dates = []
        end_date = datetime.now().date()
        for i in range(days - 1, -1, -1):
            date = end_date - timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        
        return {
            "dates": dates,
            "health_scores": [0] * days,
        }
    
    def get_domain_heatmap(self) -> Dict[str, Any]:
        """
        获取领域覆盖热力图数据
        
        Returns:
            Dict: 热力图数据
        """
        # TODO: 需要与领域模块集成
        return {
            "domains": [],
            "message": "领域覆盖数据需要与 domain 模块集成",
        }
    
    def get_metrics_comparison(
        self,
        period1: str,
        period2: str
    ) -> Dict[str, Any]:
        """
        获取指标对比数据
        
        Args:
            period1: 第一个时期（YYYY-MM-DD）
            period2: 第二个时期（YYYY-MM-DD）
            
        Returns:
            Dict: 对比数据
        """
        if self.metrics_calculator is None:
            return {"error": "No metrics calculator configured"}
        
        try:
            history = self.metrics_calculator.get_metrics_history(limit=720)
            
            period1_metrics = None
            period2_metrics = None
            
            for metrics in history:
                date = metrics.calculated_at.strftime("%Y-%m-%d")
                if date == period1 and period1_metrics is None:
                    period1_metrics = metrics
                if date == period2 and period2_metrics is None:
                    period2_metrics = metrics
            
            if period1_metrics is None or period2_metrics is None:
                return {"error": "Insufficient data for comparison"}
            
            return {
                "period1": {
                    "date": period1,
                    "health_score": period1_metrics.health_score,
                    "total_entries": period1_metrics.total_entries,
                    "hit_rate": period1_metrics.retrieval_hit_rate,
                },
                "period2": {
                    "date": period2,
                    "health_score": period2_metrics.health_score,
                    "total_entries": period2_metrics.total_entries,
                    "hit_rate": period2_metrics.retrieval_hit_rate,
                },
                "changes": {
                    "health_score": period2_metrics.health_score - period1_metrics.health_score,
                    "total_entries": period2_metrics.total_entries - period1_metrics.total_entries,
                    "hit_rate": period2_metrics.retrieval_hit_rate - period1_metrics.retrieval_hit_rate,
                },
            }
        except Exception as e:
            logger.error(f"Error getting metrics comparison: {e}")
            return {"error": str(e)}
    
    def get_candidates_chart(self) -> Dict[str, Any]:
        """
        获取候选条目统计图表数据
        
        Returns:
            Dict: 候选条目图表数据
        """
        if self.updater is None:
            return self._default_candidates_chart()
        
        try:
            stats = self.updater.get_update_stats()
            candidates = self.updater.get_pending_candidates(limit=100)
            
            # 按来源分类
            source_counts = {}
            for candidate in candidates:
                source = candidate.source.value
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                "total_pending": stats.get("pending_candidates", 0),
                "auto_approved": stats.get("auto_approved", 0),
                "manual_approved": stats.get("manual_approved", 0),
                "rejected": stats.get("rejected", 0),
                "by_source": source_counts,
                "source_labels": list(source_counts.keys()),
                "source_values": list(source_counts.values()),
            }
        except Exception as e:
            logger.error(f"Error getting candidates chart: {e}")
            return self._default_candidates_chart()
    
    def _default_candidates_chart(self) -> Dict[str, Any]:
        """返回默认候选条目图表数据"""
        return {
            "total_pending": 0,
            "auto_approved": 0,
            "manual_approved": 0,
            "rejected": 0,
            "by_source": {},
            "source_labels": [],
            "source_values": [],
        }
    
    def get_knowledge_gaps_table(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取知识缺口表格数据
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 知识缺口列表
        """
        if self.updater is None:
            return []
        
        try:
            gaps = self.updater.get_knowledge_gaps(min_frequency=2)
            
            result = []
            for gap in gaps[:limit]:
                result.append({
                    "query": gap.get("query", ""),
                    "frequency": gap.get("frequency", 0),
                    "first_seen": gap.get("first_seen", datetime.now()).isoformat() if isinstance(gap.get("first_seen"), datetime) else gap.get("first_seen"),
                    "last_seen": gap.get("last_seen", datetime.now()).isoformat() if isinstance(gap.get("last_seen"), datetime) else gap.get("last_seen"),
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting knowledge gaps: {e}")
            return []
