# NecoRAG 知识库管理模块 - 快速参考

## 🚀 快速开始

```python
from src.domain.knowledge_base import KnowledgeBaseManager
from src.domain.config import KeywordLevel

# 1. 创建管理器
manager = KnowledgeBaseManager()

# 2. 创建知识库
kb = manager.create_knowledge_base("ai", "AI 知识库")

# 3. 添加关键字
kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)

# 4. 添加 FAQ
kb.add_faq("什么是 AI？", "人工智能", ["AI"])

# 5. 保存
manager.save_knowledge_base("ai")
```

---

## 📋 核心 API

### 添加关键字
```python
kb.add_keyword(
    keyword="向量检索",           # 关键字
    level=KeywordLevel.CORE,      # 等级
    weight=1.8,                   # 权重
    aliases=["vector search"],    # 别名
    description="基于向量的检索"   # 描述
)
```

### 添加 FAQ
```python
kb.add_faq(
    question="如何提高检索质量？",  # 问题
    answer="优化分块策略...",      # 答案
    keywords=["检索", "优化"],     # 关键字
    category="性能优化"            # 分类
)
```

### 搜索 FAQ
```python
results = kb.search_faqs("检索质量", top_k=5)
for score, faq in results:
    print(f"匹配度：{score}")
    print(f"问题：{faq.question}")
```

### 提取关键字
```python
text = "机器学习是人工智能的核心技术"
keywords = kb.extract_keywords_from_text(text)
```

### 语料库扩充
```python
suggestions = kb.suggest_new_keywords(corpus, min_frequency=3)
manager.expand_from_corpus("ai", corpus, auto_add=True)
```

---

## 📊 关键字等级

| 等级 | 权重范围 | 说明 |
|------|---------|------|
| CORE | 1.5-2.0 | 核心概念 |
| IMPORTANT | 1.2-1.5 | 重要术语 |
| NORMAL | 0.9-1.1 | 普通词汇 |
| PERIPHERAL | 0.5-0.8 | 边缘词汇 |

---

## 💾 数据格式

### JSON 关键字文件
```json
{
  "keywords": [
    {
      "keyword": "知识图谱",
      "level": "important",
      "weight": 1.3,
      "aliases": ["KG"],
      "description": "结构化知识"
    }
  ]
}
```

### CSV FAQ 文件
```csv
question,answer,keywords,category
什么是 RAG？,检索增强生成...,RAG;检索，基础概念
```

---

## 🔧 常用工具方法

```python
# 列出所有领域
domains = manager.list_all_domains()

# 获取知识库
kb = manager.get_knowledge_base("ai")

# 加载知识库
kb = manager.load_knowledge_base("ai")

# 导入关键字
count = manager.import_keywords_from_file("ai", "file.json", "json")

# 导入 FAQ
count = manager.import_faqs_from_file("ai", "file.csv", "csv")
```

---

## ⚡ 最佳实践

### 1. 初始化时加载预定义知识
```python
from src.domain.knowledge_base import create_example_knowledge_base

kb = create_example_knowledge_base()
manager.knowledge_bases["ai_ml"] = kb
```

### 2. 定期从用户数据中学习
```python
user_queries = [...]  # 收集用户查询
manager.expand_from_corpus("ai", user_queries, auto_add=False)
```

### 3. 批量导入历史数据
```python
manager.import_keywords_from_file("domain", "legacy_keywords.json", "json")
manager.import_faqs_from_file("domain", "legacy_faqs.csv", "csv")
```

### 4. 备份知识库
```python
import shutil
shutil.copytree(manager.storage_dir, "/backup/path")
```

---

## 🐛 常见问题

### Q: 如何删除关键字？
A: 当前版本暂不支持删除，可通过修改 `kb.keywords` 字典实现

### Q: FAQ 搜索的评分规则？
A: 问题匹配 0.5 + 答案匹配 0.3 + 关键字匹配 0.2×数量

### Q: 如何合并两个知识库？
A: 分别导出为 JSON，然后手动合并或编写脚本处理

---

## 📖 完整文档

- **使用指南**: `/src/domain/README_KNOWLEDGE_BASE.md`
- **实施报告**: `/src/domain/KNOWLEDGE_BASE_FINAL_REPORT.md`
- **示例代码**: `/example/knowledge_base_example.py`
- **集成示例**: `/example/knowledge_base_integration.py`

---

**版本**: v3.3.0-alpha | **更新时间**: 2026-03-19
