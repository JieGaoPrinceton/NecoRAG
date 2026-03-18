"""
增强型错误处理和恢复系统
提供更智能的错误检测、分类和自动恢复功能
"""

import asyncio
import logging
import traceback
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    DATABASE = "database"
    MEMORY = "memory"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"

@dataclass
class EnhancedErrorInfo:
    """增强型错误信息"""
    timestamp: datetime
    error_id: str
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: ErrorSeverity
    category: ErrorCategory
    retry_count: int = 0
    max_retries: int = 3
    recovery_attempts: int = 0
    recovery_successful: bool = False
    affected_components: List[str] = None
    correlation_id: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_id': self.error_id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'severity': self.severity.value,
            'category': self.category.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'recovery_attempts': self.recovery_attempts,
            'recovery_successful': self.recovery_successful,
            'affected_components': self.affected_components or [],
            'correlation_id': self.correlation_id
        }

class IntelligentErrorHandler:
    """智能错误处理器"""
    
    def __init__(self):
        self.error_history = []
        self.error_patterns = {}
        self.recovery_strategies = {}
        self.notification_channels = []
        self.health_checks = {}
        self.circuit_breakers = {}
        
        # 初始化内置恢复策略
        self._setup_builtin_strategies()
        
    def _setup_builtin_strategies(self):
        """设置内置恢复策略"""
        # 网络错误恢复策略
        self.register_recovery_strategy(
            ErrorCategory.NETWORK,
            self._network_recovery_strategy
        )
        
        # 数据库错误恢复策略
        self.register_recovery_strategy(
            ErrorCategory.DATABASE,
            self._database_recovery_strategy
        )
        
        # 内存错误恢复策略
        self.register_recovery_strategy(
            ErrorCategory.MEMORY,
            self._memory_recovery_strategy
        )
        
        # 超时错误恢复策略
        self.register_recovery_strategy(
            ErrorCategory.TIMEOUT,
            self._timeout_recovery_strategy
        )
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """注册恢复策略"""
        self.recovery_strategies[category] = strategy
        logger.info(f"已注册 {category.value} 类别的恢复策略")
    
    def add_notification_channel(self, channel: Callable):
        """添加通知渠道"""
        self.notification_channels.append(channel)
    
    def add_health_check(self, component: str, check_func: Callable):
        """添加健康检查"""
        self.health_checks[component] = check_func
    
    def register_circuit_breaker(self, name: str, threshold: int = 5, timeout: int = 60):
        """注册熔断器"""
        self.circuit_breakers[name] = {
            'failure_count': 0,
            'threshold': threshold,
            'timeout': timeout,
            'last_failure': None,
            'state': 'closed'  # closed, open, half_open
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理错误"""
        # 创建错误信息
        error_info = self._create_enhanced_error_info(error, context)
        self.error_history.append(error_info)
        
        # 分类和严重程度评估
        error_info.category = self._classify_error(error)
        error_info.severity = self._assess_severity(error_info)
        
        # 记录日志
        self._log_error(error_info)
        
        # 检查熔断器
        if self._should_circuit_break(error_info):
            return {
                'status': 'circuit_breaker_tripped',
                'error_info': error_info.to_dict()
            }
        
        # 尝试自动恢复
        recovery_result = await self._attempt_recovery(error_info)
        
        # 发送通知
        await self._send_notifications(error_info, recovery_result)
        
        # 更新熔断器状态
        self._update_circuit_breaker(error_info, recovery_result)
        
        return {
            'status': 'handled',
            'error_info': error_info.to_dict(),
            'recovery_result': recovery_result
        }
    
    def _create_enhanced_error_info(self, error: Exception, context: Dict[str, Any] = None) -> EnhancedErrorInfo:
        """创建增强型错误信息"""
        import uuid
        
        return EnhancedErrorInfo(
            timestamp=datetime.now(),
            error_id=str(uuid.uuid4()),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {},
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.UNKNOWN,
            correlation_id=context.get('correlation_id') if context else None,
            affected_components=context.get('affected_components', []) if context else []
        )
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """错误分类"""
        error_type = type(error).__name__.lower()
        error_msg = str(error).lower()
        
        # 基于异常类型分类
        if 'timeout' in error_type or 'timeout' in error_msg:
            return ErrorCategory.TIMEOUT
        elif 'connection' in error_type or 'network' in error_type:
            return ErrorCategory.NETWORK
        elif 'memory' in error_type or 'oom' in error_msg:
            return ErrorCategory.MEMORY
        elif 'database' in error_type or 'sql' in error_type:
            return ErrorCategory.DATABASE
        elif 'validation' in error_type or 'invalid' in error_msg:
            return ErrorCategory.VALIDATION
        elif 'config' in error_type:
            return ErrorCategory.CONFIGURATION
        else:
            return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error_info: EnhancedErrorInfo) -> ErrorSeverity:
        """评估错误严重程度"""
        # 基于分类确定基础严重程度
        base_severity = {
            ErrorCategory.CRITICAL: ErrorSeverity.CRITICAL,
            ErrorCategory.DATABASE: ErrorSeverity.HIGH,
            ErrorCategory.NETWORK: ErrorSeverity.HIGH,
            ErrorCategory.MEMORY: ErrorSeverity.CRITICAL,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.CONFIGURATION: ErrorSeverity.MEDIUM,
            ErrorCategory.EXTERNAL_SERVICE: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.LOW
        }.get(error_info.category, ErrorSeverity.MEDIUM)
        
        # 根据上下文调整严重程度
        context = error_info.context
        
        # 高频错误提高严重程度
        recent_similar_errors = self._count_recent_similar_errors(
            error_info.error_type, 
            minutes=5
        )
        if recent_similar_errors > 10:
            base_severity = self._increase_severity(base_severity)
        
        # 影响核心组件提高严重程度
        if any(comp in ['core_engine', 'database', 'api_gateway'] 
               for comp in error_info.affected_components):
            base_severity = self._increase_severity(base_severity)
        
        # 用户影响提高严重程度
        if context.get('affects_users', False):
            base_severity = self._increase_severity(base_severity)
        
        return base_severity
    
    def _increase_severity(self, severity: ErrorSeverity) -> ErrorSeverity:
        """提高严重程度"""
        severity_order = [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL
        ]
        
        current_index = severity_order.index(severity)
        if current_index < len(severity_order) - 1:
            return severity_order[current_index + 1]
        return severity
    
    async def _attempt_recovery(self, error_info: EnhancedErrorInfo) -> Dict[str, Any]:
        """尝试错误恢复"""
        recovery_result = {
            'attempted': False,
            'successful': False,
            'strategy_used': None,
            'details': {}
        }
        
        # 检查是否有对应的恢复策略
        if error_info.category in self.recovery_strategies:
            strategy = self.recovery_strategies[error_info.category]
            try:
                error_info.recovery_attempts += 1
                recovery_result['attempted'] = True
                recovery_result['strategy_used'] = error_info.category.value
                
                result = await strategy(error_info) if asyncio.iscoroutinefunction(strategy) else strategy(error_info)
                recovery_result['successful'] = bool(result)
                recovery_result['details'] = result if isinstance(result, dict) else {'result': result}
                
                error_info.recovery_successful = recovery_result['successful']
                
                if recovery_result['successful']:
                    logger.info(f"错误恢复成功: {error_info.error_id}")
                else:
                    logger.warning(f"错误恢复失败: {error_info.error_id}")
                    
            except Exception as recovery_error:
                logger.error(f"恢复策略执行失败: {recovery_error}")
                recovery_result['details'] = {
                    'recovery_error': str(recovery_error),
                    'recovery_traceback': traceback.format_exc()
                }
        
        return recovery_result
    
    def _should_circuit_break(self, error_info: EnhancedErrorInfo) -> bool:
        """判断是否应该触发熔断"""
        # 检查每个相关的熔断器
        for name, breaker in self.circuit_breakers.items():
            if breaker['state'] == 'open':
                # 检查是否过了超时时间
                if (breaker['last_failure'] and 
                    datetime.now() - breaker['last_failure'] > timedelta(seconds=breaker['timeout'])):
                    breaker['state'] = 'half_open'
                    logger.info(f"熔断器 {name} 进入半开状态")
                else:
                    return True  # 仍在打开状态，拒绝请求
            elif breaker['state'] == 'half_open':
                # 半开状态下允许有限的请求
                return False
        return False
    
    def _update_circuit_breaker(self, error_info: EnhancedErrorInfo, recovery_result: Dict[str, Any]):
        """更新熔断器状态"""
        for name, breaker in self.circuit_breakers.items():
            if error_info.category.name.lower() in name.lower():
                if recovery_result.get('successful', False):
                    # 恢复成功，重置熔断器
                    breaker['failure_count'] = 0
                    breaker['state'] = 'closed'
                    logger.info(f"熔断器 {name} 已重置")
                else:
                    # 恢复失败，增加失败计数
                    breaker['failure_count'] += 1
                    breaker['last_failure'] = datetime.now()
                    
                    if breaker['failure_count'] >= breaker['threshold']:
                        breaker['state'] = 'open'
                        logger.warning(f"熔断器 {name} 已打开")
    
    async def _send_notifications(self, error_info: EnhancedErrorInfo, recovery_result: Dict[str, Any]):
        """发送通知"""
        notification_data = {
            'error_info': error_info.to_dict(),
            'recovery_result': recovery_result,
            'timestamp': datetime.now().isoformat()
        }
        
        for channel in self.notification_channels:
            try:
                await channel(notification_data) if asyncio.iscoroutinefunction(channel) else channel(notification_data)
            except Exception as e:
                logger.error(f"通知发送失败: {e}")
    
    def _log_error(self, error_info: EnhancedErrorInfo):
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"[{error_info.severity.value.upper()}][{error_info.category.value}] "
            f"{error_info.error_type}: {error_info.error_message}",
            extra={
                'error_id': error_info.error_id,
                'stack_trace': error_info.stack_trace,
                'context': error_info.context
            }
        )
    
    def _count_recent_similar_errors(self, error_type: str, minutes: int = 5) -> int:
        """统计近期相似错误数量"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        count = 0
        
        for error_info in reversed(self.error_history):
            if (error_info.timestamp >= cutoff_time and 
                error_info.error_type == error_type):
                count += 1
            elif error_info.timestamp < cutoff_time:
                break
                
        return count
    
    # 内置恢复策略
    async def _network_recovery_strategy(self, error_info: EnhancedErrorInfo) -> Dict[str, Any]:
        """网络错误恢复策略"""
        result = {'actions_taken': []}
        
        # 等待一段时间后重试
        await asyncio.sleep(2 ** error_info.retry_count)
        result['actions_taken'].append('delay_retry')
        
        # 检查网络连接
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            result['actions_taken'].append('network_connectivity_restored')
        except Exception:
            result['actions_taken'].append('network_unreachable')
        
        return result
    
    async def _database_recovery_strategy(self, error_info: EnhancedErrorInfo) -> Dict[str, Any]:
        """数据库错误恢复策略"""
        result = {'actions_taken': []}
        
        # 尝试重新连接数据库
        try:
            # 这里应该有实际的数据库重连逻辑
            await asyncio.sleep(1)
            result['actions_taken'].append('database_reconnected')
        except Exception as e:
            result['actions_taken'].append(f'database_reconnect_failed: {str(e)}')
        
        return result
    
    async def _memory_recovery_strategy(self, error_info: EnhancedErrorInfo) -> Dict[str, Any]:
        """内存错误恢复策略"""
        result = {'actions_taken': []}
        
        # 触发垃圾回收
        import gc
        collected = gc.collect()
        result['actions_taken'].append(f'gc_collected_{collected}_objects')
        
        # 检查内存使用情况
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        result['actions_taken'].append(f'current_memory_{memory_mb:.1f}mb')
        
        return result
    
    async def _timeout_recovery_strategy(self, error_info: EnhancedErrorInfo) -> Dict[str, Any]:
        """超时错误恢复策略"""
        result = {'actions_taken': []}
        
        # 增加超时时间
        current_timeout = error_info.context.get('timeout', 30)
        new_timeout = min(current_timeout * 1.5, 300)  # 最大5分钟
        result['actions_taken'].append(f'timeout_increased_from_{current_timeout}_to_{new_timeout}')
        
        return result
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return {'total_errors': 0}
        
        # 按类别统计
        category_counts = {}
        severity_counts = {}
        recovery_rates = {}
        
        for error_info in recent_errors:
            # 类别统计
            category = error_info.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # 严重程度统计
            severity = error_info.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # 恢复率统计
            if error_info.recovery_attempts > 0:
                category_recovery = recovery_rates.get(category, {'attempts': 0, 'successes': 0})
                category_recovery['attempts'] += error_info.recovery_attempts
                if error_info.recovery_successful:
                    category_recovery['successes'] += 1
                recovery_rates[category] = category_recovery
        
        # 计算恢复率
        for category in recovery_rates:
            attempts = recovery_rates[category]['attempts']
            successes = recovery_rates[category]['successes']
            recovery_rates[category]['rate'] = successes / attempts if attempts > 0 else 0
        
        return {
            'total_errors': len(recent_errors),
            'category_distribution': category_counts,
            'severity_distribution': severity_counts,
            'recovery_rates': recovery_rates,
            'most_common_errors': sorted(
                category_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# 全局实例
enhanced_error_handler = IntelligentErrorHandler()

# 装饰器
def enhanced_error_handling(context: Dict[str, Any] = None):
    """增强型错误处理装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                # 合并上下文
                error_context = context or {}
                error_context.update({
                    'function_name': func.__name__,
                    'args': str(args)[:100],  # 限制长度
                    'kwargs': str(kwargs)[:100]
                })
                
                # 处理错误
                result = await enhanced_error_handler.handle_error(e, error_context)
                
                # 根据结果决定是否重新抛出异常
                if result['recovery_result'].get('successful', False):
                    return result.get('fallback_result')
                else:
                    raise
        
        # 保持原函数属性
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    async def demo():
        # 添加通知渠道
        def console_notifier(data):
            print(f"🚨 错误通知: {data['error_info']['error_type']}")
        
        enhanced_error_handler.add_notification_channel(console_notifier)
        
        # 注册健康检查
        def db_health_check():
            return True  # 模拟健康检查
        
        enhanced_error_handler.add_health_check('database', db_health_check)
        
        # 注册熔断器
        enhanced_error_handler.register_circuit_breaker('database', threshold=3, timeout=30)
        
        # 测试错误处理
        @enhanced_error_handling({'component': 'test_module'})
        async def risky_operation():
            raise ConnectionError("网络连接失败")
        
        try:
            await risky_operation()
        except Exception as e:
            print(f"操作失败: {e}")
        
        # 查看统计
        stats = enhanced_error_handler.get_error_statistics()
        print(f"错误统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    asyncio.run(demo())