# NecoRAG 意图分析系统初始化设置指南

## 📋 概述

NecoRAG 意图分析系统现已支持**三级层次化意图体系**，允许用户预定义基础意图，然后通过 AI 学习和知识库进行智能细分和扩充。

### 核心特性

1. **三级意图体系**
   - L1: 大类意图（宏观）- 3-6 个基础意图
   - L2: 详细意图（具体）- 每个 L1 下 3-5 个子意图
   - L3: 最细节意图（原子）- 通过 AI 学习自动填充

2. **灵活的初始化方式**
   - 基于模板快速设置
   - 完全自定义配置
   - 混合模式

3. **AI 驱动的智能扩充**
   - 从用户查询中自动发现新意图
   - 智能推荐层级结构
   - 持续学习和优化

---

## 🚀 快速开始

### 1. 基础使用（推荐新手）

```python
from src.intent import IntentInitializer

# 创建初始化工具
initializer = IntentInitializer()

# 选择 3-6 个模板快速设置
tree = initializer.quick_setup([
    'knowledge_base',      # 知识查询
    'task_guidance',       # 任务指导
    'analysis_reasoning',  # 分析推理
    'creative_exploration', # 创造探索
])

# 保存配置
initializer.save_configuration("my_intent_system.json")
```

### 2. 查看可用模板

```python
initializer = IntentInitializer()

print("可用的意图模板:")
for key, template in initializer.intent_templates.items():
    print(f"- {key}: {template['name']} ({template['description']})")
```

**可用模板列表：**
- `knowledge_base` - 知识查询
- `task_guidance` - 任务指导
- `analysis_reasoning` - 分析推理
- `creative_exploration` - 创造探索
- `conversation_interaction` - 对话交互
- `technical_support` - 技术支持

---

## 📊 三级意图体系结构

### L1 - 大类意图（宏观层）

用户预定义的 3-6 个基础意图方向，例如：
- 知识查询
- 任务指导
- 分析推理

### L2 - 详细意图（具体层）

每个 L1 下的具体子类别，例如"知识查询"下：
- 事实查证
- 概念解释
- 定义询问
- 数据检索

### L3 - 最细节意图（原子层）

通过 AI 学习从真实用户查询中自动提取，例如"事实查证"下：
- 简单事实查询
- 复杂事实验证
- 数据统计查询

---

## 🔧 详细使用教程

### 方法 1: 使用预设模板（最简单）

```python
from src.intent import IntentInitializer

initializer = IntentInitializer()

# 选择 4 个基础意图
tree = initializer.quick_setup(
    template_keys=[
        'knowledge_base',
        'task_guidance', 
        'analysis_reasoning',
        'creative_exploration'
    ],
    tree_name="我的意图体系 v3.3"
)

# 显示结构
print(f"L1 数量：{len(tree.roots)}")
print(f"总节点数：{len(tree.all_intents)}")

for l1_id in tree.roots:
    l1 = tree.get_intent(l1_id)
    print(f"\nL1: {l1.name}")
    
    l2_intents = tree.get_l2_intents(l1_id)
    for l2 in l2_intents:
        print(f"  ├─ L2: {l2.name}")
```

### 方法 2: 完全自定义

```python
from src.intent import IntentInitializer

initializer = IntentInitializer()

# 定义自定义结构
custom_intents = [
    {
        "name": "技术咨询",
        "description": "技术相关的问题和咨询",
        "keywords": ["技术", "开发", "编程"],
        "l2_children": [
            {"name": "代码问题", "description": "代码编写和调试"},
            {"name": "架构设计", "description": "系统架构和设计"},
            {"name": "性能优化", "description": "性能调优"},
        ]
    },
    # ... 可以添加更多 L1 意图
]

# 创建自定义意图树
tree = initializer.create_custom_hierarchy(
    custom_intents=custom_intents,
    tree_name="定制化意图体系"
)
```

### 方法 3: 手动添加 L3 意图

