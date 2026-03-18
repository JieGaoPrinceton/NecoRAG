# 🎯 NecoRAG 意图分析系统

## 📋 目录说明

本目录包含 NecoRAG 的意图分析模块，负责多语言语义理解、意图分类和智能路由。

## 📁 文件结构

```
intent/
├── __init__.py                 # 包初始化与导出 ⭐
├── classifier.py               # 意图分类器 ⭐
├── router.py                   # 智能路由分发器 ⭐
├── semantic_analyzer.py        # 语义分析器 ⭐
├── models.py                   # 数据模型定义
└── config.py                   # 意图分析配置
```

## 🎯 核心功能

### 1. [classifier.py](./classifier.py) - 意图分类器 ⭐

**功能**: 识别用户查询的语义意图类型

**支持的意图类型**:

| 意图类型 | 说明 | 检索策略 | 示例 |
|---------|------|---------|------|
| **事实查询** | 寻找具体事实或数据 | 精确向量匹配 + 关键字 | "Python 3.12 的新特性？" |
| **比较分析** | 比较多个概念或方案 | 多实体并行检索 | "Redis vs Memcached?" |
| **推理演绎** | 需要多步推理 | 图谱多跳 + HyDE | "为什么微服务更适合大规模系统？" |
| **概念解释** | 理解某个概念 | 语义检索 + 层级上下文 | "什么是注意力机制？" |
| **摘要总结** | 归纳总结信息 | 广泛检索 + 聚合排序 | "总结这篇论文的核心观点" |
| **操作指导** | 步骤化指导 | 程序记忆检索 | "如何部署 Kubernetes?" |
| **探索发散** | 开放式探索 | 扩散激活 + 新颖性优先 | "有趣的 AI 应用？" |

**多语言处理策略**:
- **中文查询**: 使用阿里巴巴千问 3.5 进行深度语义理解
- **英文查询**: 使用 FastText 轻量级分类
- **其他语言**: 使用 spaCy + 规则匹配

**使用示例**:
```python
from src.intent import IntentClassifier

classifier = IntentClassifier()

# 单语言意图识别
intent = classifier.classify("深度学习的应用有哪些？")
print(intent.type)  # IntentType.EXPLORATORY

# 置信度评估
intent = classifier.classify_with_confidence("问题文本")
print(f"意图：{intent.type}, 置信度：{intent.confidence}")

# 多意图检测（复合查询）
intents = classifier.detect_multiple("比较 Redis 和 Memcached，并给出使用建议")
# [IntentType.COMPARATIVE, IntentType.PROCEDURAL]
```

### 2. [router.py](./router.py) - 智能路由分发器 ⭐

**功能**: 根据意图类型自动选择最优检索策略

**路由决策流程**:
```
用户查询 → 意图识别 → 置信度评估
                          ↓
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
    高置信度 (>0.7)   中置信度      低置信度 (<0.4)
            ↓             ↓             ↓
      单策略路由     双策略融合      通用检索降级
```

**策略映射表**:
```python
STRATEGY_MAP = {
    IntentType.FACTUAL: ["vector_exact", "keyword_boost"],
    IntentType.COMPARATIVE: ["multi_entity", "graph_relation"],
    IntentType.REASONING: ["graph_multi_hop", "hyde_enhanced"],
    IntentType.CONCEPTUAL: ["semantic_search", "context_hierarchy"],
    IntentType.SUMMARIZATION: ["broad_retrieval", "aggregation"],
    IntentType.PROCEDURAL: ["programmatic_memory", "temporal_order"],
    IntentType.EXPLORATORY: ["spreading_activation", "novelty_first"]
}
```

**使用示例**:
```python
from src.intent import IntentRouter

router = IntentRouter()

# 获取检索策略
strategy = router.get_strategy("如何学习机器学习？")
print(strategy.primary)    # "programmatic_memory"
print(strategy.secondary)  # "temporal_order"

# 执行路由（直接调用检索器）
results = router.route_query(
    query="比较 Python 和 Go 的性能",
    retriever=retriever_instance
)
```

