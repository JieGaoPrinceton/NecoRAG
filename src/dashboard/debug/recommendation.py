"""
优化建议引擎 - Optimization Recommendation Engine
基于AI分析系统性能数据，提供智能化的优化建议和改进方案
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """建议类型枚举"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COST = "cost"
    SCALABILITY = "scalability"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"


class PriorityLevel(str, Enum):
    """优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """置信度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationRule:
    """优化规则数据模型"""
    rule_id: str
    name: str
    description: str
    condition: Dict[str, Any]
    recommendation: str
    recommendation_type: RecommendationType
    priority: PriorityLevel
    confidence: ConfidenceLevel
    impact_score: float  # 0-1
    implementation_effort: str  # low, medium, high
    estimated_benefit: str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['recommendation_type'] = self.recommendation_type.value
        data['priority'] = self.priority.value
        data['confidence'] = self.confidence.value
        return data


@dataclass
class SystemMetrics:
    """系统指标数据模型"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    response_time_ms: float
    throughput_qps: float
    error_rate: float
    cache_hit_rate: float
    active_connections: int
    queue_length: int
    disk_io: float
    network_io: float
    custom_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PerformancePattern:
    """性能模式数据模型"""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    duration: timedelta
    metrics_snapshot: SystemMetrics
    associated_issues: List[str]
    confidence: float
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['duration'] = self.duration.total_seconds()
        data['metrics_snapshot'] = self.metrics_snapshot.to_dict()
        return data


@dataclass
class OptimizationRecommendation:
    """优化建议数据模型"""
    recommendation_id: str
    rule_id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: PriorityLevel
    confidence: ConfidenceLevel
    impact_score: float
    implementation_effort: str
    estimated_benefit: str
    affected_components: List[str]
    implementation_steps: List[str]
    risk_assessment: str
    validation_method: str
    created_at: datetime = None
    applied_at: Optional[datetime] = None
    status: str = "pending"  # pending, applied, validated, rejected
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.affected_components is None:
            self.affected_components = []
        if self.implementation_steps is None:
            self.implementation_steps = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.applied_at:
            data['applied_at'] = self.applied_at.isoformat()
        data['recommendation_type'] = self.recommendation_type.value
        data['priority'] = self.priority.value
        data['confidence'] = self.confidence.value
        return data


class RecommendationEngine:
    """优化建议引擎"""
    
    def __init__(self):
        self.rules: List[OptimizationRule] = []
        self.recommendations: Dict[str, List[OptimizationRecommendation]] = {}
        self.performance_patterns: Dict[str, List[PerformancePattern]] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.pattern_detectors: Dict[str, Callable] = {}
        self.recommendation_generators: Dict[RecommendationType, Callable] = {}
        
        # 初始化系统
        self._load_optimization_rules()
        self._register_pattern_detectors()
        self._register_recommendation_generators()
    
    def _load_optimization_rules(self):
        """加载优化规则"""
        self.rules = [
            # 性能优化规则
            OptimizationRule(
                rule_id="perf_001",
                name="高CPU使用率优化",
                description="当CPU使用率持续超过80%时建议优化",
                condition={
                    "metric": "cpu_usage",
                    "operator": ">",
                    "threshold": 80.0,
                    "duration": "5m"
                },
                recommendation="考虑优化算法复杂度、增加缓存或水平扩展",
                recommendation_type=RecommendationType.PERFORMANCE,
                priority=PriorityLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                impact_score=0.8,
                implementation_effort="medium",
                estimated_benefit="降低20-30% CPU使用率"
            ),
            OptimizationRule(
                rule_id="perf_002",
                name="慢响应时间优化",
                description="当平均响应时间超过2秒时建议优化",
                condition={
                    "metric": "response_time_ms",
                    "operator": ">",
                    "threshold": 2000.0,
                    "duration": "10m"
                },
                recommendation="分析慢查询、优化数据库索引、增加并发处理",
                recommendation_type=RecommendationType.PERFORMANCE,
                priority=PriorityLevel.CRITICAL,
                confidence=ConfidenceLevel.HIGH,
                impact_score=0.9,
                implementation_effort="high",
                estimated_benefit="提升50%响应速度"
            ),
            OptimizationRule(
                rule_id="perf_003",
                name="低缓存命中率优化",
                description="当缓存命中率低于70%时建议优化",
                condition={
                    "metric": "cache_hit_rate",
                    "operator": "<",
                    "threshold": 70.0
                },
                recommendation="调整缓存策略、增加缓存容量、优化缓存键设计",
                recommendation_type=RecommendationType.PERFORMANCE,
                priority=PriorityLevel.MEDIUM,
                confidence=ConfidenceLevel.MEDIUM,
                impact_score=0.6,
                implementation_effort="low",
                estimated_benefit="提升15-25%性能"
            ),
            
            # 质量优化规则
            OptimizationRule(
                rule_id="qual_001",
                name="高错误率优化",
                description="当错误率超过5%时建议优化",
                condition={
                    "metric": "error_rate",
                    "operator": ">",
                    "threshold": 5.0
                },
                recommendation="加强输入验证、完善错误处理、增加监控告警",
                recommendation_type=RecommendationType.QUALITY,
                priority=PriorityLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                impact_score=0.7,
                implementation_effort="medium",
                estimated_benefit="降低80%错误率"
            ),
            
            # 成本优化规则
            OptimizationRule(
                rule_id="cost_001",
                name="资源利用率优化",
                description="当资源利用率低于30%时建议优化",
                condition={
                    "metric": "resource_utilization",
                    "operator": "<",
                    "threshold": 30.0
                },
                recommendation="调整资源配置、实施自动扩缩容、优化调度策略",
                recommendation_type=RecommendationType.COST,
                priority=PriorityLevel.MEDIUM,
                confidence=ConfidenceLevel.MEDIUM,
                impact_score=0.5,
                implementation_effort="high",
                estimated_benefit="节省20-40%成本"
            )
        ]
    
    def _register_pattern_detectors(self):
        """注册模式检测器"""
        self.pattern_detectors = {
            "spike_detection": self._detect_spike_patterns,
            "trend_analysis": self._detect_trend_patterns,
            "correlation_analysis": self._detect_correlation_patterns,
            "anomaly_detection": self._detect_anomaly_patterns
        }
    
    def _register_recommendation_generators(self):
        """注册建议生成器"""
        self.recommendation_generators = {
            RecommendationType.PERFORMANCE: self._generate_performance_recommendations,
            RecommendationType.QUALITY: self._generate_quality_recommendations,
            RecommendationType.COST: self._generate_cost_recommendations,
            RecommendationType.SCALABILITY: self._generate_scalability_recommendations,
            RecommendationType.MAINTAINABILITY: self._generate_maintainability_recommendations,
            RecommendationType.SECURITY: self._generate_security_recommendations
        }
    
    async def collect_metrics(self, metrics: SystemMetrics):
        """
        收集系统指标
        
        Args:
            metrics: 系统指标数据
        """
        self.system_metrics_history.append(metrics)
        
        # 保持历史数据在合理范围内
        if len(self.system_metrics_history) > 1000:
            self.system_metrics_history = self.system_metrics_history[-1000:]
        
        # 检测性能模式
        await self._detect_performance_patterns(metrics)
        
        # 生成优化建议
        await self._generate_recommendations_from_metrics(metrics)
    
    async def _detect_performance_patterns(self, metrics: SystemMetrics):
        """检测性能模式"""
        for detector_name, detector_func in self.pattern_detectors.items():
            try:
                patterns = await detector_func(metrics)
                if patterns:
                    if detector_name not in self.performance_patterns:
                        self.performance_patterns[detector_name] = []
                    self.performance_patterns[detector_name].extend(patterns)
            except Exception as e:
                logger.error(f"模式检测器 {detector_name} 执行失败: {e}")
    
    async def _detect_spike_patterns(self, metrics: SystemMetrics) -> List[PerformancePattern]:
        """检测尖峰模式"""
        patterns = []
        
        # 检查最近的指标历史
        recent_metrics = self.system_metrics_history[-10:] if len(self.system_metrics_history) >= 10 else []
        
        if len(recent_metrics) >= 5:
            # 计算各项指标的平均值和标准差
            cpu_values = [m.cpu_usage for m in recent_metrics[:-1]]
            response_values = [m.response_time_ms for m in recent_metrics[:-1]]
            
            if cpu_values and response_values:
                cpu_mean = statistics.mean(cpu_values)
                cpu_std = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
                resp_mean = statistics.mean(response_values)
                resp_std = statistics.stdev(response_values) if len(response_values) > 1 else 0
                
                # 检测CPU尖峰
                if metrics.cpu_usage > cpu_mean + 2 * cpu_std and cpu_std > 5:
                    pattern = PerformancePattern(
                        pattern_id=f"cpu_spike_{int(datetime.now().timestamp())}",
                        pattern_type="cpu_spike",
                        description=f"CPU使用率尖峰: {metrics.cpu_usage:.1f}%",
                        frequency=1,
                        duration=timedelta(seconds=60),
                        metrics_snapshot=metrics,
                        associated_issues=["high_cpu", "potential_performance_degradation"],
                        confidence=0.8
                    )
                    patterns.append(pattern)
                
                # 检测响应时间尖峰
                if metrics.response_time_ms > resp_mean + 2 * resp_std and resp_std > 100:
                    pattern = PerformancePattern(
                        pattern_id=f"response_spike_{int(datetime.now().timestamp())}",
                        pattern_type="response_spike",
                        description=f"响应时间尖峰: {metrics.response_time_ms:.0f}ms",
                        frequency=1,
                        duration=timedelta(seconds=60),
                        metrics_snapshot=metrics,
                        associated_issues=["slow_response", "user_experience_impact"],
                        confidence=0.7
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_trend_patterns(self, metrics: SystemMetrics) -> List[PerformancePattern]:
        """检测趋势模式"""
        patterns = []
        
        # 检查长期趋势（最近30个数据点）
        recent_metrics = self.system_metrics_history[-30:] if len(self.system_metrics_history) >= 30 else []
        
        if len(recent_metrics) >= 10:
            # 分析CPU使用率趋势
            cpu_values = [m.cpu_usage for m in recent_metrics]
            if len(cpu_values) >= 5:
                # 简单的线性趋势检测
                x = list(range(len(cpu_values)))
                y = cpu_values
                
                # 计算趋势斜率
                n = len(x)
                slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / \
                       (n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2) if n > 1 else 0
                
                if slope > 2:  # 上升趋势
                    pattern = PerformancePattern(
                        pattern_id=f"cpu_upward_trend_{int(datetime.now().timestamp())}",
                        pattern_type="upward_trend",
                        description=f"CPU使用率持续上升趋势: 斜率 {slope:.2f}",
                        frequency=1,
                        duration=timedelta(minutes=30),
                        metrics_snapshot=metrics,
                        associated_issues=["growing_resource_demand", "potential_scaling_needed"],
                        confidence=0.6
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_correlation_patterns(self, metrics: SystemMetrics) -> List[PerformancePattern]:
        """检测相关性模式"""
        patterns = []
        
        recent_metrics = self.system_metrics_history[-20:] if len(self.system_metrics_history) >= 20 else []
        
        if len(recent_metrics) >= 10:
            # 检查CPU使用率和响应时间的相关性
            cpu_values = [m.cpu_usage for m in recent_metrics]
            response_values = [m.response_time_ms for m in recent_metrics]
            
            if len(cpu_values) == len(response_values) and len(cpu_values) > 2:
                # 计算相关系数
                correlation = self._calculate_correlation(cpu_values, response_values)
                
                if correlation > 0.7:
                    pattern = PerformancePattern(
                        pattern_id=f"cpu_response_correlation_{int(datetime.now().timestamp())}",
                        pattern_type="correlation",
                        description=f"CPU使用率与响应时间强相关: {correlation:.2f}",
                        frequency=1,
                        duration=timedelta(minutes=20),
                        metrics_snapshot=metrics,
                        associated_issues=["resource_bound_performance", "cpu_bottleneck"],
                        confidence=0.8
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_anomaly_patterns(self, metrics: SystemMetrics) -> List[PerformancePattern]:
        """检测异常模式"""
        patterns = []
        
        recent_metrics = self.system_metrics_history[-50:] if len(self.system_metrics_history) >= 50 else []
        
        if len(recent_metrics) >= 20:
            # 使用孤立森林算法思想的简单异常检测
            cpu_values = [m.cpu_usage for m in recent_metrics[:-1]]
            current_cpu = metrics.cpu_usage
            
            if cpu_values:
                cpu_mean = statistics.mean(cpu_values)
                cpu_std = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 1
                
                # 3-sigma规则检测异常
                if abs(current_cpu - cpu_mean) > 3 * cpu_std:
                    pattern = PerformancePattern(
                        pattern_id=f"cpu_anomaly_{int(datetime.now().timestamp())}",
                        pattern_type="anomaly",
                        description=f"CPU使用率异常: {current_cpu:.1f}% (均值: {cpu_mean:.1f}%)",
                        frequency=1,
                        duration=timedelta(seconds=60),
                        metrics_snapshot=metrics,
                        associated_issues=["unexpected_load", "potential_issue"],
                        confidence=0.9
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算皮尔逊相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    async def _generate_recommendations_from_metrics(self, metrics: SystemMetrics):
        """基于指标生成优化建议"""
        session_id = f"metrics_{int(datetime.now().timestamp())}"
        recommendations = []
        
        # 应用优化规则
        for rule in self.rules:
            if await self._evaluate_rule(rule, metrics):
                recommendation = await self._create_recommendation_from_rule(rule, metrics)
                recommendations.append(recommendation)
        
        # 使用AI生成器生成建议
        for rec_type, generator in self.recommendation_generators.items():
            try:
                ai_recommendations = await generator(metrics)
                recommendations.extend(ai_recommendations)
            except Exception as e:
                logger.error(f"建议生成器 {rec_type.value} 执行失败: {e}")
        
        if recommendations:
            self.recommendations[session_id] = recommendations
            logger.info(f"生成 {len(recommendations)} 条优化建议")
    
    async def _evaluate_rule(self, rule: OptimizationRule, metrics: SystemMetrics) -> bool:
        """评估优化规则条件"""
        condition = rule.condition
        metric_name = condition.get("metric")
        operator = condition.get("operator")
        threshold = condition.get("threshold")
        
        if not metric_name or not operator or threshold is None:
            return False
        
        # 获取指标值
        metric_value = getattr(metrics, metric_name, None)
        if metric_value is None:
            # 检查自定义指标
            metric_value = metrics.custom_metrics.get(metric_name)
            if metric_value is None:
                return False
        
        # 评估条件
        if operator == ">":
            return metric_value > threshold
        elif operator == "<":
            return metric_value < threshold
        elif operator == ">=":
            return metric_value >= threshold
        elif operator == "<=":
            return metric_value <= threshold
        elif operator == "==":
            return metric_value == threshold
        elif operator == "!=":
            return metric_value != threshold
        
        return False
    
    async def _create_recommendation_from_rule(self, rule: OptimizationRule, metrics: SystemMetrics) -> OptimizationRecommendation:
        """从规则创建优化建议"""
        recommendation_id = f"rec_{rule.rule_id}_{int(datetime.now().timestamp())}"
        
        # 分析受影响的组件
        affected_components = self._analyze_affected_components(rule, metrics)
        
        # 生成实施步骤
        implementation_steps = self._generate_implementation_steps(rule)
        
        return OptimizationRecommendation(
            recommendation_id=recommendation_id,
            rule_id=rule.rule_id,
            title=rule.name,
            description=rule.description,
            recommendation_type=rule.recommendation_type,
            priority=rule.priority,
            confidence=rule.confidence,
            impact_score=rule.impact_score,
            implementation_effort=rule.implementation_effort,
            estimated_benefit=rule.estimated_benefit,
            affected_components=affected_components,
            implementation_steps=implementation_steps,
            risk_assessment=self._assess_risk(rule),
            validation_method=self._determine_validation_method(rule)
        )
    
    def _analyze_affected_components(self, rule: OptimizationRule, metrics: SystemMetrics) -> List[str]:
        """分析受影响的组件"""
        affected = []
        
        # 基于规则类型和指标类型推断受影响组件
        metric_name = rule.condition.get("metric", "")
        
        if "cpu" in metric_name.lower():
            affected.extend(["CPU调度器", "算法模块", "并发处理"])
        elif "memory" in metric_name.lower():
            affected.extend(["内存管理", "缓存系统", "数据结构"])
        elif "response" in metric_name.lower():
            affected.extend(["API接口", "数据库查询", "网络通信"])
        elif "cache" in metric_name.lower():
            affected.extend(["缓存层", "数据预取", "存储系统"])
        elif "error" in metric_name.lower():
            affected.extend(["输入验证", "异常处理", "监控系统"])
        
        return list(set(affected))  # 去重
    
    def _generate_implementation_steps(self, rule: OptimizationRule) -> List[str]:
        """生成实施步骤"""
        base_steps = [
            "1. 备份当前配置和数据",
            "2. 在测试环境中验证方案",
            "3. 制定回滚计划"
        ]
        
        # 基于规则类型添加特定步骤
        if rule.recommendation_type == RecommendationType.PERFORMANCE:
            base_steps.extend([
                "4. 监控关键性能指标",
                "5. 逐步部署变更",
                "6. 验证性能改善效果"
            ])
        elif rule.recommendation_type == RecommendationType.QUALITY:
            base_steps.extend([
                "4. 增加测试覆盖率",
                "5. 实施代码审查",
                "6. 建立质量门禁"
            ])
        
        return base_steps
    
    def _assess_risk(self, rule: OptimizationRule) -> str:
        """评估风险"""
        if rule.priority == PriorityLevel.CRITICAL:
            return "高风险 - 可能影响系统稳定性"
        elif rule.implementation_effort == "high":
            return "中等风险 - 实施复杂度较高"
        else:
            return "低风险 - 标准优化措施"
    
    def _determine_validation_method(self, rule: OptimizationRule) -> str:
        """确定验证方法"""
        if rule.recommendation_type == RecommendationType.PERFORMANCE:
            return "A/B测试 + 性能基准测试"
        elif rule.recommendation_type == RecommendationType.QUALITY:
            return "单元测试 + 集成测试 + 用户验收测试"
        else:
            return "监控指标对比 + 用户反馈收集"
    
    async def _generate_performance_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成性能优化建议"""
        recommendations = []
        
        # 基于指标组合生成智能建议
        if metrics.cpu_usage > 80 and metrics.response_time_ms > 1000:
            rec = OptimizationRecommendation(
                recommendation_id=f"perf_ai_{int(datetime.now().timestamp())}",
                rule_id="ai_generated",
                title="复合性能瓶颈优化",
                description="检测到CPU高使用率和响应时间延迟的复合问题",
                recommendation_type=RecommendationType.PERFORMANCE,
                priority=PriorityLevel.HIGH,
                confidence=ConfidenceLevel.MEDIUM,
                impact_score=0.85,
                implementation_effort="high",
                estimated_benefit="综合性能提升30-50%",
                affected_components=["CPU密集型任务", "I/O操作", "算法效率"],
                implementation_steps=[
                    "1. 分析CPU热点函数",
                    "2. 优化数据库查询",
                    "3. 实施异步处理",
                    "4. 增加缓存层",
                    "5. 调整资源分配"
                ],
                risk_assessment="中等风险 - 需要全面测试",
                validation_method="压力测试 + 用户体验测试"
            )
            recommendations.append(rec)
        
        return recommendations
    
    async def _generate_quality_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成质量优化建议"""
        return []
    
    async def _generate_cost_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成成本优化建议"""
        return []
    
    async def _generate_scalability_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成可扩展性建议"""
        return []
    
    async def _generate_maintainability_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成可维护性建议"""
        return []
    
    async def _generate_security_recommendations(self, metrics: SystemMetrics) -> List[OptimizationRecommendation]:
        """生成安全性建议"""
        return []
    
    async def get_recommendations(self, 
                                session_id: Optional[str] = None,
                                rec_type: Optional[RecommendationType] = None,
                                priority: Optional[PriorityLevel] = None) -> List[OptimizationRecommendation]:
        """
        获取优化建议
        
        Args:
            session_id: 会话ID（可选）
            rec_type: 建议类型（可选）
            priority: 优先级（可选）
            
        Returns:
            优化建议列表
        """
        if session_id:
            recommendations = self.recommendations.get(session_id, [])
        else:
            # 获取所有建议
            recommendations = []
            for rec_list in self.recommendations.values():
                recommendations.extend(rec_list)
        
        # 应用过滤器
        if rec_type:
            recommendations = [rec for rec in recommendations if rec.recommendation_type == rec_type]
        
        if priority:
            recommendations = [rec for rec in recommendations if rec.priority == priority]
        
        # 按优先级和创建时间排序
        recommendations.sort(key=lambda x: (x.priority.value, x.created_at), reverse=True)
        
        return recommendations
    
    async def apply_recommendation(self, recommendation_id: str) -> bool:
        """
        应用优化建议
        
        Args:
            recommendation_id: 建议ID
            
        Returns:
            是否成功应用
        """
        # 查找建议
        target_recommendation = None
        for rec_list in self.recommendations.values():
            for rec in rec_list:
                if rec.recommendation_id == recommendation_id:
                    target_recommendation = rec
                    break
            if target_recommendation:
                break
        
        if not target_recommendation:
            logger.warning(f"未找到建议: {recommendation_id}")
            return False
        
        if target_recommendation.status != "pending":
            logger.warning(f"建议状态不正确: {target_recommendation.status}")
            return False
        
        # 更新状态
        target_recommendation.status = "applied"
        target_recommendation.applied_at = datetime.now()
        
        logger.info(f"应用优化建议: {recommendation_id}")
        return True
    
    async def get_patterns_summary(self) -> Dict[str, Any]:
        """获取模式分析摘要"""
        summary = {
            "total_patterns": 0,
            "pattern_types": {},
            "recent_patterns": []
        }
        
        for detector_name, patterns in self.performance_patterns.items():
            summary["pattern_types"][detector_name] = len(patterns)
            summary["total_patterns"] += len(patterns)
            
            # 添加最近的模式
            recent_patterns = sorted(patterns, key=lambda x: x.metrics_snapshot.timestamp, reverse=True)[:5]
            summary["recent_patterns"].extend(recent_patterns)
        
        # 按时间排序最近模式
        summary["recent_patterns"].sort(key=lambda x: x.metrics_snapshot.timestamp, reverse=True)
        summary["recent_patterns"] = summary["recent_patterns"][:10]  # 限制数量
        
        return summary