```python
# 先获取 L2 意图
l2_intents = tree.get_l2_intents(first_l1_id)
target_l2 = l2_intents[0]

# 添加 L3 子意图
l3_intents = [
    {
        "name": "简单事实查询",
        "description": "查询简单的事实性问题",
        "keywords": ["是什么", "定义"],
        "examples": ["什么是机器学习？"]
    },
    {
        "name": "复杂事实验证",
        "description": "验证复杂的事实信息",
        "keywords": ["真实性", "验证"],
    }
]

initializer.add_l3_intents(target_l2.intent_id, l3_intents)
```

### 方法 4: AI 自动填充 L3

```python
# 准备学习数据（真实的用户查询）
learning_queries = {
    "l2_intent_id_1": [
        "什么是人工智能？",
        "机器学习的定义是什么？",
        "深度学习是什么意思？",
    ],
    "l2_intent_id_2": [
        "如何安装 Python？",
        "怎么配置 Git 环境？",
        "教我写第一个程序",
    ],
}

# 自动创建 L3 意图
count = initializer.auto_populate_l3(learning_queries)
print(f"自动创建了 {count} 个 L3 意图")
```

---

## 🤖 AI 智能扩充

### 使用意图扩充器

```python
from src.intent import IntentExpander, create_intent_knowledge_manager

# 创建知识管理器
knowledge_manager = create_intent_knowledge_manager()
knowledge_manager.load_default_tree()

# 创建扩充器
expander = IntentExpander(knowledge_manager)

# 收集用户查询
new_queries = [
    "如何安装 Python 环境？",
    "Python 虚拟环境怎么使用？",
    "pip 安装失败怎么办？",
    # ... 更多查询
]

# 发现新的意图模式
candidates = expander.discover_new_intents(new_queries, min_frequency=2)

print(f"发现 {len(candidates)} 个新意图候选")
for candidate in candidates:
    print(f"- 基础意图：{candidate['base_intent']}")
    print(f"  关键词：{candidate['keywords'][:3]}")
    print(f"  频率：{candidate['frequency']}")
```

### 扩展现有意图

```python
# 为特定 L1 意图扩展 L2 子意图
new_l2_ids = expander.expand_intent_hierarchy(
    parent_intent_id="l1_knowledge_query",
    queries=new_queries,
    expansion_strategy="auto"
)

if new_l2_ids:
    print(f"扩展了 {len(new_l2_ids)} 个新的 L2 子意图")
```

---

## 💾 保存和加载

### 保存配置

```python
# 保存当前配置
config_file = initializer.save_configuration("intent_system.json")
print(f"配置已保存到：{config_file}")

# 导出学习数据
initializer.knowledge_manager.export_learning_data("learning_data.json")
```

### 加载配置

```python
# 从文件加载
success = initializer.load_configuration("intent_system.json")

if success:
    tree = initializer.knowledge_manager.current_tree
    print(f"成功加载意图树：{tree.name}")
```

### 版本管理

```python
# 保存版本
version_path = initializer.knowledge_manager.save_version(
    version_name="v3.3 - 初始版本",
    description="包含基础的 L1 和 L2 意图"
)

# 列出所有版本
versions = initializer.knowledge_manager.list_versions()
for v in versions:
    print(f"- {v['version_name']} ({v['timestamp']})")

# 加载特定版本
old_tree = initializer.knowledge_manager.load_version("v_20260319_120000")
```

---

## 📈 统计信息

```python
stats = initializer.knowledge_manager.get_statistics()

print("📊 意图体系统计:")
print(f"  总意图数：{stats['total_intents']}")
print(f"  L1 数量：{stats['l1_count']}")
print(f"  L2 数量：{stats['l2_count']}")
print(f"  L3 数量：{stats['l3_count']}")
print(f"  总示例数：{stats['total_examples']}")
print(f"  平均子节点数：{stats['avg_children_per_intent']:.2f}")
```

---

## 🎯 最佳实践

### 1. 分阶段构建