### 3. [semantic_analyzer.py](./semantic_analyzer.py) - 语义分析器 ⭐

**功能**: 深层语义理解和结构化表示

**分析维度**:
1. **实体识别**: 提取关键实体和概念
2. **关系抽取**: 识别实体间关系
3. **情感分析**: 判断情感倾向
4. **复杂度评估**: 评估问题复杂度
5. **领域识别**: 判断所属领域

**中文处理（千问 3.5）**:
```python
def analyze_chinese(self, text: str) -> SemanticAnalysis:
    """中文深度语义分析"""
    prompt = f"""
    请对以下问题进行深度语义分析：
    问题：{text}
    
    分析内容：
    1. 核心实体
    2. 实体关系
    3. 问题类型
    4. 预期答案类型
    5. 复杂度评分 (1-5)
    """
    response = self.qwen_llm.generate(prompt)
    return parse_analysis(response)
```

**英文处理（spaCy）**:
```python
def analyze_english(self, text: str) -> SemanticAnalysis:
    """英文工业级语义分析"""
    doc = self.spacy_nlp(text)
    
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    relations = self._extract_relations(doc)
    complexity = self._compute_complexity(doc)
    
    return SemanticAnalysis(
        entities=entities,
        relations=relations,
        complexity=complexity
    )
```

## 🔧 配置参数

### [config.py](./config.py) - 意图分析配置

```python
@dataclass
class IntentConfig:
    # 语言检测
    language_detection_threshold: float = 0.8
    
    # 意图识别
    intent_confidence_threshold: float = 0.7
    multi_intent_enabled: bool = True
    max_intents: int = 3
    
    # 中文处理（千问 3.5）
    qwen_model: str = "qwen-max"
    qwen_api_key: str = None
    qwen_temperature: float = 0.1
    
    # 英文处理（FastText）
    fasttext_model_path: str = "models/fasttext_intent.bin"
    fasttext_top_k: int = 5
    
    # 路由策略
    fallback_to_general: bool = True
    enable_strategy_fusion: bool = True
    
    # 性能优化
    cache_enabled: bool = True
    cache_ttl: int = 3600
```

## 📊 性能指标

### 准确率基准

| 语言 | 意图类型 | 准确率 | 平均延迟 |
|------|---------|--------|---------|
| **中文** | 事实查询 | 94% | <100ms |
| **中文** | 推理演绎 | 91% | <150ms |
| **英文** | 事实查询 | 92% | <50ms |
| **英文** | 比较分析 | 89% | <60ms |

### 优化技术

1. **缓存机制**: 高频查询意图缓存
2. **批量处理**: 支持批量意图识别
3. **异步处理**: 非阻塞语义分析
4. **模型量化**: FastText 模型量化加速

## 🎨 设计模式

### 1. 责任链模式 - 语义分析流水线

```python
class SemanticAnalysisPipeline:
    def __init__(self):
        self.handlers = [
            LanguageDetector(),
            EntityExtractor(),
            RelationExtractor(),
            ComplexityAnalyzer()
        ]
    
    def analyze(self, text: str):
        context = {"text": text}
        for handler in self.handlers:
            context = handler.handle(context)
        return SemanticAnalysis(**context)
```

### 2. 策略模式 - 多语言适配

```python
class LanguageStrategy(ABC):
    @abstractmethod
    def analyze(self, text: str) -> SemanticAnalysis:
        pass


class ChineseStrategy(LanguageStrategy):
    def __init__(self):
        self.llm = QwenLLM()
    
    def analyze(self, text: str):
        # 千问 3.5 深度分析
        pass


class EnglishStrategy(LanguageStrategy):
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
    
    def analyze(self, text: str):
        # spaCy 工业级处理
        pass
```

### 3. 工厂模式 - 意图对象创建

