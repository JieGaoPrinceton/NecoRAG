# Pounce Strategy - 扑击检索策略

## 概述

Pounce Strategy（扑击检索策略）是 NecoRAG 的**检索层**核心组件，负责智能化的信息检索与重排序。模拟猫捕猎时的"锁定-跳跃"机制，实现精准、高效的知识获取。

## 核心功能

### 1. 混合检索策略

```
┌──────────────────────────────────────────────────────┐
│                  Pounce Strategy                      │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Query ──┬── 向量检索 (Vector Search)               │
│          │                                           │
│          ├── 关键词检索 (Keyword Search)             │
│          │                                           │
│          ├── 图谱检索 (Graph Search)                 │
│          │                                           │
│          └── HyDE 增强 (Hypothetical Document)       │
│                                                       │
│              ↓  结果融合 (Fusion)                     │
│                                                       │
│         ┌─────────────────────┐                      │
│         │  重排序 (Re-ranking) │                      │
│         │  · BGE-Reranker     │                      │
│         │  · Novelty Penalty  │                      │
│         └─────────────────────┘                      │
│                                                       │
│              ↓  置信度判断                            │
│                                                       │
│    ┌───────┴────────┐                                │
│    │                 │                                │
│  置信度 > 阈值    置信度 < 阈值                      │
│    │                 │                                │
│  返回结果        继续检索/重新检索                    │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 2. 多跳联想检索
基于扩散激活理论（Spreading Activation）：

```python
# 多跳检索流程
实体 A → [关系1] → 实体 B → [关系2] → 实体 C

# 激活值传递
activation(C) = activation(A) × relation_strength1 × relation_strength2
```

**特性**：
- 支持最多 5 跳推理
- 关系强度衰减机制
- 循环路径检测
- 动态剪枝优化

### 3. HyDE 增强（Hypothetical Document Embeddings）
解决提问模糊问题：

```
用户问题："那个软件怎么用？"
    ↓
LLM 生成假设答案："该软件的安装方法是..."
    ↓
假设答案向量化
    ↓
用假设答案向量检索真实文档
    ↓
返回相关度高文档
```

**优势**：
- 解决术语不匹配问题
- 提升模糊查询效果
- 支持多语言查询

### 4. Novelty Re-ranker（新颖性重排序）

```python
# 重排序评分公式
final_score = relevance_score 
              - α × redundancy_penalty 
              + β × novelty_bonus 
              + γ × diversity_bonus

# 参数说明：
# - relevance_score: 基础相关性分数
# - redundancy_penalty: 与已选结果的重复度
# - novelty_bonus: 新信息奖励
# - diversity_bonus: 多样性奖励
# - α, β, γ: 调节系数
```

**特性**：
- 抑制重复信息
- 优先展示新异知识
- 保证结果多样性
- 可配置权重

### 5. Pounce 机制（创新点）
模拟猫捕猎的"锁定-跳跃"行为：

```python
class PounceMechanism:
    """
    一旦置信度超过阈值，立即终止冗余检索
    
    模拟猫发现猎物后：
    - 锁定目标（置信度达标）
    - 立即扑击（终止检索）
    - 不做多余动作（避免浪费）
    """
    
    def should_pounce(self, confidence: float) -> bool:
        """
        判断是否应该"扑击"（返回结果）
        
        Args:
            confidence: 当前置信度
            
        Returns:
            是否立即返回结果
        """
        # 策略1: 固定阈值
        if confidence > self.threshold:
            return True
        
        # 策略2: 自适应阈值（基于查询复杂度）
        adaptive_threshold = self.calculate_adaptive_threshold()
        if confidence > adaptive_threshold:
            return True
        
        # 策略3: 边际收益递减
        if self.marginal_gain < self.min_gain:
            return True
        
        return False
```

## 核心类设计

### Retriever
检索器基类。

```python
class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]
    
    def batch_retrieve(self, queries: List[str]) -> List[List[RetrievalResult]]
```

### VectorRetriever
向量检索器。

```python
class VectorRetriever(Retriever):
    def __init__(self, memory: SemanticMemory, encoder: VectorEncoder)
    
    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]
    def hybrid_retrieve(self, query: str, vector_weight: float) -> List[RetrievalResult]
```

### GraphRetriever
图谱检索器。

```python
class GraphRetriever(Retriever):
    def __init__(self, graph: EpisodicGraph)
    
    def retrieve(self, query: str, top_k: int) -> List[RetrievalResult]
    def multi_hop_retrieve(self, entity: str, hops: int) -> List[GraphPath]
    def causal_retrieve(self, event: str) -> List[CausalChain]
