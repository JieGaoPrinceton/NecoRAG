# NecoRAG 调试面板 API 参考文档

## REST API 端点

### 调试会话管理

#### 创建调试会话
```
POST /api/debug/sessions
```
**请求体:**
```json
{
  "query": "用户查询内容",
  "user_id": "可选的用户ID"
}
```

**响应:**
```json
{
  "session_id": "会话唯一标识符",
  "query": "用户查询内容",
  "status": "active",
  "start_time": "ISO时间戳"
}
```

#### 获取会话详情
```
GET /api/debug/sessions/{session_id}
```

**响应:**
```json
{
  "session_id": "会话ID",
  "query": "查询内容",
  "status": "completed|failed|active",
  "start_time": "开始时间",
  "end_time": "结束时间",
  "duration": "总耗时(秒)",
  "evidence": [...],
  "retrieval_steps": [...],
  "performance_metrics": {...}
}
```

#### 完成会话
```
POST /api/debug/sessions/{session_id}/complete
```
**请求体:**
```json
{
  "accuracy": 0.95,
  "confidence": 0.88
}
```

#### 标记会话失败
```
POST /api/debug/sessions/{session_id}/fail
```
**请求体:**
```json
{
  "error_message": "失败原因描述"
}
```

### 检索步骤管理

#### 添加检索步骤
```
POST /api/debug/sessions/{session_id}/steps
```
**请求体:**
```json
{
  "name": "步骤名称",
  "description": "步骤描述",
  "input_data": {"key": "value"},
  "output_data": {"result": "data"},
  "metrics": {"latency": 0.5, "accuracy": 0.9},
  "completed": true
}
```

### 证据管理

#### 添加证据
```
POST /api/debug/sessions/{session_id}/evidence
```
**请求体:**
```json
{
  "source": "vector|keyword|hybrid",
  "content": "证据内容",
  "relevance_score": 0.85,
  "metadata": {"document_id": "doc_123"},
  "source_url": "可选的来源URL",
  "document_id": "可选的文档ID"
}
```

### 查询历史

#### 获取查询历史
```
GET /api/debug/queries/history?page=1&page_size=20&status=completed&start_date=2024-01-01&end_date=2024-12-31
```

**响应:**
```json
{
  "records": [...],
  "total_count": 100,
  "page": 1,
  "page_size": 20
}
```

### 路径分析

#### 分析思维路径
```
POST /api/debug/analyze
```
**请求体:**
```json
{
  "session_id": "会话ID",
  "analysis_type": "performance|bottleneck|optimization"
}
```

**响应:**
```json
{
  "session_id": "会话ID",
  "analysis_results": {
    "total_steps": 5,
    "total_duration": 2.5,
    "avg_step_duration": 0.5,
    "bottlenecks": [...]
  },
  "recommendations": ["优化建议1", "优化建议2"],
  "timestamp": "分析时间"
}
```

### 参数调优

#### 参数调优
```
POST /api/debug/tune-parameters
```
**请求体:**
```json
{
  "parameters": {
    "top_k": 10,
    "confidence_threshold": 0.8
  },
  "test_queries": ["测试查询1", "测试查询2"]
}
```

**响应:**
```json
{
  "test_results": [...],
  "best_parameters": {...},
  "performance_improvement": 0.25
}
```

### 系统监控

#### 获取调试统计
```
GET /api/debug/stats
```

**响应:**
```json
{
  "total_sessions": 150,
  "completed_sessions": 145,
  "failed_sessions": 5,
  "completion_rate": 0.967,
  "total_query_records": 320,
  "avg_confidence": 0.875,
  "recent_24h_queries": 45,
  "websocket_connections": 3,
  "active_sessions": 2
}
```

#### 获取仪表板统计
```
GET /api/debug/stats/dashboard
```

**响应:**
```json
{
  "active_sessions": 2,
  "total_queries": 320,
  "avg_response_time": 156.7,
  "success_rate": 0.94,
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "websocket_connections": 3
}
```

#### 健康检查
```
GET /api/debug/health
```

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "3.0.0-alpha",
  "components": {
    "websocket": true,
    "database": true,
    "cache": true
  }
}
```

#### 刷新数据
```
POST /api/debug/refresh
```

**响应:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "status": "success",
  "message": "数据刷新成功"
}
```

## WebSocket API

### 思维路径实时推送
```
WebSocket: ws://localhost:8000/ws/thinking-path/{session_id}
```

**客户端消息格式:**
```json
{
  "type": "subscribe",
  "session_id": "目标会话ID"
}
```

**服务器推送消息格式:**
```json
{
  "type": "session_update",
  "session_id": "会话ID",
  "data": {...}
}
```

### 应用状态推送
```
WebSocket: ws://localhost:8000/ws/app
```

**推送的消息类型:**
- `stats_update`: 统计信息更新
- `alert`: 系统告警
- `session_created`: 新会话创建
- `session_completed`: 会话完成

## 数据模型参考

### DebugSession
```python
class DebugSession:
    session_id: str
    query: str
    user_id: Optional[str]
    status: DebugSessionStatus
    start_time: datetime
    end_time: Optional[datetime]
    evidence: List[EvidenceInfo]
    retrieval_steps: List[RetrievalStep]
    performance_metrics: Dict[str, float]
```

### EvidenceInfo
```python
class EvidenceInfo:
    evidence_id: str
    source: EvidenceSource
    content: str
    relevance_score: float
    metadata: Dict[str, Any]
    source_url: Optional[str]
    document_id: Optional[str]
    timestamp: datetime
```

### RetrievalStep
```python
class RetrievalStep:
    step_id: str
    name: str
    description: str
    input_data: Optional[Any]
    output_data: Optional[Any]
    metrics: Dict[str, float]
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
```

## 错误响应格式

所有API端点在出错时都会返回统一的错误格式：

```json
{
  "detail": "错误描述信息"
}
```

HTTP状态码说明：
- 200: 请求成功
- 400: 请求参数错误
- 404: 资源未找到
- 500: 服务器内部错误

## 认证和授权

> 注意：当前版本的API未实现认证机制。生产环境中应添加JWT Token或OAuth2认证。

## 限流和配额

> 注意：当前版本未实现API限流。建议在生产环境中添加请求频率限制。

## 版本控制

API版本通过URL前缀管理：
- `/api/v1/debug/` - 版本1（当前）
- 未来版本将使用相应的版本号

---
*文档版本: v3.0.0-alpha*
*最后更新: 2026年3月19日*