# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0-alpha] - 2026-03-17

### 新增 ✨

#### 核心模块
- ✅ Whiskers Engine (感知层) - 文档解析与向量化
  - 文档解析器 (支持 PDF/Word/Markdown)
  - 三种分块策略 (语义/固定/结构化)
  - 情境标签生成器 (时间/情感/重要性)
  - 向量编码器 (稠密/稀疏/实体三元组)

- ✅ Nine-Lives Memory (记忆层) - 三层存储系统
  - L1 工作记忆 (Redis TTL 机制)
  - L2 语义记忆 (向量存储与检索)
  - L3 情景图谱 (实体关系与多跳推理)
  - 记忆衰减机制 (动态权重管理)

- ✅ Pounce Strategy (检索层) - 智能检索
  - 多跳联想检索 (实体扩散)
  - HyDE 增强 (假设文档生成)
  - Novelty Re-ranker (新颖性重排序)
  - Pounce 机制 (智能终止检索)

- ✅ Grooming Agent (巩固层) - 知识固化
  - Generator-Critic-Refiner 闭环
  - 幻觉检测器 (事实/逻辑/证据)
  - 知识固化器 (缺口识别/碎片合并)
  - 记忆修剪器 (噪声清理/权重强化)

- ✅ Purr Interface (交互层) - 情境交互
  - 用户画像管理 (专业度/风格/偏好)
  - Tone 适配器 (专业/友好/幽默)
  - Detail Level 适配 (4级详细程度)
  - 思维链可视化 (检索路径/证据来源)

#### Dashboard 配置管理系统 ⭐

- ✅ Web UI 界面
  - 现代化响应式设计
  - Profile 管理
  - 参数实时编辑
  - 统计信息展示

- ✅ RESTful API
  - Profile CRUD 操作
  - 模块参数管理
  - 统计信息接口
  - 自动生成文档

- ✅ 配置管理
  - Profile 创建/编辑/删除
  - 配置导入/导出
  - 多环境支持
  - 参数持久化

#### 文档体系 📚

- ✅ 设计文档
  - 总体设计任务书
  - 5 个模块设计文档
  - Dashboard 设计文档

- ✅ 指南文档
  - README 主文档 (中英双语)
  - 快速开始指南
  - Dashboard 使用指南
  - 项目总结文档

- ✅ 示例代码
  - 完整使用示例
  - 导入测试脚本
  - Dashboard 启动脚本

#### 项目配置 ⚙️

- ✅ 依赖管理
  - requirements.txt
  - pyproject.toml
  - .gitignore

- ✅ 许可证
  - MIT License

- ✅ 启动脚本
  - Python 脚本
  - Windows 批处理
  - Linux/Mac Shell

### 技术债务 ⚠️

- 当前使用内存模拟实现，需要集成真实组件：
  - BGE-M3 向量化模型
  - Qdrant 向量数据库
  - Neo4j 图数据库
  - RAGFlow 文档解析
  - Redis 缓存
  - LangGraph 编排

### 性能指标 📊

| 指标 | 目标值 | 当前状态 |
|------|--------|---------|
| 检索准确率 | +20% | 架构完成 |
| 幻觉率 | < 5% | 框架就绪 |
| 简单查询延迟 | < 800ms | 待集成 |
| 上下文压缩 | -40% | 框架就绪 |

### 下一步计划 🗓️

#### Phase 2: 大脑注入 (2026 Q3)
- 🔄 集成真实组件 (BGE-M3, Qdrant, Neo4j)
- 🔄 完善 LangGraph 编排
- 📦 Docker 一键部署
- 🎨 Dashboard 实时监控增强

#### Phase 3: 进化与生态 (2026 Q4)
- 🚀 异步知识固化
- 📊 可视化调试面板
- 🔌 插件市场
- 🌍 社区运营

---

## 版本说明

- **[1.0.0-alpha]**: MVP 版本，完成架构和框架
- **[1.0.0-beta]**: Beta 版本，集成真实组件 (计划中)
- **[1.0.0]**: 正式版本，生产可用 (计划中)

---

<div align="center">

**Let's make AI think like a brain, and act like a cat.** 🐱🧠

</div>