```

### HyDEEnhancer
HyDE 增强器。

```python
class HyDEEnhancer:
    def __init__(self, llm: BaseLLM, encoder: VectorEncoder)
    
    def generate_hypothetical_doc(self, query: str) -> str
    def enhance_retrieval(self, query: str, retriever: Retriever) -> List[RetrievalResult]
```

### ReRanker
重排序器。

```python
class ReRanker:
    def __init__(self, model: str = "BGE-Reranker-v2")
    
    def rerank(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]
    def apply_novelty_penalty(self, results: List[RetrievalResult]) -> List[RetrievalResult]
    def ensure_diversity(self, results: List[RetrievalResult]) -> List[RetrievalResult]
```

### PounceController
扑击控制器。

```python
class PounceController:
    def __init__(self, threshold: float = 0.85)
    
    def evaluate_confidence(self, results: List[RetrievalResult]) -> float
    def should_pounce(self, confidence: float) -> bool
    def calculate_adaptive_threshold(self, query: str) -> float
```

### FusionStrategy
结果融合策略。

```python
class FusionStrategy:
    def reciprocal_rank_fusion(self, results: List[List[RetrievalResult]]) -> List[RetrievalResult]
    def weighted_fusion(self, results: List[List[RetrievalResult]], weights: List[float]) -> List[RetrievalResult]
```

## 使用示例

```python
from necorag.retrieval import PounceRetriever
from necorag.memory import MemoryManager

# 初始化
memory = MemoryManager(...)
retriever = PounceRetriever(
    memory=memory,
    reranker="BGE-Reranker-v2",
    pounce_threshold=0.85
)

# 基础检索
results = retriever.retrieve(
    query="机器学习有哪些应用？",
    top_k=10
)

# 多跳检索
graph_results = retriever.multi_hop_retrieve(
    entity="人工智能",
    hops=3
)

# HyDE 增强检索
hyde_results = retriever.retrieve_with_hyde(
    query="那个算法怎么优化？",
    top_k=10
)

# 查看检索路径
print(retriever.get_retrieval_trace())
```

## 检索流程详解

### 完整检索流程

```
1. 查询预处理
   - 查询改写
   - 实体识别
   - 意图分析

2. 多路并行检索
   - 向量检索（L2）
   - 图谱检索（L3）
   - HyDE 增强（可选）

3. 结果融合
   - RRF（倒数排名融合）
   - 或加权融合

4. 重排序
   - BGE-Reranker 精排
   - Novelty 惩罚
   - 多样性保证

5. Pounce 判断
   - 计算置信度
   - 判断是否终止
   - 返回结果或继续检索
```

### 自适应检索策略

```python
# 简单查询 → 快速路径
if query_complexity == "simple":
    return vector_search_only()

# 复杂查询 → 完整路径
if query_complexity == "complex":
    return full_retrieval_pipeline()

# 推理查询 → 图谱优先
if query_type == "reasoning":
    return graph_first_strategy()
```

## 配置参数

### 检索参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `top_k` | int | 10 | 检索数量 |
| `min_score` | float | 0.3 | 最低相关度 |
| `max_hops` | int | 3 | 最大跳数 |
| `hyde_enabled` | bool | True | 启用 HyDE |

### 重排序参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `novelty_weight` | float | 0.3 | 新颖性权重 |
| `diversity_weight` | float | 0.2 | 多样性权重 |
| `redundancy_penalty` | float | 0.4 | 冗余惩罚 |

### Pounce 参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `pounce_threshold` | float | 0.85 | 扑击阈值 |
| `min_gain` | float | 0.05 | 最小边际收益 |
| `max_iterations` | int | 3 | 最大迭代次数 |

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 简单查询延迟 | < 200ms | 纯向量检索 |
| 复杂查询延迟 | < 800ms | 多跳+重排 |
| Recall@10 | > 85% | 前10结果召回率 |
| NDCG@10 | > 0.8 | 排序质量 |

## 依赖组件

- BGE-Reranker-v2：重排序模型
- BGE-M3：向量化模型
- Qdrant：向量检索
- Neo4j：图谱检索

## 后续优化方向

1. 学习排序（Learning to Rank）
2. 查询理解增强
3. 个性化检索
4. 多模态检索
5. 增量检索优化
