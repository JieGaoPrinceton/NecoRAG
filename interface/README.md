# NecoRAG Interface 接口服务

## 概述

Interface模块为NecoRAG知识库提供完整的外部访问接口，包括RESTful API和WebSocket两种服务方式，支持知识的查询、插入、更新、删除等核心操作。

## 功能特性

### 🔍 知识查询
- 多意图识别（事实查询、比较分析、推理演绎等）
- 多层检索（工作记忆、语义记忆、情景图谱）
- 智能重排序和结果融合
- 查询建议生成

### ➕ 知识插入
- 批量插入支持
- 数据预处理和验证
- 多层存储同步
- 异步知识巩固

### 🔄 知识更新
- 部分更新和全量更新
- 相关性传播更新
- 版本控制支持

### 🗑️ 知识删除
- 批量删除支持
- 关系清理
- 软删除选项

### 📊 实时监控
- 健康状态检查
- 性能指标统计
- 实时状态推送

## 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Layer                      │
├─────────────────────────────────────────────────────────┤
│  RESTful API           │        WebSocket Service       │
│  (Port: 8000)          │        (Port: 8001)            │
├─────────────────────────────────────────────────────────┤
│                    Knowledge Service                    │
├─────────────────────────────────────────────────────────┤
│  Perception  │  Memory  │  Retrieval  │  Refinement    │
│    Engine    │  Layers  │   Engine    │    Agent       │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn websockets pydantic
```

### 2. 启动服务

```bash
# 方式1：直接运行
python -m interface.main

# 方式2：分别启动API和WebSocket
python -m interface.api  # RESTful API (端口 8000)
python -m interface.websocket  # WebSocket (端口 8001)
```

### 3. 访问接口

- **API文档**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8001
- **健康检查**: http://localhost:8000/health

## RESTful API 接口

### 基础信息
```
GET /                    # 服务信息
GET /health             # 健康检查
GET /docs               # API文档
```

### 知识操作
```
POST /query             # 知识查询
POST /insert            # 知识插入
PUT /update             # 知识更新
DELETE /delete          # 知识删除
GET /stats              # 统计信息
GET /suggestions/{query} # 查询建议
```

### 查询示例

```bash
# 查询知识
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "language": "zh",
    "top_k": 5
  }'

# 插入知识
curl -X POST http://localhost:8000/insert \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [{
      "content": "人工智能是计算机科学的一个分支...",
      "title": "人工智能定义",
      "tags": ["AI", "计算机科学"],
      "domain": "technology"
    }]
  }'
```

## WebSocket 接口

### 连接方式

```javascript
const ws = new WebSocket('ws://localhost:8001');

ws.onopen = function(event) {
    console.log('连接已建立');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
};
```

### 消息格式

```json
{
  "type": "query",
  "data": {
    "query": "什么是机器学习？",
    "language": "zh"
  },
  "timestamp": "2026-03-18T10:30:00Z"
}
```

### 支持的消息类型

| 类型 | 说明 | 数据格式 |
|------|------|----------|
| `query` | 知识查询 | QueryRequest |
| `insert` | 知识插入 | InsertRequest |
| `update` | 知识更新 | UpdateRequest |
| `delete` | 知识删除 | DeleteRequest |
| `subscribe` | 订阅房间 | {"room": "room_name"} |
| `unsubscribe` | 取消订阅 | {"room": "room_name"} |
| `ping` | 心跳检测 | 任意数据 |

### 房间系统

```javascript
// 订阅知识更新房间
ws.send(JSON.stringify({
  "type": "subscribe",
  "data": {"room": "knowledge_updates"}
}));

// 取消订阅
ws.send(JSON.stringify({
  "type": "unsubscribe",
  "data": {"room": "knowledge_updates"}
}));
```

## 数据模型

### 查询请求 (QueryRequest)
```json
{
  "query": "查询内容",
  "intent": "factual",
  "domain": "technology",
  "language": "zh",
  "top_k": 5,
  "filters": {}
}
```

### 查询响应 (QueryResponse)
```json
{
  "query_id": "uuid-string",
  "results": [...],
  "execution_time": 0.123,
  "intent_detected": "concept",
  "confidence": 0.95,
  "suggestions": ["相关问题1", "相关问题2"]
}
```

### 知识条目 (KnowledgeEntry)
```json
{
  "id": "entry-uuid",
  "content": "知识内容",
  "title": "标题",
  "tags": ["tag1", "tag2"],
  "domain": "technology",
  "language": "zh",
  "metadata": {}
}
```

## 性能指标

### 响应时间目标
- 查询响应: < 800ms
- 插入操作: < 500ms
- 更新操作: < 300ms
- 删除操作: < 200ms

### 并发能力
- 支持 1000+ 并发连接
- 每秒处理 500+ 查询请求
- 批量操作支持 1000+ 条目

## 错误处理

### HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### WebSocket错误格式
```json
{
  "type": "error",
  "data": {
    "message": "错误描述"
  },
  "timestamp": "2026-03-18T10:30:00Z"
}
```

## 监控和日志

### 健康检查端点
```
GET /health
```

响应示例：
```json
{
  "status": "healthy",
  "components": {
    "knowledge_service": "healthy",
    "memory_layers": "healthy"
  },
  "uptime": 3600.5,
  "timestamp": "2026-03-18T10:30:00Z"
}
```

### 统计信息
```
GET /stats
```

## 部署建议

### 生产环境配置
```python
# interface/main.py
service = InterfaceService(
    api_port=8000,
    ws_port=8001
)
```

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY interface/ ./interface/
CMD ["python", "-m", "interface.main"]
```

### 负载均衡
建议使用Nginx进行负载均衡：
```
upstream api_servers {
    server 127.0.0.1:8000;
    server 127.0.0.1:8002;
}

upstream ws_servers {
    server 127.0.0.1:8001;
    server 127.0.0.1:8003;
}
```

## 客户端示例

### Python客户端
```python
import requests
import websocket
import json

# RESTful API调用
def query_knowledge(query_text):
    response = requests.post(
        'http://localhost:8000/query',
        json={
            'query': query_text,
            'language': 'zh',
            'top_k': 5
        }
    )
    return response.json()

# WebSocket客户端
def connect_websocket():
    ws = websocket.WebSocket()
    ws.connect('ws://localhost:8001')
    
    # 发送查询
    ws.send(json.dumps({
        'type': 'query',
        'data': {'query': '人工智能'},
        'timestamp': '2026-03-18T10:30:00Z'
    }))
    
    result = ws.recv()
    return json.loads(result)
```

### JavaScript客户端
```javascript
class NecoRAGClient {
    constructor(apiUrl, wsUrl) {
        this.apiUrl = apiUrl;
        this.wsUrl = wsUrl;
        this.ws = null;
    }
    
    async query(text) {
        const response = await fetch(`${this.apiUrl}/query`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: text,
                language: 'zh'
            })
        });
        return await response.json();
    }
    
    connect() {
        this.ws = new WebSocket(this.wsUrl);
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
        };
    }
    
    sendQuery(query) {
        this.ws.send(JSON.stringify({
            type: 'query',
            data: {query: query}
        }));
    }
}
```

## 贡献指南

欢迎提交Issue和Pull Request来改进Interface模块！

## 许可证

MIT License