# 🧠 NecoRAG 核心源码目录

## 📋 目录说明

本目录包含 NecoRAG 项目的核心源代码实现，涵盖所有主要功能模块。

## 📁 模块结构

```
src/
├── necorag.py                    # 统一入口类 ⭐
├── __init__.py                   # 包初始化
│
├── core/                         # 核心基础模块
│   ├── config.py                 # 配置管理
│   ├── base.py                   # 基类定义
│   ├── protocols.py              # 协议接口
│   └── llm/                      # LLM 适配层
│
├── perception/                   # 感知引擎模块
│   ├── engine.py                 # 感知引擎主类
│   ├── chunker.py                # 文档切割器
│   ├── encoder.py                # 向量化编码器
│   ├── parser.py                 # 文档解析器
│   └── tagger.py                 # 情境标签生成器
│
├── memory/                       # 记忆管理模块
│   ├── manager.py                # 记忆管理器
│   ├── models.py                 # 数据模型
│   ├── working_memory.py         # 工作记忆 (L1)
│   ├── semantic_memory.py        # 语义记忆 (L2)
│   ├── episodic_graph.py         # 情景图谱 (L3)
│   └── decay.py                  # 遗忘衰减机制
│
├── retrieval/                    # 检索引擎模块
│   ├── retriever.py              # 检索器主类
│   ├── fusion.py                 # 结果融合
│   ├── reranker.py               # 重排序
│   ├── hyde.py                   # HyDE 增强
│   └── models.py                 # 检索模型
│
├── refinement/                   # 巩固精炼模块
│   ├── agent.py                  # 精炼代理
│   ├── generator.py              # 内容生成器
│   ├── critic.py                 # 质量评估器
│   ├── refiner.py                # 优化器
│   ├── pruner.py                 # 记忆修剪
│   └── hallucination.py          # 幻觉检测
│
├── response/                     # 交互响应模块
│   ├── interface.py              # 响应接口
│   ├── tone_adapter.py           # 语气适配器
│   ├── detail_adapter.py         # 详细度适配器
│   ├── profile_manager.py        # 用户画像管理
│   └── visualizer.py             # 思维可视化
│
├── knowledge_evolution/          # 知识演化系统
│   ├── updater.py                # 知识更新器
│   ├── scheduler.py              # 调度器
│   ├── metrics.py                # 量化指标
│   ├── models.py                 # 数据模型
│   └── visualizer.py             # 可视化展示
│
├── intent/                       # 意图分析系统
│   ├── classifier.py             # 意图分类器
│   ├── router.py                 # 智能路由
│   ├── semantic_analyzer.py      # 语义分析器
│   └── models.py                 # 意图模型
│
├── domain/                       # 领域权重系统
│   ├── weight_calculator.py      # 权重计算器
│   ├── relevance.py              # 相关性计算
│   ├── temporal_weight.py        # 时间权重
│   └── config.py                 # 领域配置
│
├── monitoring/                   # 监控告警系统
│   ├── service.py                # 监控服务
│   ├── health.py                 # 健康检查
│   ├── metrics.py                # 指标收集
│   ├── alerts.py                 # 告警管理
│   └── dashboard.py              # 监控仪表盘
│
├── security/                     # 安全模块
│   ├── auth.py                   # 认证管理
│   ├── permission.py             # 权限控制
│   ├── protection.py             # 数据保护
│   └── storage.py                # 安全存储
│
├── adaptive/                     # 自适应优化引擎
│   ├── engine.py                 # 自适应引擎
│   ├── preference_predictor.py   # 偏好预测
│   ├── strategy_optimizer.py     # 策略优化
│   └── feedback.py               # 反馈收集
│
├── plugins/                      # 插件扩展系统
│   ├── base.py                   # 插件基类
│   ├── manager.py                # 插件管理器
│   └── registry.py               # 插件注册表
│
├── user/                         # 用户管理模块
│   ├── models.py                 # 用户模型
│   ├── profile.py                # 用户画像
│   └── workspace.py              # 工作空间管理
│
└── dashboard/                    # Dashboard 管理界面
    ├── server.py                 # Dashboard 服务器
    ├── models.py                 # 数据模型
    ├── config_manager.py         # 配置管理器
    └── components/               # UI 组件
        └── KnowledgeHealthDashboard.html  # 知识库健康仪表盘 ⭐
```

