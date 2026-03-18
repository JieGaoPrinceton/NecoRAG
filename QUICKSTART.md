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
# 测试模块导入（使用新的测试入口）
python test_init.py
```

**预期输出**：
```
测试 NecoRAG 模块导入...

[OK] 导入 src
[OK] 导入 src.perception (Whiskers Engine)
[OK] 导入 src.memory (Nine-Lives Memory)
[OK] 导入 src.retrieval (Pounce Strategy)
[OK] 导入 src.refinement (Grooming Agent)
[OK] 导入 src.response (Purr Interface)
[OK] 导入 src.dashboard (Dashboard)

所有模块导入成功！
```

### 第三步：运行示例

```bash
# 运行完整使用示例
python example_usage.py

# 或者运行调试面板示例（推荐）
python example/debug_panel_demo.py
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
- API文档：http://localhost:8000/docs
- **调试面板**: http://localhost:8000/debug ⭐ (v1.7.0 新增)

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

### 最小工作示例（推荐使用新路径）

```python
from src import PerceptionEngine, MemoryManager, AdaptiveRetriever

# 1. 初始化（使用重构后的模块名）
engine = PerceptionEngine()
memory = MemoryManager()
retriever = AdaptiveRetriever(memory=memory)

# 2. 处理文本
text = "深度学习是机器学习的一个分支..."
chunks = engine.process_text(text)

# 3. 存储知识
for chunk in chunks:
    memory.store(chunk)

# 4. 检索知识（支持领域权重计算）
results = retriever.retrieve(
    query="什么是深度学习？",
    domain_weight_enabled=True  # v1.7.0 新功能
)

# 5. 查看结果和检索路径
print(f"检索到 {len(results)} 条结果")
for r in results[:3]:
    print(f"\n分数：{r.score:.3f}")
    print(f"内容：{r.content[:100]}...")
    
# 6. 查看完整的检索路径（思维链可视化）
print("\n检索路径:")
print(retriever.get_retrieval_trace())
```

---

## 🎨 Dashboard 使用（含可视化调试面板）

### 1. 创建配置 Profile

1. 访问 http://localhost:8000
2. 点击 "+ 新建 Profile"
3. 输入名称和描述（如"开发环境"、"生产环境"）
4. 点击 "创建"

### 2. 配置模块参数（包含 v1.7.0 新模块）

1. 选择一个 Profile
2. 切换到对应模块 Tab：
   - **核心五层**：感知、记忆、检索、巩固、交互
   - **v1.7.0 新增**：意图分析、领域权重、知识演化、监控告警、安全、自适应优化、插件管理、Interface 模块
3. 修改参数值（实时生效）
4. 点击 "保存配置"

### 3. 激活与使用

点击 Profile 卡片上的 "激活" 按钮，然后重启应用即可生效。

### 4. 查看统计信息（实时监控）

Dashboard 底部实时显示：
- 文档总数 / 块总数
- 查询总数 / 活动会话
- **系统资源使用**：CPU、内存、磁盘、网络（20+ 指标）⭐
- **错误统计**：错误分类、严重程度、恢复状态 ⭐

---

## 🔌 RESTful API 使用（v1.7.0 新增 Interface 模块）

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

### 更新模块参数（支持所有模块）

```bash
curl -X PUT http://localhost:8000/api/profiles/{profile_id}/modules/retrieval \
  -H "Content-Type: application/json" \
  -d '{
    "module": "retrieval",
    "parameters": {
      "top_k": 20,
      "pounce_threshold": 0.90,
      "domain_weight_enabled": true  // v1.7.0 新功能
    }
  }'
```

### 获取统计信息（详细版）

```bash
curl http://localhost:8000/api/stats | jq .
```

### WebSocket 实时推送（v1.7.0 新增）

```python
import asyncio
import websockets

async def listen():
    async with websockets.connect("ws://localhost:8000/ws/app") as ws:
        while True:
            msg = await ws.recv()
            print(f"收到推送：{msg}")

asyncio.run(listen())
```

