<div align="center">

# NecoRAG

**Neuro-Cognitive Retrieval-Augmented Generation**

**模拟人脑双系统记忆与认知科学理论，构建下一代认知型 RAG 框架**

*Let's make AI think like a brain!* 🧠

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Alpha-orange.svg)]()

[English](#english) | [中文文档](#中文文档)

</div>

---

# 中文文档

## 📖 项目简介

NecoRAG 是一个创新的认知型 RAG 框架，模拟人脑的双系统记忆理论和神经认知科学原理。通过五层架构设计，实现了从感知到交互的完整认知闭环。

### 核心特性

- 🧠 **类脑记忆结构**：三层记忆系统（工作记忆 L1 + 语义记忆 L2 + 情景图谱 L3）
- ⚡ **智能早停机制**：Early Termination 策略精准捕捉关键信息
- 🔄 **自我反思能力**：Refinement Agent 幻觉自检与知识进化
- 🎨 **可解释性输出**：思维链可视化，展示推理过程
- ⚙️ **配置管理系统**：Web Dashboard 实时配置和监控

## 🏗️ 核心架构

NecoRAG 采用"五层认知"分层架构，每一层对应人脑认知机制的不同阶段：

```
┌─────────────────────────────────────────────────────────┐
│                NecoRAG 五层架构                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🎨 Layer 5: Response Interface (交互层)                │
│     响应接口 - 情境自适应生成与可解释性输出              │
│     • 用户画像适配                                       │
│     • Tone/Detail Level 调整                            │
│     • 思维链可视化                                       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🔄 Layer 4: Refinement Agent (巩固层)                  │
│     精炼代理 - 异步固化、幻觉自检与记忆修剪              │
│     • Generator → Critic → Refiner 闭环                 │
│     • 幻觉检测                                           │
│     • 知识固化                                           │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⚡ Layer 3: Adaptive Retrieval (检索层)                │
│     自适应检索 - 混合检索与重排序                        │
│     • 多跳联想检索                                       │
│     • HyDE 增强                                          │
│     • Novelty Re-ranker                                  │
│     • 早停机制（Early Termination）                      │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  💾 Layer 2: Hierarchical Memory (记忆层)               │
│     层级记忆存储 - 分层存储与管理                        │
│     • L1 工作记忆 (Redis)                                │
│     • L2 语义记忆 (Qdrant/Milvus)                        │
│     • L3 情景图谱 (Neo4j/NebulaGraph)                    │
│     • 动态权重衰减                                       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📄 Layer 1: Perception Engine (感知层)                 │
│     感知引擎 - 多模态数据的高精度编码与情境标记           │
│     • 深度文档解析 (RAGFlow)                             │
│     • 多维度向量化 (BGE-M3)                              │
│     • 情境标签生成器                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/NecoRAG/core.git
cd core

# 安装依赖
pip install -r requirements.txt

# 或使用 pip 安装（发布后）
pip install necorag
```

### 基础使用

```python
from necorag import (
    PerceptionEngine,
    MemoryManager,
    AdaptiveRetriever,
    RefinementAgent,
    ResponseInterface
)

# 1. 初始化组件
engine = PerceptionEngine(chunk_size=512)
memory = MemoryManager()
retriever = AdaptiveRetriever(memory=memory)
refinement = RefinementAgent(memory=memory)
interface = ResponseInterface(memory=memory)

# 2. 处理文档
chunks = engine.process_file("document.pdf")

# 3. 存储知识
for chunk in chunks:
    memory.store(chunk)

# 4. 检索与生成
query = "什么是深度学习？"
results = retriever.retrieve(query)
answer = refinement.process(query, [r.content for r in results])
response = interface.respond(query, answer)

print(response.content)
print(response.thinking_chain)  # 查看思维链
```

### 启动 Dashboard

```bash
# 方式 1: Python 脚本
python start_dashboard.py

# 方式 2: Windows
start_dashboard.bat

# 方式 3: Linux/Mac
./start_dashboard.sh

# 方式 4: Python 模块
python -m necorag.dashboard.dashboard
```

访问地址：
- **Web UI**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 📦 模块详解

### 1. Perception Engine - 感知引擎

**功能**：多模态数据的高精度编码与情境标记

**核心能力**：
- 📄 深度文档解析（集成 RAGFlow）
- 🔢 多维度向量化（BGE-M3：稠密向量 + 稀疏向量 + 实体三元组）
- 🏷️ 情境标签生成（时间、情感、重要性、主题）

**使用示例**：
```python
from necorag import PerceptionEngine

engine = PerceptionEngine(
    chunk_size=512,
    chunk_overlap=50,
    enable_ocr=True
)

# 处理文件
chunks = engine.process_file("report.pdf")

# 处理文本
chunks = engine.process_text("这是一段文本...")
```

**配置参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chunk_size | int | 512 | 分块大小 |
| chunk_overlap | int | 50 | 分块重叠 |
| enable_ocr | bool | True | 启用 OCR |
| vector_model | str | BGE-M3 | 向量化模型 |

📖 [详细文档](src/perception/README.md)

---

### 2. Hierarchical Memory - 层级记忆存储

**功能**：分层存储，模拟短期工作记忆与长期结构化记忆

**三层架构**：
- **L1 工作记忆** (Redis)：当前会话上下文、用户意图轨迹，TTL 自动过期
- **L2 语义记忆** (Qdrant/Milvus)：高维向量存储，模糊匹配与直觉检索
- **L3 情景图谱** (Neo4j/NebulaGraph)：实体关系网络，多跳推理

**核心创新**：
动态权重衰减机制：
```
weight(t) = initial_weight × e^(-λt) × access_frequency
```

**使用示例**：
```python
from necorag import MemoryManager

memory = MemoryManager()

# 存储知识
memory_id = memory.store(chunk)

# 检索知识
results = memory.retrieve(
    query="机器学习",
    query_vector=query_vector,
    layers=[MemoryLayer.L2, MemoryLayer.L3]
)

# 记忆巩固
memory.consolidate()

# 主动遗忘
forgotten = memory.forget(threshold=0.05)
```

**配置参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| l1_ttl | int | 3600 | L1 TTL（秒） |
| decay_rate | float | 0.1 | 衰减速率 |
| archive_threshold | float | 0.05 | 归档阈值 |

📖 [详细文档](src/memory/README.md)

---

### 3. Adaptive Retrieval - 自适应检索

**功能**：基于扩散激活理论的混合检索与重排序

**核心特性**：
- 🔄 多跳联想检索（实体 A → B → C）
- 🎯 HyDE 增强（解决提问模糊问题）
- 📊 Novelty Re-ranker（抑制重复，优先新颖知识）
- ⚡ 早停机制（一旦置信度超过阈值，立即终止检索）

**使用示例**：
```python
from necorag import AdaptiveRetriever

retriever = AdaptiveRetriever(
    memory=memory,
    confidence_threshold=0.85
)

# 基础检索
results = retriever.retrieve(query, top_k=10)

# HyDE 增强检索
results = retriever.retrieve_with_hyde(query)

# 多跳检索
results = retriever.multi_hop_retrieve(entity="AI", hops=3)

# 查看检索路径
print(retriever.get_retrieval_trace())
```

**配置参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| top_k | int | 10 | 检索数量 |
| confidence_threshold | float | 0.85 | 早停阈值 |
| hyde_enabled | bool | True | 启用 HyDE |

📖 [详细文档](src/retrieval/README.md)

---

### 4. Refinement Agent - 精炼代理

**功能**：异步知识固化、幻觉自检与记忆修剪

**核心闭环**：
```
Generator → Critic → Refiner
    ↓
HallucinationDetector
    ↓
KnowledgeConsolidator + MemoryPruner
```

**使用示例**：
```python
from necorag import RefinementAgent

refinement = RefinementAgent(
    memory=memory,
    max_iterations=3
)

# 处理查询
result = refinement.process(query, evidence)

print(result.answer)
print(result.confidence)
print(result.hallucination_report)

# 运行后台任务
await refinement.run_background_tasks()
```

**配置参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| min_confidence | float | 0.7 | 最低置信度 |
| hallucination_threshold | float | 0.6 | 幻觉判定阈值 |

📖 [详细文档](src/refinement/README.md)

---

### 5. Response Interface - 响应接口

**功能**：情境自适应生成与可解释性输出

**核心特性**：
- 👤 用户画像适配（专业程度、交互风格、偏好领域）
- 🎨 Tone 适配（专业严谨/亲切友好/幽默轻松）
- 📝 Detail Level 调整（4 级详细程度）
- 🧠 思维链可视化（检索路径 + 证据来源 + 推理过程）

**使用示例**：
```python
from necorag import ResponseInterface

interface = ResponseInterface(memory=memory)

# 生成响应
response = interface.respond(
    query=query,
    refinement_result=refinement_result,
    session_id="user_123",
    tone="friendly"
)

print(response.content)
print(response.thinking_chain)
```

**输出示例**：
```
🔍 检索路径：
  1. 查询理解：识别实体"深度学习"
  2. 向量检索：在 L2 语义记忆中检索
  3. 图谱推理：发现相关路径

📚 证据来源：
  - [证据 1] 文档 A (相关度: 0.89)
  - [证据 2] 文档 B (相关度: 0.85)

💡 答案：
  深度学习是机器学习的一个分支...
```

📖 [详细文档](src/response/README.md)

---

### 6. Dashboard - 配置管理系统 ⭐ NEW

**功能**：Web 界面管理和配置所有模块参数

**核心能力**：
- ⚙️ 配置 Profile 管理（创建/编辑/删除/导入导出）
- 🎛️ 模块参数配置（五大模块完整参数）
- 📊 实时统计监控
- 🔌 RESTful API

**Web UI 界面**：
- 现代化响应式设计
- Profile 列表管理
- 参数实时编辑
- 统计信息展示

**使用示例**：
```python
from necorag.dashboard import ConfigManager, DashboardServer

# 配置管理
config_manager = ConfigManager()
profile = config_manager.create_profile("生产环境")

# 更新参数
config_manager.update_profile(profile.profile_id, {
    "retrieval_config": {
        "top_k": 20,
        "pounce_threshold": 0.90
    }
})

# 启动 Dashboard
server = DashboardServer(port=8000)
server.run()
```

**API 接口**：
```bash
# 获取所有 Profiles
GET /api/profiles

# 创建 Profile
POST /api/profiles

# 更新模块参数
PUT /api/profiles/{id}/modules/retrieval

# 获取统计信息
GET /api/stats
```

📖 [详细文档](necorag/dashboard/README.md) | [使用指南](DASHBOARD_GUIDE.md)

## 🎯 核心创新点

### 1. 记忆权重衰减机制

模拟生物记忆的巩固与遗忘：
```python
weight(t) = initial_weight × e^(-λt) × access_frequency
```

### 2. 早停机制 (Early Termination)

智能检索终止策略，当置信度达标时立即返回：
```python
if confidence > threshold:
    return results  # 立即终止检索
```

### 3. 思维链可视化

展示 AI 的思考过程：
- 检索路径图
- 证据来源追溯
- 推理过程展示

### 4. 幻觉自检闭环

Generator → Critic → Refiner 三重验证：
- 事实一致性检查
- 证据支撑度验证
- 逻辑连贯性分析

## 📊 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 检索准确率 (Recall@K) | +20% | 相比传统 Vector RAG |
| 幻觉率 | < 5% | 通过 Refinement Agent |
| 简单查询延迟 | < 800ms | 首字延迟 |
| 复杂查询延迟 | < 1500ms | 多跳+重排 |
| 上下文压缩率 | -40% | 通过记忆衰减 |

## 🗓️ 开发路线图

### Phase 1: 骨架搭建 (MVP) - ✅ 2026 Q2
- ✅ Perception Engine 基础对接
- ✅ Hierarchical Memory 三层架构
- ✅ 基本 Vector + Graph 混合检索
- ✅ NecoRAG Core SDK (Python)
- ✅ Dashboard 配置管理系统

### Phase 2: 大脑注入 - 🔄 2026 Q3
- 🔄 集成 LangGraph 实现 Refinement Agent
- 🔄 动态重排序与 Novelty 检测
- 📦 NecoRAG Server (Docker 一键部署)
- 🎨 Dashboard 实时监控增强

### Phase 3: 进化与生态 - 📅 2026 Q4
- 🚀 异步知识固化与自动遗忘
- 📊 可视化调试面板 (NecoRAG Dashboard)
- 🔌 插件市场
- 🌍 社区运营

## 🛠️ 技术栈

### 核心组件

| 组件 | 推荐开源项目 | 用途 |
|------|------------|------|
| 编排引擎 | LangGraph | 检索-反思-校正闭环 |
| 文档解析 | RAGFlow | 深度文档解析 |
| 向量数据库 | Qdrant | 向量检索 |
| 图数据库 | Neo4j | 图谱推理 |
| 缓存 | Redis | 工作记忆 |
| 嵌入模型 | BGE-M3 | 向量化 |
| 重排序 | BGE-Reranker-v2 | 精排 |
| Web 框架 | FastAPI | Dashboard |

### 依赖安装

```bash
# 基础依赖
pip install numpy python-dateutil

# Dashboard 依赖
pip install fastapi uvicorn pydantic

# 完整依赖
pip install -r requirements.txt
```

## 📚 文档导航

### 模块文档
- [Perception Engine](src/perception/README.md) - 感知层设计
- [Hierarchical Memory](src/memory/README.md) - 记忆层设计
- [Adaptive Retrieval](src/retrieval/README.md) - 检索层设计
- [Refinement Agent](src/refinement/README.md) - 巩固层设计
- [Response Interface](src/response/README.md) - 交互层设计
- [Dashboard](src/dashboard/README.md) - 配置管理系统

### 指南文档
- [Dashboard 使用指南](DASHBOARD_GUIDE.md)
- [项目创建总结](PROJECT_SUMMARY.md)
- [Dashboard 更新说明](DASHBOARD_UPDATE.md)

### 示例代码
- [完整使用示例](example_usage.py)
- [Dashboard 示例](dashboard_demo.py)
- [导入测试](test_imports.py)

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下开源项目：

- [RAGFlow](https://github.com/infiniflow/ragflow) - 深度文档解析
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) - 向量化模型
- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [Neo4j](https://neo4j.com/) - 图数据库
- [LangGraph](https://github.com/langchain-ai/langgraph) - 编排引擎
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

# English

## Overview

NecoRAG is an innovative cognitive RAG framework that simulates the human brain's dual-system memory theory and neuroscience principles. Through a five-layer architecture design, it achieves a complete cognitive loop from perception to interaction.

### Key Features

- 🧠 **Brain-like Memory Structure**: Three-layer memory system (L1 Working + L2 Semantic + L3 Episodic)
- ⚡ **Early Termination**: Intelligent retrieval termination strategy
- 🔄 **Self-reflection**: Refinement Agent for hallucination detection and knowledge evolution
- 🎨 **Explainable Output**: Thinking chain visualization
- ⚙️ **Configuration Management**: Web Dashboard for real-time configuration

## Quick Start

### Installation

```bash
pip install necorag
```

### Basic Usage

```python
from necorag import (
    PerceptionEngine,
    MemoryManager,
    AdaptiveRetriever,
    RefinementAgent,
    ResponseInterface
)

# Initialize
engine = PerceptionEngine()
memory = MemoryManager()
retriever = AdaptiveRetriever(memory=memory)
refinement = RefinementAgent(memory=memory)
interface = ResponseInterface(memory=memory)

# Process documents
chunks = engine.process_file("document.pdf")

# Store knowledge
for chunk in chunks:
    memory.store(chunk)

# Retrieve and generate
query = "What is deep learning?"
results = retriever.retrieve(query)
answer = refinement.process(query, [r.content for r in results])
response = interface.respond(query, answer)

print(response.content)
```

### Start Dashboard

```bash
python start_dashboard.py
```

Visit: http://localhost:8000

## Architecture

NecoRAG adopts a "five-layer cognitive" architecture:

1. **Perception Engine** (Perception) - Document parsing and encoding
2. **Hierarchical Memory** (Memory) - Three-layer storage system
3. **Adaptive Retrieval** (Retrieval) - Hybrid search and re-ranking
4. **Refinement Agent** (Consolidation) - Hallucination detection and knowledge consolidation
5. **Response Interface** (Interaction) - Context-adaptive generation

## Performance Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Recall@K | +20% | vs. traditional Vector RAG |
| Hallucination Rate | < 5% | Via Refinement Agent |
| Simple Query Latency | < 800ms | First token latency |
| Context Compression | -40% | Via memory decay |

## Documentation

- [Perception Engine](src/perception/README.md)
- [Hierarchical Memory](src/memory/README.md)
- [Adaptive Retrieval](src/retrieval/README.md)
- [Refinement Agent](src/refinement/README.md)
- [Response Interface](src/response/README.md)
- [Dashboard](src/dashboard/README.md)

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Let's make AI think like a brain!** 🧠

Made with ❤️ by NecoRAG Team

[GitHub](https://github.com/NecoRAG/core) | [Documentation](https://github.com/NecoRAG/core#readme) | [Issues](https://github.com/NecoRAG/core/issues)

</div>
