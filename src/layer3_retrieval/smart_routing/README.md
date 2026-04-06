# 🧠 智能路由与策略融合引擎

## 📋 概述

**版本**: v1.9-Alpha  
**日期**: 2026-03-19  
**模块位置**: `src/retrieval/smart_routing/`

智能路由与策略融合引擎整合了**语义意图分类**、**CoT思维链推理**和**用户画像**三大核心能力，构建智能化的检索 - 响应决策系统。

---

## ✨ 核心特性

### 1. 三层决策架构

```
┌─────────────────────────────────────────────────────────────┐
│                  智能路由与策略融合引擎                        │
├─────────────────────────────────────────────────────────────┤
│   第一层：意图识别层 ──▶ 识别问题类型和复杂度                │
│   第二层：用户画像层 ──▶ 匹配用户专业度和偏好               │
│   第三层：策略融合层 ──▶ 动态选择最优策略组合               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 7 大类语义意图

| 意图类型 | 说明 | CoT 触发概率 | 典型策略 |
|---------|------|-------------|---------|
| **事实查询** | 寻找具体事实 | 低 (0.1) | 向量匹配 + 关键字 |
| **比较分析** | 比较多个概念 | 中 (0.4) | 多实体检索 + 图谱关联 |
| **推理演绎** | 需要多步推理 | 高 (0.9) | 图谱多跳+HyDE+CoT |
| **概念解释** | 理解概念 | 中 (0.5) | 语义检索 + 示例 |
| **摘要总结** | 归纳信息 | 中 (0.3) | 广泛检索 + 聚合 |
| **操作指导** | 步骤化指导 | 低 (0.2) | 程序记忆 + 时序 |
| **探索发散** | 开放式探索 | 高 (0.7) | 扩散激活 + 跨领域 |

### 3. 个性化专业度适配

| 用户类型 | 专业度 | 检索策略 | 响应风格 | CoT 深度 |
|---------|-------|---------|---------|---------|
| **专家** | ≥0.8 | 深度检索优先 | 简洁专业 | L1 精简版 |
| **中级** | 0.5-0.8 | 平衡深度广度 | 适度解释 | L2 标准版 |
| **新手** | <0.5 | 增加基础概念 | 通俗易懂 | L3 详细版 |

### 4. 智能早停与降级

**早停条件** (满足任一即停止):
1. 置信度阈值达成 (≥0.95)
2. 边际收益递减 (<2% 提升)
3. 资源约束 (延迟预算 80%)
4. 用户满意度预测 (≥4.5 分)

**四级降级机制**:
- Level 1 (500ms): 减少并行策略数
- Level 2 (700ms): 跳过 CoT
- Level 3 (900ms): 仅向量检索
- Level 4 (1000ms): 返回缓存

---

## 🚀 快速开始

### 安装依赖

```bash
# 该模块无额外依赖，使用项目现有依赖即可
pip install -e .
```

### 基础使用

```python
import asyncio
from src.retrieval.smart_routing import StrategyFusionEngine

async def main():
    # 1. 初始化引擎
    engine = StrategyFusionEngine(
        intent_router=IntentRouter(),
        user_profile_adapter=UserProfileAdapter(),
        cot_controller=CoTController(),
        strategy_fusion=StrategyFusion(),
        early_stopping=EarlyStoppingManager(),
        feedback_collector=FeedbackCollector(),
        strategy_learner=StrategyLearner(feedback_collector),
    )
    
    # 2. 路由决策
    query = "为什么微服务架构更适合大规模系统？"
    decision = await engine.route_query(
        query=query,
        user_id="user_123"
    )
    
    print(f"意图类型：{decision.intent.intent_type}")
    print(f"CoT 启用：{decision.cot_enabled}")
    print(f"策略数量：{len(decision.strategies)}")

asyncio.run(main())
```

### 完整流程

```python
# 3. 执行检索并监控
results = await engine.execute_and_monitor(
    query=query,
    decision=decision,
    retrieval_func=your_retrieval_function,
    # 其他参数...
)

