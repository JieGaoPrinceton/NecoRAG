"""
路径分析工具 - Path Analysis Tool
深度分析检索路径、识别瓶颈、提供优化建议
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PathSegmentType(str, Enum):
    """路径段类型枚举"""
    QUERY_ANALYSIS = "query_analysis"
    ENTITY_RECOGNITION = "entity_recognition"
    VECTOR_RETRIEVAL = "vector_retrieval"
    GRAPH_REASONING = "graph_reasoning"
    RESULT_FUSION = "result_fusion"
    ANSWER_GENERATION = "answer_generation"


class BottleneckType(str, Enum):
    """瓶颈类型枚举"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COVERAGE = "coverage"
    CONSISTENCY = "consistency"


@dataclass
class PathSegment:
    """路径段数据模型"""
    segment_id: str
    segment_type: PathSegmentType
    start_time: datetime
    end_time: datetime
    duration_ms: int
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metrics: Dict[str, float]
    status: str  # success, failed, timeout
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        data['segment_type'] = self.segment_type.value
        return data


@dataclass
class PathAnalysisResult:
    """路径分析结果"""
    analysis_id: str
    session_id: str
    total_duration_ms: int
    segment_count: int
    success_rate: float
    avg_segment_duration: float
    longest_segment: Optional[str] = None
    shortest_segment: Optional[str] = None
    bottleneck_segments: List[str] = None
    quality_issues: List[str] = None
    optimization_suggestions: List[str] = None
    performance_metrics: Dict[str, float] = None
    analyzed_at: datetime = None
    
    def __post_init__(self):
        if self.bottleneck_segments is None:
            self.bottleneck_segments = []
        if self.quality_issues is None:
            self.quality_issues = []
        if self.optimization_suggestions is None:
            self.optimization_suggestions = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['analyzed_at'] = self.analyzed_at.isoformat()
        return data


@dataclass
class Bottleneck:
    """瓶颈分析结果"""
    bottleneck_id: str
    segment_type: PathSegmentType
    bottleneck_type: BottleneckType
    severity: str  # low, medium, high, critical
    description: str
    impact_score: float  # 0-1
    affected_metrics: List[str]
    suggested_actions: List[str]
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
        if self.affected_metrics is None:
            self.affected_metrics = []
        if self.suggested_actions is None:
            self.suggested_actions = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        data['segment_type'] = self.segment_type.value
        data['bottleneck_type'] = self.bottleneck_type.value
        return data