---

## 💡 v1.7.0 核心功能演示

### 1. 记忆衰减机制（增强版）

```python
from src.memory import MemoryDecay

decay = MemoryDecay(
    decay_rate=0.1,
    consolidation_interval=300  # v1.7.0: 支持固化间隔配置
)

# 计算权重（融合时间衰减和访问频率）
weight = decay.calculate_weight(memory_item)

# 应用衰减（自动触发巩固机制）
updates = decay.apply_decay(memories)

# 归档低权重记忆（阈值可配置）
to_archive = decay.archive_low_weight(memories, threshold=0.05)
```

### 2. Pounce 机制（智能早停）

```python
from src.retrieval import AdaptiveRetriever

retriever = AdaptiveRetriever(
    memory=memory,
    confidence_threshold=0.85,  # 置信度阈值达标时立即停止
    domain_weight_enabled=True  # v1.7.0: 启用领域权重计算
)

# 检索时自动判断是否扑击（早停）
results = retriever.retrieve(query)

# 查看检索路径（思维链可视化）
print(retriever.get_retrieval_trace())
```

**输出示例**：
```
🔍 检索路径:
  1. 查询理解：识别实体"深度学习"
  2. 向量检索：在 L2 语义记忆中检索到 15 条结果
  3. 领域权重计算：融合时间衰减和相关性 ⭐
  4. 重排序：按新颖性和相关性重新排序
  5. 早停判定：置信度 0.92 > 阈值 0.85，终止检索 ✅
```

### 3. 思维链可视化（增强版）

```python
from src.response import ResponseInterface

interface = ResponseInterface(
    memory=memory,
    enable_thinking_chain=True  # 默认开启思维链可视化
)

response = interface.respond(
    query=query,
    refinement_result=grooming_result,
    include_evidence_sources=True  # v1.7.0: 包含证据来源追溯
)

# 输出详细的思维链（检索路径 + 证据来源 + 推理过程）
print(response.thinking_chain)
print(response.evidence_sources)  # v1.7.0 新增
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

## 🛠️ 常见问题（v1.7.0 更新）

### Q1: 如何安装所有依赖？

```bash
# 仅安装核心依赖
pip install -r requirements.txt

# 安装 v1.7.0 新功能依赖（推荐）
pip install jieba scipy prometheus-client PyJWT python-jose plotly scikit-learn

# 安装开发依赖
cd tools && pip install -r requirements-dev.txt
```

### Q2: Dashboard 启动失败？

检查端口占用并更换端口：
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# 更换端口启动（支持 --host 参数）
python start_dashboard.py --port 8080 --host 0.0.0.0
```

### Q3: 如何使用自定义配置目录？

```python
from src.dashboard import ConfigManager

# 指定自定义配置目录（支持相对路径）
config_manager = ConfigManager(config_dir="./my_configs")

# 导出配置到指定位置（支持 JSON/YAML格式）
config_manager.export_profile(
    profile_id=profile_id,
    export_path="./exported_config.json",
    format='json'  # 或 'yaml'
)

# 从导出文件导入配置（支持批量导入）
config_manager.import_profile(
    import_path="./exported_config.json",
    profile_name="导入的配置"
)
```

---

## 📖 进阶学习（文档已移动到模块目录）

### 深入理解各模块（使用新路径）

1. [Perception Engine](src/perception/README.md) - 感知层设计 ⭐
2. [Hierarchical Memory](src/memory/README.md) - 记忆层设计 ⭐
3. [Adaptive Retrieval](src/retrieval/README.md) - 检索层设计 ⭐
4. [Refinement Agent](src/refinement/README.md) - 巩固层设计 ⭐
5. [Response Interface](src/response/README.md) - 交互层设计 ⭐
6. [Dashboard](src/dashboard/README.md) - 配置管理系统 ⭐
7. [Debug Panel](src/dashboard/debug/README.md) - 可视化调试面板 ⭐ NEW

