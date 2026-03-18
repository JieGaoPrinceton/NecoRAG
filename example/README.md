# 📝 NecoRAG 示例代码目录

## 📋 目录说明

本目录包含 NecoRAG 项目的使用示例、代码片段和最佳实践演示。

## 📁 文件结构

```
example/
├── example_usage.py              # 基础使用示例 ⭐
├── domain_weight_example.py      # 领域权重计算示例
└── [更多示例文件...]             # 持续更新中
```

## 🎯 示例列表

### 1. [基础使用示例](./example_usage.py) ⭐

**内容**:
- NecoRAG 初始化
- 文档导入流程
- 智能问答演示
- 配置管理方法

**适用场景**:
- 快速上手
- Hello World 级别演示
- 基础功能测试

**运行方式**:
```bash
cd /Users/ll/NecoRAG
python example/example_usage.py
```

### 2. [领域权重示例](./domain_weight_example.py)

**内容**:
- 领域关键字配置
- 权重计算方法
- 时间衰减函数
- 多因子融合策略

**适用场景**:
- 领域定制化配置
- 权重参数调优
- 检索效果优化

**运行方式**:
```bash
python example/domain_weight_example.py
```

## 💡 典型使用场景

### 场景 1: 个人知识库构建

```python
from src import NecoRAG

# 初始化
rag = NecoRAG()

# 导入个人文档
rag.import_documents("~/Documents/notes")

# 开始问答
response = rag.query("如何学习机器学习？")
print(response)
```

### 场景 2: 企业知识管理系统

```python
from src import NecoRAG

# 配置企业级参数
config = {
    "multi_user": True,
    "privacy_mode": True,
    "audit_log": True
}

rag = NecoRAG(config=config)

# 导入企业文档
rag.import_documents("/company/docs", space="public")

# 权限控制查询
response = rag.query(
    "公司财务报表",
    user_id="employee_001",
    permission_level=2
)
```

### 场景 3: 研究领域专用

```python
from src import NecoRAG

# 配置领域关键字
domain_keywords = {
    "core": ["深度学习", "神经网络", "机器学习"],
    "important": ["算法", "模型", "训练"],
    "normal": ["数据", "实验", "结果"]
}

rag = NecoRAG(domain_keywords=domain_keywords)

# 学术文献检索
papers = rag.retrieval_search(
    "Transformer 架构的优缺点",
    strategy="graph_multi_hop"
)
```

## 🔧 代码模板

### 模板 1: 最简单的使用方式

```python
from src import NecoRAG

# 一行初始化
rag = NecoRAG()

# 一行导入
rag.import_documents("path/to/docs")

# 一行问答
answer = rag.ask("你的问题")
```

### 模板 2: 完整配置示例

```python
from src import NecoRAG
from src.core.config import NecoRAGConfig

# 创建配置
config = NecoRAGConfig(
    # 记忆层配置
    memory_ttl=3600,
    vector_size=1024,
    
    # 检索层配置
    top_k=10,
    rerank_enabled=True,
    
    # 交互层配置
    show_trace=True,
    detail_level=2
)

# 初始化
rag = NecoRAG(config=config)

# 使用
rag.import_documents("docs")
response = rag.query("问题", strategy="hybrid")
```

### 模板 3: 高级用法

```python
from src import NecoRAG
from src.retrieval.models import RetrievalStrategy

# 自定义检索策略
strategy = RetrievalStrategy(
    primary="vector",
    fallback="graph",
    web_search_fallback=True,
    novelty_boost=0.3
)

rag = NecoRAG()

# 多轮对话
context = rag.start_session()
for question in questions:
    response = rag.query(
        question,
        context=context,
        strategy=strategy
    )
    print(f"Q: {question}\nA: {response}")
```

## 📚 学习路径

### 入门级（1-2 小时）
1. ✅ 运行 `example_usage.py`
2. 理解基础 API
3. 尝试简单问答

### 进阶级（半天）
1. 阅读 `domain_weight_example.py`
2. 理解权重机制
3. 调整参数观察效果

### 高级（1-2 天）
1. 研究源码实现
2. 自定义插件开发
3. 性能调优实践

## 🎨 最佳实践

### 1. 文档组织

```
我的知识库/
├── 技术文档/
│   ├── Python/
│   ├── AI/
│   └── Web/
├── 学术论文/
├── 笔记/
└── 配置文件
```

### 2. 查询优化

**不好的查询**:
```python
# 太宽泛
rag.query("AI")

# 缺少上下文
rag.query("怎么弄？")
```

**好的查询**:
```python
# 具体明确
rag.query("深度学习在医疗影像分析中的应用有哪些？")

# 带约束
rag.query("比较 Redis 和 Memcached 的优缺点，从性能和内存角度")
```

### 3. 配置调优

```python
# 根据场景选择配置
config_map = {
    "快速原型": {"top_k": 5, "rerank": False},
    "精准问答": {"top_k": 10, "rerank": True},
    "探索发现": {"top_k": 20, "novelty_boost": 0.5},
    "学术研究": {"top_k": 30, "graph_hops": 3}
}
```

## 🐛 常见问题

### Q1: 导入文档失败？
```python
# 检查文件路径
import os
print(os.path.exists("path/to/docs"))

# 检查文件格式
rag.supported_formats  # 查看支持的格式
```

### Q2: 回答质量不高？
```python
# 增加检索数量
response = rag.query("问题", top_k=20)

# 启用重排序
response = rag.query("问题", rerank=True)

# 使用图谱检索
response = rag.query("问题", strategy="graph")
```

### Q3: 响应速度慢？
```python
# 减少检索范围
response = rag.query("问题", top_k=5)

# 禁用复杂功能
response = rag.query("问题", graph_enabled=False)

# 使用缓存
response = rag.query("相同的问题")  # 第二次会快很多
```

## 📊 性能基准

### 小数据集 (<1000 文档)
- 导入速度：~100 文档/秒
- 查询延迟：<200ms
- 内存占用：~500MB

### 中等数据集 (1 万 -10 万文档)
- 导入速度：~500 文档/秒
- 查询延迟：<500ms
- 内存占用：~2GB

### 大数据集 (>10 万文档)
- 导入速度：~1000 文档/秒
- 查询延迟：<800ms
- 内存占用：~4GB+

## 🔗 相关资源

- [API 参考文档](../interface/README.md)
- [配置指南](../src/dashboard/README.md)
- [教程文档](../docs/wiki/快速开始.md)

## 🚀 贡献示例

欢迎提交你的使用示例！

**提交方式**:
1. Fork 项目
2. 在 `example/` 目录添加你的示例文件
3. 命名格式：`example_your_feature.py`
4. 提交 Pull Request

**示例要求**:
- 代码简洁清晰
- 包含必要注释
- 可独立运行
- 展示特定功能

## 📞 维护信息

**负责人**: NecoRAG Team  
**最后更新**: 2026-03-19  
**文档状态**: ✅ 持续更新中

---

*示例代码是学习的最佳途径。通过运行和修改这些示例，你可以快速掌握 NecoRAG 的使用方法。*
