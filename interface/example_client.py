"""
Interface客户端使用示例
演示如何使用RESTful API和WebSocket接口
"""

import asyncio
import requests
import json
import websockets
from typing import Dict, Any


class NecoRAGAPIClient:
    """RESTful API客户端示例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def query_knowledge(self, query: str, **kwargs) -> Dict[str, Any]:
        """查询知识"""
        data = {
            "query": query,
            "language": kwargs.get("language", "zh"),
            "top_k": kwargs.get("top_k", 5)
        }
        
        response = requests.post(
            f"{self.base_url}/query",
            json=data
        )
        return response.json()
    
    def insert_knowledge(self, entries: list) -> Dict[str, Any]:
        """插入知识"""
        data = {"entries": entries}
        response = requests.post(
            f"{self.base_url}/insert",
            json=data
        )
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()


class NecoRAGWebSocketClient:
    """WebSocket客户端示例"""
    
    def __init__(self, ws_url: str = "ws://localhost:8001"):
        self.ws_url = ws_url
        self.websocket = None
    
    async def connect(self):
        """建立WebSocket连接"""
        self.websocket = await websockets.connect(self.ws_url)
        print("WebSocket连接已建立")
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            print("WebSocket连接已断开")
    
    async def send_message(self, message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": "2026-03-18T10:30:00Z"  # 实际使用时应该用当前时间
        }
        
        await self.websocket.send(json.dumps(message, ensure_ascii=False))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def query(self, query_text: str) -> Dict[str, Any]:
        """查询知识"""
        return await self.send_message("query", {"query": query_text})
    
    async def subscribe(self, room: str) -> Dict[str, Any]:
        """订阅房间"""
        return await self.send_message("subscribe", {"room": room})
    
    async def unsubscribe(self, room: str) -> Dict[str, Any]:
        """取消订阅"""
        return await self.send_message("unsubscribe", {"room": room})


# 使用示例
async def demo_restful_api():
    """RESTful API使用演示"""
    print("=== RESTful API 演示 ===")
    
    client = NecoRAGAPIClient()
    
    # 健康检查
    print("1. 健康检查:")
    health = client.health_check()
    print(f"   状态: {health}")
    
    # 知识查询
    print("\n2. 知识查询:")
    result = client.query_knowledge("什么是人工智能？")
    print(f"   查询ID: {result.get('query_id')}")
    print(f"   结果数量: {len(result.get('results', []))}")
    print(f"   执行时间: {result.get('execution_time')}秒")
    
    # 获取统计信息
    print("\n3. 统计信息:")
    stats = client.get_stats()
    print(f"   总条目数: {stats.get('total_entries', 0)}")


async def demo_websocket():
    """WebSocket使用演示"""
    print("\n=== WebSocket 演示 ===")
    
    client = NecoRAGWebSocketClient()
    
    try:
        # 建立连接
        await client.connect()
        
        # 查询知识
        print("1. 知识查询:")
        result = await client.query("机器学习的发展历程")
        print(f"   类型: {result.get('type')}")
        if result.get('type') == 'query_result':
            print(f"   结果数量: {len(result.get('data', {}).get('results', []))}")
        
        # 订阅房间
        print("\n2. 房间订阅:")
        subscribe_result = await client.subscribe("knowledge_updates")
        print(f"   订阅结果: {subscribe_result}")
        
        # 取消订阅
        print("\n3. 取消订阅:")
        unsubscribe_result = await client.unsubscribe("knowledge_updates")
        print(f"   取消结果: {unsubscribe_result}")
        
    except Exception as e:
        print(f"WebSocket演示出错: {e}")
    finally:
        await client.disconnect()


async def demo_combined():
    """综合使用演示"""
    print("\n=== 综合使用演示 ===")
    
    # RESTful API插入数据
    api_client = NecoRAGAPIClient()
    
    print("1. 插入知识条目:")
    entries = [{
        "content": "这是一个测试知识条目，用于演示NecoRAG的插入功能。",
        "title": "测试条目",
        "tags": ["测试", "演示"],
        "domain": "example"
    }]
    
    insert_result = api_client.insert_knowledge(entries)
    print(f"   插入结果: {insert_result}")
    
    # WebSocket实时查询
    ws_client = NecoRAGWebSocketClient()
    
    try:
        await ws_client.connect()
        
        print("\n2. 实时查询:")
        query_result = await ws_client.query("测试条目")
        print(f"   查询结果: {query_result}")
        
    finally:
        await ws_client.disconnect()


def main():
    """主函数"""
    print("NecoRAG Interface 客户端演示")
    print("=" * 50)
    
    # 运行演示
    asyncio.run(demo_restful_api())
    asyncio.run(demo_websocket())
    asyncio.run(demo_combined())
    
    print("\n演示完成！")


if __name__ == "__main__":
    main()