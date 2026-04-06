# NecoRAG 模块化架构说明

## 📁 重构后的模块结构

本项目已按照认知科学五层架构进行了模块化重构，形成了清晰的层次结构：

```
src/
├── core/                    # 核心基础设施
│   ├── config.py           # 统一配置管理
│   ├── protocols.py        # 数据协议定义
│   ├── exceptions.py       # 异常体系
│   └── llm/                # LLM 客户端抽象
│
├── layer1_perception/      # 感知层 (Layer 1)
│   ├── engine.py           # 感知引擎
│   ├── encoder.py          # 多模态编码器
│   ├── chunker.py          # 自适应分块器
│   ├── parser.py           # 文档解析器
│   ├── tagger.py           # 语义标记器
│   └── models.py           # 感知数据模型
│
├── layer2_memory/          # 记忆层 (Layer 2)
│   ├── manager.py          # 记忆管理器
│   ├── working_memory.py   # 工作记忆
│   ├── semantic_memory.py  # 语义记忆
│   ├── episodic_graph.py   # 情景记忆图
│   ├── decay.py            # 记忆衰减机制
│   └── models.py           # 记忆数据模型
│
├── layer3_retrieval/       # 检索层 (Layer 3)
│   ├── retriever.py        # 自适应检索器
│   ├── hyde.py             # HyDE 增强器
│   ├── reranker.py         # 重排序器
│   ├── fusion.py           # 融合策略
│   ├── smart_routing/      # 智能路由
│   ├── web_search/         # 网络搜索
│   └── models.py           # 检索数据模型
│
├── layer4_consolidation/   # 巩固层 (Layer 4)
│   ├── agent.py            # 精炼代理
│   ├── generator.py        # 响应生成器
│   ├── critic.py           # 批判性评估
│   ├── refiner.py          # 优化器
│   ├── hallucination.py    # 幻觉检测
│   ├── consolidator.py     # 知识固化
│   ├── pruner.py           # 记忆修剪
│   └── models.py           # 精炼数据模型
│
├── layer5_interaction/     # 交互层 (Layer 5)
│   ├── interface.py        # 响应接口
│   ├── profile_manager.py  # 用户画像管理
│   ├── tone_adapter.py     # 语调适配器
│   ├── detail_adapter.py   # 细节适配器
│   ├── visualizer.py       # 思维链可视化
│   └── models.py           # 交互数据模型
│
├── modules/                # 功能增强模块
│   ├── classifier.py       # 意图分类器
│   ├── router.py           # 意图路由器
│   ├── semantic_analyzer.py # 语义分析器
│   ├── updater.py          # 知识更新器
│   ├── scheduler.py        # 更新调度器
│   ├── metrics.py          # 知识度量
│   ├── visualizer.py       # 知识可视化
│   ├── engine.py           # 自适应学习引擎
│   ├── feedback.py         # 反馈收集器
│   ├── strategy_optimizer.py # 策略优化器
│   ├── preference_predictor.py # 偏好预测器
│   ├── collective.py       # 集体智慧
│   └── models.py           # 模块数据模型
│
├── extensions/             # 可扩展组件
│   ├── base.py             # 插件基类
│   ├── manager.py          # 插件管理器
│   ├── registry.py         # 插件注册表
│   ├── auth.py             # 认证管理
│   ├── permission.py       # 权限控制
│   ├── protection.py       # 数据保护
│   ├── health.py           # 健康检查
│   ├── metrics.py          # 指标收集
│   ├── alerts.py           # 告警管理
│   ├── store.py            # 市场存储
│   ├── sandbox.py          # 沙箱隔离
│   ├── discovery.py        # 发现引擎
│   ├── quality.py          # 质量评估
│   ├── version_manager.py  # 版本管理
│   ├── dependency_resolver.py # 依赖解析
│   ├── installer.py        # 插件安装器
│   ├── repository.py       # 仓库管理
│   ├── client.py           # 市场客户端
│   ├── api.py              # REST API
│   └── models.py           # 扩展数据模型
│
├── dashboard/              # 可视化仪表板
│   ├── dashboard.py        # 主仪表板
│   ├── server.py           # Web 服务器
│   ├── components/         # UI 组件
│   └── models.py           # 仪表板模型
│
└── utils/                  # 工具函数
    └── ...                 # 各种辅助工具
```

