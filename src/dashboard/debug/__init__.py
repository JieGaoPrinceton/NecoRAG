"""
Debug Panel Module - 可视化调试面板模块
提供思维路径可视化、实时监控和调试工具功能
"""

from .models import DebugSession, EvidenceInfo, DebugQueryRecord
from .websocket import DebugWebSocketManager
from .api import router as DebugAPIRouter
from .analyzer import PathAnalyzer, PerformanceAnalyzer
from .push_service import RealTimePushService
from .history import QueryHistoryManager, QueryTracker, QueryRecord, QueryStatus
from .performance import (
    PerformanceMonitor, ErrorHandler, PerformanceOptimizer,
    performance_monitor, error_handler, performance_optimizer,
    monitor_performance, handle_errors
)
from .enhanced_error_handler import (
    IntelligentErrorHandler, EnhancedErrorInfo,
    ErrorSeverity, ErrorCategory, enhanced_error_handling,
    enhanced_error_handler
)
from .connection import ConnectionManager, ConnectionHealthMonitor, ConnectionState, ConnectionStatus, ConnectionType
from .tuning import ParameterStore, InMemoryParameterStore, ParameterOptimizer, ParameterConfig, ParameterValue, ExperimentConfig, ExperimentResult, ParameterType, OptimizationStrategy
from .path_analyzer import PathAnalyzer as DebugPathAnalyzer, PathSegment, PathAnalysisResult, Bottleneck, PathSegmentType, BottleneckType
from .ab_testing import ABTestingFramework, ABTestConfig, TestVariant, TestResult, TestReport, TestStatus, TestType, StatisticalTest
from .recommendation import RecommendationEngine, OptimizationRule, OptimizationRecommendation, SystemMetrics, PerformancePattern, RecommendationType, PriorityLevel, ConfidenceLevel

__all__ = [
    "DebugSession",
    "EvidenceInfo", 
    "DebugQueryRecord",
    "DebugWebSocketManager",
    "DebugAPIRouter",
    "PathAnalyzer",
    "PerformanceAnalyzer",
    "PerformanceMonitor",
    "ErrorHandler",
    "PerformanceOptimizer",
    "ConnectionManager",
    "InMemoryParameterStore",
    "DebugPathAnalyzer",
    "ABTestingFramework",
    "RecommendationEngine",
    "IntelligentErrorHandler",
    "EnhancedErrorInfo",
    "ErrorSeverity",
    "ErrorCategory",
    "enhanced_error_handling",
    "enhanced_error_handler"
]