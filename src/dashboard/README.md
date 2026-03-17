# NecoRAG Dashboard - 配置管理系统

## 概述

NecoRAG Dashboard 是一个基于 FastAPI 的 Web 管理界面，用于配置和管理 NecoRAG 各个模块的参数。

## 核心功能

### 1. 配置 Profile 管理

```
┌──────────────────────────────────────────────┐
│          Dashboard Configuration              │
├──────────────────────────────────────────────┤
│                                               │
│  Profile 管理                                 │
│  ├── 创建新 Profile                           │
│  ├── 加载/保存 Profile                        │
│  ├── 切换活动 Profile                         │
│  ├── 导入/导出 Profile                        │
│  └── 复制/删除 Profile                        │
│                                               │
│  模块参数配置                                 │
│  ├── Whiskers Engine (感知层)                │
│  ├── Nine-Lives Memory (记忆层)              │
│  ├── Pounce Strategy (检索层)                │
│  ├── Grooming Agent (巩固层)                 │
│  └── Purr Interface (交互层)                 │
│                                               │
│  统计监控                                     │
│  ├── 文档/块统计                              │
│  ├── 查询历史                                 │
│  └── 性能指标                                 │
│                                               │
└──────────────────────────────────────────────┘
```

### 2. Profile 结构

每个 Profile 包含五大模块的完整配置：

```python
RAGProfile:
  - profile_id: 唯一标识
  - profile_name: Profile 名称
  - description: 描述
  - is_active: 是否活动
  
  WhiskersConfig:
    - chunk_size: 512
    - chunk_overlap: 50
    - enable_ocr: True
    - vector_model: "BGE-M3"
    ...
  
  MemoryConfig:
    - l1_ttl: 3600
    - l2_vector_size: 1024
    - decay_rate: 0.1
    ...
  
  RetrievalConfig:
    - top_k: 10
    - pounce_threshold: 0.85
    - hyde_enabled: True
    ...
  
  GroomingConfig:
    - min_confidence: 0.7
    - hallucination_threshold: 0.6
    ...
  
  PurrConfig:
    - default_tone: "friendly"
    - default_detail_level: 2
    ...
```

### 3. Web UI 功能

- **Profile 列表**：查看所有配置 Profile
- **参数编辑器**：实时修改各模块参数
- **活动切换**：一键切换活动配置
- **统计面板**：查看系统运行状态

## API 接口

### Profile 管理

#### 获取所有 Profiles
```http
GET /api/profiles
```

#### 获取单个 Profile
```http
GET /api/profiles/{profile_id}
```

#### 创建 Profile
```http
POST /api/profiles
Content-Type: application/json

{
  "profile_name": "生产环境配置",
  "description": "用于生产环境的优化配置"
}
```

#### 更新 Profile
```http
PUT /api/profiles/{profile_id}
Content-Type: application/json

{
  "profile_name": "新名称",
  "description": "新描述",
  "whiskers_config": {
    "chunk_size": 1024
  }
}
```

#### 激活 Profile
```http
POST /api/profiles/{profile_id}/activate
```

#### 删除 Profile
```http
DELETE /api/profiles/{profile_id}
```

#### 导出 Profile
```http
POST /api/profiles/{profile_id}/export?export_path=./my_config.json
```

#### 导入 Profile
```http
POST /api/profiles/import?import_path=./my_config.json
```

### 模块参数管理

#### 获取模块参数
```http
GET /api/profiles/{profile_id}/modules/{module}
```

支持的模块：
- `whiskers` - Whiskers Engine
- `memory` - Nine-Lives Memory
- `retrieval` - Pounce Strategy
- `grooming` - Grooming Agent
- `purr` - Purr Interface

#### 更新模块参数
```http
PUT /api/profiles/{profile_id}/modules/{module}
Content-Type: application/json

{
  "module": "whiskers",
  "parameters": {
    "chunk_size": 1024,
    "enable_ocr": false
  }
}
```

### 统计信息

#### 获取统计信息
```http
GET /api/stats
```

响应示例：
```json
{
  "total_documents": 1000,
  "total_chunks": 5000,
  "total_queries": 1500,
  "active_sessions": 5,
  "memory_usage": {
    "l1": 1024,
    "l2": 512000,
    "l3": 10000
  },
  "performance_metrics": {
    "avg_latency": 0.5,
    "recall_at_10": 0.85
  }
}
```

#### 重置统计信息
```http
POST /api/stats/reset
```

## 使用方法

### 方法 1: 命令行启动

```bash
# 默认配置启动
python -m necorag.dashboard.dashboard

# 自定义配置
python -m necorag.dashboard.dashboard --host 127.0.0.1 --port 8080 --config-dir ./my_configs
```

### 方法 2: Python 代码启动

