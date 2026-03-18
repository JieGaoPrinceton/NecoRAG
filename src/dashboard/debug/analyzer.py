"""
Path Analyzer - 路径分析器
分析思维路径的性能、瓶颈和优化机会
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict

from src.dashboard.debug.models import DebugSession, RetrievalStep, EvidenceInfo
from src.dashboard.debug.models import DebugSessionStatus

logger = logging.getLogger(__name__)


class PathAnalyzer:
    """路径分析器"""
    
    def __init__(self):
        """初始化分析器"""
        pass
    
    def analyze_performance(self, session: DebugSession) -> Dict[str, Any]:
        """
        性能分析
        
        Args:
            session: 调试会话
            
        Returns:
            Dict: 性能分析结果
        """
        if not session.retrieval_steps:
            return {"error": "No retrieval steps found"}
        
        # 计算总体性能指标
        total_duration = session.total_duration
        step_durations = [step.duration for step in session.retrieval_steps if step.is_completed]
        avg_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0
        
        # 识别最耗时的步骤
        slowest_steps = sorted(
            [step for step in session.retrieval_steps if step.is_completed],
            key=lambda x: x.duration,
            reverse=True
        )[:3]
        
        # 计算步骤分布
        step_types = defaultdict(int)
        for step in session.retrieval_steps:
            step_types[step.name] += 1
        
        return {
            "total_duration": total_duration,
            "avg_step_duration": avg_step_duration,
            "step_count": len(session.retrieval_steps),
            "completed_steps": len([s for s in session.retrieval_steps if s.is_completed]),
            "failed_steps": len([s for s in session.retrieval_steps if s.status == "failed"]),
            "slowest_steps": [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "percentage": (step.duration / total_duration) * 100 if total_duration > 0 else 0
                }
                for step in slowest_steps
            ],
            "step_distribution": dict(step_types),
            "throughput": len(session.retrieval_steps) / total_duration if total_duration > 0 else 0
        }
    
    def identify_bottlenecks(self, session: DebugSession) -> List[Dict[str, Any]]:
        """
        识别性能瓶颈
        
        Args:
            session: 调试会话
            
        Returns:
            List: 瓶颈列表
        """
        bottlenecks = []
        
        if not session.retrieval_steps:
            return bottlenecks
        
        # 计算平均步骤时间
        completed_steps = [step for step in session.retrieval_steps if step.is_completed]
        if not completed_steps:
            return bottlenecks
            
        avg_duration = sum(step.duration for step in completed_steps) / len(completed_steps)
        threshold = avg_duration * 2  # 超过平均时间2倍的步骤视为瓶颈
        
        # 识别慢步骤
        for step in completed_steps:
            if step.duration > threshold:
                bottleneck = {
                    "type": "slow_step",
                    "step_name": step.name,
                    "actual_duration": step.duration,
                    "expected_duration": avg_duration,
                    "impact": "high" if step.duration > avg_duration * 3 else "medium",
                    "recommendation": self._get_slow_step_recommendation(step)
                }
                bottlenecks.append(bottleneck)
        
        # 识别失败步骤
        failed_steps = [step for step in session.retrieval_steps if step.status == "failed"]
        for step in failed_steps:
            bottleneck = {
                "type": "failed_step",
                "step_name": step.name,
                "error": step.output_data.get("error") if step.output_data else "Unknown error",
                "impact": "high",
                "recommendation": self._get_failed_step_recommendation(step)
            }
            bottlenecks.append(bottleneck)
        
        # 识别证据质量问题
        if session.evidence_sources:
            avg_relevance = sum(e.relevance_score for e in session.evidence_sources) / len(session.evidence_sources)
            if avg_relevance < 0.6:  # 平均相关度低于0.6视为问题
                bottleneck = {
                    "type": "low_quality_evidence",
                    "issue": "Low average evidence relevance",
                    "avg_relevance": avg_relevance,
                    "impact": "medium",
                    "recommendation": "Consider adjusting retrieval parameters or expanding knowledge base"
                }
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def analyze_reasoning_chain(self, session: DebugSession) -> Dict[str, Any]:
        """
        分析推理链条
        
        Args:
            session: 调试会话
            
        Returns:
            Dict: 推理分析结果
        """
        if not session.reasoning_chain:
            return {"message": "No reasoning chain found"}
        
        # 置信度分析
        confidences = [step.confidence for step in session.reasoning_chain]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        
        # 迭代分析
        iterations = [step.iteration for step in session.reasoning_chain]
        max_iterations = max(iterations)
        
        # 证据使用分析
        evidence_usage = defaultdict(int)
        for step in session.reasoning_chain:
            for evidence_id in step.evidence_used:
                evidence_usage[evidence_id] += 1
        
        return {
            "iteration_count": len(session.reasoning_chain),
            "max_iterations": max_iterations,
            "avg_confidence": avg_confidence,
            "confidence_variance": confidence_variance,
            "confidence_trend": "increasing" if len(confidences) > 1 and confidences[-1] > confidences[0] else "decreasing",
            "most_used_evidence": dict(evidence_usage),
            "unique_evidence_used": len(set(evidence_usage.keys()))
        }
    
    def generate_optimization_recommendations(self, session: DebugSession) -> List[str]:
        """
        生成优化建议
        
        Args:
            session: 调试会话
            
        Returns:
            List: 优化建议列表
        """
        recommendations = []
        
        # 性能相关建议
        performance_analysis = self.analyze_performance(session)
        if performance_analysis.get("avg_step_duration", 0) > 1.0:
            recommendations.append("Consider optimizing slow retrieval steps or implementing caching")
        
        if performance_analysis.get("failed_steps", 0) > 0:
            recommendations.append("Investigate and fix consistently failing steps")
        
        # 瓶颈相关建议
        bottlenecks = self.identify_bottlenecks(session)
        high_impact_bottlenecks = [b for b in bottlenecks if b["impact"] == "high"]
        if high_impact_bottlenecks:
            recommendations.append(f"Address {len(high_impact_bottlenecks)} high-impact bottlenecks")
        
        # 证据质量建议
        if session.evidence_sources:
            high_quality_count = len([e for e in session.evidence_sources if e.is_high_quality])
            total_count = len(session.evidence_sources)
            quality_ratio = high_quality_count / total_count if total_count > 0 else 0
            
            if quality_ratio < 0.5:
                recommendations.append("Improve evidence quality by adjusting retrieval parameters")
            elif quality_ratio < 0.8:
                recommendations.append("Consider fine-tuning evidence filtering criteria")
        
        # 推理链建议
        reasoning_analysis = self.analyze_reasoning_chain(session)
        if reasoning_analysis.get("max_iterations", 0) > 5:
            recommendations.append("High iteration count suggests complex reasoning - consider simplifying queries")
        
        if reasoning_analysis.get("confidence_variance", 0) > 0.1:
            recommendations.append("High confidence variance indicates unstable reasoning - review prompting strategy")
        
        # 默认建议
        if not recommendations:
            recommendations.extend([
                "Monitor performance trends over time",
                "Regular review of retrieval parameters",
                "Consider implementing result caching for frequent queries"
            ])
        
        return recommendations
    
    def _get_slow_step_recommendation(self, step: RetrievalStep) -> str:
        """为慢步骤生成建议"""
        if "vector" in step.name.lower():
            return "Optimize vector index or consider dimensionality reduction"
        elif "graph" in step.name.lower():
            return "Review graph traversal algorithms or implement query optimization"
        elif "fusion" in step.name.lower():
            return "Consider alternative fusion strategies or weight adjustments"
        else:
            return "Profile this step to identify specific optimization opportunities"
    
    def _get_failed_step_recommendation(self, step: RetrievalStep) -> str:
        """为失败步骤生成建议"""
        error_msg = step.output_data.get("error", "") if step.output_data else ""
        if "timeout" in error_msg.lower():
            return "Increase timeout limits or optimize underlying operations"
        elif "memory" in error_msg.lower():
            return "Check memory allocation or implement batch processing"
        else:
            return "Investigate error logs and implement proper error handling"


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        """初始化性能分析器"""
        pass
    
    def calculate_metrics(self, sessions: List[DebugSession]) -> Dict[str, Any]:
        """
        计算性能指标
        
        Args:
            sessions: 调试会话列表
            
        Returns:
            Dict: 性能指标
        """
        if not sessions:
            return {}
        
        # 过滤完成的会话
        completed_sessions = [s for s in sessions if s.status == DebugSessionStatus.COMPLETED]
        if not completed_sessions:
            return {"message": "No completed sessions for analysis"}
        
        # 计算基本指标
        durations = [s.total_duration for s in completed_sessions]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # 计算成功率
        total_sessions = len(sessions)
        success_rate = len(completed_sessions) / total_sessions
        
        # 计置信度统计
        confidences = [s.avg_confidence for s in completed_sessions]
        avg_confidence = sum(confidences) / len(confidences)
        
        # 计算证据质量
        evidence_counts = [len(s.evidence_sources) for s in completed_sessions]
        avg_evidence_count = sum(evidence_counts) / len(evidence_counts)
        
        high_quality_ratios = []
        for session in completed_sessions:
            if session.evidence_sources:
                high_quality = len([e for e in session.evidence_sources if e.is_high_quality])
                ratio = high_quality / len(session.evidence_sources)
                high_quality_ratios.append(ratio)
        
        avg_high_quality_ratio = sum(high_quality_ratios) / len(high_quality_ratios) if high_quality_ratios else 0
        
        return {
            "session_count": total_sessions,
            "completed_sessions": len(completed_sessions),
            "success_rate": success_rate,
            "duration_stats": {
                "average": avg_duration,
                "minimum": min_duration,
                "maximum": max_duration,
                "std_deviation": self._calculate_std_deviation(durations, avg_duration)
            },
            "confidence_stats": {
                "average": avg_confidence,
                "std_deviation": self._calculate_std_deviation(confidences, avg_confidence)
            },
            "evidence_stats": {
                "average_count": avg_evidence_count,
                "average_high_quality_ratio": avg_high_quality_ratio
            },
            "trend_analysis": self._analyze_trends(completed_sessions)
        }
    
    def _calculate_std_deviation(self, values: List[float], mean: float) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _analyze_trends(self, sessions: List[DebugSession]) -> Dict[str, Any]:
        """分析趋势"""
        if len(sessions) < 2:
            return {"insufficient_data": True}
        
        # 按时间排序
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)
        
        # 分析最近的趋势（最后1/3的数据）
        recent_count = max(1, len(sorted_sessions) // 3)
        recent_sessions = sorted_sessions[-recent_count:]
        
        # 计算趋势指标
        recent_avg_duration = sum(s.total_duration for s in recent_sessions) / len(recent_sessions)
        overall_avg_duration = sum(s.total_duration for s in sorted_sessions) / len(sorted_sessions)
        
        recent_avg_confidence = sum(s.avg_confidence for s in recent_sessions) / len(recent_sessions)
        overall_avg_confidence = sum(s.avg_confidence for s in sorted_sessions) / len(sorted_sessions)
        
        return {
            "duration_trend": "improving" if recent_avg_duration < overall_avg_duration else "degrading",
            "confidence_trend": "improving" if recent_avg_confidence > overall_avg_confidence else "degrading",
            "recent_performance": {
                "avg_duration": recent_avg_duration,
                "avg_confidence": recent_avg_confidence,
                "session_count": len(recent_sessions)
            }
        }
    
    def benchmark_comparison(self, current_sessions: List[DebugSession], 
                           baseline_sessions: List[DebugSession]) -> Dict[str, Any]:
        """
        基准比较
        
        Args:
            current_sessions: 当前会话
            baseline_sessions: 基准会话
            
        Returns:
            Dict: 比较结果
        """
        current_metrics = self.calculate_metrics(current_sessions)
        baseline_metrics = self.calculate_metrics(baseline_sessions)
        
        if not current_metrics or not baseline_metrics:
            return {"error": "Insufficient data for comparison"}
        
        # 计算改进百分比
        improvements = {}
        
        current_duration = current_metrics["duration_stats"]["average"]
        baseline_duration = baseline_metrics["duration_stats"]["average"]
        if baseline_duration > 0:
            improvements["duration_improvement"] = ((baseline_duration - current_duration) / baseline_duration) * 100
        
        current_confidence = current_metrics["confidence_stats"]["average"]
        baseline_confidence = baseline_metrics["confidence_stats"]["average"]
        improvements["confidence_improvement"] = ((current_confidence - baseline_confidence) / baseline_confidence) * 100
        
        current_success = current_metrics["success_rate"]
        baseline_success = baseline_metrics["success_rate"]
        improvements["success_rate_improvement"] = ((current_success - baseline_success) / baseline_success) * 100
        
        return {
            "current_metrics": current_metrics,
            "baseline_metrics": baseline_metrics,
            "improvements": improvements,
            "overall_assessment": self._assess_overall_improvement(improvements)
        }
    
    def _assess_overall_improvement(self, improvements: Dict[str, float]) -> str:
        """评估整体改进情况"""
        positive_improvements = [v for v in improvements.values() if v > 0]
        negative_improvements = [v for v in improvements.values() if v < 0]
        
        if len(positive_improvements) >= len(improvements) * 0.7:
            return "significant_improvement"
        elif len(negative_improvements) >= len(improvements) * 0.7:
            return "regression"
        else:
            return "mixed_results"