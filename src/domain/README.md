# 🌐 NecoRAG 领域权重系统

## 📋 目录说明

本目录包含 NecoRAG 的领域权重计算模块，实现领域知识增强、时间衰减和多维权重融合。

## 📁 文件结构

```
domain/
├── __init__.py                 # 包初始化与导出 ⭐
├── weight_calculator.py        # 权重计算器 ⭐
├── relevance.py                # 领域相关性计算 ⭐
├── temporal_weight.py          # 时间权重计算 ⭐
└── config.py                   # 领域配置管理
```

## 🎯 核心功能

### 1. [weight_calculator.py](./weight_calculator.py) - 权重计算器 ⭐

**功能**: 综合多因子计算最终检索权重

**权重公式**:
```python
final_weight = base_score × α × keyword_weight × β × temporal_weight × γ × domain_weight × δ × intent_weight

默认系数: α=β=γ=δ=1.0
```

**权重因子**:
1. **base_score**: 向量相似度基础分数
2. **keyword_weight**: 领域关键字权重
3. **temporal_weight**: 时间衰减权重
4. **domain_weight**: 领域相关性权重
5. **intent_weight**: 意图匹配权重

**使用示例**:
```python
from src.domain import WeightCalculator

calculator = WeightCalculator()

# 计算综合权重
weight = calculator.calculate(
    base_score=0.85,
    keywords=["深度学习", "神经网络"],
    document_time=datetime.now(),
    document_domain="AI",
    query_intent="conceptual"
)

print(f"最终权重：{weight}")  # 0.92
```

### 2. [relevance.py](./relevance.py) - 领域相关性计算 ⭐

**功能**: 计算文档与查询的领域相关性

**领域分类层级**:
```
技术领域
├── 人工智能
│   ├── 深度学习 ⭐ (核心)
│   ├── 机器学习 (重要)
│   └── 自然语言处理 (相关)
├── 数据库
│   ├── NoSQL (核心)
│   └── SQL (相关)
└── 网络 (边缘)
```

**相关性等级**:
| 等级 | 权重 | 说明 | 示例 |
|------|------|------|------|
| **核心领域** | 1.5 | 完全属于目标领域 | AI 论文中的"注意力机制" |
| **重要领域** | 1.2 | 与目标领域强相关 | AI 应用中的"图像处理" |
| **相关领域** | 1.0 | 弱相关但有价值 | "统计学方法" |
| **边缘领域** | 0.6 | 跨领域参考 | "心理学理论" |
| **领域外** | 0.2 | 基本无关 | "娱乐新闻" |

**计算方法**:
```python
def calculate_domain_relevance(
    self,
    document_keywords: List[str],
    target_domain: str,
    domain_hierarchy: Dict
) -> float:
    """计算领域相关性"""
    
    # 1. 识别文档所属领域
    doc_domain = self._classify_domain(document_keywords)
    
    # 2. 计算领域距离
    distance = self._compute_domain_distance(
        doc_domain,
        target_domain,
        domain_hierarchy
    )
    
    # 3. 映射到权重
    weight = self._distance_to_weight(distance)
    
    return weight
```

### 3. [temporal_weight.py](./temporal_weight.py) - 时间权重计算 ⭐

**功能**: 基于时间衰减函数计算知识新鲜度权重

**衰减模型**:
```python
# 指数衰减模型
temporal_weight = e^(-λ × Δt)

λ: 衰减系数（领域相关）
Δt: 时间差（年）
```

**衰减系数参考**:
| 领域类型 | λ 值 | 半衰期 | 适用场景 |
|---------|-----|--------|---------|
| **快速变化** | 2.0 | 4 个月 | 技术新闻、框架版本 |
| **中速变化** | 1.0 | 8 个月 | 编程技术、最佳实践 |
| **慢速变化** | 0.5 | 16 个月 | 基础理论、算法原理 |
| **稳定知识** | 0.1 | 8 年 | 数学定理、物理定律 |

**时间分级策略**:
```python
TIME_RANGES = {
    "recent": (0, 30),      # 0-30 天，权重 1.0-1.2
    "new": (30, 90),        # 30-90 天，权重 0.8-1.0
    "medium": (90, 365),    # 90-365 天，权重 0.5-0.8
    "old": (365, 1095),     # 1-3 年，权重 0.3-0.5
    "historical": (1095,)   # 3 年以上，权重 0.1-0.3
}
```

**使用示例**:
```python
from src.domain import TemporalWeightCalculator

twc = TemporalWeightCalculator()

# 计算时间权重（30 天前的文档）
weight = twc.calculate(
    document_date=datetime.now() - timedelta(days=30),
    decay_coefficient=1.0
)
print(weight)  # 0.91

# 计算时间权重（1 年前的文档）
weight = twc.calculate(
    document_date=datetime.now() - timedelta(days=365),
    decay_coefficient=0.5  # 基础理论
)
print(weight)  # 0.61
```

