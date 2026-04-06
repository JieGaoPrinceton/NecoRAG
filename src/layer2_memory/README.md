# Nine-Lives Memory - 九命记忆存储

## 概述

Nine-Lives Memory（九命记忆存储）是 NecoRAG 的**记忆层**核心组件，负责知识的分层存储与管理。模拟人脑的多层记忆系统和猫的"九命"特性，实现短期工作记忆与长期结构化记忆的协同。

## 核心功能

### 1. 三层记忆架构

```
┌────────────────────────────────────────────────────────┐
│                  Nine-Lives Memory                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  L1 工作记忆 (Working Memory)                    │  │
│  │  · Redis 缓存层                                  │  │
│  │  · 当前会话上下文                                │  │
│  │  · 用户意图轨迹                                  │  │
│  │  · TTL 自动过期（瞬时遗忘）                      │  │
│  └─────────────────────────────────────────────────┘  │
│                       ↕                                │
│  ┌─────────────────────────────────────────────────┐  │
│  │  L2 语义记忆 (Semantic Memory)                   │  │
│  │  · Qdrant/Milvus 向量库                         │  │
│  │  · 高维向量存储                                  │  │
│  │  · 模糊匹配与直觉检索                            │  │
│  └─────────────────────────────────────────────────┘  │
│                       ↕                                │
│  ┌─────────────────────────────────────────────────┐  │
│  │  L3 情景图谱 (Episodic Graph)                    │  │
│  │  · Neo4j/NebulaGraph                            │  │
│  │  · 实体关系网络                                  │  │
│  │  · 多跳推理与因果链条                            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### 2. L1 工作记忆 (Redis)
- **存储内容**：当前会话上下文、用户意图轨迹
- **特性**：极低延迟访问，TTL 自动过期
- **容量管理**：LRU 淘汰策略，防止内存溢出
- **模拟机制**：瞬时遗忘 - 不活跃信息自动衰减

### 3. L2 语义记忆 (Qdrant/Milvus)
- **存储内容**：高维向量、稠密向量、稀疏向量
- **特性**：支持混合搜索（向量+关键词）
- **索引优化**：HNSW 算法，毫秒级检索
- **模拟机制**：模糊匹配 - 类似人脑的联想回忆

### 4. L3 情景图谱 (Neo4j/NebulaGraph)
- **存储内容**：实体、关系、属性、事件
- **特性**：支持 Cypher 查询，多跳推理
- **图谱类型**：
  - 知识图谱：实体-关系-实体
  - 事件图谱：时间-事件-影响
  - 因果图谱：原因-结果-强度
- **模拟机制**：结构化记忆 - 深度理解与推理

### 5. 动态权重衰减（创新点）
模拟生物记忆的巩固与遗忘机制：

```python
# 记忆权重衰减公式
weight(t) = initial_weight × e^(-λt) × access_frequency

# 参数说明：
# - initial_weight: 初始重要性权重
# - λ: 衰减速率
# - t: 时间间隔
# - access_frequency: 访问频率
```

**衰减策略**：
- 低频访问知识自动降权
- 低于阈值自动归档
- 重要知识权重强化
- 热点知识保持鲜活

## 核心类设计

### MemoryManager
记忆管理器，统一管理三层记忆。

```python
class MemoryManager:
    def store(chunk: EncodedChunk) -> MemoryID
    def retrieve(query: Query, layers: List[MemoryLayer]) -> List[MemoryItem]
    def consolidate() -> None  # 记忆巩固
    def forget(threshold: float) -> int  # 主动遗忘
```

### WorkingMemory (L1)
工作记忆实现。

```python
class WorkingMemory:
    def __init__(self, redis_client: Redis, ttl: int = 3600)
    
    def add_context(session_id: str, context: Dict) -> None
    def get_context(session_id: str) -> Dict
    def track_intent(session_id: str, intent: Intent) -> None
    def get_intent_trajectory(session_id: str) -> List[Intent]
    def clear_expired() -> int
