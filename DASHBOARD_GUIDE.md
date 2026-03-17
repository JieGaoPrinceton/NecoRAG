# NecoRAG Dashboard 快速指南

## 🎯 Dashboard 功能概览

NecoRAG Dashboard 是一个功能强大的 Web 管理界面，用于配置和管理 NecoRAG 的各个模块。

### 核心功能

1. **配置 Profile 管理**
   - 创建、编辑、删除配置 Profile
   - 多环境配置管理（开发、测试、生产）
   - 配置导入导出

2. **模块参数配置**
   - Whiskers Engine (感知层)
   - Nine-Lives Memory (记忆层)
   - Pounce Strategy (检索层)
   - Grooming Agent (巩固层)
   - Purr Interface (交互层)

3. **实时统计监控**
   - 文档和块统计
   - 查询历史
   - 性能指标

## 🚀 启动 Dashboard

### 方式 1: Python 脚本启动

```bash
python start_dashboard.py
```

### 方式 2: 命令行参数启动

```bash
python start_dashboard.py --host 127.0.0.1 --port 8080 --config-dir ./my_configs
```

### 方式 3: Windows 双击启动

双击 `start_dashboard.bat` 文件

### 方式 4: Linux/Mac 启动

```bash
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### 方式 5: Python 模块方式

```bash
python -m necorag.dashboard.dashboard
```

## 📱 Web 界面使用

### 1. 访问 Dashboard

启动后，在浏览器中访问：
- **Dashboard UI**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 2. 创建配置 Profile

1. 点击右上角 "+ 新建 Profile" 按钮
2. 输入 Profile 名称和描述
3. 点击 "创建" 按钮

### 3. 配置模块参数

1. 从左侧列表选择一个 Profile
2. 切换到对应的模块 Tab（Whiskers/Memory/Retrieval/Grooming/Purr）
3. 修改参数值
4. 点击 "保存配置" 按钮

### 4. 激活 Profile

1. 选择要激活的 Profile
2. 点击 "激活" 按钮
3. 该 Profile 将作为当前运行的配置

### 5. 查看统计信息

统计面板实时显示：
- 文档总数
- 块总数
- 查询总数
- 活动会话数

## 🔌 API 使用

### Profile 管理 API

```bash
# 获取所有 Profiles
curl http://localhost:8000/api/profiles

# 创建 Profile
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "测试配置", "description": "测试用"}'

# 更新 Profile
curl -X PUT http://localhost:8000/api/profiles/{profile_id} \
  -H "Content-Type: application/json" \
  -d '{
    "retrieval_config": {
      "top_k": 20
    }
  }'

# 激活 Profile
curl -X POST http://localhost:8000/api/profiles/{profile_id}/activate

# 删除 Profile
curl -X DELETE http://localhost:8000/api/profiles/{profile_id}
```

### 模块参数 API

```bash
# 获取模块参数
curl http://localhost:8000/api/profiles/{profile_id}/modules/whiskers

# 更新模块参数
curl -X PUT http://localhost:8000/api/profiles/{profile_id}/modules/retrieval \
  -H "Content-Type: application/json" \
  -d '{
    "module": "retrieval",
    "parameters": {
      "top_k": 15,
      "pounce_threshold": 0.88
    }
  }'
```

### 统计信息 API

```bash
# 获取统计信息
curl http://localhost:8000/api/stats

# 重置统计信息
curl -X POST http://localhost:8000/api/stats/reset
```

## 💡 Python 代码集成

### 加载配置并初始化模块

```python
from necorag.dashboard import ConfigManager
from necorag import WhiskersEngine, MemoryManager

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

### 动态更新配置

```python
# 运行时更新配置
config_manager.update_profile(active_profile.profile_id, {
    "retrieval_config": {
        "top_k": 20
    }
})

# 重新加载配置
active_profile = config_manager.get_active_profile()
```

## 📁 配置文件存储

配置文件存储在 `configs/` 目录下，每个 Profile 一个 JSON 文件：

```
configs/
├── profile_abc123.json    # Profile 1
├── profile_def456.json    # Profile 2
└── profile_ghi789.json    # Profile 3
```

### 配置文件格式

```json
{
  "profile_id": "abc123",
  "profile_name": "生产环境配置",
  "description": "用于生产环境的优化配置",
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
  "memory_config": {
    "module_type": "memory",
    "parameters": {
      "decay_rate": 0.1
    }
  },
  ...
}
```

## 🔧 高级功能

### 配置导入导出

```python
# 导出配置
config_manager.export_profile(
    profile_id="abc123",
    export_path="./exported_config.json"
)

# 导入配置
imported = config_manager.import_profile("./exported_config.json")
```

### 复制配置

```python
# 复制现有配置
new_profile = config_manager.duplicate_profile(
    profile_id="abc123",
    new_name="复制的配置"
)
```

### 多环境管理

```python
# 创建不同环境的配置
dev_profile = config_manager.create_profile("开发环境", "开发测试用")
test_profile = config_manager.create_profile("测试环境", "集成测试用")
prod_profile = config_manager.create_profile("生产环境", "生产环境用")

# 切换环境
config_manager.set_active_profile(prod_profile.profile_id)
```

## 🎨 自定义 Dashboard

### 修改端口

```bash
python start_dashboard.py --port 8080
```

### 修改配置目录

```bash
python start_dashboard.py --config-dir /path/to/configs
```

### 修改主机地址

```bash
python start_dashboard.py --host 127.0.0.1
```

## 📊 性能优化建议

1. **合理设置分块大小**: 512-1024 字符
2. **调整检索数量**: 根据需求设置 top_k
3. **优化扑击阈值**: 0.85-0.90 之间
4. **配置记忆衰减**: 根据数据量调整 decay_rate

## ❓ 常见问题

### Q: 如何查看所有可用参数？

A: 参考 `necorag/dashboard/README.md` 中的参数说明表格。

### Q: 配置修改后何时生效？

A: 配置保存后立即生效，但需要重新初始化模块才能应用新配置。

### Q: 如何备份配置？

A: 复制 `configs/` 目录，或使用导出功能导出单个 Profile。

### Q: Dashboard 无法访问怎么办？

A: 检查防火墙设置，确认端口未被占用。

---

*Let's make AI think like a brain, and act like a cat.* 🐱🧠