## 🔧 配置管理

### [config.py](./config.py) - 领域配置

```python
@dataclass
class DomainConfig:
    # 领域关键字词典
    domain_keywords: Dict[str, List[str]] = field(default_factory=dict)
    
    # 关键字权重分级
    keyword_weights: Dict[str, float] = field(default_factory=dict)
    # 示例: {"深度学习": 2.0, "算法": 1.5, "数据": 1.0}
    
    # 领域层次结构
    domain_hierarchy: Dict[str, Any] = field(default_factory=dict)
    
    # 时间衰减系数（按领域）
    decay_coefficients: Dict[str, float] = field(default_factory=dict)
    # 示例: {"AI": 1.5, "数学": 0.3}
    
    # 权重融合系数
    fusion_coefficients: Dict[str, float] = field(
        default_factory=lambda: {
            "alpha": 1.0,  # 基础分数系数
            "beta": 1.0,   # 关键字系数
            "gamma": 1.0,  # 时间系数
            "delta": 1.0   # 领域系数
        }
    )
    
    # 是否启用经典知识保护（不受时间衰减）
    classic_protection_enabled: bool = True
    classic_threshold: float = 0.95  # 置信度阈值
```

## 📊 权重计算实例

### 完整计算流程

```python
from src.domain import WeightCalculator, DomainConfig
from datetime import datetime, timedelta

# 1. 创建配置
config = DomainConfig(
    domain_keywords={
        "core": ["深度学习", "神经网络", "反向传播"],
        "important": ["梯度下降", "损失函数", "优化器"],
        "normal": ["训练", "模型", "参数"]
    },
    keyword_weights={
        "深度学习": 2.0,
        "神经网络": 1.8,
        "梯度下降": 1.5,
        "训练": 1.0
    },
    decay_coefficients={"AI": 1.2}
)

# 2. 创建计算器
calculator = WeightCalculator(config=config)

# 3. 准备数据
document = {
    "keywords": ["深度学习", "神经网络", "训练技巧"],
    "created_at": datetime.now() - timedelta(days=60),
    "domain": "AI"
}

query = {
    "keywords": ["深度学习", "如何训练"],
    "intent": "procedural"
}

# 4. 计算各项权重
base_score = 0.75  # 向量相似度

keyword_weight = calculator.calculate_keyword_weight(
    doc_keywords=document["keywords"],
    query_keywords=query["keywords"]
)
# 结果：1.6 (命中核心关键字"深度学习")

temporal_weight = calculator.calculate_temporal_weight(
    doc_date=document["created_at"],
    domain="AI"
)
# 结果：0.85 (60 天前，中等新鲜度)

domain_weight = calculator.calculate_domain_weight(
    doc_domain=document["domain"],
    query_domain="AI"
)
# 结果：1.5 (完全匹配核心领域)

intent_weight = calculator.calculate_intent_weight(
    doc_type="tutorial",
    query_intent=query["intent"]
)
# 结果：1.2 (教程类文档匹配操作指导意图)

# 5. 综合计算
final_weight = calculator.calculate_composite(
    base_score=base_score,
    keyword_weight=keyword_weight,
    temporal_weight=temporal_weight,
    domain_weight=domain_weight,
    intent_weight=intent_weight
)

print(f"基础分数：{base_score}")
print(f"最终权重：{final_weight}")
# 输出：0.75 × 1.6 × 0.85 × 1.5 × 1.2 = 1.84
```

## 🎨 设计模式

### 1. 策略模式 - 衰减函数选择

```python
class DecayStrategy(ABC):
    @abstractmethod
    def decay(self, delta_t: float) -> float:
        pass


class ExponentialDecay(DecayStrategy):
    def __init__(self, lambda_: float):
        self.lambda_ = lambda_
    
    def decay(self, delta_t: float) -> float:
        return math.exp(-self.lambda_ * delta_t)


class LinearDecay(DecayStrategy):
    def __init__(self, slope: float):
        self.slope = slope
    
    def decay(self, delta_t: float) -> float:
        return max(0, 1 - self.slope * delta_t)


class StepDecay(DecayStrategy):
    def __init__(self, steps: List[Tuple[int, float]]):
        self.steps = steps  # [(天数，权重), ...]
    
    def decay(self, delta_t: float) -> float:
        for days, weight in reversed(self.steps):
            if delta_t >= days:
                return weight
        return 1.0
```

### 2. 构建者模式 - 权重计算链

