"""
Debug API Router - 调试API路由
提供调试面板所需的REST API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException, Query, Body, WebSocket, Depends
from pydantic import BaseModel

from src.dashboard.debug.models import (
    DebugSession, DebugQueryRecord, 
    DebugSessionStatus, EvidenceInfo, RetrievalStep
)
from src.dashboard.debug.websocket import DebugWebSocketManager

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/api/debug", tags=["debug"])

# 全局WebSocket管理器实例（在实际应用中应该通过依赖注入）
websocket_manager: Optional[DebugWebSocketManager] = None

# 模拟数据存储（实际应用中应该使用数据库）
debug_sessions: Dict[str, DebugSession] = {}
query_records: List[DebugQueryRecord] = []


class DebugSessionCreate(BaseModel):
    """创建调试会话请求"""
    query: str
    user_id: Optional[str] = None


class DebugSessionResponse(BaseModel):
    """调试会话响应"""
    session_id: str
    query: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration: float
    evidence_count: int
    avg_confidence: float


class QueryHistoryResponse(BaseModel):
    """查询历史响应"""
    records: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class PathAnalysisRequest(BaseModel):
    """路径分析请求"""
    session_id: str
    analysis_type: str = "performance"  # performance/bottleneck/optimization


class PathAnalysisResponse(BaseModel):
    """路径分析响应"""
    session_id: str
    analysis_results: Dict[str, Any]
    recommendations: List[str]
    timestamp: str


class ParameterTuningRequest(BaseModel):
    """参数调优请求"""
    parameters: Dict[str, Any]
    test_queries: List[str]


class ParameterTuningResponse(BaseModel):
    """参数调优响应"""
    test_results: List[Dict[str, Any]]
    best_parameters: Dict[str, Any]
    performance_improvement: float


def set_websocket_manager(manager: DebugWebSocketManager):
    """设置WebSocket管理器"""
    global websocket_manager
    websocket_manager = manager


@router.post("/sessions", response_model=Dict[str, Any])
async def create_debug_session(request: DebugSessionCreate):
    """
    创建新的调试会话
    
    Args:
        request: 调试会话创建请求
        
    Returns:
        Dict: 创建的会话信息
    """
    try:
        # 创建新的调试会话
        session = DebugSession(
            query=request.query,
            user_id=request.user_id
        )
        
        # 保存会话
        debug_sessions[session.session_id] = session
        
        # 注册到WebSocket管理器
        if websocket_manager:
            await websocket_manager.register_session(session)
        
        logger.info(f"Created debug session: {session.session_id}")
        
        return {
            "session_id": session.session_id,
            "query": session.query,
            "status": session.status.value,
            "start_time": session.start_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create debug session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create debug session")


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_debug_session(session_id: str):
    """
    获取调试会话详情
    
    Args:
        session_id: 会话ID
        
    Returns:
        Dict: 会话详细信息
    """
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[session_id]
    return session.to_dict()


@router.post("/sessions/{session_id}/complete")
async def complete_debug_session(
    session_id: str,
    metrics: Optional[Dict[str, float]] = Body(None)
):
    """
    完成调试会话
    
    Args:
        session_id: 会话ID
        metrics: 最终性能指标
        
    Returns:
        Dict: 操作结果
    """
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[session_id]
    session.complete_session(metrics)
    
    # 广播会话完成消息
    if websocket_manager:
        await websocket_manager.broadcast_session_update(session)
        await websocket_manager.unregister_session(session_id)
    
    # 创建查询记录
    record = DebugQueryRecord.from_debug_session(session)
    query_records.append(record)
    
    logger.info(f"Completed debug session: {session_id}")
    
    return {"message": "Session completed", "session_id": session_id}


@router.post("/sessions/{session_id}/fail")
async def fail_debug_session(
    session_id: str,
    error_message: str = Body(..., embed=True)
):
    """
    标记调试会话失败
    
    Args:
        session_id: 会话ID
        error_message: 错误信息
        
    Returns:
        Dict: 操作结果
    """
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[session_id]
    session.fail_session(error_message)
    
    # 广播会话失败消息
    if websocket_manager:
        await websocket_manager.broadcast_session_update(session)
        await websocket_manager.unregister_session(session_id)
    
    logger.info(f"Failed debug session {session_id}: {error_message}")
    
    return {"message": "Session marked as failed", "session_id": session_id}


@router.post("/sessions/{session_id}/steps")
async def add_retrieval_step(
    session_id: str,
    step_data: Dict[str, Any] = Body(...)
):
    """
    添加检索步骤
    
    Args:
        session_id: 会话ID
        step_data: 步骤数据
        
    Returns:
        Dict: 操作结果
    """
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[session_id]
    
    # 创建检索步骤
    step = RetrievalStep(
        name=step_data.get("name", ""),
        description=step_data.get("description", ""),
        input_data=step_data.get("input_data"),
        output_data=step_data.get("output_data"),
        metrics=step_data.get("metrics", {})
    )
    
    # 如果提供了完成信息，则标记步骤完成
    if step_data.get("completed"):
        step.complete(
            output_data=step_data.get("output_data"),
            metrics=step_data.get("metrics")
        )
    
    session.add_retrieval_step(step)
    
    # 广播步骤更新
    if websocket_manager:
        await websocket_manager.broadcast_step_update(session_id, step.to_dict())
    
    logger.info(f"Added retrieval step to session {session_id}: {step.name}")
    
    return {"message": "Step added", "step_id": step.step_id}


@router.post("/sessions/{session_id}/evidence")
async def add_evidence(
    session_id: str,
    evidence_data: Dict[str, Any] = Body(...)
):
    """
    添加证据
    
    Args:
        session_id: 会话ID
        evidence_data: 证据数据
        
    Returns:
        Dict: 操作结果
    """
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[session_id]
    
    # 创建证据信息
    evidence = EvidenceInfo(
        source=evidence_data.get("source", "vector"),
        content=evidence_data.get("content", ""),
        relevance_score=evidence_data.get("relevance_score", 0.0),
        metadata=evidence_data.get("metadata", {}),
        source_url=evidence_data.get("source_url"),
        document_id=evidence_data.get("document_id")
    )
    
    session.add_evidence(evidence)
    
    logger.info(f"Added evidence to session {session_id}: {evidence.evidence_id}")
    
    return {"message": "Evidence added", "evidence_id": evidence.evidence_id}


@router.get("/queries/history", response_model=QueryHistoryResponse)
async def get_query_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取查询历史记录
    
    Args:
        page: 页码
        page_size: 每页大小
        status: 状态过滤
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        QueryHistoryResponse: 查询历史响应
    """
    try:
        # 过滤记录
        filtered_records = query_records.copy()
        
        # 状态过滤
        if status:
            filtered_records = [
                record for record in filtered_records
                if record.status.value == status
            ]
        
        # 日期过滤
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_records = [
                record for record in filtered_records
                if record.timestamp >= start_dt
            ]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_records = [
                record for record in filtered_records
                if record.timestamp <= end_dt
            ]
        
        # 排序（按时间倒序）
        filtered_records.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 分页
        total_count = len(filtered_records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_records = filtered_records[start_idx:end_idx]
        
        return QueryHistoryResponse(
            records=[record.to_dict() for record in paginated_records],
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve query history")


@router.post("/analyze", response_model=PathAnalysisResponse)
async def analyze_thinking_path(request: PathAnalysisRequest):
    """
    分析思维路径
    
    Args:
        request: 路径分析请求
        
    Returns:
        PathAnalysisResponse: 分析结果
    """
    if request.session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Debug session not found")
    
    session = debug_sessions[request.session_id]
    
    try:
        # 执行路径分析（这里应该是实际的分析逻辑）
        analysis_results = {
            "analysis_type": request.analysis_type,
            "total_steps": len(session.retrieval_steps),
            "total_duration": session.total_duration,
            "avg_step_duration": session.total_duration / max(len(session.retrieval_steps), 1),
            "bottlenecks": [],  # 实际实现中应该识别瓶颈步骤
            "performance_metrics": session.performance_metrics
        }
        
        # 生成优化建议
        recommendations = [
            "Consider increasing vector search top_k for better recall",
            "Optimize chunk size for improved retrieval precision",
            "Review early termination threshold settings"
        ]
        
        return PathAnalysisResponse(
            session_id=request.session_id,
            analysis_results=analysis_results,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze thinking path: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze thinking path")


@router.post("/tune-parameters", response_model=ParameterTuningResponse)
async def tune_parameters(request: ParameterTuningRequest):
    """
    参数调优
    
    Args:
        request: 参数调优请求
        
    Returns:
        ParameterTuningResponse: 调优结果
    """
    try:
        # 这里应该是实际的参数调优逻辑
        # 目前返回模拟结果
        
        test_results = []
        for i, query in enumerate(request.test_queries[:3]):  # 限制测试查询数量
            test_results.append({
                "query": query,
                "confidence": 0.85 + i * 0.05,
                "latency": 0.5 - i * 0.1,
                "evidence_count": 5 + i,
                "hallucination_score": 0.1 - i * 0.02
            })
        
        # 确定最佳参数（模拟）
        best_parameters = request.parameters.copy()
        best_parameters["top_k"] = 15
        best_parameters["confidence_threshold"] = 0.8
        
        return ParameterTuningResponse(
            test_results=test_results,
            best_parameters=best_parameters,
            performance_improvement=0.25  # 25% 性能提升
        )
        
    except Exception as e:
        logger.error(f"Failed to tune parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to tune parameters")


@router.get("/stats")
async def get_debug_stats():
    """
    获取调试统计信息
    
    Returns:
        Dict: 统计信息
    """
    try:
        # 计算各种统计指标
        total_sessions = len(debug_sessions)
        completed_sessions = len([
            s for s in debug_sessions.values() 
            if s.status == DebugSessionStatus.COMPLETED
        ])
        failed_sessions = len([
            s for s in debug_sessions.values() 
            if s.status == DebugSessionStatus.FAILED
        ])
        
        total_records = len(query_records)
        avg_confidence = (
            sum(record.confidence for record in query_records) / max(len(query_records), 1)
            if query_records else 0.0
        )
        
        # 计算最近24小时的统计数据
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        recent_records = [
            record for record in query_records
            if record.timestamp >= twenty_four_hours_ago
        ]
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "completion_rate": completed_sessions / max(total_sessions, 1),
            "total_query_records": total_records,
            "avg_confidence": round(avg_confidence, 3),
            "recent_24h_queries": len(recent_records),
            "websocket_connections": (
                await websocket_manager.get_connection_count() 
                if websocket_manager else 0
            ),
            "active_sessions": (
                await websocket_manager.get_active_sessions_count()
                if websocket_manager else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Failed to get debug stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve debug statistics")


@router.get("/stats/dashboard")
async def get_dashboard_stats():
    """获取仪表板统计信息"""
    try:
        stats = {
            "active_sessions": len(debug_sessions),
            "total_queries": len(query_records),
            "avg_response_time": 156.7,
            "success_rate": 0.94,
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "websocket_connections": (
                await websocket_manager.get_connection_count() 
                if websocket_manager else 0
            )
        }
        return stats
    except Exception as e:
        logger.error(f"获取仪表板统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_debug_data():
    """刷新调试数据"""
    try:
        # 模拟数据刷新
        refreshed_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "message": "数据刷新成功"
        }
        return refreshed_data
    except Exception as e:
        logger.error(f"刷新调试数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "websocket": websocket_manager is not None,
            "database": True,  # 模拟数据库连接正常
            "cache": True      # 模拟缓存服务正常
        }
    }