```

### SemanticMemory (L2)
语义记忆实现。

```python
class SemanticMemory:
    def __init__(self, vector_db: QdrantClient)
    
    def store_vectors(chunks: List[EncodedChunk]) -> List[str]
    def search(query_vector: np.ndarray, top_k: int) -> List[SearchResult]
    def hybrid_search(query: str, vector_weight: float) -> List[SearchResult]
    def update_metadata(memory_id: str, metadata: Dict) -> bool
```

### EpisodicGraph (L3)
情景图谱实现。

```python
class EpisodicGraph:
    def __init__(self, graph_db: Neo4jClient)
    
    def add_entity(entity: Entity) -> str
    def add_relation(source: str, target: str, relation: Relation) -> str
    def multi_hop_query(start: str, hops: int) -> List[GraphPath]
    def find_causal_chain(event: str) -> List[CausalLink]
    def get_related_entities(entity: str, depth: int) -> List[Entity]
```

### MemoryDecay
记忆衰减机制。

```python
class MemoryDecay:
    def __init__(self, decay_rate: float = 0.1)
    
    def calculate_weight(memory: MemoryItem) -> float
    def apply_decay() -> Dict[str, float]  # 批量衰减
    def archive_low_weight(threshold: float) -> int
    def reinforce(memory_id: str) -> None  # 强化权重
```

## 使用示例

```python
from necorag.memory import MemoryManager, MemoryLayer
from necorag.whiskers import EncodedChunk

# 初始化记忆管理器
memory = MemoryManager(
    redis_url="redis://localhost:6379",
    qdrant_url="http://localhost:6333",
    neo4j_url="bolt://localhost:7687"
)

# 存储知识
chunk = EncodedChunk(content="...", vectors=..., tags=...)
memory_id = memory.store(chunk)

# 检索知识（跨层）
results = memory.retrieve(
    query="什么是机器学习？",
    layers=[MemoryLayer.L1, MemoryLayer.L2, MemoryLayer.L3]
)

# 记忆巩固
memory.consolidate()

# 主动遗忘低价值记忆
forgotten_count = memory.forget(threshold=0.1)
```

## 数据流转

```
1. 新知识入库流程：
   EncodedChunk → L1 缓存 → L2 向量化存储 → L3 图谱节点创建
   
2. 检索流程：
   Query → L1 查上下文 → L2 向量检索 → L3 图谱推理 → 融合结果

3. 记忆巩固流程：
   L1 高频数据 → L2 持久化
   L2 关联数据 → L3 图谱连接
   低频数据 → 归档/删除
```

## 配置参数

### L1 工作记忆配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `redis_ttl` | int | 3600 | 会话 TTL（秒） |
| `max_session_items` | int | 1000 | 单会话最大条目 |
| `lru_max_size` | int | 10000 | LRU 最大缓存数 |

### L2 语义记忆配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `vector_size` | int | 1024 | 向量维度 |
| `collection_name` | str | "necorag" | 集合名称 |
| `index_type` | str | "HNSW" | 索引类型 |

### L3 情景图谱配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_relation_depth` | int | 5 | 最大关系深度 |
| `enable_causal_graph` | bool | True | 启用因果图谱 |

### 衰减机制配置
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `decay_rate` | float | 0.1 | 衰减速率 λ |
| `archive_threshold` | float | 0.05 | 归档阈值 |
| `consolidation_interval` | int | 3600 | 巩固间隔（秒） |

## 性能指标

| 层级 | 写入延迟 | 检索延迟 | 容量 |
|------|----------|----------|------|
| L1 | < 5ms | < 2ms | 10万条 |
| L2 | < 50ms | < 100ms | 千万级 |
| L3 | < 100ms | < 500ms | 亿级节点 |

## 依赖组件

- **Redis**：L1 工作记忆
- **Qdrant / Milvus**：L2 语义记忆
- **Neo4j / NebulaGraph**：L3 情景图谱

## 后续优化方向

1. 记忆压缩技术（减少存储空间）
2. 分布式记忆存储
3. 冷热数据自动迁移
4. 记忆一致性保证
5. 多租户隔离机制
