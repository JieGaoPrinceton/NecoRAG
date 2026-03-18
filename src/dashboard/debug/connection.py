"""
连接状态管理器 - Connection Status Manager
管理WebSocket连接状态、健康检查和故障恢复
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """连接状态枚举"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ConnectionType(str, Enum):
    """连接类型枚举"""
    DEBUG_PANEL = "debug_panel"
    THINKING_PATH = "thinking_path"
    PERFORMANCE = "performance"
    QUERY_HISTORY = "query_history"


@dataclass
class ConnectionState:
    """连接状态数据模型"""
    client_id: str
    connection_type: ConnectionType
    status: ConnectionStatus
    connect_time: datetime
    last_activity: datetime
    disconnect_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 5
    reconnect_delay: float = 1.0  # 秒
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['connect_time'] = self.connect_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        if self.disconnect_time:
            data['disconnect_time'] = self.disconnect_time.isoformat()
        data['connection_type'] = self.connection_type.value
        data['status'] = self.status.value
        return data


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    client_id: str
    status: ConnectionStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['checked_at'] = self.checked_at.isoformat()
        data['status'] = self.status.value
        return data


class ConnectionHealthMonitor:
    """连接健康监控器"""
    
    def __init__(self, check_interval: float = 30.0):
        """
        初始化健康监控器
        
        Args:
            check_interval: 健康检查间隔（秒）
        """
        self.check_interval = check_interval
        self.health_checks: Dict[str, List[HealthCheckResult]] = {}
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_checkers: Dict[ConnectionType, Callable] = {}
        self.alert_handlers: List[Callable] = []
        
        # 注册默认健康检查器
        self._register_default_checkers()
    
    def _register_default_checkers(self):
        """注册默认健康检查器"""
        self.register_health_checker(ConnectionType.DEBUG_PANEL, self._check_debug_panel)
        self.register_health_checker(ConnectionType.THINKING_PATH, self._check_thinking_path)
        self.register_health_checker(ConnectionType.PERFORMANCE, self._check_performance)
        self.register_health_checker(ConnectionType.QUERY_HISTORY, self._check_query_history)
    
    def register_health_checker(self, conn_type: ConnectionType, checker_func: Callable):
        """
        注册健康检查器
        
        Args:
            conn_type: 连接类型
            checker_func: 检查函数
        """
        self.health_checkers[conn_type] = checker_func
        logger.info(f"注册健康检查器: {conn_type.value}")
    
    def add_alert_handler(self, handler: Callable):
        """
        添加告警处理器
        
        Args:
            handler: 告警处理函数
        """
        self.alert_handlers.append(handler)
    
    async def start_monitoring(self):
        """开始健康监控"""
        if self.is_monitoring:
            logger.warning("健康监控已在运行中")
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("开始连接健康监控")
    
    async def stop_monitoring(self):
        """停止健康监控"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("停止连接健康监控")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 对所有连接执行健康检查
                await self._perform_health_checks()
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康监控循环出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        # 这里应该遍历所有活动连接并执行检查
        # 由于我们没有实际的连接列表，这里只是示例
        pass
    
    async def _check_debug_panel(self, client_id: str) -> HealthCheckResult:
        """检查调试面板连接"""
        # 实现具体的健康检查逻辑
        return HealthCheckResult(
            client_id=client_id,
            status=ConnectionStatus.CONNECTED,
            response_time_ms=50.0
        )
    
    async def _check_thinking_path(self, client_id: str) -> HealthCheckResult:
        """检查思维路径连接"""
        return HealthCheckResult(
            client_id=client_id,
            status=ConnectionStatus.CONNECTED,
            response_time_ms=75.0
        )
    
    async def _check_performance(self, client_id: str) -> HealthCheckResult:
        """检查性能监控连接"""
        return HealthCheckResult(
            client_id=client_id,
            status=ConnectionStatus.CONNECTED,
            response_time_ms=40.0
        )
    
    async def _check_query_history(self, client_id: str) -> HealthCheckResult:
        """检查查询历史连接"""
        return HealthCheckResult(
            client_id=client_id,
            status=ConnectionStatus.CONNECTED,
            response_time_ms=60.0
        )
    
    async def record_health_check(self, result: HealthCheckResult):
        """
        记录健康检查结果
        
        Args:
            result: 健康检查结果
        """
        if result.client_id not in self.health_checks:
            self.health_checks[result.client_id] = []
        
        self.health_checks[result.client_id].append(result)
        
        # 保留最近100次检查结果
        if len(self.health_checks[result.client_id]) > 100:
            self.health_checks[result.client_id] = self.health_checks[result.client_id][-100:]
        
        # 如果检查失败，触发告警
        if result.status != ConnectionStatus.CONNECTED:
            await self._trigger_health_alert(result)
    
    async def _trigger_health_alert(self, result: HealthCheckResult):
        """触发健康告警"""
        alert_message = f"连接 {result.client_id} 健康检查失败: {result.status.value}"
        if result.error_message:
            alert_message += f" - {result.error_message}"
        
        logger.warning(alert_message)
        
        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                await handler({
                    "type": "health_alert",
                    "client_id": result.client_id,
                    "status": result.status.value,
                    "message": alert_message,
                    "timestamp": result.checked_at.isoformat()
                })
            except Exception as e:
                logger.error(f"健康告警处理器执行失败: {e}")
    
    async def get_client_health(self, client_id: str, hours: int = 1) -> Dict[str, any]:
        """
        获取客户端健康状况
        
        Args:
            client_id: 客户端ID
            hours: 时间范围（小时）
            
        Returns:
            健康状况统计
        """
        if client_id not in self.health_checks:
            return {"status": "unknown", "checks": 0}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [
            check for check in self.health_checks[client_id]
            if check.checked_at >= cutoff_time
        ]
        
        if not recent_checks:
            return {"status": "no_data", "checks": 0}
        
        # 统计状态分布
        status_counts = {}
        total_response_time = 0
        successful_checks = 0
        
        for check in recent_checks:
            status = check.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if check.response_time_ms is not None:
                total_response_time += check.response_time_ms
                successful_checks += 1
        
        # 确定总体状态
        connected_checks = status_counts.get("connected", 0)
        total_checks = len(recent_checks)
        success_rate = connected_checks / total_checks if total_checks > 0 else 0
        
        if success_rate >= 0.95:
            overall_status = "healthy"
        elif success_rate >= 0.8:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "total_checks": total_checks,
            "status_distribution": status_counts,
            "avg_response_time": total_response_time / successful_checks if successful_checks > 0 else 0,
            "last_check": recent_checks[-1].to_dict() if recent_checks else None
        }


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self, max_connections: int = 1000):
        """
        初始化连接管理器
        
        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self.connections: Dict[str, ConnectionState] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> {client_ids}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> {client_ids}
        self.connection_lock = asyncio.Lock()
        self.health_monitor = ConnectionHealthMonitor()
        
        # 事件处理器
        self.event_handlers: Dict[str, List[Callable]] = {
            "connection_opened": [],
            "connection_closed": [],
            "connection_failed": [],
            "connection_recovered": []
        }
    
    async def add_connection(self, 
                           client_id: str,
                           connection_type: ConnectionType,
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None,
                           metadata: Optional[Dict[str, any]] = None) -> bool:
        """
        添加连接
        
        Args:
            client_id: 客户端ID
            connection_type: 连接类型
            user_id: 用户ID
            session_id: 会话ID
            ip_address: IP地址
            user_agent: 用户代理
            metadata: 元数据
            
        Returns:
            是否成功添加
        """
        async with self.connection_lock:
            # 检查连接数限制
            if len(self.connections) >= self.max_connections:
                logger.warning(f"达到最大连接数限制: {self.max_connections}")
                return False
            
            # 创建连接状态
            connection_state = ConnectionState(
                client_id=client_id,
                connection_type=connection_type,
                status=ConnectionStatus.CONNECTING,
                connect_time=datetime.now(),
                last_activity=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.connections[client_id] = connection_state
            
            # 更新用户和会话映射
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(client_id)
            
            if session_id:
                if session_id not in self.session_connections:
                    self.session_connections[session_id] = set()
                self.session_connections[session_id].add(client_id)
            
            logger.info(f"添加连接: {client_id} ({connection_type.value})")
            
            # 触发连接打开事件
            await self._trigger_event("connection_opened", connection_state.to_dict())
            
            return True
    
    async def update_connection_status(self, client_id: str, status: ConnectionStatus):
        """
        更新连接状态
        
        Args:
            client_id: 客户端ID
            status: 新状态
        """
        async with self.connection_lock:
            if client_id in self.connections:
                old_status = self.connections[client_id].status
                self.connections[client_id].status = status
                self.connections[client_id].last_activity = datetime.now()
                
                # 记录断开时间
                if status in [ConnectionStatus.DISCONNECTED, ConnectionStatus.FAILED, ConnectionStatus.TIMEOUT]:
                    self.connections[client_id].disconnect_time = datetime.now()
                
                logger.info(f"更新连接状态: {client_id} {old_status.value} -> {status.value}")
                
                # 触发相应事件
                if status == ConnectionStatus.CONNECTED and old_status != ConnectionStatus.CONNECTED:
                    await self._trigger_event("connection_recovered", self.connections[client_id].to_dict())
                elif status in [ConnectionStatus.DISCONNECTED, ConnectionStatus.FAILED]:
                    await self._trigger_event("connection_closed", self.connections[client_id].to_dict())
    
    async def remove_connection(self, client_id: str):
        """
        移除连接
        
        Args:
            client_id: 客户端ID
        """
        async with self.connection_lock:
            if client_id in self.connections:
                connection = self.connections[client_id]
                
                # 从映射中移除
                if connection.user_id and connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(client_id)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]
                
                if connection.session_id and connection.session_id in self.session_connections:
                    self.session_connections[connection.session_id].discard(client_id)
                    if not self.session_connections[connection.session_id]:
                        del self.session_connections[connection.session_id]
                
                del self.connections[client_id]
                logger.info(f"移除连接: {client_id}")
                
                # 触发连接关闭事件
                await self._trigger_event("connection_closed", connection.to_dict())
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """
        添加事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    async def _trigger_event(self, event_type: str, data: Dict[str, any]):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"事件处理器执行失败 {event_type}: {e}")
    
    async def get_connection_stats(self) -> Dict[str, any]:
        """获取连接统计信息"""
        async with self.connection_lock:
            total_connections = len(self.connections)
            
            # 按状态统计
            status_counts = {}
            type_counts = {}
            
            for connection in self.connections.values():
                status = connection.status.value
                conn_type = connection.connection_type.value
                
                status_counts[status] = status_counts.get(status, 0) + 1
                type_counts[conn_type] = type_counts.get(conn_type, 0) + 1
            
            # 按用户统计
            users_count = len(self.user_connections)
            sessions_count = len(self.session_connections)
            
            return {
                "total_connections": total_connections,
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "users_count": users_count,
                "sessions_count": sessions_count,
                "max_connections": self.max_connections,
                "utilization_rate": total_connections / self.max_connections if self.max_connections > 0 else 0
            }
    
    async def get_user_connections(self, user_id: str) -> List[ConnectionState]:
        """
        获取用户的所有连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            连接状态列表
        """
        async with self.connection_lock:
            if user_id not in self.user_connections:
                return []
            
            client_ids = self.user_connections[user_id]
            return [self.connections[cid] for cid in client_ids if cid in self.connections]
    
    async def cleanup_inactive_connections(self, inactive_minutes: int = 30):
        """
        清理不活跃连接
        
        Args:
            inactive_minutes: 不活跃时间阈值（分钟）
        """
        cutoff_time = datetime.now() - timedelta(minutes=inactive_minutes)
        inactive_clients = []
        
        async with self.connection_lock:
            for client_id, connection in self.connections.items():
                if connection.last_activity < cutoff_time:
                    inactive_clients.append(client_id)
            
            # 移除不活跃连接
            for client_id in inactive_clients:
                await self.remove_connection(client_id)
        
        if inactive_clients:
            logger.info(f"清理了 {len(inactive_clients)} 个不活跃连接")


# 使用示例和测试函数
async def demo_connection_management():
    """演示连接管理功能"""
    
    # 创建连接管理器
    conn_manager = ConnectionManager(max_connections=100)
    
    # 添加事件处理器
    async def connection_handler(event_data):
        print(f"🔌 连接事件: {event_data}")
    
    conn_manager.add_event_handler("connection_opened", connection_handler)
    conn_manager.add_event_handler("connection_closed", connection_handler)
    
    # 添加一些连接
    await conn_manager.add_connection(
        client_id="client_001",
        connection_type=ConnectionType.DEBUG_PANEL,
        user_id="user_001",
        session_id="session_001",
        ip_address="192.168.1.100"
    )
    
    await conn_manager.add_connection(
        client_id="client_002",
        connection_type=ConnectionType.THINKING_PATH,
        user_id="user_001",
        session_id="session_001"
    )
    
    # 更新连接状态
    await conn_manager.update_connection_status("client_001", ConnectionStatus.CONNECTED)
    await conn_manager.update_connection_status("client_002", ConnectionStatus.CONNECTED)
    
    # 获取统计信息
    stats = await conn_manager.get_connection_stats()
    print(f"连接统计: {stats}")
    
    # 获取用户连接
    user_conns = await conn_manager.get_user_connections("user_001")
    print(f"用户连接数: {len(user_conns)}")
    
    # 清理不活跃连接
    await conn_manager.cleanup_inactive_connections(inactive_minutes=1)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_connection_management())