```python
from necorag.dashboard import DashboardServer

# 创建服务器
server = DashboardServer(
    config_dir="./configs",
    host="0.0.0.0",
    port=8000
)

# 启动
server.run()
```

### 方法 3: 在应用中集成

```python
from necorag import WhiskersEngine, MemoryManager
from necorag.dashboard import ConfigManager

# 加载活动配置
config_manager = ConfigManager()
active_profile = config_manager.get_active_profile()

# 使用配置初始化模块
engine = WhiskersEngine(
    chunk_size=active_profile.whiskers_config.parameters['chunk_size'],
    enable_ocr=active_profile.whiskers_config.parameters['enable_ocr']
)

memory = MemoryManager(
    decay_rate=active_profile.memory_config.parameters['decay_rate']
)
```

## 配置文件存储

所有配置以 JSON 格式存储在配置目录中：

```
configs/
├── profile_abc123.json    # Profile 1
├── profile_def456.json    # Profile 2
└── profile_ghi789.json    # Profile 3
```

每个文件包含完整的 Profile 配置：

```json
{
  "profile_id": "abc123",
  "profile_name": "默认配置",
  "description": "NecoRAG 默认配置",
  "is_active": true,
  "created_at": "2026-03-17T10:00:00",
  "updated_at": "2026-03-17T11:00:00",
  "whiskers_config": {
    "module_type": "whiskers",
    "parameters": {
      "chunk_size": 512,
      "enable_ocr": true
    }
  },
  ...
}
```

## 典型使用场景

### 场景 1: 多环境管理

```python
# 创建不同环境的配置
dev_profile = config_manager.create_profile("开发环境", "用于开发和测试")
prod_profile = config_manager.create_profile("生产环境", "生产环境优化配置")

# 切换环境
config_manager.set_active_profile(prod_profile.profile_id)
```

### 场景 2: 参数调优

```python
# 获取当前配置
profile = config_manager.get_active_profile()

# 调整检索参数
config_manager.update_profile(profile.profile_id, {
    "retrieval_config": {
        "top_k": 20,
        "pounce_threshold": 0.90
    }
})

# 对比不同配置效果
```

### 场景 3: 配置导入导出

```python
# 导出配置
config_manager.export_profile(
    profile_id="abc123",
    export_path="./shared_config.json"
)

# 导入配置（从其他环境或团队）
imported = config_manager.import_profile("./shared_config.json")
```

## 性能优化建议

### 1. 配置缓存
系统会缓存所有加载的 Profile，避免频繁读取文件。

### 2. 参数验证
建议在更新参数前进行验证，确保参数在合理范围内。

### 3. 批量操作
对于大量参数更新，建议使用批量更新接口减少 API 调用。

## 配置参数说明

### Whiskers Engine 参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| chunk_size | int | 512 | 文本分块大小 |
| chunk_overlap | int | 50 | 分块重叠长度 |
| enable_ocr | bool | True | 是否启用 OCR |
| vector_model | str | "BGE-M3" | 向量化模型 |
| vector_size | int | 1024 | 向量维度 |

### Memory 参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| l1_ttl | int | 3600 | L1 记忆 TTL（秒） |
| decay_rate | float | 0.1 | 记忆衰减速率 |
| archive_threshold | float | 0.05 | 归档阈值 |

### Retrieval 参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| top_k | int | 10 | 检索数量 |
| pounce_threshold | float | 0.85 | 扑击阈值 |
| hyde_enabled | bool | True | 是否启用 HyDE |

### Grooming 参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| min_confidence | float | 0.7 | 最低置信度 |
| hallucination_threshold | float | 0.6 | 幻觉判定阈值 |

### Purr 参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| default_tone | str | "friendly" | 默认语气 |
| default_detail_level | int | 2 | 默认详细程度 |

## 故障排查

### 问题 1: 无法启动 Dashboard

**原因**: 端口被占用
**解决**: 更换端口或关闭占用端口的程序

```bash
python -m necorag.dashboard.dashboard --port 8080
```

### 问题 2: 配置保存失败

**原因**: 配置目录无写入权限
**解决**: 检查目录权限或更换配置目录

```bash
python -m necorag.dashboard.dashboard --config-dir /tmp/necorag_configs
```

### 问题 3: API 调用返回 404

**原因**: Profile ID 不存在
**解决**: 先获取所有 Profile 列表，确认正确的 ID

## 后续优化方向

1. **实时监控**：WebSocket 实时推送统计信息
2. **参数推荐**：基于历史数据推荐最优参数
3. **A/B 测试**：支持配置对比测试
4. **权限管理**：多用户权限控制
5. **审计日志**：配置变更历史记录

---

*Let's make AI think like a brain, and act like a cat.* 🐱🧠
