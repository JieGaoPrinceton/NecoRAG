# NecoRAG 技术栈详解

**Third-Party Systems Integration Guide**

版本：v3.2.0-alpha  
更新日期：2026-03-19

---

## 📋 目录

- [概述](#概述)
- [五层认知架构](#五层认知架构)
- [AI/ML 模型服务](#aiml 模型服务)
- [数据存储系统](#数据存储系统)
- [文档处理系统](#文档处理系统)
- [任务调度系统](#任务调度系统)
- [监控运维系统](#监控运维系统)
- [选型决策指南](#选型决策指南)

---

## 🎯 概述

NecoRAG 采用**可插拔架构设计**,支持 23 个第三方系统的灵活组合，实现完整的五层认知架构。

### 技术栈全景图

```
┌─────────────────────────────────────────────────────────┐
│              NecoRAG 技术栈全景图                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🎨 应用层 (2 个系统)                                    │
│     Streamlit(前端) | LangGraph(编排引擎)                │
│                                                         │
│  🔤 AI 模型层 (8 个系统)                                 │
│     Ollama/vLLM | BGE-M3 | BGE-Reranker | Rasa          │
│     spaCy+jieba | PaddleOCR | HuggingFace TGI           │
│                                                         │
│  💾 存储层 (5 个系统)                                    │
│     Redis(L1) | Qdrant(L2) | Neo4j(L3)                  │
│     MySQL(元数据) | MinIO(文件)                          │
│                                                         │
│  ⚙️ 中间件层 (2 个系统)                                  │
│     APScheduler(定时) | Celery(异步队列)                 │
│                                                         │
│  📊 监控层 (3 个系统)                                    │
│     Prometheus(采集) | Grafana(可视化) | APM(性能监控)    │
│                                                         │
│  🔍 增强层 (3 个系统)                                    │
│     Elasticsearch(全文搜索) | Kibana(可视化)             │
│     RAGFlow(深度文档解析)                                │
│                                                         │
│  总计：23 个第三方系统 | 覆盖率 100%                      │
└─────────────────────────────────────────────────────────┘
```

### 核心创新

1. **L1/L2/L3三级存储**: Redis(工作记忆) → Qdrant(向量) → Neo4j(图谱)
2. **智能路由融合**: 多路召回 + Rerank 优化 + 意图溯源
3. **零依赖启动**: Mock 方案 + 本地部署，5 分钟快速体验
4. **生产就绪**: 完整监控、告警、日志系统

---

## 🧠 五层认知架构

### 1. Whiskers Engine（推理引擎）

**职责**: 查询理解、任务分解、逻辑推理

**核心组件**:
- Intent Classifier: 意图识别（Rasa/BERT）
- Query Decomposer: 查询分解
- Logic Reasoner: 逻辑推理

**依赖**: Ollama/vLLM, Rasa, BERT

### 2. Nine-Lives Memory（记忆系统）

**职责**: 多粒度知识存储与检索

**三级存储结构**:
```
L1 Working Memory (Redis)
  ├─ 短期会话状态
  ├─ 上下文缓存
  └─ TTL: 1-24 小时
  
L2 Semantic Memory (Qdrant)
  ├─ 向量知识库
  ├─ 稠密 + 稀疏混合索引
  └─ 检索延迟：< 10ms
  
L3 Episodic Graph (Neo4j)
  ├─ 情景知识图谱
  ├─ 多跳推理查询
  └─ 节点规模：千万级
```

### 3. Pounce Strategy（策略引擎）

**职责**: 动态路由、资源调度、质量评估

**核心功能**:
- Multi-path Routing: 多路召回（向量 + 图谱 + 关键词）
- Quality Scorer: 质量评分
- Resource Scheduler: 资源调度

### 4. Grooming Agent（校正代理）

**职责**: 事实核查、一致性验证、去重聚合

**校正流程**:
```
检索结果 → 事实核查 → 一致性验证 → 去重聚合 → 最终输出
```

### 5. Purr Interface（交互界面）

**职责**: 流式响应、多模态交互、用户反馈

**实现方式**:
- RESTful API (FastAPI)
- WebSocket 实时通信
- Streamlit 可视化界面

---

## 🔤 AI/ML 模型服务

### 1. LLM 推理服务

#### 推荐方案：Ollama + vLLM

| 方案 | 类型 | 优点 | 缺点 | 适用场景 |
|-----|------|------|------|---------|
| **Ollama** | 本地 | ✅ 部署简单<br/>✅ 模型丰富<br/>✅ 免费开源 | ❌ 性能中等 | 开发/中小规模 |
| **vLLM** | 本地 | ✅ 性能极强<br/>✅ 高吞吐<br/>✅ 显存优化 | ❌ 配置复杂 | 大规模生产 |
| **OpenAI** | 云端 | ✅ 质量最高<br/>✅ 无需运维 | ❌ 成本高 | 高质量需求 |

#### 部署配置

**开发环境 (Ollama)**:
```bash
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest

# 拉取模型
docker exec ollama ollama pull llama3
```

**生产环境 (vLLM)**:
```bash
docker run -d \
  --gpus all \
  --name vllm \
  -p 8000:8000 \
  -v model_cache:/models \
  vllm/vllm-openai:latest \
  --model /models/Llama-3-70B-Instruct \
  --tensor-parallel-size 2
```

#### 性能基准

| 模型 | 并发 | P50 | P95 | 吞吐量 |
|-----|------|-----|-----|--------|
| Ollama (Llama3 8B) | 1 | 120ms | 180ms | 45 tok/s |
| Ollama (Llama3 8B) | 10 | 350ms | 520ms | 38 tok/s |
| vLLM (Llama3 70B) | 1 | 80ms | 120ms | 120 tok/s |
| vLLM (Llama3 70B) | 10 | 200ms | 320ms | 95 tok/s |

### 2. 向量化模型

#### 推荐方案：BGE-M3

**技术特性**:
- 支持多语言（中/英/其他）
- 支持长文本（最长 8192 tokens）
- 稠密 + 稀疏混合嵌入
- 维度：1024

**部署配置**:
```bash
docker run -d \
  --name bge-m3 \
  --gpus all \
  -p 8001:8000 \
  -v ./models:/app/models \
  xhluca/bge-m3:latest
```

**Python 调用**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')
embeddings = model.encode(
    ["什么是深度学习？"],
    normalize_embeddings=True
)
```

### 3. 重排序模型

#### 推荐方案：BGE-Reranker-v2

**技术特性**:
- Cross-Encoder 架构
- 中文优化
- 精度高（~92%）

**部署配置**:
```bash
docker run -d \
  --name reranker \
  --gpus all \
  -p 8002:8000 \
  flagembedding/bge-reranker:latest
```

### 4. 意图识别

#### 推荐方案：Rasa NLU

**技术栈**:
- Jieba 分词（中文）
- DIETClassifier（双塔编码器）
- 支持实体抽取

**训练数据要求**:
- 每个意图：≥ 50 条样本
- 总样本：≥ 1000 条
- 测试集：20%

**准确率预期**:
- 意图识别：> 90%
- 实体抽取 F1: > 0.85

### 5. OCR 文档扫描

#### 推荐方案：PaddleOCR

**支持能力**:
- 100+ 语言
- 文本检测 + 识别
- 表格识别
- 公式识别

**部署配置**:
```bash
docker run -d \
  --name paddleocr \
  -p 8003:8866 \
  -v ocr_output:/output \
  paddlepaddle/paddleocr:latest
```

---

## 💾 数据存储系统

### 1. Redis（L1 工作记忆）

**功能定位**:
- 短期会话状态存储
- Embedding 缓存（减少重复计算）
- 限流计数器

**部署配置**:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --maxmemory 2gb
```

**性能指标**:
- 读写延迟：< 1ms
- 并发连接：10,000+
- 内存利用：LRU 自动淘汰

### 2. Qdrant（L2 向量数据库）

**功能定位**:
- 语义向量检索
- 混合搜索（向量 + 元数据过滤）
- 多路召回主索引

**技术优势**:
- Rust 编写，性能强
- HNSW 索引高效
- 支持分布式集群

**部署配置**:
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

**集合配置示例**:
```python
client.create_collection(
    collection_name="semantic_memory",
    vectors_config=models.VectorParams(
        size=1024,  # BGE-M3 维度
        distance=models.Distance.COSINE
    ),
    hnsw_config=models.HnswConfigDiff(
        m=16,
        ef_construct=100
    )
)
```

**性能指标**:
- 百万级向量检索：< 10ms
- 写入速度：~5K/s
- 内存占用：中等

### 3. Neo4j（L3 情景图谱）

**功能定位**:
- 情景知识图谱存储
- 多跳推理查询
- 关系挖掘分析

**技术优势**:
- Cypher 查询语言
- 内置 30+ 图算法
- ACID 事务保证

**部署配置**:
```bash
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  -e NEO4J_AUTH=neo4j/necorag_password \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  neo4j:5-community
```

**查询示例**:
```cypher
// 2 跳关联检索
MATCH path = (start:Entity {id: "深度学习"})
             -[:RELATED_TO*2..3]-(end)
RETURN path
ORDER BY length(path) DESC
LIMIT 50
```

**性能指标**:
- 2-3 跳查询：< 100ms
- 节点规模：500 万 +
- 并发查询：50-100 QPS

---

## 📄 文档处理系统

### RAGFlow（深度文档解析）

**功能定位**:
- PDF/Word/Excel/PPT 解析
- 表格结构还原
- 公式识别
- 段落层级保持

**核心能力**:
- 内置 PaddleOCR
- 表格识别准确率 > 90%
- 解析速度：10-20 页/秒

**部署配置**:
```bash
docker-compose up -d ragflow mysql minio
```

**API 调用**:
```python
import requests

response = requests.post(
    "http://localhost:9380/api/v1/document/upload",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    files={"file": open("document.pdf", "rb")}
)
```

---

## ⚙️ 任务调度系统

### 1. APScheduler（轻量定时）

**适用场景**:
- 定期知识更新
- 内存清理
- 日志轮转

**使用示例**:
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=knowledge_updater.update,
    trigger="interval",
    hours=1
)
scheduler.start()
```

### 2. Celery（分布式队列）

**适用场景**:
- 异步任务队列
- 批量数据处理
- 分布式任务调度

**部署配置**:
```yaml
celery_worker:
  image: necorag/celery:latest
  command: celery -A tasks worker --loglevel=info
  environment:
    - CELERY_BROKER=redis://redis:6379/0
    - CELERY_BACKEND=redis://redis:6379/1
```

---

## 📊 监控运维系统

### 1. Prometheus（指标采集）

**采集指标**:
- HTTP 请求数/延迟
- 向量检索 QPS/延迟
- GPU/CPU/内存使用率
- Redis 命中率

**部署配置**:
```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### 2. Grafana（可视化）

**Dashboard 模板**:
- FastAPI 监控（ID: 10280）
- Redis 监控（ID: 763）
- Qdrant 监控（自定义）
- Neo4j 监控（ID: 1752）

**部署配置**:
```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. APM（应用性能监控）

**集成方案**:
- Elastic APM（推荐）
- Jaeger（分布式追踪）
- New Relic（商业方案）

---

## 🎯 选型决策指南

### 快速选型决策树

```
开始
│
├─ 需求场景？
│   ├─ 开发测试 → 使用 Mock/轻量方案
│   ├─ 小规模生产 (< 100 QPS) → 单机部署开源方案
│   └─ 大规模生产 (> 100 QPS) → 集群部署商业/云服务
│
├─ 预算限制？
│   ├─ 零预算 → 全部开源 + 本地部署
│   ├─ 有限预算 → 核心用开源，关键用云服务
│   └─ 充足预算 → 全链路商业服务
│
└─ 部署环境？
    ├─ 本地/私有云 → Ollama + Qdrant + Neo4j
    ├─ 公有云 → 云厂商托管服务
    └─ 混合云 → 核心本地 + 弹性云端
```

### 四套推荐配置

#### 1. MVP（零成本）

```yaml
LLM: Ollama (CPU 模式，Phi-3-mini)
向量库：Chroma (In-memory)
图谱：NetworkX (内存)
意图：FastText
文档：Unstructured
成本：$0/月
```

#### 2. 初创团队（<$200/月）

```yaml
LLM: Ollama + GPU 云服务器 (~$80)
向量库：Qdrant Cloud (~$50)
图谱：Neo4j Aura Free ($0)
意图：Rasa NLU ($0)
文档：RAGFlow ($0)
总计：~$130/月
```

#### 3. 成长企业（$500-2000/月）

```yaml
LLM: vLLM 自建集群 (~$600)
向量库：Qdrant Cluster (~$300)
图谱：Neo4j Aura Pro (~$400)
意图：Rasa + Redis (~$50)
文档：RAGFlow Cluster (~$100)
云服务备用：OpenAI API (~$500)
总计：~$2100/月
```

#### 4. 大型企业（$5000+/月）

```yaml
LLM: vLLM 多集群 (~$3000)
向量库：Milvus Cluster (~$1000)
图谱：Neo4j Enterprise (~$333)
意图：BERT 微调 (~$200)
文档：RAGFlow+Adobe (~$500)
监控：Datadog (~$500)
云服务备用：多云 (~$2000)
总计：~$7533/月
```

---

## 📈 性能基准汇总

### 整体系统性能

| 指标 | 开发环境 | 生产环境 | 企业环境 |
|-----|---------|---------|---------|
| 端到端延迟 | < 2s | < 1s | < 500ms |
| 并发 QPS | 10-50 | 100-500 | 500-2000 |
| 可用性 | 95% | 99% | 99.9% |
| 数据规模 | < 10 万 | < 1000 万 | > 1 亿 |

### 各组件延迟分布

| 组件 | 开发环境 | 生产环境 | 企业环境 |
|-----|---------|---------|---------|
| LLM 推理 | 120-350ms | 80-200ms | 50-150ms |
| 向量检索 | 5-25ms | 8-25ms | 20-50ms |
| 图谱查询 | 45-120ms | 45-100ms | 95-150ms |
| 意图识别 | < 50ms | < 50ms | < 50ms |

---

## 🔄 迁移策略

### 抽象层设计

所有第三方系统通过**抽象基类**实现即插即用：

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        pass

# 所有 LLM 提供商都实现此接口
class OllamaClient(BaseLLMClient): ...
class OpenAIClient(BaseLLMClient): ...
class ZhipuClient(BaseLLMClient): ...
```

### 迁移示例：Ollama → OpenAI

```python
# 步骤 1: 修改配置文件 (.env)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4-turbo-preview

# 步骤 2: 代码无需修改（自动适配）
from src.core.llm import create_llm_client
client = create_llm_client()  # 返回 OpenAIClient

# 步骤 3: 验证迁移
response = client.generate("Hello")
print(response)
```

---

## 📚 总结

NecoRAG 集成了**23 个第三方系统**,覆盖五层认知架构的所有需求：

✅ **AI 模型层**: 8 个系统（LLM/向量化/重排序/意图/OCR）  
✅ **存储层**: 5 个系统（Redis/Qdrant/Neo4j/MySQL/MinIO）  
✅ **处理层**: 3 个系统（RAGFlow/APScheduler/Celery）  
✅ **监控层**: 3 个系统（Prometheus/Grafana/APM）  
✅ **增强层**: 3 个系统（Elasticsearch/Kibana/RAGFlow）  
✅ **应用层**: 2 个系统（Streamlit/LangGraph）

通过**抽象层设计**和**配置驱动**,实现：
- 🔌 **即插即用**: 修改配置即可切换供应商
- 📊 **性能优异**: 端到端延迟 < 500ms（企业环境）
- 💰 **成本可控**: 从零成本到企业级，4 套方案可选
- 🛡️ **生产就绪**: 完整监控、告警、日志系统

根据您的具体需求、预算和团队情况，选择合适的组合方案即可！

---

<div align="center">

**Let's make AI think like a brain!** 🧠

[NecoRAG Team](https://github.com/NecoRAG)

</div>