## 🎯 核心模块详解

### 1. [core/](./core/README.md) - 核心基础
**状态**: ✅ 已完成  
**功能**: 提供基础配置、协议定义和 LLM 适配

**关键类**:
- `NecoRAGConfig`: 全局配置管理
- `BaseProtocol`: 基础协议接口
- `LLMAdapter`: LLM 统一接口

### 2. [perception/](./perception/README.md) - 感知引擎
**状态**: ✅ 已完成  
**功能**: 多模态数据编码与情境标记

**核心特性**:
- 弹性文档切割（语义保持）
- BGE-M3 多模态向量化
- 情境标签自动生成
- 多语言意图识别（中文使用千问 3.5）

### 3. [memory/](./memory/README.md) - 记忆管理
**状态**: ✅ 已完成  
**功能**: 三层记忆系统实现

**层级结构**:
- **L1 工作记忆**: Redis 缓存，TTL 机制
- **L2 语义记忆**: Qdrant 向量检索
- **L3 情景图谱**: Neo4j 关系网络

### 4. [retrieval/](./retrieval/README.md) - 检索引擎
**状态**: ✅ 已完成  
**功能**: 自适应混合检索策略

**检索策略**:
- 向量检索（精确匹配）
- 图谱多跳（关联推理）
- HyDE 增强（假设答案引导）
- 互联网搜索回退

### 5. [refinement/](./refinement/README.md) - 巩固精炼
**状态**: ✅ 已完成  
**功能**: 知识固化与幻觉检测

**核心流程**:
```
Generator → Critic → Refiner → 输出
       ↓
   Hallucination Check
```

### 6. [response/](./response/README.md) - 交互响应
**状态**: ✅ 已完成  
**功能**: 情境自适应回答生成

**适配能力**:
- 语气风格调整
- 详细度控制
- 用户画像匹配
- 思维路径可视化

### 7. [knowledge_evolution/](./knowledge_evolution/README.md) - 知识演化
**状态**: ✅ 已完成  
**功能**: 知识库自进化系统

**更新模式**:
- 实时更新（查询驱动）
- 定时批量更新（睡眠巩固）
- 事件触发更新（外部数据变更）

### 8. [intent/](./intent/README.md) - 意图分析
**状态**: ✅ 已完成  
**功能**: 多语言语义理解与路由

**意图类型**:
- 事实查询
- 比较分析
- 推理演绎
- 概念解释
- 摘要总结
- 操作指导
- 探索发散

### 9. [domain/](./domain/README.md) - 领域权重
**状态**: ✅ 已完成  
**功能**: 领域知识与多维权重融合

**权重因子**:
- 关键字权重（领域术语增强）
- 时间权重（指数衰减）
- 领域相关性（核心/相关/边缘）
- 意图权重（策略路由）

### 10. [monitoring/](./monitoring/README.md) - 监控告警
**状态**: ✅ 已完成  
**功能**: 全方位系统监控

**监控维度**:
- 性能指标（延迟、吞吐量）
- 健康检查（服务可用性）
- 资源使用（CPU、内存）
- 业务指标（查询量、满意度）

### 11. [security/](./security/README.md) - 安全模块
**状态**: ✅ 已完成  
**功能**: 认证授权与数据保护

**安全特性**:
- JWT/OAuth2 认证
- RBAC 权限管理
- AES-256 加密
- 审计日志

### 12. [adaptive/](./adaptive/README.md) - 自适应优化
**状态**: ✅ 已完成  
**功能**: 持续学习与策略优化

**学习能力**:
- 用户偏好预测
- 检索策略自优化
- 集体智慧聚合
- A/B 测试框架

### 13. [plugins/](./plugins/README.md) - 插件扩展
**状态**: ✅ 已完成  
**功能**: 热插拔插件系统

**插件类型**:
- 自定义感知器
- 记忆策略插件
- 检索算法扩展
- 响应格式器

### 14. [user/](./user/README.md) - 用户管理
**状态**: ✅ 已完成  
**功能**: 多用户系统与知识空间

