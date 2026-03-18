"""
性能监控和错误处理模块
提供系统性能监控、错误捕获和恢复机制
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import traceback
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    
    # 新增的详细指标
    cpu_cores: int = 0
    memory_total: int = 0  # bytes
    memory_available: int = 0  # bytes
    disk_usage_percent: float = 0.0
    disk_free_space: int = 0  # bytes
    network_packets_sent: int = 0
    network_packets_recv: int = 0
    load_average_1min: float = 0.0
    load_average_5min: float = 0.0
    load_average_15min: float = 0.0
    thread_count: int = 0
    process_count: int = 0
    file_descriptor_count: int = 0
    swap_percent: float = 0.0
    swap_used: int = 0  # bytes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'cpu_cores': self.cpu_cores,
            'memory_percent': self.memory_percent,
            'memory_total': self.memory_total,
            'memory_available': self.memory_available,
            'disk_io_read': self.disk_io_read,
            'disk_io_write': self.disk_io_write,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_free_space': self.disk_free_space,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'network_packets_sent': self.network_packets_sent,
            'network_packets_recv': self.network_packets_recv,
            'active_connections': self.active_connections,
            'load_average_1min': self.load_average_1min,
            'load_average_5min': self.load_average_5min,
            'load_average_15min': self.load_average_15min,
            'thread_count': self.thread_count,
            'process_count': self.process_count,
            'file_descriptor_count': self.file_descriptor_count,
            'swap_percent': self.swap_percent,
            'swap_used': self.swap_used,
            'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            'error_count': self.error_count
        }

@dataclass
class ErrorInfo:
    """错误信息数据类"""
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: str  # 'low', 'medium', 'high', 'critical'
    handled: bool = False
    recovery_attempted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'severity': self.severity,
            'handled': self.handled,
            'recovery_attempted': self.recovery_attempted
        }

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.metrics_history: deque = deque(maxlen=3600)  # 1小时的历史数据
        self.current_metrics: Optional[PerformanceMetrics] = None
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # 系统资源基准值
        self.baseline_cpu = 0.0
        self.baseline_memory = 0.0
        
        # 性能阈值
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'response_time_warning': 1000.0,  # ms
            'response_time_critical': 5000.0  # ms
        }
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        
    async def start_monitoring(self):
        """启动性能监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.baseline_cpu = psutil.cpu_percent(interval=1)
        self.baseline_memory = psutil.virtual_memory().percent
        
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("性能监控已启动")
    
    async def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("性能监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        last_net_io = psutil.net_io_counters()
        last_disk_io = psutil.disk_io_counters()
        
        while self.is_monitoring:
            try:
                # 收集系统指标
                current_time = datetime.now()
                cpu_percent = psutil.cpu_percent(interval=None)
                cpu_cores = psutil.cpu_count()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                # 获取负载平均值（Unix/Linux系统）
                try:
                    load_avg = psutil.getloadavg()
                    load_1min, load_5min, load_15min = load_avg
                except AttributeError:
                    # Windows系统不支持getloadavg
                    load_1min = load_5min = load_15min = 0.0
                
                # 获取进程相关信息
                current_process = psutil.Process()
                thread_count = current_process.num_threads()
                file_descriptors = current_process.num_fds() if hasattr(current_process, 'num_fds') else 0
                
                # 获取系统进程总数
                process_count = len(psutil.pids())
                
                # 获取交换分区信息
                try:
                    swap = psutil.swap_memory()
                    swap_percent = swap.percent
                    swap_used = swap.used
                except Exception:
                    swap_percent = 0.0
                    swap_used = 0
                
                # 计算IO差异
                disk_read_diff = disk_io.read_bytes - last_disk_io.read_bytes
                disk_write_diff = disk_io.write_bytes - last_disk_io.write_bytes
                net_sent_diff = net_io.bytes_sent - last_net_io.bytes_sent
                net_recv_diff = net_io.bytes_recv - last_net_io.bytes_recv
                packets_sent_diff = net_io.packets_sent - last_net_io.packets_sent
                packets_recv_diff = net_io.packets_recv - last_net_io.packets_recv
                
                # 创建性能指标对象
                metrics = PerformanceMetrics(
                    timestamp=current_time,
                    cpu_percent=cpu_percent,
                    cpu_cores=cpu_cores,
                    memory_percent=memory.percent,
                    memory_total=memory.total,
                    memory_available=memory.available,
                    disk_io_read=disk_read_diff,
                    disk_io_write=disk_write_diff,
                    disk_usage_percent=disk.percent,
                    disk_free_space=disk.free,
                    network_bytes_sent=net_sent_diff,
                    network_bytes_recv=net_recv_diff,
                    network_packets_sent=packets_sent_diff,
                    network_packets_recv=packets_recv_diff,
                    active_connections=len(psutil.net_connections()),
                    load_average_1min=load_1min,
                    load_average_5min=load_5min,
                    load_average_15min=load_15min,
                    thread_count=thread_count,
                    process_count=process_count,
                    file_descriptor_count=file_descriptors,
                    swap_percent=swap_percent,
                    swap_used=swap_used
                )
                
                self.current_metrics = metrics
                self.metrics_history.append(metrics)
                
                # 检查性能阈值并触发告警
                await self._check_thresholds(metrics)
                
                # 更新上次读数
                last_disk_io = disk_io
                last_net_io = net_io
                
                await asyncio.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"性能监控循环出错: {e}")
                await asyncio.sleep(self.sample_interval)
    
    async def _check_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值并触发告警"""
        alerts = []
        
        # CPU使用率检查
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            alerts.append({
                'type': 'cpu',
                'level': 'critical',
                'message': f'CPU使用率过高: {metrics.cpu_percent:.1f}%'
            })
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f'CPU使用率偏高: {metrics.cpu_percent:.1f}%'
            })
        
        # 内存使用率检查
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            alerts.append({
                'type': 'memory',
                'level': 'critical',
                'message': f'内存使用率过高: {metrics.memory_percent:.1f}%'
            })
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'内存使用率偏高: {metrics.memory_percent:.1f}%'
            })
        
        # 响应时间检查
        if metrics.response_times:
            avg_response_time = sum(metrics.response_times) / len(metrics.response_times)
            if avg_response_time >= self.thresholds['response_time_critical']:
                alerts.append({
                    'type': 'response_time',
                    'level': 'critical',
                    'message': f'响应时间过长: {avg_response_time:.1f}ms'
                })
            elif avg_response_time >= self.thresholds['response_time_warning']:
                alerts.append({
                    'type': 'response_time',
                    'level': 'warning',
                    'message': f'响应时间较长: {avg_response_time:.1f}ms'
                })
        
        # 触发告警回调
        if alerts:
            for alert in alerts:
                await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """触发告警"""
        logger.warning(f"[{alert['level'].upper()}] {alert['message']}")
        
        # 调用所有告警回调函数
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable):
        """移除告警回调函数"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        return self.current_metrics
    
    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """获取指定时间范围内的历史指标"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        recent_metrics = self.get_metrics_history(60)  # 最近1小时
        
        if not recent_metrics:
            return {'status': 'no_recent_data'}
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        response_times = []
        for m in recent_metrics:
            response_times.extend(m.response_times)
        
        report = {
            'status': 'ok',
            'period_start': recent_metrics[0].timestamp.isoformat(),
            'period_end': recent_metrics[-1].timestamp.isoformat(),
            'sample_count': len(recent_metrics),
            'cpu': {
                'current': self.current_metrics.cpu_percent if self.current_metrics else 0,
                'average': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'baseline': self.baseline_cpu
            },
            'memory': {
                'current': self.current_metrics.memory_percent if self.current_metrics else 0,
                'average': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'baseline': self.baseline_memory
            },
            'response_time': {
                'average': sum(response_times) / len(response_times) if response_times else 0,
                'count': len(response_times)
            } if response_times else {'average': 0, 'count': 0}
        }
        
        return report

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.error_history: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recovery_strategies: Dict[str, Callable] = {}
        self.notification_callbacks: List[Callable] = []
        
        # 错误严重程度映射
        self.severity_mapping = {
            'ValueError': 'medium',
            'TypeError': 'medium',
            'KeyError': 'medium',
            'AttributeError': 'medium',
            'ConnectionError': 'high',
            'TimeoutError': 'high',
            'MemoryError': 'critical',
            'SystemExit': 'critical'
        }
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """注册错误恢复策略"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"已注册 {error_type} 的恢复策略")
    
    def add_notification_callback(self, callback: Callable):
        """添加通知回调函数"""
        self.notification_callbacks.append(callback)
    
    def remove_notification_callback(self, callback: Callable):
        """移除通知回调函数"""
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """处理错误"""
        error_info = self._create_error_info(error, context)
        self.error_history.append(error_info)
        self.error_counts[type(error).__name__] += 1
        
        # 记录错误日志
        logger.error(
            f"[{error_info.severity.upper()}] {error_info.error_type}: {error_info.error_message}",
            extra={'stack_trace': error_info.stack_trace, 'context': error_info.context}
        )
        
        # 尝试自动恢复
        recovery_success = await self._attempt_recovery(error_info)
        error_info.recovery_attempted = True
        error_info.handled = recovery_success
        
        # 发送通知
        await self._send_notifications(error_info)
        
        return recovery_success
    
    def _create_error_info(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """创建错误信息对象"""
        error_type = type(error).__name__
        severity = self.severity_mapping.get(error_type, 'low')
        
        return ErrorInfo(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {},
            severity=severity
        )
    
    async def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """尝试错误恢复"""
        error_type = error_info.error_type
        
        # 查找对应的恢复策略
        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                result = await strategy(error_info) if asyncio.iscoroutinefunction(strategy) else strategy(error_info)
                logger.info(f"{error_type} 恢复策略执行{'成功' if result else '失败'}")
                return bool(result)
            except Exception as e:
                logger.error(f"恢复策略执行失败: {e}")
                return False
        
        # 默认恢复策略
        return await self._default_recovery(error_info)
    
    async def _default_recovery(self, error_info: ErrorInfo) -> bool:
        """默认恢复策略"""
        # 对于临时性错误，简单的重试可能有效
        if error_info.severity in ['low', 'medium']:
            logger.info(f"对 {error_info.error_type} 执行默认恢复策略")
            await asyncio.sleep(1)  # 短暂等待后重试
            return True
        return False
    
    async def _send_notifications(self, error_info: ErrorInfo):
        """发送错误通知"""
        for callback in self.notification_callbacks:
            try:
                await callback(error_info.to_dict())
            except Exception as e:
                logger.error(f"通知回调执行失败: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {'total_errors': 0}
        
        # 按类型统计
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        recent_errors = []
        
        # 统计最近24小时的错误
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for error_info in self.error_history:
            type_counts[error_info.error_type] += 1
            severity_counts[error_info.severity] += 1
            
            if error_info.timestamp >= cutoff_time:
                recent_errors.append(error_info)
        
        return {
            'total_errors': len(self.error_history),
            'recent_24h_errors': len(recent_errors),
            'error_types': dict(type_counts),
            'severity_distribution': dict(severity_counts),
            'most_common_errors': sorted(
                type_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
    
    def get_error_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取错误历史记录"""
        recent_errors = list(self.error_history)[-limit:]
        return [error.to_dict() for error in reversed(recent_errors)]

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_rules = []
        self.optimization_history = []
    
    def add_optimization_rule(self, name: str, condition: Callable, action: Callable):
        """添加优化规则"""
        self.optimization_rules.append({
            'name': name,
            'condition': condition,
            'action': action,
            'enabled': True
        })
    
    async def run_optimization_cycle(self, metrics: PerformanceMetrics):
        """运行优化周期"""
        optimizations_applied = []
        
        for rule in self.optimization_rules:
            if not rule['enabled']:
                continue
                
            try:
                # 检查优化条件
                if await rule['condition'](metrics) if asyncio.iscoroutinefunction(rule['condition']) else rule['condition'](metrics):
                    # 执行优化动作
                    result = await rule['action'](metrics) if asyncio.iscoroutinefunction(rule['action']) else rule['action'](metrics)
                    
                    optimization_record = {
                        'timestamp': datetime.now().isoformat(),
                        'rule_name': rule['name'],
                        'result': result
                    }
                    optimizations_applied.append(optimization_record)
                    self.optimization_history.append(optimization_record)
                    
                    logger.info(f"应用优化规则: {rule['name']}")
                    
            except Exception as e:
                logger.error(f"优化规则 {rule['name']} 执行失败: {e}")
        
        return optimizations_applied
    
    def get_optimization_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history[-limit:]

# 全局实例
performance_monitor = PerformanceMonitor()
error_handler = ErrorHandler()
performance_optimizer = PerformanceOptimizer()

# 装饰器
def monitor_performance(func):
    """性能监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            # 记录响应时间
            if performance_monitor.current_metrics:
                performance_monitor.current_metrics.response_times.append(response_time)
    
    # 保持原函数属性
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return wrapper

def handle_errors(context: Dict[str, Any] = None):
    """错误处理装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                await error_handler.handle_error(e, context)
                raise
        
        # 保持原函数属性
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    return decorator

# 使用示例和测试
if __name__ == "__main__":
    async def main():
        # 启动性能监控
        await performance_monitor.start_monitoring()
        
        # 注册错误处理回调
        def alert_callback(alert):
            print(f"告警: {alert}")
        
        performance_monitor.add_alert_callback(alert_callback)
        
        # 模拟一些操作
        @monitor_performance
        @handle_errors({'operation': 'test_operation'})
        async def test_operation():
            await asyncio.sleep(0.1)
            if time.time() % 5 < 1:  # 偶尔抛出异常
                raise ValueError("测试错误")
            return "success"
        
        # 运行测试
        for i in range(20):
            try:
                result = await test_operation()
                print(f"操作结果: {result}")
            except Exception as e:
                print(f"操作失败: {e}")
            await asyncio.sleep(1)
        
        # 显示统计信息
        print("\n=== 性能报告 ===")
        report = performance_monitor.get_performance_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
        print("\n=== 错误统计 ===")
        error_stats = error_handler.get_error_statistics()
        print(json.dumps(error_stats, indent=2, ensure_ascii=False))
        
        # 停止监控
        await performance_monitor.stop_monitoring()
    
    asyncio.run(main())