# 4. 收集反馈
await engine.feedback_collector.collect_explicit_feedback(
    user_id="user_123",
    query=query,
    results=results,
    rating=5  # 1-5 分
)

# 5. 从反馈中学习
await engine.update_from_feedback(
    intent_type="reasoning_inference",
    strategy_id="graph_multi_hop",
    reward=0.8,
    expected_reward=0.5
)
```

---

## 📊 模块结构

```
smart_routing/
├── __init__.py              # 导出接口
├── engine.py                # 主引擎类
├── intent_router.py         # 意图路由器
├── user_adapter.py          # 用户画像适配器
├── cot_controller.py        # CoT 控制器
├── strategy_fusion.py       # 策略融合引擎
├── early_stopping.py        # 早停管理器
├── feedback_loop.py         # 反馈闭环学习
├── example_usage.py         # 使用示例
└── README.md                # 本文档
```

---

## 🔧 配置参数

### CoT 控制器配置

```python
cot_config = {
    'min_complexity': 0.7,           # 触发 CoT 的最小复杂度
    'max_steps': 7,                  # 最大推理步骤数
    'graph_max_hops': 3,             # 图谱多跳最大跳数
    'evidence_min_count': 3,         # 每个步骤最少证据数
}
```

### 早停配置

```python
early_stop_config = {
    'enabled': True,
    'confidence_threshold': 0.95,
    'diminishing_returns_threshold': 0.02,
    'latency_budget_ratio': 0.8,
    'satisfaction_threshold': 4.5,
    'max_allowed_latency_ms': 1000,
    'level1_latency_ms': 500,
    'level2_latency_ms': 700,
    'level3_latency_ms': 900,
    'level4_latency_ms': 1000,
}
```

### 融合配置

```python
fusion_config = FusionConfig(
    diversity_enabled=True,
    novelty_boost=0.1,
    max_same_domain_ratio=0.6,
    min_cross_domain_count=2,
    temporal_diversity=True,
    source_diversity=True,
)
```

---

## 📈 性能指标

### 预期效果

| 指标 | 基线 | 目标值 | 提升 |
|------|------|--------|------|
| 用户满意度 | 3.5/5.0 | 4.5/5.0 | **+28.6%** |
| 平均延迟 | 1200ms | 800ms | **-33.3%** |
| 检索命中率 | 65% | 80% | **+23.1%** |
| 新用户留存 | 45% | 65% | **+44.4%** |
| 资源成本 | 100% | 60% | **-40%** |

### 监控统计

```python
# 获取引擎统计
stats = engine.get_stats()
print(stats)
# 输出:
# {
#     'total_requests': 1000,
#     'avg_processing_time_ms': 650.5,
#     'strategy_weights': {...},
#     'cot_trigger_rate': 0.35,
# }

# 获取早停统计
early_stop_stats = engine.early_stopping.get_stats()
print(early_stop_stats)
# 输出:
# {
#     'total_checks': 5000,
#     'early_stops_triggered': 1200,
#     'early_stop_rate': 0.24,
#     'degradation_events': {...},
# }
```

---

## 💡 应用场景

### 场景 1: 技术方案选型

```python
query = "我们应该选择微服务还是单体架构？"
# 自动识别为：推理演绎类
# 触发 CoT(L2 标准版)
# 策略：图谱多跳 (0.4) + HyDE(0.3) + CoT(0.3)
```

### 场景 2: 简单事实查询

```python
query = "Python 3.12 的发布时间？"
# 自动识别为：事实查询类
# 不触发 CoT
# 策略：向量匹配 (0.7) + 关键字 (0.3)
# 早停：置信度>0.95 立即返回
```

### 场景 3: 跨领域探索

```python
query = "区块链如何应用于供应链管理？"
# 自动识别为：探索发散类
# 触发 CoT(L3 详细版)
# 策略：扩散激活 (0.4) + 新颖性优先 (0.4) + 跨领域 (0.2)
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/test_retrieval/test_smart_routing.py -v