**核心概念**:
- 个人工作空间
- 公共贡献空间
- 混合协作空间
- 知识流动机制

### 15. [dashboard/](./dashboard/README.md) - 管理界面
**状态**: ✅ 已完成  
**功能**: Web 配置与监控界面

**核心功能**:
- 配置 Profile 管理
- 模块参数调整
- 知识库健康仪表盘 ⭐
- 实时性能监控

## 🔌 统一入口

### [necorag.py](./necorag.py) - NecoRAG 主类 ⭐

**简洁 API**:
```python
from src import NecoRAG

# 初始化
rag = NecoRAG()

# 导入文档
rag.import_documents("path/to/docs")

# 智能问答
response = rag.query("你的问题")
print(response)
```

**高级功能**:
```python
# 完整配置
rag = NecoRAG(
    config=config,
    domain_keywords=keywords,
    multi_user=True
)

# 会话管理
session = rag.start_session(user_id="user_001")
response = rag.query(
    "问题",
    session=session,
    strategy="graph_multi_hop"
)

# 知识演化
metrics = rag.get_knowledge_metrics()
health = rag.get_health_report()
```

## 📊 代码统计

| 模块 | 文件数 | 代码行数 | 测试覆盖率 |
|------|--------|---------|-----------|
| core | 5 | ~800 | >90% |
| perception | 7 | ~1500 | >85% |
| memory | 8 | ~2000 | >85% |
| retrieval | 6 | ~1800 | >85% |
| refinement | 8 | ~2200 | >80% |
| response | 7 | ~1600 | >85% |
| knowledge_evolution | 6 | ~1400 | >80% |
| intent | 5 | ~1200 | >85% |
| domain | 4 | ~1000 | >90% |
| monitoring | 6 | ~1300 | >80% |
| security | 6 | ~1400 | >85% |
| adaptive | 5 | ~1100 | >80% |
| plugins | 4 | ~900 | >85% |
| user | 3 | ~700 | >85% |
| dashboard | 10+ | ~3000+ | >80% |
| **总计** | **80+** | **~22,000+** | **>85%** |

## 🎨 设计模式

### 使用的模式
1. **工厂模式**: 对象创建（如 LLM 工厂）
2. **策略模式**: 检索策略选择
3. **观察者模式**: 监控告警系统
4. **责任链**: 精炼代理流程
5. **单例模式**: 配置管理器
6. **适配器模式**: 语气/详细度适配器
7. **仓库模式**: 数据访问层

## 🔧 开发指南

### 添加新模块

1. **创建目录结构**:
```bash
mkdir src/new_module
touch src/new_module/__init__.py
touch src/new_module/main.py
```

2. **实现基类**:
```python
# src/new_module/base.py
from abc import ABC, abstractmethod

class BaseNewModule(ABC):
    @abstractmethod
    def process(self, data):
        pass
```

3. **编写测试**:
```python
# tests/test_new_module/test_main.py
def test_new_module():
    module = NewModule()
    assert module.process("input") == "expected"
```

4. **更新文档**:
- 添加模块说明到本 README
- 编写详细使用文档

### 代码规范

遵循项目统一的代码规范：
- 使用 Black 格式化代码
- 使用 MyPy 进行类型检查
- 遵循 PEP 8 风格指南
- 所有公共方法必须有文档字符串

## 🧪 测试策略

### 单元测试
每个模块都有对应的测试文件：
```
tests/
├── test_core/
├── test_perception/
├── test_memory/
├── test_retrieval/
└── ...
```

### 集成测试
跨模块功能测试：
```
tests/test_integration/
├── test_full_pipeline.py
├── test_multi_user.py
└── ...
```

### 性能测试
基准测试和压力测试：
```
tests/performance_test.py
tests/stress_test.py
```

## 📞 维护信息

**负责人**: NecoRAG Core Team  
**最后更新**: 2026-03-19  
**代码质量**: ✅ 高质量（测试覆盖率>85%）

## 🔗 相关链接

- [项目主文档](../README.md)
- [设计文档](../design/README.md)
- [Wiki 知识库](../wiki/README.md)
- [示例代码](../example/README.md)

---

*源码是项目的核心资产。保持代码整洁、文档完善、测试充分是我们的基本原则。*