class PathAnalyzer:
    """路径分析器"""
    
    def __init__(self):
        self.analysis_history: Dict[str, PathAnalysisResult] = {}
        self.bottleneck_detectors: Dict[BottleneckType, Callable] = {}
        self.optimization_rules: List[Dict[str, Any]] = []
        
        # 注册默认瓶颈检测器
        self._register_default_detectors()
        self._load_optimization_rules()
    
    def _register_default_detectors(self):
        """注册默认瓶颈检测器"""
        self.bottleneck_detectors[BottleneckType.PERFORMANCE] = self._detect_performance_bottlenecks
        self.bottleneck_detectors[BottleneckType.QUALITY] = self._detect_quality_bottlenecks
        self.bottleneck_detectors[BottleneckType.COVERAGE] = self._detect_coverage_bottlenecks
        self.bottleneck_detectors[BottleneckType.CONSISTENCY] = self._detect_consistency_bottlenecks
    
    def _load_optimization_rules(self):
        """加载优化规则"""
        self.optimization_rules = [
            {
                "condition": {"segment_type": "vector_retrieval", "duration_threshold": 500},
                "suggestion": "考虑增加向量数据库索引或优化查询向量",
                "priority": "high"
            },
            {
                "condition": {"segment_type": "graph_reasoning", "quality_threshold": 0.7},
                "suggestion": "调整图谱推理参数或扩充知识图谱数据",
                "priority": "medium"
            },
            {
                "condition": {"success_rate_threshold": 0.8},
                "suggestion": "检查整体系统稳定性，可能需要增加容错机制",
                "priority": "high"
            }
        ]
    
    async def analyze_path(self, 
                         session_id: str,
                         segments: List[PathSegment],
                         historical_data: Optional[List[List[PathSegment]]] = None) -> PathAnalysisResult:
        """
        分析检索路径
        
        Args:
            session_id: 会话ID
            segments: 路径段列表
            historical_data: 历史路径数据用于对比分析
            
        Returns:
            路径分析结果
        """
        analysis_id = f"analysis_{int(datetime.now().timestamp() * 1000)}"
        
        if not segments:
            return PathAnalysisResult(
                analysis_id=analysis_id,
                session_id=session_id,
                total_duration_ms=0,
                segment_count=0,
                success_rate=0.0
            )
        
        # 计算基本统计信息
        total_duration = sum(segment.duration_ms for segment in segments)
        successful_segments = [s for s in segments if s.status == "success"]
        success_rate = len(successful_segments) / len(segments)
        avg_duration = total_duration / len(segments) if segments else 0
        
        # 找出最长和最短段
        longest_segment = max(segments, key=lambda x: x.duration_ms).segment_type.value if segments else None
        shortest_segment = min(segments, key=lambda x: x.duration_ms).segment_type.value if segments else None
        
        # 检测瓶颈
        bottlenecks = await self._detect_bottlenecks(segments, historical_data)
        bottleneck_segments = [b.segment_type.value for b in bottlenecks]
        
        # 识别质量问题
        quality_issues = await self._identify_quality_issues(segments)
        
        # 生成优化建议
        suggestions = await self._generate_optimization_suggestions(
            segments, bottlenecks, quality_issues, historical_data
        )
        
        # 计算性能指标
        performance_metrics = await self._calculate_performance_metrics(segments, historical_data)
        
        # 创建分析结果
        result = PathAnalysisResult(
            analysis_id=analysis_id,
            session_id=session_id,
            total_duration_ms=total_duration,
            segment_count=len(segments),
            success_rate=success_rate,
            avg_segment_duration=avg_duration,
            longest_segment=longest_segment,
            shortest_segment=shortest_segment,
            bottleneck_segments=bottleneck_segments,
            quality_issues=quality_issues,
            optimization_suggestions=suggestions,
            performance_metrics=performance_metrics
        )
        
        # 保存分析结果
        self.analysis_history[analysis_id] = result
        logger.info(f"完成路径分析: {analysis_id} (会话: {session_id})")
        
        return result
    
    async def _detect_bottlenecks(self, 
                                segments: List[PathSegment],
                                historical_data: Optional[List[List[PathSegment]]] = None) -> List[Bottleneck]:
        """检测瓶颈"""
        bottlenecks = []
        
        # 使用各种检测器检测瓶颈
        for bottleneck_type, detector in self.bottleneck_detectors.items():
            try:
                detected = await detector(segments, historical_data)
                bottlenecks.extend(detected)
            except Exception as e:
                logger.error(f"瓶颈检测器 {bottleneck_type.value} 执行失败: {e}")
        
        return bottlenecks
    
    async def _detect_performance_bottlenecks(self, 
                                            segments: List[PathSegment],
                                            historical_data: Optional[List[List[PathSegment]]] = None) -> List[Bottleneck]:
        """检测性能瓶颈"""
        bottlenecks = []
        
        # 分析各段耗时
        for segment in segments:
            # 绝对时间阈值检测
            if segment.duration_ms > 1000:  # 超过1秒
                bottlenecks.append(Bottleneck(
                    bottleneck_id=f"perf_{segment.segment_id}",
                    segment_type=segment.segment_type,
                    bottleneck_type=BottleneckType.PERFORMANCE,
                    severity="high" if segment.duration_ms > 2000 else "medium",
                    description=f"段 {segment.segment_type.value} 耗时过长: {segment.duration_ms}ms",
                    impact_score=min(segment.duration_ms / 5000.0, 1.0),
                    affected_metrics=["response_time", "throughput"]
                ))
            
            # 相对时间比例检测（相对于总时间）
            total_time = sum(s.duration_ms for s in segments)
            if total_time > 0:
                time_ratio = segment.duration_ms / total_time
                if time_ratio > 0.4:  # 占总时间40%以上
                    bottlenecks.append(Bottleneck(
                        bottleneck_id=f"perf_ratio_{segment.segment_id}",
                        segment_type=segment.segment_type,
                        bottleneck_type=BottleneckType.PERFORMANCE,
                        severity="medium",
                        description=f"段 {segment.segment_type.value} 占总时间比例过高: {time_ratio:.1%}",
                        impact_score=time_ratio,
                        affected_metrics=["efficiency"]
                    ))
        
        # 与历史数据对比
        if historical_data and len(historical_data) >= 5:
            await self._compare_with_history(bottlenecks, segments, historical_data)
        
        return bottlenecks
    
    async def _detect_quality_bottlenecks(self, 
                                        segments: List[PathSegment],
                                        historical_data: Optional[List[List[PathSegment]]] = None) -> List[Bottleneck]:
        """检测质量瓶颈"""
        bottlenecks = []
        
        for segment in segments:
            # 检查成功率
            if segment.status != "success":
                bottlenecks.append(Bottleneck(
                    bottleneck_id=f"qual_{segment.segment_id}",
                    segment_type=segment.segment_type,
                    bottleneck_type=BottleneckType.QUALITY,
                    severity="high" if segment.status == "failed" else "medium",
                    description=f"段 {segment.segment_type.value} 执行失败: {segment.error_message or '未知错误'}",
                    impact_score=1.0,
                    affected_metrics=["accuracy", "reliability"]
                ))
            
            # 检查质量指标
            quality_score = segment.metrics.get("quality_score", 1.0)
            if quality_score < 0.7:
                bottlenecks.append(Bottleneck(
                    bottleneck_id=f"qual_score_{segment.segment_id}",
                    segment_type=segment.segment_type,
                    bottleneck_type=BottleneckType.QUALITY,
                    severity="medium" if quality_score < 0.5 else "low",
                    description=f"段 {segment.segment_type.value} 质量分数偏低: {quality_score:.2f}",
                    impact_score=1.0 - quality_score,
                    affected_metrics=["quality"]
                ))
        
        return bottlenecks
    
    async def _detect_coverage_bottlenecks(self, 
                                         segments: List[PathSegment],
                                         historical_data: Optional[List[List[PathSegment]]] = None) -> List[Bottleneck]:
        """检测覆盖率瓶颈"""
        bottlenecks = []
        
        # 检查实体识别覆盖率
        entity_segments = [s for s in segments if s.segment_type == PathSegmentType.ENTITY_RECOGNITION]
        if entity_segments:
            segment = entity_segments[0]
            coverage_rate = segment.metrics.get("coverage_rate", 1.0)
            if coverage_rate < 0.8:
                bottlenecks.append(Bottleneck(
                    bottleneck_id=f"cov_{segment.segment_id}",
                    segment_type=segment.segment_type,
                    bottleneck_type=BottleneckType.COVERAGE,
                    severity="medium" if coverage_rate < 0.6 else "low",
                    description=f"实体识别覆盖率不足: {coverage_rate:.1%}",
                    impact_score=1.0 - coverage_rate,
                    affected_metrics=["completeness", "recall"]
                ))
        
        return bottlenecks
    
    async def _detect_consistency_bottlenecks(self, 
                                            segments: List[PathSegment],
                                            historical_data: Optional[List[List[PathSegment]]] = None) -> List[Bottleneck]:
        """检测一致性瓶颈"""
        bottlenecks = []
        
        # 检查结果一致性
        fusion_segments = [s for s in segments if s.segment_type == PathSegmentType.RESULT_FUSION]
        if fusion_segments:
            segment = fusion_segments[0]
            consistency_score = segment.metrics.get("consistency_score", 1.0)
            if consistency_score < 0.8:
                bottlenecks.append(Bottleneck(
                    bottleneck_id=f"cons_{segment.segment_id}",
                    segment_type=segment.segment_type,
                    bottleneck_type=BottleneckType.CONSISTENCY,
                    severity="medium" if consistency_score < 0.6 else "low",
                    description=f"结果融合一致性不足: {consistency_score:.2f}",
                    impact_score=1.0 - consistency_score,
                    affected_metrics=["consistency", "coherence"]
                ))
        
        return bottlenecks
    
    async def _compare_with_history(self, 
                                  bottlenecks: List[Bottleneck],
                                  current_segments: List[PathSegment],
                                  historical_data: List[List[PathSegment]]):
        """与历史数据对比分析"""
        # 计算历史平均耗时
        historical_durations = defaultdict(list)
        for hist_segments in historical_data[-10:]:  # 最近10次
            for segment in hist_segments:
                historical_durations[segment.segment_type].append(segment.duration_ms)
        
        # 对比当前数据
        for segment in current_segments:
            if segment.segment_type in historical_durations:
                hist_avg = statistics.mean(historical_durations[segment.segment_type])
                if segment.duration_ms > hist_avg * 1.5:  # 超过历史平均值50%
                    bottlenecks.append(Bottleneck(
                        bottleneck_id=f"hist_perf_{segment.segment_id}",
                        segment_type=segment.segment_type,
                        bottleneck_type=BottleneckType.PERFORMANCE,
                        severity="medium",
                        description=f"段 {segment.segment_type.value} 耗时显著高于历史平均水平",
                        impact_score=min((segment.duration_ms / hist_avg - 1.0), 1.0),
                        affected_metrics=["performance_degradation"]
                    ))
    
    async def _identify_quality_issues(self, segments: List[PathSegment]) -> List[str]:
        """识别质量问题"""
        issues = []
        
        # 检查重复查询
        query_types = [s.input_data.get("query_type") for s in segments if s.input_data.get("query_type")]
        if len(query_types) != len(set(query_types)):
            issues.append("检测到重复的查询处理")
        
        # 检查数据完整性
        for segment in segments:
            if not segment.output_data:
                issues.append(f"段 {segment.segment_type.value} 输出数据为空")
        
        # 检查异常指标
        for segment in segments:
            for metric_name, value in segment.metrics.items():
                if "error" in metric_name.lower() and value > 0:
                    issues.append(f"段 {segment.segment_type.value} 存在 {metric_name}: {value}")
        
        return issues
    
    async def _generate_optimization_suggestions(self,
                                               segments: List[PathSegment],
                                               bottlenecks: List[Bottleneck],
                                               quality_issues: List[str],
                                               historical_data: Optional[List[List[PathSegment]]] = None) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 基于瓶颈生成建议
        for bottleneck in bottlenecks:
            suggestions.extend(bottleneck.suggested_actions)
        
        # 基于规则生成建议
        for rule in self.optimization_rules:
            condition = rule["condition"]
            if self._match_condition(segments, condition):
                suggestions.append(rule["suggestion"])
        
        # 基于质量问题生成建议
        if quality_issues:
            suggestions.append("建议加强数据质量监控和验证机制")
        
        # 基于性能统计生成建议
        total_time = sum(s.duration_ms for s in segments)
        if total_time > 5000:  # 总时间超过5秒
            suggestions.append("考虑并行化处理或优化算法复杂度")
        
        # 去重并排序
        unique_suggestions = list(set(suggestions))
        return sorted(unique_suggestions, key=lambda x: ("高优先级" in x, "紧急" in x), reverse=True)
    
    def _match_condition(self, segments: List[PathSegment], condition: Dict[str, Any]) -> bool:
        """匹配优化条件"""
        for segment in segments:
            # 检查段类型条件
            if "segment_type" in condition:
                if segment.segment_type.value != condition["segment_type"]:
                    continue
            
            # 检查耗时条件
            if "duration_threshold" in condition:
                if segment.duration_ms <= condition["duration_threshold"]:
                    continue
            
            # 检查质量条件
            if "quality_threshold" in condition:
                quality_score = segment.metrics.get("quality_score", 1.0)
                if quality_score >= condition["quality_threshold"]:
                    continue
            
            return True
        
        # 检查整体条件
        if "success_rate_threshold" in condition:
            successful = len([s for s in segments if s.status == "success"])
            success_rate = successful / len(segments) if segments else 0
            if success_rate >= condition["success_rate_threshold"]:
                return False
        
        return False
    
    async def _calculate_performance_metrics(self,
                                           segments: List[PathSegment],
                                           historical_data: Optional[List[List[PathSegment]]] = None) -> Dict[str, float]:
        """计算性能指标"""
        metrics = {}
        
        if not segments:
            return metrics
        
        # 基本指标
        durations = [s.duration_ms for s in segments]
        metrics.update({
            "total_duration_ms": sum(durations),
            "avg_segment_duration_ms": statistics.mean(durations),
            "max_segment_duration_ms": max(durations),
            "min_segment_duration_ms": min(durations),
            "duration_std_dev": statistics.stdev(durations) if len(durations) > 1 else 0,
            "success_rate": len([s for s in segments if s.status == "success"]) / len(segments)
        })
        
        # 段类型分布
        type_counter = Counter(s.segment_type.value for s in segments)
        for seg_type, count in type_counter.items():
            metrics[f"{seg_type}_count"] = count
        
        # 与历史数据对比
        if historical_data and len(historical_data) >= 3:
            await self._calculate_trends(metrics, segments, historical_data)
        
        return metrics
    
    async def _calculate_trends(self, 
                              metrics: Dict[str, float],
                              current_segments: List[PathSegment],
                              historical_data: List[List[PathSegment]]):
        """计算趋势指标"""
        # 计算最近几次的平均耗时
        recent_durations = []
        for hist_segments in historical_data[-5:]:  # 最近5次
            if hist_segments:
                recent_durations.append(sum(s.duration_ms for s in hist_segments))
        
        if recent_durations:
            current_total = sum(s.duration_ms for s in current_segments)
            historical_avg = statistics.mean(recent_durations)
            metrics["performance_trend"] = (current_total - historical_avg) / historical_avg
            
            # 性能改善/恶化标识
            if metrics["performance_trend"] > 0.1:
                metrics["performance_status"] = -1  # 恶化
            elif metrics["performance_trend"] < -0.1:
                metrics["performance_status"] = 1   # 改善
            else:
                metrics["performance_status"] = 0   # 稳定
    
    async def get_analysis_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[PathAnalysisResult]:
        """
        获取分析历史
        
        Args:
            session_id: 会话ID（可选）
            limit: 返回记录数限制
            
        Returns:
            分析结果列表
        """
        if session_id:
            results = [result for result in self.analysis_history.values() 
                      if result.session_id == session_id]
        else:
            results = list(self.analysis_history.values())
        
        # 按时间排序并限制数量
        results.sort(key=lambda x: x.analyzed_at, reverse=True)
        return results[:limit]


