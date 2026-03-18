"""
WebSocket 服务
提供实时的知识库操作和状态推送
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from .models import WebSocketMessage
from .knowledge_service import knowledge_service


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger(__name__)
        self.running = False
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """启动WebSocket服务器"""
        self.running = True
        server = await websockets.serve(
            self.handle_client,
            host,
            port
        )
        self.logger.info(f"WebSocket服务器启动于 ws://{host}:{port}")
        await server.wait_closed()
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_id = str(id(websocket))
        self.clients[client_id] = websocket
        self.logger.info(f"客户端 {client_id} 已连接")
        
        try:
            async for message in websocket:
                await self.process_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"客户端 {client_id} 断开连接")
        finally:
            await self.disconnect_client(client_id)
    
    async def process_message(self, client_id: str, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            ws_message = WebSocketMessage(**data)
            
            response = await self.route_message(client_id, ws_message)
            if response:
                await self.send_to_client(client_id, response)
                
        except json.JSONDecodeError:
            await self.send_error(client_id, "无效的JSON格式")
        except Exception as e:
            self.logger.error(f"处理消息失败: {str(e)}")
            await self.send_error(client_id, f"处理失败: {str(e)}")
    
    async def route_message(self, client_id: str, message: WebSocketMessage) -> Dict[str, Any]:
        """路由消息到相应处理器"""
        handlers = {
            "query": self.handle_query,
            "insert": self.handle_insert,
            "update": self.handle_update,
            "delete": self.handle_delete,
            "subscribe": self.handle_subscribe,
            "unsubscribe": self.handle_unsubscribe,
            "ping": self.handle_ping
        }
        
        handler = handlers.get(message.type)
        if handler:
            return await handler(client_id, message.data)
        else:
            return {
                "type": "error",
                "data": {"message": f"未知的消息类型: {message.type}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_query(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询请求"""
        try:
            # 转换为QueryRequest并执行查询
            from .models import QueryRequest
            request = QueryRequest(**data)
            response = await knowledge_service.query_knowledge(request)
            
            return {
                "type": "query_result",
                "data": response.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "type": "error",
                "data": {"message": f"查询失败: {str(e)}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_insert(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理插入请求"""
        try:
            from .models import InsertRequest
            request = InsertRequest(**data)
            result = await knowledge_service.insert_knowledge(request)
            
            # 通知其他订阅者
            await self.broadcast_to_room("knowledge_updates", {
                "type": "inserted",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "type": "insert_result",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "type": "error",
                "data": {"message": f"插入失败: {str(e)}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_update(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新请求"""
        try:
            from .models import UpdateRequest
            request = UpdateRequest(**data)
            result = await knowledge_service.update_knowledge(request)
            
            # 通知其他订阅者
            await self.broadcast_to_room("knowledge_updates", {
                "type": "updated",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "type": "update_result",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "type": "error",
                "data": {"message": f"更新失败: {str(e)}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_delete(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理删除请求"""
        try:
            from .models import DeleteRequest
            request = DeleteRequest(**data)
            result = await knowledge_service.delete_knowledge(request)
            
            # 通知其他订阅者
            await self.broadcast_to_room("knowledge_updates", {
                "type": "deleted",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "type": "delete_result",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "type": "error",
                "data": {"message": f"删除失败: {str(e)}"},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def handle_subscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理订阅请求"""
        room = data.get("room", "general")
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(client_id)
        
        return {
            "type": "subscribed",
            "data": {"room": room, "message": f"已订阅房间 {room}"},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_unsubscribe(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理取消订阅请求"""
        room = data.get("room", "general")
        if room in self.rooms and client_id in self.rooms[room]:
            self.rooms[room].remove(client_id)
            if not self.rooms[room]:  # 房间为空时删除
                del self.rooms[room]
        
        return {
            "type": "unsubscribed",
            "data": {"room": room, "message": f"已取消订阅房间 {room}"},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_ping(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理心跳请求"""
        return {
            "type": "pong",
            "data": {"message": "pong"},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """发送消息给指定客户端"""
        if client_id in self.clients:
            try:
                await self.clients[client_id].send(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                self.logger.error(f"发送消息失败: {str(e)}")
                await self.disconnect_client(client_id)
    
    async def broadcast_to_room(self, room: str, message: Dict[str, Any]):
        """广播消息到房间"""
        if room in self.rooms:
            disconnected_clients = []
            for client_id in self.rooms[room]:
                try:
                    await self.send_to_client(client_id, message)
                except Exception:
                    disconnected_clients.append(client_id)
            
            # 清理断开的连接
            for client_id in disconnected_clients:
                await self.disconnect_client(client_id)
    
    async def broadcast_all(self, message: Dict[str, Any]):
        """广播消息给所有客户端"""
        disconnected_clients = []
        for client_id in self.clients:
            try:
                await self.send_to_client(client_id, message)
            except Exception:
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)
    
    async def send_error(self, client_id: str, message: str):
        """发送错误消息"""
        error_msg = {
            "type": "error",
            "data": {"message": message},
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_client(client_id, error_msg)
    
    async def disconnect_client(self, client_id: str):
        """断开客户端连接"""
        if client_id in self.clients:
            del self.clients[client_id]
        
        # 从所有房间中移除
        rooms_to_remove = []
        for room, clients in self.rooms.items():
            if client_id in clients:
                clients.remove(client_id)
                if not clients:  # 房间为空
                    rooms_to_remove.append(room)
        
        for room in rooms_to_remove:
            del self.rooms[room]
    
    def get_client_count(self) -> int:
        """获取当前连接数"""
        return len(self.clients)
    
    def get_room_info(self) -> Dict[str, int]:
        """获取房间信息"""
        return {room: len(clients) for room, clients in self.rooms.items()}


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()


async def start_websocket_server():
    """启动WebSocket服务器"""
    await websocket_manager.start_server()