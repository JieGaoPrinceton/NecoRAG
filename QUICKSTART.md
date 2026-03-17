# NecoRAG 快速开始指南

## 🎯 5 分钟上手 NecoRAG

### 第一步：安装依赖

```bash
# 进入项目目录
cd NecoRAG

# 安装依赖
pip install -r requirements.txt
```

### 第二步：运行测试

```bash
# 测试模块导入
python test_imports.py
```

**预期输出**：
```
测试 NecoRAG 模块导入...

[OK] 导入 necorag
[OK] 导入 necorag.whiskers
[OK] 导入 necorag.memory
[OK] 导入 necorag.retrieval
[OK] 导入 necorag.grooming
[OK] 导入 necorag.purr

所有模块导入成功！
```

### 第三步：运行示例

```bash
# 运行完整示例
python example_usage.py
```

**示例内容**：
1. Whiskers Engine - 文档解析与编码
2. Memory Manager - 知识存储与检索
3. Pounce Retriever - 智能检索与重排序
4. Grooming Agent - 答案生成与幻觉检测
5. Purr Interface - 情境自适应交互

### 第四步：启动 Dashboard

```bash
# 方式 1: Python 脚本
python start_dashboard.py

# 方式 2: Windows
start_dashboard.bat

# 方式 3: Linux/Mac
./start_dashboard.sh
```

**访问地址**：
- Web UI: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 📚 核心概念

### 五层架构

```
Whiskers Engine (感知层)
    ↓
Nine-Lives Memory (记忆层)
    ↓
Pounce Strategy (检索层)
    ↓
Grooming Agent (巩固层)
    ↓
Purr Interface (交互层)
```

### 最小工作示例

```python
from necorag import WhiskersEngine, MemoryManager, PounceRetriever

# 1. 初始化
engine = WhiskersEngine()
memory = MemoryManager()
retriever = PounceRetriever(memory=memory)

# 2. 处理文本
chunks = engine.process_text("深度学习是机器学习的一个分支...")

# 3. 存储知识
for chunk in chunks:
    memory.store(chunk)

# 4. 检索知识
results = retriever.retrieve("什么是深度学习？")

# 5. 查看结果
for r in results[:3]:
    print(f"分数: {r.score:.3f}")
    print(f"内容: {r.content[:100]}")
```

---

## 🎨 Dashboard 使用

### 1. 创建配置 Profile

1. 访问 http://localhost:8000
2. 点击 "+ 新建 Profile"
3. 输入名称和描述
4. 点击 "创建"

### 2. 配置模块参数

1. 选择一个 Profile
2. 切换到对应模块 Tab
3. 修改参数值
4. 点击 "保存配置"

### 3. 激活 Profile

点击 Profile 卡片上的 "激活" 按钮

### 4. 查看统计信息

Dashboard 底部实时显示：
- 文档总数
- 块总数
- 查询总数
- 活动会话

---

## 🔌 API 使用

### 获取所有 Profiles

```bash
curl http://localhost:8000/api/profiles
```

### 创建 Profile

```bash
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "测试配置", "description": "测试用"}'
```

### 更新模块参数

```bash
curl -X PUT http://localhost:8000/api/profiles/{profile_id}/modules/retrieval \
  -H "Content-Type: application/json" \
  -d '{
    "module": "retrieval",
    "parameters": {
      "top_k": 20,
      "pounce_threshold": 0.90
    }
  }'
```

---

## 💡 核心功能演示

### 1. 记忆衰减机制

```python
from necorag.memory import MemoryDecay

decay = MemoryDecay(decay_rate=0.1)

# 计算权重
weight = decay.calculate_weight(memory_item)

# 应用衰减
updates = decay.apply_decay(memories)

# 归档低权重记忆
to_archive = decay.archive_low_weight(memories)
```

### 2. Pounce 机制

```python
from necorag.retrieval import PounceRetriever

retriever = PounceRetriever(
    memory=memory,
    pounce_threshold=0.85
)

# 检索时自动判断是否扑击
results = retriever.retrieve(query)

# 查看检索路径
print(retriever.get_retrieval_trace())
```

### 3. 思维链可视化

```python
from necorag.purr import PurrInterface

interface = PurrInterface(memory=memory)

response = interface.respond(query, grooming_result)

# 输出思维链
print(response.thinking_chain)
```

输出示例：
```
🔍 检索路径：
  1. 查询理解：识别实体"深度学习"
  2. 向量检索：在 L2 语义记忆中检索
  3. 图谱推理：发现相关路径

📚 证据来源：
  - [证据 1] 文档 A (相关度: 0.89)
```

---

## 🛠️ 常见问题

### Q1: 如何安装所有依赖？

```bash
pip install -r requirements.txt
```

### Q2: Dashboard 启动失败？

检查端口是否被占用：
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

更换端口：
```bash
python start_dashboard.py --port 8080
```

### Q3: 如何使用自定义配置？

```python
from necorag.dashboard import ConfigManager

config_manager = ConfigManager(config_dir="./my_configs")
```

### Q4: 如何导出配置？

```python
config_manager.export_profile(
    profile_id=profile_id,
    export_path="./exported_config.json"
)
```

---

## 📖 进阶学习

### 深入理解各模块

1. [Whiskers Engine](necorag/whiskers/README.md) - 感知层设计
2. [Nine-Lives Memory](necorag/memory/README.md) - 记忆层设计
3. [Pounce Strategy](necorag/retrieval/README.md) - 检索层设计
4. [Grooming Agent](necorag/grooming/README.md) - 巩固层设计
5. [Purr Interface](necorag/purr/README.md) - 交互层设计

### Dashboard 详细指南

- [Dashboard 使用指南](DASHBOARD_GUIDE.md)
- [Dashboard API 文档](necorag/dashboard/README.md)

### 项目架构

- [项目总览](PROJECT_OVERVIEW.md)
- [项目总结](PROJECT_SUMMARY.md)

---

## 🎯 下一步

1. ✅ 集成真实组件（BGE-M3, Qdrant, Neo4j）
2. ✅ 完善单元测试
3. ✅ Docker 部署
4. ✅ 性能优化

---

## 💬 获取帮助

- **GitHub Issues**: https://github.com/NecoRAG/core/issues
- **文档**: https://github.com/NecoRAG/core#readme

---

<div align="center">

**祝你使用愉快！** 🐱🧠

*Let's make AI think like a brain, and act like a cat.*

</div>
