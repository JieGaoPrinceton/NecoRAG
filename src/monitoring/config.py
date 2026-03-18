"""
监控配置管理
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel
from enum import Enum


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """指标类型"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"         # 仪表盘
    HISTOGRAM = "histogram" # 直方图
    SUMMARY = "summary"     # 摘要


class MonitoringConfig(BaseModel):
    """监控配置模型"""
    
    # 指标收集配置
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    collection_interval: int = 15  # 秒
    
    # 健康检查配置
    health_check_enabled: bool = True
    health_check_interval: int = 30  # 秒
    health_check_timeout: int = 10   # 秒
    
    # 告警配置
    alerts_enabled: bool = True
    alert_evaluation_interval: int = 60  # 秒
    alert_retention_days: int = 30
    
    # 通知渠道配置
    notification_channels: List[str] = ["console"]  # console, email, webhook, slack
    email_config: Optional[Dict[str, str]] = None
    webhook_urls: List[str] = []
    slack_webhooks: List[str] = []
    
    # 性能阈值配置
    cpu_threshold_warning: float = 80.0    # CPU 使用率警告阈值 (%)
    cpu_threshold_critical: float = 95.0   # CPU 使用率严重阈值 (%)
    memory_threshold_warning: float = 85.0 # 内存使用率警告阈值 (%)
    memory_threshold_critical: float = 95.0 # 内存使用率严重阈值 (%)
    disk_threshold_warning: float = 80.0   # 磁盘使用率警告阈值 (%)
    disk_threshold_critical: float = 95.0  # 磁盘使用率严重阈值 (%)
    
    # 应用特定指标
    rag_response_time_threshold: float = 5.0  # RAG 响应时间阈值 (秒)
    api_error_rate_threshold: float = 5.0     # API 错误率阈值 (%)
    cache_hit_rate_threshold: float = 80.0    # 缓存命中率阈值 (%)


class MonitoringManager:
    """监控管理器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> MonitoringConfig:
        """加载监控配置"""
        return MonitoringConfig(
            metrics_enabled=os.getenv("MONITORING_METRICS_ENABLED", "true").lower() == "true",
            metrics_port=int(os.getenv("MONITORING_METRICS_PORT", "9090")),
            metrics_path=os.getenv("MONITORING_METRICS_PATH", "/metrics"),
            collection_interval=int(os.getenv("MONITORING_COLLECTION_INTERVAL", "15")),
            
            health_check_enabled=os.getenv("MONITORING_HEALTH_CHECK_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.getenv("MONITORING_HEALTH_CHECK_INTERVAL", "30")),
            health_check_timeout=int(os.getenv("MONITORING_HEALTH_CHECK_TIMEOUT", "10")),
            
            alerts_enabled=os.getenv("MONITORING_ALERTS_ENABLED", "true").lower() == "true",
            alert_evaluation_interval=int(os.getenv("MONITORING_ALERT_EVALUATION_INTERVAL", "60")),
            alert_retention_days=int(os.getenv("MONITORING_ALERT_RETENTION_DAYS", "30")),
            
            notification_channels=os.getenv("MONITORING_NOTIFICATION_CHANNELS", "console").split(","),
            
            cpu_threshold_warning=float(os.getenv("MONITORING_CPU_THRESHOLD_WARNING", "80.0")),
            cpu_threshold_critical=float(os.getenv("MONITORING_CPU_THRESHOLD_CRITICAL", "95.0")),
            memory_threshold_warning=float(os.getenv("MONITORING_MEMORY_THRESHOLD_WARNING", "85.0")),
            memory_threshold_critical=float(os.getenv("MONITORING_MEMORY_THRESHOLD_CRITICAL", "95.0")),
            disk_threshold_warning=float(os.getenv("MONITORING_DISK_THRESHOLD_WARNING", "80.0")),
            disk_threshold_critical=float(os.getenv("MONITORING_DISK_THRESHOLD_CRITICAL", "95.0")),
            
            rag_response_time_threshold=float(os.getenv("MONITORING_RAG_RESPONSE_TIME_THRESHOLD", "5.0")),
            api_error_rate_threshold=float(os.getenv("MONITORING_API_ERROR_RATE_THRESHOLD", "5.0")),
            cache_hit_rate_threshold=float(os.getenv("MONITORING_CACHE_HIT_RATE_THRESHOLD", "80.0"))
        )
    
    def get_config(self) -> MonitoringConfig:
        """获取监控配置"""
        return self.config
    
    def update_config(self, new_config: MonitoringConfig) -> None:
        """更新监控配置"""
        self.config = new_config


# 全局监控管理器实例
monitoring_manager = MonitoringManager()


def get_monitoring_config() -> MonitoringConfig:
    """获取监控配置依赖"""
    return monitoring_manager.get_config()