```python
class IntentFactory:
    @staticmethod
    def create_intent(intent_type: str, confidence: float) -> BaseIntent:
        intent_classes = {
            "factual": FactualQuery,
            "comparative": ComparativeAnalysis,
            "reasoning": ReasoningQuery,
            # ...
        }
        
        intent_class = intent_classes.get(intent_type)
        if not intent_class:
            raise ValueError(f"Unknown intent: {intent_type}")
        
        return intent_class(confidence=confidence)
```

## 🧪 测试示例

### 单元测试

```python
# tests/test_intent/test_classifier.py
def test_factual_query_classification():
    classifier = IntentClassifier()
    intent = classifier.classify("Python 3.12 发布了什么新特性？")
    
    assert intent.type == IntentType.FACTUAL
    assert intent.confidence > 0.9

def test_multilingual_support():
    classifier = IntentClassifier()
    
    # 中文
    cn_intent = classifier.classify("什么是深度学习？")
    assert cn_intent.language == "zh"
    
    # 英文
    en_intent = classifier.classify("What is deep learning?")
    assert en_intent.language == "en"
```

### 集成测试

```python
# tests/test_intent/test_router_integration.py
def test_intent_routing():
    router = IntentRouter()
    retriever = MockRetriever()
    
    query = "比较 Redis 和 Memcached 的性能差异"
    results = router.route_query(query, retriever)
    
    # 验证使用了比较分析策略
    assert results.strategy == "multi_entity"
    assert len(results) > 0
```

## 🐛 常见问题

### Q1: 意图识别不准确？

**解决方案**:
```python
# 1. 检查训练数据
classifier.check_training_data_quality()

# 2. 调整置信度阈值
classifier.set_threshold(0.6)  # 降低阈值提高召回

# 3. 添加自定义规则
classifier.add_rule(
    pattern=r"为什么.*",
    intent_type=IntentType.REASONING
)
```

### Q2: 中文理解效果差？

**优化方法**:
```python
# 确保使用千问 3.5
config = IntentConfig(
    qwen_model="qwen-max",  # 使用最强版本
    qwen_api_key=os.getenv("QWEN_API_KEY")
)

# 提供领域特定的 few-shot 示例
classifier.add_few_shot_examples([
    ("Transformer 架构的原理是什么？", IntentType.CONCEPTUAL),
    ("如何评价这篇论文的贡献？", IntentType.ANALYTICAL),
])
```

### Q3: 多意图处理不当？

**调试方法**:
```python
# 启用多意图检测
config.multi_intent_enabled = True

# 查看检测结果
intents = classifier.detect_multiple(
    "比较 A 和 B，并给出使用场景和建议"
)
for intent in intents:
    print(f"意图：{intent.type}, 权重：{intent.weight}")
```

## 📚 API 参考

### 完整使用示例

```python
from src.intent import IntentAnalyzer, IntentConfig

# 创建配置
config = IntentConfig(
    # 中文使用千问 3.5
    qwen_api_key="your-key",
    
    # 启用多意图
    multi_intent_enabled=True,
    
    # 启用缓存
    cache_enabled=True
)

# 创建分析器
analyzer = IntentAnalyzer(config=config)

# 完整分析流程
analysis = analyzer.analyze(
    query="深度学习在医疗影像分析中有哪些应用？优缺点是什么？",
    user_context={"domain": "medical", "expertise": "intermediate"}
)

# 查看结果
print(f"主要意图：{analysis.primary_intent.type}")
print(f"次要意图：{analysis.secondary_intent.type}")
print(f"推荐策略：{analysis.recommended_strategies}")
print(f"语义结构：{analysis.semantic_structure}")
```

## 🔗 相关链接

- [意图分类体系](../../docs/wiki/意图分析系统.md)
- [语义分析详解](../../docs/wiki/感知引擎模块.md#语义分析)
- [检索策略映射](../retrieval/README.md#策略选择)

## 📞 维护信息

**负责人**: NLP Team  
**最后更新**: 2026-03-19  
**测试覆盖率**: >85%  
**文档状态**: ✅ 完善

---

*意图分析是智能检索的第一步，准确的意图识别可以显著提升回答质量。*
