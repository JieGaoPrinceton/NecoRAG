"""
实时推送服务 - Real-time Push Service
提供调试面板的实时数据推送功能
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from src.dashboard.debug.websocket import DebugWebSocketManager
from src.dashboard.debug.models import DebugSession

logger = logging.getLogger(__name__)


class RealTimePushService:
    """实时推送服务"""
    
    def __init__(self, ws_manager: DebugWebSocketManager):
        """
        初始化实时推送服务
        
        Args:
            ws_manager: WebSocket管理器实例
        """
        self.ws_manager = ws_manager
        self.push_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_session_monitoring(self, session_id: str, session: DebugSession):
        """
        开始会话监控
        
        Args:
            session_id: 会话ID
            session: 调试会话对象
        """
        if session_id in self.push_tasks:
            logger.warning(f"会话 {session_id} 已在监控中")
            return
            
        # 启动监控任务
        task = asyncio.create_task(self._monitor_session(session_id, session))
        self.push_tasks[session_id] = task
        logger.info(f"开始监控会话: {session_id}")
        
    async def stop_session_monitoring(self, session_id: str):
        """
        停止会话监控
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.push_tasks:
            task = self.push_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.push_tasks[session_id]
            logger.info(f"停止监控会话: {session_id}")
    
    async def _monitor_session(self, session_id: str, session: DebugSession):
        """
        监控会话并推送实时更新
        
        Args:
            session_id: 会话ID
            session: 调试会话对象
        """
        try:
            # 推送会话开始通知
            await self.ws_manager.broadcast_session_update(session)
            await self.ws_manager.broadcast_system_notification(
                "session_started", 
                f"调试会话 {session_id} 已开始", 
                "info"
            )
            
            # 模拟实时数据推送
            step_index = 0
            while session.status != "completed" and session.status != "failed":
                # 模拟检索步骤更新
                if step_index < len(session.retrieval_trace or []):
                    step_data = {
                        "step_id": f"step_{step_index}",
                        "type": "retrieval",
                        "description": session.retrieval_trace[step_index] if session.retrieval_trace else "",
                        "status": "completed",
                        "duration": 150 + (step_index * 50),
                        "confidence": 0.85 + (step_index * 0.02),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.ws_manager.broadcast_step_update(session_id, step_data)
                    step_index += 1
                
                # 模拟性能指标更新
                metrics = {
                    "response_time": 200 + (step_index * 30),
                    "throughput": 5.2,
                    "memory_usage": 128.5,
                    "cpu_usage": 45.3
                }
                await self.ws_manager.broadcast_realtime_metrics(session_id, metrics)
                
                # 模拟进度更新
                progress = min(1.0, step_index / max(len(session.retrieval_trace or []), 1))
                await self.ws_manager.push_progress_update(session_id, progress, f"处理步骤 {step_index}")
                
                # 等待一段时间再推送下一批数据
                await asyncio.sleep(2)
                
                # 模拟会话完成
                if step_index >= len(session.retrieval_trace or []):
                    session.status = "completed"
                    session.end_time = datetime.now()
                    break
            
            # 推送会话完成通知
            await self.ws_manager.broadcast_session_update(session)
            await self.ws_manager.broadcast_system_notification(
                "session_completed", 
                f"调试会话 {session_id} 已完成", 
                "success"
            )
            
        except asyncio.CancelledError:
            logger.info(f"会话监控任务被取消: {session_id}")
        except Exception as e:
            logger.error(f"会话监控出错 {session_id}: {e}")
            await self.ws_manager.push_error_notification(session_id, "monitoring_error", str(e))
    
    async def push_evidence_data(self, session_id: str, evidence_list: list):
        """
        推送证据数据
        
        Args:
            session_id: 会话ID
            evidence_list: 证据数据列表
        """
        for evidence in evidence_list:
            await self.ws_manager.broadcast_evidence_update(session_id, evidence)
            await asyncio.sleep(0.1)  # 避免推送过于频繁
    
    async def push_reasoning_data(self, session_id: str, reasoning_steps: list):
        """
        推送推理数据
        
        Args:
            session_id: 会话ID
            reasoning_steps: 推理步骤列表
        """
        for step in reasoning_steps:
            await self.ws_manager.broadcast_reasoning_update(session_id, step)
            await asyncio.sleep(0.2)  # 避免推送过于频繁
    
    async def push_performance_snapshot(self, session_id: str, metrics: Dict[str, float]):
        """
        推送性能快照
        
        Args:
            session_id: 会话ID
            metrics: 性能指标字典
        """
        await self.ws_manager.broadcast_performance_update(session_id, metrics)
    
    async def send_heartbeat(self):
        """发送心跳信号"""
        await self.ws_manager.broadcast_system_notification(
            "heartbeat", 
            "系统心跳", 
            "info"
        )
    
    async def cleanup(self):
        """清理资源"""
        # 取消所有监控任务
        for session_id, task in self.push_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.push_tasks.clear()
        logger.info("实时推送服务已清理")


# 使用示例和测试函数
async def demo_realtime_push_service():
    """演示实时推送服务功能"""
    # 创建WebSocket管理器
    ws_manager = DebugWebSocketManager(max_connections=10)
    
    # 创建实时推送服务
    push_service = RealTimePushService(ws_manager)
    
    # 创建模拟会话
    from src.dashboard.debug.models import DebugSession, DebugSessionStatus
    
    session = DebugSession(
        session_id="demo_session_001",
        query="演示查询",
        start_time=datetime.now(),
        status=DebugSessionStatus.RUNNING,
        retrieval_trace=[
            "查询分析完成",
            "实体识别完成", 
            "向量检索完成",
            "图谱推理完成",
            "结果融合完成"
        ]
    )
    
    # 注册会话
    await ws_manager.register_session(session)
    
    # 开始监控
    await push_service.start_session_monitoring("demo_session_001", session)
    
    # 模拟一些操作
    await asyncio.sleep(5)
    
    # 推送一些证据数据
    evidence_data = [
        {
            "evidence_id": "ev_001",
            "source": "vector_db",
            "content": "这是第一个证据内容...",
            "relevance_score": 0.95,
            "timestamp": datetime.now().isoformat()
        },
        {
            "evidence_id": "ev_002", 
            "source": "knowledge_graph",
            "content": "这是第二个证据内容...",
            "relevance_score": 0.87,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    await push_service.push_evidence_data("demo_session_001", evidence_data)
    
    # 等待一段时间
    await asyncio.sleep(10)
    
    # 停止监控
    await push_service.stop_session_monitoring("demo_session_001")
    
    # 清理
    await push_service.cleanup()
    await ws_manager.unregister_session("demo_session_001")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_realtime_push_service())