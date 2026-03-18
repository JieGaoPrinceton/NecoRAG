"""
NecoRAG 监控告警模块
提供系统性能监控、健康检查、指标收集和告警通知功能。
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Monitoring Team"

# 核心监控组件
from .metrics import SystemMetrics, ApplicationMetrics
from .health import HealthChecker, HealthStatus
from .alerts import AlertManager, AlertRule, NotificationChannel
from .dashboard import MonitoringDashboard
from .service import MonitoringService, create_monitoring_app

# 配置管理
from .config import MonitoringConfig, get_monitoring_config

__all__ = [
    # 核心组件
    "SystemMetrics",
    "ApplicationMetrics", 
    "HealthChecker",
    "HealthStatus",
    "AlertManager",
    "AlertRule",
    "NotificationChannel",
    "MonitoringDashboard",
    "MonitoringService",
    "create_monitoring_app",
    
    # 配置管理
    "MonitoringConfig",
    "get_monitoring_config"
]