# 使用示例和测试函数
async def demo_path_analysis():
    """演示路径分析功能"""
    
    # 创建路径分析器
    analyzer = PathAnalyzer()
    
    # 创建模拟路径段
    segments = [
        PathSegment(
            segment_id="seg_001",
            segment_type=PathSegmentType.QUERY_ANALYSIS,
            start_time=datetime.now() - timedelta(milliseconds=100),
            end_time=datetime.now() - timedelta(milliseconds=50),
            duration_ms=50,
            input_data={"query": "什么是人工智能"},
            output_data={"intent": "definition", "entities": ["人工智能"]},
            metrics={"quality_score": 0.95},
            status="success"
        ),
        PathSegment(
            segment_id="seg_002",
            segment_type=PathSegmentType.VECTOR_RETRIEVAL,
            start_time=datetime.now() - timedelta(milliseconds=50),
            end_time=datetime.now() - timedelta(milliseconds=10),
            duration_ms=40,
            input_data={"entities": ["人工智能"]},
            output_data={"documents": ["doc1", "doc2", "doc3"]},
            metrics={"quality_score": 0.85, "recall": 0.75},
            status="success"
        ),
        PathSegment(
            segment_id="seg_003",
            segment_type=PathSegmentType.GRAPH_REASONING,
            start_time=datetime.now() - timedelta(milliseconds=10),
            end_time=datetime.now(),
            duration_ms=10,
            input_data={"documents": ["doc1", "doc2", "doc3"]},
            output_data={"relations": ["rel1", "rel2"]},
            metrics={"quality_score": 0.92, "consistency_score": 0.88},
            status="success"
        )
    ]
    
    # 执行分析
    result = await analyzer.analyze_path("test_session_001", segments)
    
    print("=== 路径分析结果 ===")
    print(f"总耗时: {result.total_duration_ms}ms")
    print(f"成功率: {result.success_rate:.1%}")
    print(f"平均段耗时: {result.avg_segment_duration:.1f}ms")
    print(f"最长段: {result.longest_segment}")
    print(f"瓶颈段: {result.bottleneck_segments}")
    print(f"质量问题: {result.quality_issues}")
    print("\n优化建议:")
    for suggestion in result.optimization_suggestions:
        print(f"  • {suggestion}")
    
    print("\n性能指标:")
    for key, value in result.performance_metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_path_analysis())