```python
class WeightBuilder:
    def __init__(self, base_score: float):
        self.score = base_score
        self.multipliers = []
    
    def add_keyword_boost(self, keywords: List[str]) -> 'WeightBuilder':
        boost = self._calc_keyword_boost(keywords)
        self.multipliers.append(boost)
        return self
    
    def add_temporal_decay(self, date: datetime) -> 'WeightBuilder':
        decay = self._calc_temporal_decay(date)
        self.multipliers.append(decay)
        return self
    
    def add_domain_relevance(self, domain: str) -> 'WeightBuilder':
        relevance = self._calc_domain_relevance(domain)
        self.multipliers.append(relevance)
        return self
    
    def build(self) -> float:
        result = self.score
        for mult in self.multipliers:
            result *= mult
        return result

# 流式调用
weight = (WeightBuilder(0.75)
    .add_keyword_boost(["深度学习"])
    .add_temporal_decay(past_date)
    .add_domain_relevance("AI")
    .build())
```

## 🧪 测试示例

### 单元测试

```python
# tests/test_domain/test_temporal_weight.py
def test_exponential_decay():
    twc = TemporalWeightCalculator()
    
    # 刚发布的文档
    weight = twc.calculate(datetime.now(), decay_coefficient=1.0)
    assert weight == 1.0
    
    # 半年前的文档
    half_year_ago = datetime.now() - timedelta(days=180)
    weight = twc.calculate(half_year_ago, decay_coefficient=1.0)
    assert 0.5 < weight < 0.7
    
    # 经典知识（衰减慢）
    old_date = datetime.now() - timedelta(days=730)  # 2 年前
    weight = twc.calculate(old_date, decay_coefficient=0.1)
    assert weight > 0.8  # 仍然保持较高权重
```

### 集成测试

```python
# tests/test_domain/test_weight_integration.py
def test_full_weight_pipeline():
    calculator = WeightCalculator()
    
    # 模拟高质量新文档
    weight_new = calculator.calculate(
        base_score=0.9,
        keywords=["最新技术"],
        document_time=datetime.now(),
        document_domain="AI"
    )
    
    # 模拟低质量旧文档
    weight_old = calculator.calculate(
        base_score=0.5,
        keywords=["过时技术"],
        document_time=datetime.now() - timedelta(days=365),
        document_domain="AI"
    )
    
    # 新文档权重应该显著高于旧文档
    assert weight_new > weight_old * 1.5
```

## 🐛 常见问题

### Q1: 权重计算结果异常？

**排查步骤**:
```python
# 1. 检查各项权重分量
weights = calculator.decompose(
    base_score=0.8,
    keywords=["test"],
    date=datetime.now(),
    domain="AI"
)

print(weights)
# 输出：{
#   'base': 0.8,
#   'keyword': 1.2,
#   'temporal': 0.9,
#   'domain': 1.5,
#   'final': 1.3
# }

# 2. 检查配置是否正确
print(calculator.config.keyword_weights)
print(calculator.config.decay_coefficients)
```

### Q2: 时间衰减过快/过慢？

**调整方法**:
```python
# 针对特定领域调整衰减系数
config = DomainConfig(
    decay_coefficients={
        "AI": 1.5,      # AI 领域衰减快（技术更新快）
        "数学": 0.2,    # 数学衰减慢（知识稳定）
        "历史": 0.1     # 历史几乎不衰减
    }
)

# 或者全局调整
calculator.set_global_decay(0.5)  # 降低全局衰减系数
```

### Q3: 领域关键字不生效？

**解决方案**:
```python
# 1. 确保关键字在词典中
assert "深度学习" in config.keyword_weights

# 2. 检查权重设置是否合理
print(config.keyword_weights["深度学习"])  # 应该 > 1.0

# 3. 添加同义词映射
config.synonym_map = {
    "DL": "深度学习",
    "神经网络": "NN",
    "CNN": "卷积神经网络"
}
```

## 📚 API 参考

### 完整参数说明

```python
WeightCalculator.calculate(
    # 基础分数
    base_score: float,
    
    # 关键字相关
    keywords: List[str],
    keyword_boost: float = 1.0,
    
    # 时间相关
    document_time: datetime,
    decay_coefficient: float = 1.0,
    
    # 领域相关
    document_domain: str,
    target_domain: str,
    domain_relevance: float = 1.0,
    
    # 意图相关
    query_intent: str,
    document_type: str,
    
    # 融合系数
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    delta: float = 1.0
) -> float
```

## 🔗 相关链接

- [领域权重设计文档](../../design/design.md#领域知识与关键字权重系统)
- [时间权重详解](../../docs/wiki/领域权重系统/时间权重机制.md)
- [检索融合策略](../retrieval/README.md#结果融合)

## 📞 维护信息

**负责人**: Ranking Team  
**最后更新**: 2026-03-19  
**测试覆盖率**: >90%  
**文档状态**: ✅ 完善

---

*领域权重系统是检索精准度的核心保障，通过多维度加权确保最相关的知识优先呈现。*
