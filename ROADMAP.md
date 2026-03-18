# NecoRAG Roadmap / 路线图

> **"Let's make AI think like a brain, and act like a cat!"** 🧠🐱

本文档追踪 NecoRAG 项目的开发路线和下一步 TODO。

---

## ✅ Phase 1 — MVP 骨架 (已完成)

- [x] 五层认知架构设计
- [x] 核心抽象层 (30+ ABC, 40+ Data Model, 19+ Exception)
- [x] 感知引擎 (文档解析 / 分块策略 / 向量编码 / 上下文标注)
- [x] 层级记忆 (工作记忆 L1 / 语义记忆 L2 / 情景图谱 L3 / 衰减机制)
- [x] 自适应检索 (HyDE / 重排序 / 融合 / 提前终止)
- [x] 精炼代理 (Generator-Critic-Refiner 闭环 / 幻觉检测)
- [x] 响应接口 (语气适配 / 详细度适配 / 思维链可视化)
- [x] 领域权重系统 (时序衰减 / 关键词评分 / 复合权重)
- [x] Web Dashboard (FastAPI / 配置管理 / 统计)
- [x] 完善的双语文档 (50+ Markdown 文件)
- [x] 单元测试套件 (256 tests, 10 test files, 全模块覆盖)
- [x] pyproject.toml / requirements.txt 配置

---

## 🔄 Phase 2 — 组件集成 (下一步)

### 2.1 LLM 集成 (优先级: 🔴 高)

- [ ] 对接 OpenAI API (GPT-4 / GPT-3.5)
- [ ] 对接 Ollama 本地模型 (Llama, Qwen, etc.)
- [ ] 对接 Anthropic Claude API
- [ ] 实现 LLM 客户端连接池与重试机制
- [ ] 流式生成 (Streaming) 支持
- [ ] Token 用量追踪与限制

### 2.2 向量数据库集成 (优先级: 🔴 高)

- [ ] Qdrant 集成 (L2 语义记忆后端)
- [ ] Milvus 集成 (备选方案)
- [ ] HNSW 索引优化
- [ ] 混合搜索 (Dense + Sparse)
- [ ] 向量维度自适应

### 2.3 图数据库集成 (优先级: 🟡 中)

- [ ] Neo4j 集成 (L3 情景图谱后端)
- [ ] NebulaGraph 集成 (备选方案)
- [ ] Multi-hop BFS/DFS 算法实现
- [ ] 因果关系链追踪

### 2.4 缓存层集成 (优先级: 🟡 中)

- [ ] Redis 集成 (L1 工作记忆后端)
- [ ] TTL 自动过期机制
- [ ] Session 管理持久化

### 2.5 嵌入模型集成 (优先级: 🔴 高)

- [ ] BGE-M3 多语言嵌入模型集成
- [ ] BGE-Reranker-v2 重排序模型集成
- [ ] Sentence-Transformers 支持
- [ ] 本地 / 远程嵌入模型切换

### 2.6 文档解析增强 (优先级: 🟡 中)

- [ ] RAGFlow 深度解析集成
- [ ] PDF 解析 (PyMuPDF)
- [ ] Word 文档解析 (python-docx)
- [ ] HTML 解析 (BeautifulSoup)
- [ ] OCR 支持 (Tesseract)
- [ ] 表格识别与结构化
- [ ] 语义分块算法 (基于嵌入相似度)

---

## 📋 Phase 3 — 功能完善

### 3.1 NLP 增强 (优先级: 🟡 中)

- [ ] 时间实体识别 (TNER)
- [ ] 情感分析模型集成
- [ ] 主题分类与关键词提取
- [ ] 内容质量评分
- [ ] 查询复杂度分析

### 3.2 精炼代理增强 (优先级: 🟡 中)

- [ ] LangGraph 工作流集成
- [ ] LLM 驱动的质量评估
- [ ] 事实一致性检测 (基于 NLI 模型)
- [ ] 逻辑连贯性验证
- [ ] 证据支持度评分
- [ ] 查询日志分析与热点检测
- [ ] 知识缺口自动补充
- [ ] 片段合并算法

### 3.3 响应接口增强 (优先级: 🟢 低)

- [ ] LLM 驱动的内容摘要
- [ ] 内容扩展与深度分析
- [ ] 基于用户满意度的配置自适应
- [ ] 历史交互分析
- [ ] 多轮对话支持

---

## 🚀 Phase 4 — 生产化

### 4.1 部署 (优先级: 🔴 高)

- [ ] Dockerfile 与 Docker Compose
- [ ] Kubernetes 部署清单
- [ ] 环境变量配置管理
- [ ] Health Check 端点
- [ ] 日志聚合 (结构化 JSON 日志)

### 4.2 可观测性 (优先级: 🟡 中)

- [ ] Prometheus 指标导出
- [ ] 链路追踪 (OpenTelemetry)
- [ ] 性能基准测试套件
- [ ] 内存使用监控

### 4.3 CI/CD (优先级: 🔴 高)

- [ ] GitHub Actions 工作流 (lint / test / build)
- [ ] 自动化版本发布
- [ ] PyPI 包发布流程
- [ ] 代码覆盖率报告 (Codecov)

### 4.4 安全 (优先级: 🟡 中)

- [ ] 依赖漏洞扫描
- [ ] API 认证与授权
- [ ] 输入验证与清理
- [ ] 速率限制

---

## 🌟 Phase 5 — 生态系统

### 5.1 扩展性 (优先级: 🟢 低)

- [ ] 插件系统架构
- [ ] 自定义 Chunker / Encoder / Retriever 接口
- [ ] 第三方插件示例

### 5.2 开发者体验 (优先级: 🟡 中)

- [ ] CLI 工具 (necorag init / ingest / query)
- [ ] Jupyter Notebook 集成示例
- [ ] 交互式调试 Dashboard
- [ ] API 文档自动生成 (OpenAPI)

### 5.3 社区 (优先级: 🟢 低)

- [ ] 贡献者指南完善
- [ ] Issue / PR 模板
- [ ] 社区 Discussions
- [ ] 示例项目与教程

---

## 📊 性能目标

| 指标 | 目标 | 当前状态 |
|------|------|----------|
| Recall@K 提升 | +20% vs 传统 RAG | 架构就绪，待集成 |
| 幻觉率 | < 5% | 框架就绪，待 LLM 集成 |
| 简单查询延迟 | < 800ms | 待组件集成后测量 |
| 上下文压缩率 | -40% | 机制已实现 |

---

## 🗓 时间线

| 阶段 | 预计时间 | 状态 |
|------|----------|------|
| Phase 1: MVP | Q2 2026 | ✅ 完成 |
| Phase 2: 组件集成 | Q3 2026 | 🔄 进行中 |
| Phase 3: 功能完善 | Q3-Q4 2026 | 📅 计划中 |
| Phase 4: 生产化 | Q4 2026 | 📅 计划中 |
| Phase 5: 生态系统 | 2027+ | 📅 远期 |