## 🎯 模块职责说明

### 核心层 (Core)
- **职责**: 提供基础配置、协议定义和异常处理
- **特点**: 无外部依赖，被所有其他模块依赖

### 五层认知架构

#### Layer 1: 感知层 (Perception)
- **职责**: 多模态数据的编码和处理
- **模拟**: 人脑的感觉记忆系统
- **核心组件**: 编码器、分块器、解析器、标记器

#### Layer 2: 记忆层 (Memory)
- **职责**: 知识的分层存储与管理
- **模拟**: 人脑的三层记忆系统（工作记忆、语义记忆、情景记忆）
- **核心组件**: 记忆管理器、三种记忆实现、衰减机制

#### Layer 3: 检索层 (Retrieval)
- **职责**: 智能化的信息检索与重排序
- **模拟**: 人脑的记忆提取机制
- **核心组件**: 自适应检索器、HyDE 增强、融合策略、智能路由

#### Layer 4: 巩固层 (Consolidation)
- **职责**: 知识的异步固化、幻觉自检与记忆修剪
- **模拟**: 人脑的记忆巩固机制
- **核心组件**: 精炼代理、生成器、批判器、幻觉检测、固化器

#### Layer 5: 交互层 (Interaction)
- **职责**: 情境自适应生成与可解释性输出
- **模拟**: 人脑的决策与表达机制
- **核心组件**: 响应接口、用户画像、语调/细节适配器、可视化

### 功能模块层 (Modules)
- **职责**: 提供高级认知能力增强
- **包含**: 意图分析、知识演化、自适应学习
- **特点**: 可选启用，按需加载

### 扩展组件层 (Extensions)
- **职责**: 提供可插拔的增强功能
- **包含**: 插件系统、安全机制、监控告警、市场生态
- **特点**: 完全解耦，支持热插拔

### 可视化层 (Dashboard)
- **职责**: 提供系统监控和管理界面
- **包含**: Web 仪表板、配置管理、健康监控
- **特点**: 独立部署，可选启用

## 🔧 使用方式

### 导入示例

```python
# 导入核心层
from src.core import NecoRAGConfig, Document, Response

# 导入五层架构模块
from src.layer1_perception import PerceptionEngine
from src.layer2_memory import MemoryManager
from src.layer3_retrieval import AdaptiveRetriever
from src.layer4_consolidation import RefinementAgent
from src.layer5_interaction import ResponseInterface

# 导入功能模块
from src.modules import IntentClassifier, KnowledgeUpdater, AdaptiveLearningEngine

# 导入扩展组件
from src.extensions import PluginManager, HealthChecker, MarketplaceClient
```

### 统一入口

```python
# 通过主入口使用（推荐）
from src import NecoRAG, create_rag

rag = create_rag(config=NecoRAGConfig.default())
response = rag.query("你的问题")
```

## 📊 重构优势

1. **清晰的层次结构**: 使用 `layer1_` 到 `layer5_` 前缀明确标识五层架构
2. **职责分离**: 每层有独立的数据模型和业务逻辑
3. **后端抽象化**: 存储引擎可轻松替换
4. **统一接口**: 通过 Facade 模式提供简洁的访问入口
5. **可扩展性**: 插件系统和模块机制支持功能扩展
6. **向后兼容**: 保留原有模块作为别名，确保现有代码继续工作

## 🔄 迁移指南

原有模块路径仍然可用，但建议迁移到新的模块路径：

| 原路径 | 新路径 |
|--------|--------|
| `src/perception` | `src/layer1_perception` |
| `src/memory` | `src/layer2_memory` |
| `src/retrieval` | `src/layer3_retrieval` |
| `src/refinement` | `src/layer4_consolidation` |
| `src/response` | `src/layer5_interaction` |
| `src/intent` + `src/knowledge_evolution` + `src/adaptive` | `src/modules` |
| `src/plugins` + `src/security` + `src/monitoring` + `src/marketplace` | `src/extensions` |

## 📝 版本信息

- **重构版本**: v3.3.0-alpha
- **重构日期**: 2024
- **架构设计**: 基于神经认知科学双系统记忆理论