# 运行特定测试类
pytest tests/test_retrieval/test_smart_routing.py::TestIntentRouter -v

# 运行覆盖率测试
pytest tests/test_retrieval/test_smart_routing.py --cov=src/retrieval/smart_routing
```

### 测试覆盖率

当前测试覆盖包括:
- ✅ 意图路由器 (7 种意图类型)
- ✅ 用户画像适配器 (专业度、偏好)
- ✅ CoT 控制器 (触发判断、深度调节)
- ✅ 策略融合 (并行执行、结果融合)
- ✅ 早停机制 (4 个条件、4 级降级)
- ✅ 反馈闭环 (显式、隐式反馈)
- ✅ 集成测试 (完整流程)

---

## 🔗 与其他模块的协同

### 与意图分析系统协同

```python
from src.intent.classifier import IntentClassifier

intent_classifier = IntentClassifier()
router = IntentRouter(intent_classifier=intent_classifier)
# 使用现有的意图分类器进行深度语义分析
```

### 与 CoT思维链协同

```python
from src.retrieval.cot_reasoner import ChainOfThoughtReasoner

cot_reasoner = ChainOfThoughtReasoner(...)
cot_controller = CoTController(reasoner=cot_reasoner)
# 使用实际的 CoT 推理器
```

### 与用户画像协同

```python
from src.memory.manager import MemoryManager

memory_manager = MemoryManager(...)
user_adapter = UserProfileAdapter(memory_manager=memory_manager)
# 从 L1 工作记忆加载用户画像
```

---

## 🎯 最佳实践

### 1. 性能优化

```python
# 启用并行检索
config = {
    'enable_parallel': True,
    'max_parallel_strategies': 5,
}

# 配置缓存
user_adapter = UserProfileAdapter(
    config={'cache_max_size': 100}
)
```

### 2. 调优建议

```python
# 根据实际数据调整阈值
cot_controller.min_complexity = 0.6  # 降低触发门槛
early_stopping.config.confidence_threshold = 0.9  # 更保守的早停
```

### 3. 监控告警

```python
# 定期检查性能
def monitor_performance():
    stats = engine.get_stats()
    if stats['avg_processing_time_ms'] > 800:
        logger.warning("平均延迟超过阈值")
    if stats['cot_trigger_rate'] < 0.2:
        logger.info("CoT 触发率偏低")
```

---

## 📚 相关文档

- [design.md](../../design/design.md) - NecoRAG整体技术框架
- [SMART_ROUTING_FUSION_ENGINE.md](../../design/SMART_ROUTING_FUSION_ENGINE.md) - 详细设计文档
- [COT_CHAIN_OF_THOUGHT.md](../../design/COT_CHAIN_OF_THOUGHT.md) - CoT思维链详解
- [意图分析系统](../../docs/wiki/意图分析系统.md) - 意图分类系统

---

## 🚧 待完成功能

### Phase 2 (进行中)
- [ ] 集成实际向量检索器
- [ ] 集成实际图谱检索器
- [ ] 实现 HyDE 假设答案生成
- [ ] 实现实际重排序模型 (BGE-Reranker)

### Phase 3 (计划中)
- [ ] A/B 测试框架集成
- [ ] 超参数自动调优
- [ ] 在线学习算法增强
- [ ] 生产环境部署验证

---

## 📞 维护信息

**版本**: v1.9-Alpha  
**开发团队**: NecoRAG DevOps Team  
**最后更新**: 2026-03-19  
**兼容性**: Python 3.9+  
**测试状态**: ✅ 已通过单元测试  

**欢迎反馈:**
- Bug 报告：提交 GitHub Issue
- 功能建议：发起 Discussion

---

**让 RAG 系统更智能、更个性化! 🚀**
