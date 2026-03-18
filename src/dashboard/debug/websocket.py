"""
Debug WebSocket Manager - 调试WebSocket管理器
处理调试面板的实时通信和会话管理
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from src.dashboard.debug.models import DebugSession, DebugQueryRecord

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """WebSocket连接包装类"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected = True
        self.last_activity = datetime.now()
        self.subscribed_sessions: Set[str] = set()
        self.subscribed_queries: Set[str] = set()
    
    async def send_json(self, data: Dict[str, Any]):
        """发送JSON数据"""
        if self.connected:
            try:
                await self.websocket.send_json(data)
                self.last_activity = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send data to client {self.client_id}: {e}")
                self.connected = False
    
    async def disconnect(self):
        """断开连接"""
        self.connected = False
        try:
            await self.websocket.close()
        except Exception:
            pass


class DebugWebSocketManager:
    """调试WebSocket管理器"""
    
    def __init__(self, max_connections: int = 100):
        """
        初始化WebSocket管理器
        
        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self.connections: Dict[str, WebSocketConnection] = {}
        self.session_subscribers: Dict[str, Set[str]] = {}  # session_id -> {client_ids}
        self.query_subscribers: Dict[str, Set[str]] = {}    # query_id -> {client_ids}
        self.active_sessions: Dict[str, DebugSession] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.cleanup_task: Optional[asyncio.Task] = None
        self.broadcast_lock = asyncio.Lock()
        
        # 清理任务将在服务器启动时启动
    
    def start_cleanup_task(self):
        """启动清理任务"""
        if self.cleanup_task is None:
            try:
                # 检查是否有运行中的事件循环
                loop = asyncio.get_running_loop()
                self.cleanup_task = asyncio.create_task(self._cleanup_inactive_connections())
            except RuntimeError:
                # 没有运行中的事件循环，稍后再启动
                print("警告: 暂时无法启动WebSocket清理任务，将在服务器启动后自动启动")
                pass
    
    async def stop_cleanup_task(self):
        """停止清理任务"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
    
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket对象
            client_id: 客户端ID
            
        Returns:
            bool: 连接是否成功
        """
        # 检查连接数限制
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Maximum connections reached: {self.max_connections}")
            return False
        
        # 创建连接对象
        connection = WebSocketConnection(websocket, client_id)
        
        # 接受连接
        try:
            await websocket.accept()
            self.connections[client_id] = connection
            logger.info(f"WebSocket client connected: {client_id}")
            
            # 发送连接确认消息
            await connection.send_json({
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to debug panel"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {client_id}: {e}")
            return False
    
    async def disconnect(self, client_id: str):
        """
        断开WebSocket连接
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.connections:
            connection = self.connections[client_id]
            
            # 清理订阅关系
            await self._unsubscribe_all(connection)
            
            # 断开连接
            await connection.disconnect()
            del self.connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def subscribe_session(self, client_id: str, session_id: str) -> bool:
        """
        订阅会话更新
        
        Args:
            client_id: 客户端ID
            session_id: 会话ID
            
        Returns:
            bool: 订阅是否成功
        """
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        connection.subscribed_sessions.add(session_id)
        
        # 更新会话订阅者映射
        if session_id not in self.session_subscribers:
            self.session_subscribers[session_id] = set()
        self.session_subscribers[session_id].add(client_id)
        
        logger.info(f"Client {client_id} subscribed to session {session_id}")
        return True
    
    async def unsubscribe_session(self, client_id: str, session_id: str) -> bool:
        """
        取消订阅会话
        
        Args:
            client_id: 客户端ID
            session_id: 会话ID
            
        Returns:
            bool: 取消订阅是否成功
        """
        if client_id not in self.connections:
            return False
        
        connection = self.connections[client_id]
        connection.subscribed_sessions.discard(session_id)
        
        # 更新会话订阅者映射
        if session_id in self.session_subscribers:
            self.session_subscribers[session_id].discard(client_id)
            if not self.session_subscribers[session_id]:
                del self.session_subscribers[session_id]
        
        logger.info(f"Client {client_id} unsubscribed from session {session_id}")
        return True
    
    async def broadcast_session_update(self, session: DebugSession):
        """
        广播会话更新
        
        Args:
            session: 调试会话
        """
        if session.session_id not in self.session_subscribers:
            return
        
        subscribers = self.session_subscribers[session.session_id]
        message = {
            "type": "session_update",
            "session_id": session.session_id,
            "data": session.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast_to_clients(subscribers, message)
    
    async def broadcast_step_update(self, session_id: str, step_data: Dict[str, Any]):
        """
        广播步骤更新
        
        Args:
            session_id: 会话ID
            step_data: 步骤数据
        """
        if session_id not in self.session_subscribers:
            return
        
        subscribers = self.session_subscribers[session_id]
        message = {
            "type": "step_update",
            "session_id": session_id,
            "step_data": step_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast_to_clients(subscribers, message)
    
    async def broadcast_performance_update(self, session_id: str, metrics: Dict[str, float]):
        """
        广播性能指标更新
        
        Args:
            session_id: 会话ID
            metrics: 性能指标
        """
        if session_id not in self.session_subscribers:
            return
        
        subscribers = self.session_subscribers[session_id]
        message = {
            "type": "performance_update",
            "session_id": session_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast_to_clients(subscribers, message)
    
    async def broadcast_query_history(self, records: List[DebugQueryRecord], 
                                    client_id: Optional[str] = None):
        """
        广播查询历史
        
        Args:
            records: 查询记录列表
            client_id: 指定客户端ID（如果为None则广播给所有客户端）
        """
        message = {
            "type": "query_history",
            "records": [record.to_dict() for record in records],
            "timestamp": datetime.now().isoformat()
        }
        
        if client_id:
            if client_id in self.connections:
                await self.connections[client_id].send_json(message)
        else:
            # 广播给所有连接的客户端
            await self._broadcast_to_all(message)
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """
        处理客户端消息
        
        Args:
            client_id: 客户端ID
            message: 消息数据
        """
        try:
            msg_type = message.get("type")
            
            if msg_type == "subscribe_session":
                session_id = message.get("session_id")
                if session_id:
                    await self.subscribe_session(client_id, session_id)
                    
            elif msg_type == "unsubscribe_session":
                session_id = message.get("session_id")
                if session_id:
                    await self.unsubscribe_session(client_id, session_id)
                    
            elif msg_type == "get_query_history":
                # 这里应该调用查询历史服务
                await self._handle_query_history_request(client_id, message)
                
            elif msg_type == "ping":
                # 回复心跳
                await self.connections[client_id].send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                logger.warning(f"Unknown message type from {client_id}: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling client message from {client_id}: {e}")
    
    async def register_session(self, session: DebugSession):
        """
        注册调试会话
        
        Args:
            session: 调试会话
        """
        self.active_sessions[session.session_id] = session
        logger.info(f"Registered debug session: {session.session_id}")
    
    async def unregister_session(self, session_id: str):
        """
        注销调试会话
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Unregistered debug session: {session_id}")
    
    async def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.connections)
    
    async def get_active_sessions_count(self) -> int:
        """获取活跃会话数"""
        return len(self.active_sessions)
    
    async def _broadcast_to_clients(self, client_ids: Set[str], message: Dict[str, Any]):
        """向指定客户端广播消息"""
        async with self.broadcast_lock:
            tasks = []
            for client_id in client_ids:
                if client_id in self.connections:
                    task = self.connections[client_id].send_json(message)
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _broadcast_to_all(self, message: Dict[str, Any]):
        """向所有客户端广播消息"""
        async with self.broadcast_lock:
            tasks = []
            for connection in self.connections.values():
                task = connection.send_json(message)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _unsubscribe_all(self, connection: WebSocketConnection):
        """取消连接的所有订阅"""
        # 取消会话订阅
        for session_id in list(connection.subscribed_sessions):
            await self.unsubscribe_session(connection.client_id, session_id)
        
        # 取消查询订阅
        for query_id in list(connection.subscribed_queries):
            connection.subscribed_queries.discard(query_id)
            if query_id in self.query_subscribers:
                self.query_subscribers[query_id].discard(connection.client_id)
                if not self.query_subscribers[query_id]:
                    del self.query_subscribers[query_id]
    
    async def _handle_query_history_request(self, client_id: str, message: Dict[str, Any]):
        """处理查询历史请求"""
        # 这里应该调用实际的查询历史服务
        # 暂时返回空的历史记录
        await self.connections[client_id].send_json({
            "type": "query_history",
            "records": [],
            "timestamp": datetime.now().isoformat()
        })
    
    async def _cleanup_inactive_connections(self):
        """清理不活跃的连接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                current_time = datetime.now()
                inactive_clients = []
                
                for client_id, connection in self.connections.items():
                    # 如果3分钟没有活动，则认为不活跃
                    if (current_time - connection.last_activity).total_seconds() > 180:
                        inactive_clients.append(client_id)
                
                # 断开不活跃的连接
                for client_id in inactive_clients:
                    logger.info(f"Cleaning up inactive connection: {client_id}")
                    await self.disconnect(client_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def shutdown(self):
        """关闭WebSocket管理器"""
        logger.info("Shutting down DebugWebSocketManager")
        
        # 停止清理任务
        await self.stop_cleanup_task()
        
        # 断开所有连接
        for client_id in list(self.connections.keys()):
            await self.disconnect(client_id)
        
        # 清理数据结构
        self.session_subscribers.clear()
        self.query_subscribers.clear()
        self.active_sessions.clear()


# 便捷的装饰器用于WebSocket端点
def debug_websocket_endpoint(path: str):
    """
    调试WebSocket端点装饰器
    
    Args:
        path: WebSocket路径
    """
    def decorator(func):
        func._debug_websocket_path = path
        return func
    return decorator


    async def broadcast_evidence_update(self, session_id: str, evidence_data: Dict[str, Any]):
        """广播证据更新"""
        message = {
            "type": "evidence_added",
            "session_id": session_id,
            "evidence": evidence_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取订阅此会话的所有客户端
        subscribers = self.session_subscribers.get(session_id, set())
        await self._broadcast_to_clients(subscribers, message)

    async def broadcast_reasoning_update(self, session_id: str, reasoning_data: Dict[str, Any]):
        """广播推理更新"""
        message = {
            "type": "reasoning_update",
            "session_id": session_id,
            "reasoning": reasoning_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取订阅此会话的所有客户端
        subscribers = self.session_subscribers.get(session_id, set())
        await self._broadcast_to_clients(subscribers, message)

    async def broadcast_connection_status(self, client_id: str, status: str):
        """广播连接状态更新"""
        message = {
            "type": "connection_status",
            "client_id": client_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送给特定客户端
        if client_id in self.connections:
            await self.connections[client_id].send_json(message)

    async def broadcast_system_notification(self, notification_type: str, message: str, severity: str = "info"):
        """广播系统通知"""
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        # 广播给所有连接的客户端
        await self._broadcast_to_all(notification)

    async def broadcast_realtime_metrics(self, session_id: str, metrics: Dict[str, Any]):
        """广播实时指标数据"""
        message = {
            "type": "realtime_metrics",
            "session_id": session_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取订阅此会话的所有客户端
        subscribers = self.session_subscribers.get(session_id, set())
        await self._broadcast_to_clients(subscribers, message)

    async def push_debug_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """推送调试事件"""
        message = {
            "type": "debug_event",
            "event_type": event_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取订阅此会话的所有客户端
        subscribers = self.session_subscribers.get(session_id, set())
        if subscribers:
            await self._broadcast_to_clients(subscribers, message)
            logger.info(f"推送调试事件 {event_type} 到会话 {session_id}")
        else:
            logger.debug(f"无订阅者接收调试事件 {event_type} for session {session_id}")

    async def push_progress_update(self, session_id: str, progress: float, message: str = ""):
        """推送进度更新"""
        progress_data = {
            "progress": progress,
            "message": message,
            "status": "running" if progress < 1.0 else "completed"
        }
        
        await self.push_debug_event(session_id, "progress_update", progress_data)

    async def push_error_notification(self, session_id: str, error_type: str, error_message: str):
        """推送错误通知"""
        error_data = {
            "error_type": error_type,
            "message": error_message,
            "severity": "error"
        }
        
        await self.push_debug_event(session_id, "error_notification", error_data)