**阶段 1**: 选择 3-6 个 L1 模板  
**阶段 2**: 收集用户查询数据  
**阶段 3**: 使用 AI 自动填充 L3  
**阶段 4**: 手动调整和优化

### 2. 数据驱动优化

```python
# 持续收集用户查询
all_queries = []

def handle_user_query(query):
    """处理用户查询"""
    all_queries.append(query)
    
    # 定期（如每周）进行批量学习
    if len(all_queries) >= 100:
        initializer.auto_populate_l3_from_queries(all_queries)
        all_queries.clear()
```

### 3. 质量控制

- ✅ 检查 L3 意图的示例数量（建议≥3 个）
- ✅ 确保关键词具有区分度
- ✅ 定期合并相似意图
- ✅ 删除低频或无用的意图

### 4. 版本控制

```python
# 每次重大更新前保存版本
initializer.knowledge_manager.save_version(
    version_name=f"v{major}.{minor}.{patch}",
    description="更新说明"
)
```

---

## 🔍 常见问题

### Q: 应该选择多少个 L1 意图？
A: 建议 3-6 个。太少覆盖不全，太多难以管理。

### Q: L2 和 L3 需要手动创建吗？
A: L2 可以手动或使用模板，L3 强烈建议使用 AI 自动填充。

### Q: 多久更新一次意图体系？
A: 初期可以频繁（每周），稳定后每月或每季度更新。

### Q: 如何处理意图重叠？
A: 使用 `merge_similar_intents()` 方法合并相似意图。

### Q: 可以动态修改意图吗？
A: 可以，但建议保存版本以便回滚。

---

## 📚 完整示例

查看完整的使用示例：
```bash
python example/intent_initialization_complete.py
```

这个示例演示了：
1. ✅ 快速设置基础意图
2. ✅ 完全自定义配置
3. ✅ 手动添加 L3 意图
4. ✅ AI 自动扩充
5. ✅ 持续学习
6. ✅ 保存和加载

---

## 🛠️ API 参考

### IntentInitializer

主要方法：
- `quick_setup(template_keys, tree_name)` - 快速设置
- `create_custom_hierarchy(custom_intents, tree_name)` - 自定义创建
- `add_l3_intents(l2_intent_id, l3_intents)` - 添加 L3
- `auto_populate_l3(learning_queries)` - AI 填充 L3
- `save_configuration(filename)` - 保存配置
- `load_configuration(filepath)` - 加载配置

### IntentHierarchyTree

主要方法：
- `get_intent(intent_id)` - 获取意图节点
- `get_children(intent_id)` - 获取子意图
- `get_l2_intents(l1_intent_id)` - 获取 L2
- `get_l3_intents(l2_intent_id)` - 获取 L3
- `find_leaf_intents(intent_id)` - 查找叶子节点

### IntentKnowledgeManager

主要方法：
- `create_tree(tree_name, description)` - 创建树
- `save_current_tree(filename)` - 保存
- `load_tree_from_file(filepath)` - 加载
- `save_version(version_name, description)` - 保存版本
- `get_statistics()` - 统计信息

### IntentExpander

主要方法：
- `discover_new_intents(queries, min_frequency)` - 发现新意图
- `expand_intent_hierarchy(parent_id, queries, strategy)` - 扩展
- `refine_intent_details(intent_id, examples)` - 细化
- `merge_similar_intents(intent_ids, strategy)` - 合并

---

## 📝 总结

NecoRAG 意图分析系统的三层级意图管理体系提供了：

1. **灵活性** - 支持多种初始化方式
2. **智能化** - AI 驱动的自动扩充
3. **可扩展** - 持续学习和优化
4. **易管理** - 完整的版本控制和统计

通过合理配置和持续优化，可以构建出符合实际业务需求的意图体系，大幅提升 RAG 系统的语义理解能力。

---

**版本**: v3.3.0-alpha  
**更新时间**: 2026-03-19  
**状态**: ✅ 已实现并测试
