# NecoRAG 意图三层级管理 - 快速参考

## 🚀 5 分钟快速开始

```python
from src.intent import IntentInitializer

# 1. 创建初始化工具
initializer = IntentInitializer()

# 2. 选择 3-6 个模板
tree = initializer.quick_setup([
    'knowledge_base',      # 知识查询
    'task_guidance',       # 任务指导
    'analysis_reasoning',  # 分析推理
])

# 3. 保存配置
initializer.save_configuration("my_intents.json")
```

---

## 📊 三级意图体系

```
L1 (大类意图 - 宏观)
├─ L2 (详细意图 - 具体)
│  ├─ L3 (最细节意图 - 原子) ← AI 自动填充
│  ├─ L3
│  └─ L3
├─ L2
│  ├─ L3
│  └─ L3
└─ L2
   └─ ...
```

---

## 🎯 核心 API

### IntentInitializer

```python
# 快速设置（3-6 个模板）
tree = initializer.quick_setup(['knowledge_base', 'task_guidance', 'analysis_reasoning'])

# 自定义创建
tree = initializer.create_custom_hierarchy(custom_intents)

# 添加 L3 意图
initializer.add_l3_intents(l2_intent_id, l3_data)

# AI 填充 L3
count = initializer.auto_populate_l3(learning_queries)

# 保存/加载
filepath = initializer.save_configuration("file.json")
success = initializer.load_configuration("file.json")
```

### IntentHierarchyTree

```python
# 获取节点
intent = tree.get_intent(intent_id)

# 获取子节点
l2_list = tree.get_l2_intents(l1_id)
l3_list = tree.get_l3_intents(l2_id)

# 遍历树
for l1_id in tree.roots:
    l1 = tree.get_intent(l1_id)
    for l2 in tree.get_children(l1_id):
        for l3 in tree.get_children(l2.intent_id):
            print(f"{l1.name} > {l2.name} > {l3.name}")
```

### IntentKnowledgeManager

```python
# 保存/加载版本
version_path = manager.save_version("v3.3", "描述")
old_tree = manager.load_version("v_20260319_120000")

# 统计信息
stats = manager.get_statistics()
print(f"总意图数：{stats['total_intents']}")
print(f"L1/L2/L3: {stats['l1_count']}/{stats['l2_count']}/{stats['l3_count']}")

# 学习数据
manager.add_learning_example(intent_id, "用户查询")
manager.export_learning_data("learning.json")
```

### IntentExpander

```python
# 发现新意图
candidates = expander.discover_new_intents(queries, min_frequency=3)

# 扩展层级
new_ids = expander.expand_intent_hierarchy(parent_id, queries)

# 细化意图
expander.refine_intent_details(intent_id, examples)

# 合并相似意图
merged_id = expander.merge_similar_intents([id1, id2, id3])
```

---

## 📋 预设模板

| 模板键 | 名称 | 描述 |
|-------|------|------|
| `knowledge_base` | 知识查询 | 查询事实性知识和信息 |
| `task_guidance` | 任务指导 | 获取操作步骤和方法指导 |
| `analysis_reasoning` | 分析推理 | 进行分析、比较和推理 |
| `creative_exploration` | 创造探索 | 创造性思维和探索性问题 |
| `conversation_interaction` | 对话交互 | 日常对话和交互 |
| `technical_support` | 技术支持 | 技术问题和支持 |

---

## 💡 常用模式

### 模式 1: 从模板开始

```python
# 适合：快速启动项目
initializer = IntentInitializer()
tree = initializer.quick_setup([
    'knowledge_base',
    'task_guidance',
    'analysis_reasoning'
])
```

### 模式 2: 完全自定义

```python
# 适合：特定业务需求
custom = [
    {
        "name": "业务咨询",
        "description": "业务相关问题",
        "l2_children": [
            {"name": "产品咨询", "desc": "产品信息"},
            {"name": "价格咨询", "desc": "价格政策"},
        ]
    }
]
tree = initializer.create_custom_hierarchy(custom)
```

### 模式 3: AI 增强

```python
# 适合：有真实用户数据的场景
learning_data = {
    "l2_concept_explanation": ["什么是 AI？", "ML 定义是什么？"],
    "l2_step_guide": ["如何安装？", "怎么配置？"],
}
count = initializer.auto_populate_l3(learning_data)
```

### 模式 4: 持续优化

```python
# 适合：生产环境
expander = IntentExpander(knowledge_manager)

# 定期收集用户查询
new_queries = collect_user_queries()

# 发现新模式
candidates = expander.discover_new_intents(new_queries)

# 更新意图体系
for candidate in candidates:
    create_new_intent(candidate)
```

---

## 🔧 实用技巧

### 查看意图结构
```python
def print_tree_structure(tree):
    for l1_id in tree.roots:
        l1 = tree.get_intent(l1_id)
        print(f"L1: {l1.name}")
        
        for l2 in tree.get_children(l1_id):
            print(f"  ├─ L2: {l2.name}")
            
            for l3 in tree.get_children(l2.intent_id):
                print(f"  │  └─ L3: {l3.name}")
```

### 批量添加示例
```python
examples_per_intent = {
    "l2_fact_check": ["地球多大？", "谁发明了计算机？"],
    "l2_concept": ["什么是 AI？", "机器学习定义？"],
}

for intent_id, examples in examples_per_intent.items():
    for ex in examples:
        knowledge_manager.add_learning_example(intent_id, ex)
```

### 版本对比
```python
# 保存当前状态
manager.save_version("before_update")

# 进行更新
update_intents()

# 如有问题可回滚
old_tree = manager.load_version("before_update")
```

---

## ⚠️ 注意事项

1. **L1 数量**: 必须 3-6 个，太少覆盖不全，太多难管理
2. **L3 示例**: 每个 L3 至少 3 个示例，确保准确性
3. **关键词质量**: 确保有区分度，避免重叠
4. **定期备份**: 重要更新前保存版本
5. **数据验证**: 使用 `tree.validate()` 检查完整性

---

## 🐛 常见问题速查

**Q: 如何选择 L1 模板？**  
A: 根据业务场景选择最相关的 3-6 个

**Q: L2 可以手动添加吗？**  
A: 可以，在 `create_custom_hierarchy` 中定义

**Q: AI 填充需要多少数据？**  
A: 每个 L2 至少 5-10 条查询

**Q: 如何删除意图？**  
A: 直接操作 `tree.all_intents` 字典

**Q: 如何合并意图？**  
A: 使用 `expander.merge_similar_intents()`

---

## 📖 完整文档

- **设置指南**: `/src/intent/INTENT_SETUP_GUIDE.md`
- **实施总结**: `/src/intent/INTENT_IMPLEMENTATION_SUMMARY.md`
- **运行示例**: `python example/intent_initialization_complete.py`

---

**版本**: v3.3.0-alpha | **更新**: 2026-03-19
