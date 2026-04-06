"""
健康检查系统
"""

from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
import asyncio
import logging

from .config import AlertLevel


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"      # 健康
    DEGRADED = "degraded"    # 降级
    UNHEALTHY = "unhealthy"  # 不健康
    UNKNOWN = "unknown"      # 未知


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None
    duration_ms: float = 0.0


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results_history: List[HealthCheckResult] = []
        self.logger = logging.getLogger(__name__)
    
    def register_check(self, name: str, check_func: Callable, critical: bool = True):
        """注册健康检查函数"""
        self.checks[name] = {
            'func': check_func,
            'critical': critical
        }
    
    async def run_single_check(self, name: str) -> HealthCheckResult:
        """运行单个健康检查"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"未知的健康检查: {name}",
                timestamp=datetime.utcnow()
            )
        
        check_info = self.checks[name]
        start_time = datetime.utcnow()
        
        try:
            result = await check_info['func']()
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 解析检查结果
            if isinstance(result, dict):
                status = result.get('status', HealthStatus.UNKNOWN)
                message = result.get('message', '')
                details = result.get('details', {})
            elif isinstance(result, tuple) and len(result) >= 2:
                status, message = result[:2]
                details = result[2] if len(result) > 2 else {}
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "检查通过" if result else "检查失败"
                details = {}
            
            # 转换状态字符串为枚举
            if isinstance(status, str):
                try:
                    status = HealthStatus(status.lower())
                except ValueError:
                    status = HealthStatus.UNKNOWN
            
            return HealthCheckResult(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                details=details,
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.error(f"健康检查 {name} 执行失败: {str(e)}")
            
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"检查执行异常: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration
            )
    
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """运行所有健康检查"""
        results = []
        tasks = [self.run_single_check(name) for name in self.checks.keys()]
        
        # 并发执行所有检查
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(self.checks.keys(), check_results):
            if isinstance(result, Exception):
                result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"检查执行异常: {str(result)}",
                    timestamp=datetime.utcnow()
                )
            results.append(result)
        
        # 保存历史记录
        self.results_history.extend(results)
        # 保留最近1000条记录
        self.results_history = self.results_history[-1000:]
        
        return results
    
    def get_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """获取整体健康状态"""
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in results]
        
        # 如果有任何关键检查失败，则整体不健康
        critical_checks = [name for name, info in self.checks.items() if info['critical']]
        critical_results = [r for r in results if r.name in critical_checks]
        
        if any(r.status == HealthStatus.UNHEALTHY for r in critical_results):
            return HealthStatus.UNHEALTHY
        
        # 如果有任何检查降级，则整体降级
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED
        
        # 如果所有检查都健康，则整体健康
        if all(r.status == HealthStatus.HEALTHY for r in results):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        recent_results = self.get_recent_results(limit=1)
        if not recent_results:
            return {"status": HealthStatus.UNKNOWN.value, "checks": []}
        
        latest_results = recent_results[0]
        overall_status = self.get_overall_status(latest_results)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [
                {
                    "name": result.name,
                    "status": result.status.value,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                    "details": result.details
                }
                for result in latest_results
            ],
            "summary": {
                "total": len(latest_results),
                "healthy": len([r for r in latest_results if r.status == HealthStatus.HEALTHY]),
                "degraded": len([r for r in latest_results if r.status == HealthStatus.DEGRADED]),
                "unhealthy": len([r for r in latest_results if r.status == HealthStatus.UNHEALTHY])
            }
        }
    
    def get_recent_results(self, limit: int = 10) -> List[List[HealthCheckResult]]:
        """获取最近的检查结果历史"""
        # 按时间分组结果
        grouped_results = {}
        for result in reversed(self.results_history[-limit*len(self.checks):]):
            timestamp_key = result.timestamp.replace(second=0, microsecond=0)
            if timestamp_key not in grouped_results:
                grouped_results[timestamp_key] = []
            grouped_results[timestamp_key].append(result)
        
        # 返回按时间排序的结果组
        sorted_groups = sorted(grouped_results.items(), key=lambda x: x[0], reverse=True)
        return [group[1] for group in sorted_groups[:limit]]
    
    def clear_history(self):
        """清空历史记录"""
        self.results_history.clear()


# 预定义的健康检查函数
async def check_database_connection() -> Dict[str, Any]:
    """检查数据库连接"""
    try:
        # 这里应该实际检查数据库连接
        # 模拟检查
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return {
            "status": HealthStatus.HEALTHY,
            "message": "数据库连接正常",
            "details": {"connection_time_ms": 100}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"数据库连接失败: {str(e)}",
            "details": {"error": str(e)}
        }

async def check_redis_connection() -> Dict[str, Any]:
    """检查 Redis 连接"""
    try:
        # 模拟 Redis 检查
        await asyncio.sleep(0.05)
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Redis 连接正常",
            "details": {"ping_time_ms": 50}
        }
    except Exception as e:
        return {
            "status": HealthStatus.DEGRADED,
            "message": f"Redis 连接缓慢: {str(e)}",
            "details": {"error": str(e)}
        }

async def check_llm_service() -> Dict[str, Any]:
    """检查 LLM 服务"""
    try:
        # 模拟 LLM 服务检查
        await asyncio.sleep(0.2)
        return {
            "status": HealthStatus.HEALTHY,
            "message": "LLM 服务正常",
            "details": {"response_time_ms": 200}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"LLM 服务不可用: {str(e)}",
            "details": {"error": str(e)}
        }

async def check_disk_space() -> Dict[str, Any]:
    """检查磁盘空间"""
    import shutil
    try:
        total, used, free = shutil.disk_usage("/")
        usage_percent = (used / total) * 100
        
        if usage_percent > 90:
            status = HealthStatus.UNHEALTHY
            message = "磁盘空间不足"
        elif usage_percent > 80:
            status = HealthStatus.DEGRADED
            message = "磁盘空间紧张"
        else:
            status = HealthStatus.HEALTHY
            message = "磁盘空间充足"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round(usage_percent, 2)
            }
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNKNOWN,
            "message": f"无法检查磁盘空间: {str(e)}",
            "details": {"error": str(e)}
        }


# 全局健康检查器实例
health_checker = HealthChecker()

# 注册默认健康检查
health_checker.register_check("database", check_database_connection, critical=True)
health_checker.register_check("redis", check_redis_connection, critical=True)
health_checker.register_check("llm_service", check_llm_service, critical=True)
health_checker.register_check("disk_space", check_disk_space, critical=False)