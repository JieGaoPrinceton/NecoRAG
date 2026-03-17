# 📚 文档导航

欢迎来到 NecoRAG 文档中心！

## 🚀 快速开始

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主文档 - 完整架构和使用说明 |
| [QUICKSTART.md](../QUICKSTART.md) | 5 分钟快速上手指南 |
| [PROJECT_FINAL_SUMMARY.md](../PROJECT_FINAL_SUMMARY.md) | 项目完整总结 |

## 📖 设计文档

### 总体设计
| 文档 | 说明 |
|------|------|
| [设计任务书](../design/design.md) | NecoRAG 总体设计任务书 |

### 模块设计
| 模块 | 文档 | 说明 |
|------|------|------|
| Layer 1 | [Whiskers Engine](../necorag/whiskers/README.md) | 感知层设计 - 文档解析与向量化 |
| Layer 2 | [Nine-Lives Memory](../necorag/memory/README.md) | 记忆层设计 - 三层存储系统 |
| Layer 3 | [Pounce Strategy](../necorag/retrieval/README.md) | 检索层设计 - 混合检索与重排序 |
| Layer 4 | [Grooming Agent](../necorag/grooming/README.md) | 巩固层设计 - 幻觉自检与知识固化 |
| Layer 5 | [Purr Interface](../necorag/purr/README.md) | 交互层设计 - 情境自适应生成 |
| Dashboard | [Dashboard](../necorag/dashboard/README.md) | 配置管理系统设计 |

## 📘 使用指南

| 文档 | 说明 |
|------|------|
| [Dashboard 使用指南](../DASHBOARD_GUIDE.md) | Dashboard 详细使用说明 |
| [完整使用示例](../example_usage.py) | Python 代码示例 |
| [导入测试](../test_imports.py) | 模块导入测试 |

## 🎯 架构概览

```
NecoRAG 五层架构
├── Layer 1: Whiskers Engine (感知层)
│   └── 文档解析、向量化、情境标签
├── Layer 2: Nine-Lives Memory (记忆层)
│   ├── L1 工作记忆 (Redis)
│   ├── L2 语义记忆 (Qdrant)
│   └── L3 情景图谱 (Neo4j)
├── Layer 3: Pounce Strategy (检索层)
│   └── 多跳检索、HyDE、重排序
├── Layer 4: Grooming Agent (巩固层)
│   └── 幻觉检测、知识固化、记忆修剪
└── Layer 5: Purr Interface (交互层)
    └── 用户画像、语气适配、思维链可视化
```

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| 编排引擎 | LangGraph |
| 文档解析 | RAGFlow |
| 向量数据库 | Qdrant / Milvus |
| 图数据库 | Neo4j / NebulaGraph |
| 缓存 | Redis |
| 嵌入模型 | BGE-M3 |
| 重排序 | BGE-Reranker-v2 |
| Web 框架 | FastAPI |

## 📊 学习路径

### 1. 入门级 (30分钟)
1. 阅读 [README.md](../README.md) 了解项目概况
2. 运行 [test_imports.py](../test_imports.py) 测试环境
3. 查看 [example_usage.py](../example_usage.py) 了解基本用法

### 2. 进阶级 (2小时)
1. 阅读 [QUICKSTART.md](../QUICKSTART.md)
2. 启动 Dashboard: `python start_dashboard.py`
3. 创建配置 Profile
4. 调整模块参数

### 3. 高级 (1天)
1. 阅读各模块设计文档
2. 理解记忆衰减机制
3. 研究 Pounce 检索策略
4. 分析 Grooming Agent 闭环

### 4. 专家级 (1周)
1. 集成真实组件 (BGE-M3, Qdrant, Neo4j)
2. 实现 LangGraph 编排
3. 优化检索性能
4. 开发自定义插件

## 🌟 核心创新点

1. **记忆权重衰减**: `weight(t) = initial × e^(-λt) × frequency`
2. **Pounce 机制**: 智能终止检索，模拟猫捕猎
3. **思维链可视化**: 展示 AI 推理过程
4. **幻觉自检闭环**: Generator → Critic → Refiner

## 🔗 外部资源

- [GitHub 仓库](https://github.com/NecoRAG/core)
- [Gitee 仓库](https://gitee.com/qijie2026/NecoRAG)
- [问题反馈](https://gitee.com/qijie2026/NecoRAG/issues)

## 📝 文档贡献

欢迎改进文档！

1. Fork 项目
2. 编辑文档
3. 提交 Pull Request

---

<div align="center">

**Let's make AI think like a brain, and act like a cat.** 🐱🧠

</div>