### v1.7.0 新增模块文档

8. [Intent Analyzer](src/intent/README.md) - 意图分析系统 ⭐
9. [Domain Weight](src/domain/README.md) - 领域权重系统 ⭐
10. [Knowledge Evolution](src/knowledge_evolution/README.md) - 知识演化 ⭐
11. [Monitoring & Alerts](src/monitoring/README.md) - 监控告警 ⭐
12. [Security](src/security/README.md) - 安全模块 ⭐
13. [Adaptive Optimization](src/adaptive/README.md) - 自适应优化 ⭐
14. [Plugins](src/plugins/README.md) - 插件扩展系统 ⭐
15. [Interface](interface/README.md) - Interface 模块 ⭐

### Dashboard 详细指南（文档已移动）

- [Dashboard 使用指南](src/dashboard/USAGE_GUIDE.md) ⭐
- [调试面板使用指南](src/dashboard/debug/README.md) ⭐ NEW
- [API参考文档](docs/wiki/调试面板系统/API参考.md) ⭐ NEW

### 项目架构与总结（更新版）

- [项目总览](README.md) - 项目主文档 ⭐
- [快速开始](QUICKSTART.md) - 本指南 ⭐
- [项目完成标志](PROJECT_COMPLETE.md) - v1.7.0 完成报告 ⭐
- [最终状态报告](PROJECT_FINAL_STATUS.md) - 技术架构和成果 ⭐
- [更新日志](CHANGELOG.md) - 详细变更记录 ⭐

---

## 🎯 下一步（结合当前进度）

### ✅ 已完成（v1.7.0-alpha）
- ✅ 五层认知架构框架搭建
- ✅ 可视化调试面板完整实现（思维路径可视化、实时监控、A/B 测试）
- ✅ 8 个新增核心模块（意图分析、领域权重、知识演化、监控告警、安全、自适应优化、插件系统、Interface 模块）
- ✅ 性能监控系统（20+ 指标实时监控）
- ✅ 智能错误处理（熔断器模式、自动恢复策略）
- ✅ 完整的文档体系（16 万 + 行文档，20+ 篇详细文档）
- ✅ 测试套件（单元测试 + 集成测试 + 性能测试）

### 🔄 进行中（计划中）
- 🔄 集成真实组件（BGE-M3, Qdrant, Neo4j, RAGFlow）
- 🔄 Docker 一键部署配置
- 🔄 生产环境认证和授权系统增强
- 🔄 分布式系统监控支持（Prometheus + Grafana 深度集成）
- 🔄 移动端应用开发（响应式布局已支持）

### 📅 未来规划（2026 Q4）
- 🚀 异步知识固化与自动遗忘机制
- 🔌 插件市场和扩展生态系统
- 🌍 社区运营和开源生态建设

---

## 💬 获取帮助（多渠道支持）

### 官方渠道
- **Gitee Issues**: https://gitee.com/qijie2026/NecoRAG/issues ⭐
- **GitHub Issues**: https://github.com/NecoRAG/core/issues
- **文档中心**: [docs/wiki/README.md](docs/wiki/README.md) ⭐
- **讨论区**: [GitHub Discussions](https://github.com/NecoRAG/core/discussions)

### 社区资源
- **Wiki 知识库**: [结构化文档库](docs/wiki/) - 20+ 篇详细教程 ⭐
- **示例代码库**: [example/](example/) - 8+ 份实战示例 ⭐
- **测试套件**: [tests/](tests/) - 完整的测试用例参考 ⭐

---

<div align="center">

**祝你使用愉快！** 🐱🧠

*Let's make AI think like a brain, and act like a cat.*

**NecoRAG v1.7.0-alpha** | 最后更新：2026-03-19  
[查看完整文档](README.md) | [Wiki 知识库](docs/wiki/README.md) | [示例代码](example/)

</div>
