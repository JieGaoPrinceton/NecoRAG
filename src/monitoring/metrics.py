"""
系统指标收集器
"""

import psutil
import time
from typing import Dict, Any, List
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from enum import Enum

from .config import MetricType, get_monitoring_config


@dataclass
class MetricSample:
    """指标样本"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None


class SystemMetrics:
    """系统指标收集"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.samples_buffer = deque(maxlen=1000)  # 保留最近1000个样本
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统级指标"""
        metrics = {}
        
        # CPU 指标
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        metrics.update({
            "cpu_usage_percent": cpu_percent,
            "cpu_count": cpu_count,
            "cpu_frequency_mhz": cpu_freq.current if cpu_freq else 0,
            "cpu_load_avg_1min": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        })
        
        # 内存指标
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        metrics.update({
            "memory_total_bytes": memory.total,
            "memory_available_bytes": memory.available,
            "memory_used_bytes": memory.used,
            "memory_usage_percent": memory.percent,
            "swap_total_bytes": swap.total,
            "swap_used_bytes": swap.used,
            "swap_free_bytes": swap.free,
            "swap_usage_percent": swap.percent
        })
        
        # 磁盘指标
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        metrics.update({
            "disk_total_bytes": disk.total,
            "disk_used_bytes": disk.used,
            "disk_free_bytes": disk.free,
            "disk_usage_percent": disk.percent,
            "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
            "disk_write_bytes": disk_io.write_bytes if disk_io else 0
        })
        
        # 网络指标
        net_io = psutil.net_io_counters()
        
        metrics.update({
            "network_bytes_sent": net_io.bytes_sent,
            "network_bytes_recv": net_io.bytes_recv,
            "network_packets_sent": net_io.packets_sent,
            "network_packets_recv": net_io.packets_recv
        })
        
        # 进程指标
        processes = psutil.process_iter(['pid', 'name', 'status'])
        process_count = len(list(processes))
        
        metrics.update({
            "process_count": process_count,
            "uptime_seconds": time.time() - psutil.boot_time()
        })
        
        return metrics
    
    def collect_python_metrics(self) -> Dict[str, Any]:
        """收集 Python 运行时指标"""
        import gc
        import sys
        
        metrics = {}
        
        # 垃圾回收统计
        gc_stats = gc.get_stats()
        metrics.update({
            "gc_collections": sum(stat['collections'] for stat in gc_stats),
            "gc_collected": sum(stat['collected'] for stat in gc_stats),
            "gc_uncollectable": sum(stat['uncollectable'] for stat in gc_stats)
        })
        
        # 内存使用
        metrics.update({
            "python_memory_rss_bytes": psutil.Process().memory_info().rss,
            "python_memory_vms_bytes": psutil.Process().memory_info().vms
        })
        
        # Python 版本信息
        metrics.update({
            "python_version": sys.version,
            "python_implementation": sys.implementation.name
        })
        
        return metrics
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                     labels: Dict[str, str] = None) -> None:
        """记录指标样本"""
        sample = MetricSample(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        self.samples_buffer.append(sample)
    
    def get_recent_samples(self, metric_name: str = None, limit: int = 100) -> List[MetricSample]:
        """获取最近的指标样本"""
        samples = list(self.samples_buffer)
        if metric_name:
            samples = [s for s in samples if s.name == metric_name]
        return samples[-limit:]
    
    def export_prometheus_format(self) -> str:
        """导出 Prometheus 格式的指标"""
        output = []
        samples = list(self.samples_buffer)
        
        # 按指标名称分组
        metrics_by_name = {}
        for sample in samples:
            if sample.name not in metrics_by_name:
                metrics_by_name[sample.name] = []
            metrics_by_name[sample.name].append(sample)
        
        # 生成 Prometheus 格式
        for name, samples_list in metrics_by_name.items():
            # 添加帮助文本
            output.append(f"# HELP {name} {name} metric")
            
            # 添加类型信息
            output.append(f"# TYPE {name} gauge")
            
            # 添加最新的样本值
            if samples_list:
                latest_sample = samples_list[-1]
                labels_str = ""
                if latest_sample.labels:
                    labels_parts = [f'{k}="{v}"' for k, v in latest_sample.labels.items()]
                    labels_str = "{" + ",".join(labels_parts) + "}"
                
                output.append(f"{name}{labels_str} {latest_sample.value}")
        
        return "\n".join(output)


class ApplicationMetrics:
    """应用级指标收集"""
    
    def __init__(self):
        self.metrics = SystemMetrics()
    
    def record_rag_response_time(self, response_time: float, success: bool = True) -> None:
        """记录 RAG 响应时间"""
        self.metrics.record_metric("rag_response_time_seconds", response_time)
        self.metrics.record_metric("rag_request_success", 1.0 if success else 0.0)
    
    def record_api_call(self, endpoint: str, status_code: int, duration: float) -> None:
        """记录 API 调用"""
        labels = {"endpoint": endpoint, "status_code": str(status_code)}
        self.metrics.record_metric("api_request_duration_seconds", duration, labels=labels)
        self.metrics.record_metric("api_request_count", 1.0, labels=labels)
    
    def record_cache_operation(self, operation: str, hit: bool) -> None:
        """记录缓存操作"""
        labels = {"operation": operation, "result": "hit" if hit else "miss"}
        self.metrics.record_metric("cache_operations", 1.0, labels=labels)
    
    def record_model_inference(self, model_name: str, inference_time: float) -> None:
        """记录模型推理时间"""
        labels = {"model": model_name}
        self.metrics.record_metric("model_inference_time_seconds", inference_time, labels=labels)


# 全局指标收集器实例
system_metrics = SystemMetrics()
app_metrics = ApplicationMetrics()