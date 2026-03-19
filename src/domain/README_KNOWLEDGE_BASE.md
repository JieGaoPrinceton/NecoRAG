# NecoRAG 领域知识库管理模块

## 概述

`knowledge_base` 模块为 NecoRAG 系统提供了基础数据管理能力，支持导入和管理关键字、FAQ 文本，并提供知识扩充功能。

## 核心功能

### 1. 知识库管理
- **KnowledgeBase**: 知识库数据结构，包含关键字和 FAQ
- **KnowledgeBaseManager**: 知识库管理器，提供创建、加载、保存等功能
- **FAQItem**: FAQ 条目数据结构

### 2. 关键字管理
- 支持多级关键字（核心、重要、普通、边缘）
- 支持关键字别名/同义词
- 从文本中自动提取关键字
- 从语料库中建议新关键字

### 3. FAQ 管理
- 添加、查询、搜索 FAQ
- 支持关键字标记
- 支持分类管理
- 统计查看次数和有用次数

### 4. 数据导入导出
- 支持 JSON 格式导入导出
- 支持 CSV 格式导入 FAQ
- 支持纯文本格式导入关键字
- 持久化存储

### 5. 知识扩充
- 从已有文本中提取新关键字
- 基于频率自动推荐关键字
- 记录扩充历史

## 快速开始

### 创建知识库

```python
from src.domain.knowledge_base import KnowledgeBaseManager, create_example_knowledge_base
from src.domain.config import KeywordLevel

# 创建管理器
manager = KnowledgeBaseManager()

# 创建示例知识库
kb = create_example_knowledge_base()
manager.knowledge_bases["ai_ml"] = kb
```

### 添加关键字

```python
# 添加核心关键字
kb.add_keyword(
    keyword="向量检索",
    level=KeywordLevel.CORE,
    weight=1.8,
    aliases=["vector search", "相似度搜索"],
    description="基于向量相似度的信息检索方法"
)

# 添加重要关键字
kb.add_keyword(
    keyword="分块策略",
    level=KeywordLevel.IMPORTANT,
    weight=1.3,
    aliases=["chunking strategy"],
    description="将文档切分为合适大小的策略"
)
```

### 添加 FAQ

```python
kb.add_faq(
    question="如何提高 RAG 系统的检索质量？",
    answer="提高 RAG 检索质量的方法包括：1) 优化文本分块策略；2) 使用更好的 embedding 模型；3) 添加重排序步骤。",
    keywords=["RAG", "检索质量", "优化"],
    category="性能优化"
)
```

### 搜索 FAQ

```python
# 搜索相关 FAQ
results = kb.search_faqs("检索质量", top_k=5)
for score, faq in results:
    print(f"匹配度：{score}")
    print(f"问题：{faq.question}")
    print(f"答案：{faq.answer}")
```

### 从文件导入

```python
# 从 JSON 文件导入关键字
count = manager.import_keywords_from_file(
    domain_id="ai_ml",
    filepath="/path/to/keywords.json",
    format="json"
)

# 从 CSV 文件导入 FAQ
count = manager.import_faqs_from_file(
    domain_id="ai_ml",
    filepath="/path/to/faqs.csv",
    format="csv"
)
```

### 语料库自动扩充

```python
# 准备语料库
corpus = [
    "机器学习是人工智能的核心技术",
    "深度学习在图像识别中应用广泛",
    "强化学习是机器学习的分支",
]

# 建议新关键字
suggestions = kb.suggest_new_keywords(corpus, min_frequency=2)
print("建议的关键字:", suggestions)

# 自动扩充
added = manager.expand_from_corpus(
    domain_id="ai_ml",
    text_corpus=corpus,
    min_frequency=2,
    auto_add=True
)
```

### 保存和加载

```python
# 保存到文件
manager.save_knowledge_base("ai_ml")

# 从文件加载
kb = manager.load_knowledge_base("ai_ml")
```

## 数据格式

### JSON 关键字文件格式

```json
{
  "keywords": [
    {
      "keyword": "知识图谱",
      "level": "important",
      "weight": 1.3,
      "aliases": ["knowledge graph", "KG"],
      "description": "结构化知识表示"
    }
  ]
}
```

### JSON FAQ 文件格式

```json
{
  "faqs": [
    {
      "question": "什么是 RAG？",
      "answer": "RAG 是检索增强生成...",
      "keywords": ["RAG", "检索"],
      "category": "基础概念"
    }
  ]
}
```

### CSV FAQ 文件格式

```csv
question,answer,keywords,category
什么是 RAG？,RAG 是检索增强生成...,RAG;检索，基础概念
```

## 高级功能

### 关键字提取

```python
text = """
机器学习是人工智能的核心技术。
深度学习是机器学习的重要分支。
神经网络模拟了生物大脑结构。
"""

# 从文本中提取关键字
extracted = kb.extract_keywords_from_text(text)
print("提取的关键字:", extracted)
```

### 扩充历史记录

```python
# 查看扩充历史
for record in kb.expansion_history:
    print(f"时间：{record['timestamp']}")
    print(f"操作：{record['operation']}")
    print(f"详情：{record['details']}")
```

## 与领域权重系统集成

知识库模块与现有的领域权重系统无缝集成：

```python
from src.domain import DomainConfigManager, KnowledgeBaseManager

# 创建领域配置
domain_manager = DomainConfigManager()
domain_config = domain_manager.create_domain(
    domain_name="人工智能",
    domain_id="ai_domain"
)

# 创建知识库
kb_manager = KnowledgeBaseManager()
kb = kb_manager.create_knowledge_base(
    domain_id="ai_domain",
    name="AI 知识库"
)

# 同步到领域配置（后续实现）
kb_manager.sync_to_domain_config("ai_domain")
```

## 运行示例

执行以下命令查看完整的使用示例：

```bash
python example/knowledge_base_example.py
```

## API 参考

### KnowledgeBase 类

主要方法：
- `add_keyword(keyword, level, weight, aliases, description)`: 添加关键字
- `add_faq(question, answer, keywords, category)`: 添加 FAQ
- `search_faqs(query, top_k)`: 搜索 FAQ
- `extract_keywords_from_text(text)`: 从文本提取关键字
- `suggest_new_keywords(corpus, min_frequency)`: 建议新关键字

### KnowledgeBaseManager 类

主要方法：
- `create_knowledge_base(domain_id, name, description)`: 创建知识库
- `get_knowledge_base(domain_id)`: 获取知识库
- `save_knowledge_base(domain_id)`: 保存知识库
- `load_knowledge_base(domain_id)`: 加载知识库
- `import_keywords_from_file(domain_id, filepath, format)`: 导入关键字
- `import_faqs_from_file(domain_id, filepath, format)`: 导入 FAQ
- `expand_from_corpus(domain_id, corpus, min_frequency, auto_add)`: 从语料扩充

## 最佳实践

1. **初始化基础数据**：项目启动时加载预定义的关键字和 FAQ
2. **定期扩充**：定期从用户交互数据中提取新知识
3. **质量控制**：审核自动提取的关键字后再添加到知识库
4. **备份管理**：定期备份知识库文件
5. **版本控制**：对知识库变更进行版本管理

## 相关文件

- `/src/domain/knowledge_base.py`: 核心实现
- `/example/knowledge_base_example.py`: 使用示例
- `/src/domain/config.py`: 领域配置模块
- `/src/domain/weight_calculator.py`: 权重计算器