# 使用示例和测试函数
async def demo_recommendation_engine():
    """演示优化建议引擎功能"""
    
    # 创建建议引擎
    engine = RecommendationEngine()
    
    # 模拟系统指标数据
    test_metrics = [
        SystemMetrics(
            timestamp=datetime.now() - timedelta(minutes=5),
            cpu_usage=75.0,
            memory_usage=65.0,
            response_time_ms=1200.0,
            throughput_qps=45.0,
            error_rate=2.5,
            cache_hit_rate=68.0,
            active_connections=150,
            queue_length=5,
            disk_io=120.0,
            network_io=85.0
        ),
        SystemMetrics(
            timestamp=datetime.now() - timedelta(minutes=3),
            cpu_usage=85.0,
            memory_usage=70.0,
            response_time_ms=1800.0,
            throughput_qps=42.0,
            error_rate=3.2,
            cache_hit_rate=65.0,
            active_connections=165,
            queue_length=8,
            disk_io=145.0,
            network_io=92.0
        ),
        SystemMetrics(
            timestamp=datetime.now() - timedelta(minutes=1),
            cpu_usage=92.0,
            memory_usage=75.0,
            response_time_ms=2500.0,
            throughput_qps=38.0,
            error_rate=4.1,
            cache_hit_rate=62.0,
            active_connections=180,
            queue_length=12,
            disk_io=168.0,
            network_io=105.0
        )
    ]
    
    # 收集指标并生成建议
    for metrics in test_metrics:
        await engine.collect_metrics(metrics)
        await asyncio.sleep(0.1)  # 模拟时间间隔
    
    # 获取优化建议
    recommendations = await engine.get_recommendations()
    
    print("=== 优化建议引擎演示 ===")
    print(f"生成建议数量: {len(recommendations)}")
    
    for rec in recommendations[:3]:  # 显示前3条建议
        print(f"\n📋 建议: {rec.title}")
        print(f"   类型: {rec.recommendation_type.value}")
        print(f"   优先级: {rec.priority.value}")
        print(f"   置信度: {rec.confidence.value}")
        print(f"   影响分数: {rec.impact_score}")
        print(f"   描述: {rec.description}")
        print(f"   建议: {rec.implementation_steps[0] if rec.implementation_steps else 'N/A'}")
    
    # 获取模式分析摘要
    patterns_summary = await engine.get_patterns_summary()
    print(f"\n📊 检测到的模式总数: {patterns_summary['total_patterns']}")
    
    for pattern_type, count in patterns_summary['pattern_types'].items():
        print(f"   {pattern_type}: {count} 个模式")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_recommendation_engine())