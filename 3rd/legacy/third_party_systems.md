# NecoRAG 第三方系统集成详解

**Third-Party Systems Integration Guide**

版本：v3.2.0-alpha  
更新日期：2026-03-18

---

## 📋 目录

- [概述](#概述)
- [核心依赖系统](#核心依赖系统)
- [AI/ML 模型服务](#aiml 模型服务)
- [数据存储系统](#数据存储系统)
- [文档处理系统](#文档处理系统)
- **NLP 与意图识别](#nlp 与意图识别)
- [任务调度系统](#任务调度系统)
- [监控与运维](#监控与运维)
- [集成架构图](#集成架构图)
- [配置指南](#配置指南)

---

## 🎯 概述

NecoRAG 采用**可插拔架构设计**，支持多种第三方系统的灵活组合。本指南详细说明各第三方系统的：

- **功能定位**：系统在 NecoRAG 中的角色
- **技术选型**：推荐方案与替代方案
- **集成方式**：API 接口与通信协议
- **部署配置**：Docker 部署与参数调优
- **性能指标**：延迟、吞吐量、容量规划

### 第三方系统分类

```
┌─────────────────────────────────────────────────────────┐
│              NecoRAG 第三方系统生态                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🔤 AI 模型层 (6 个系统)                                 │
│     LLM 推理 | 向量化 | 重排序 | 意图识别 | NLP | OCR    │
│                                                         │
│  💾 存储层 (3 个系统)                                    │
│     工作记忆 | 向量数据库 | 图数据库                      │
│                                                         │
│  📄 处理层 (1 个系统)                                    │
│     深度文档解析                                         │
│                                                         │
│  ⚙️ 中间件层 (2 个系统)                                  │
│     任务调度 | 消息队列                                   │
│                                                         │
│  📊 监控层 (2 个系统)                                    │
│     指标采集 | 可视化面板                                │
│                                                         │
│  总计：14+ 第三方系统                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔤 AI/ML 模型服务

### 1. LLM 推理服务

#### 1.1 Ollama（推荐 - 本地部署）

**功能定位**: 提供本地 LLM 推理能力，用于答案生成、假设文档生成、幻觉检测等。

**技术规格**:
- **类型**: 本地 LLM 推理服务器
- **支持模型**: Llama 3、Mistral、Qwen、Baichuan 等
- **通信协议**: HTTP RESTful API
- **性能**: 取决于模型大小和硬件配置

**集成方式**:
```python
# src/core/llm/ollama_client.py
import requests

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama3"):
        self.base_url = base_url
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """生成文本"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "stream": False
            }
        )
        return response.json()["response"]
    
    def embed(self, text: str) -> List[float]:
        """生成嵌入向量"""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            }
        )
        return response.json()["embedding"]
```

**Docker 部署**:
```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=24h
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]  # GPU 加速（可选）

volumes:
  ollama_data:
```

**配置参数** (`config/llm_config.yaml`):
```yaml
ollama:
  enabled: true
  base_url: "http://localhost:11434"
  model: "llama3"  # 默认模型
  models:
    generation: "llama3"      # 生成任务
    embedding: "nomic-embed-text"  # 向量化
    reranking: null           # Ollama 不支持重排序
  
  # 性能调优
  performance:
    num_ctx: 4096            # 上下文窗口
    num_batch: 512           # 批处理大小
    num_gpu: 1               # GPU 数量
    main_gpu: 0              # 主 GPU 索引
  
  # 超时设置
  timeout:
    connect: 10              # 连接超时 (秒)
    read: 120                # 读取超时 (秒)
    total: 300               # 总超时 (秒)
```

**性能基准**:
| 模型 | 显存需求 | 生成速度 | 适用场景 |
|-----|---------|---------|---------|
| Llama 3 8B | 6GB | ~40 tokens/s | 通用对话、简单生成 |
| Llama 3 70B | 40GB | ~15 tokens/s | 复杂推理、高质量生成 |
| Mistral 7B | 5GB | ~45 tokens/s | 快速响应、资源受限 |
| Qwen 7B | 5GB | ~40 tokens/s | 中文优化场景 |

---

#### 1.2 vLLM（高性能 - 生产环境）

**功能定位**: 高吞吐、低延迟的 LLM 推理服务，适合生产环境大规模部署。

**技术优势**:
- **PagedAttention**: 显存利用率提升 4 倍
- **Continuous Batching**: 动态请求批处理
- **Tensor Parallelism**: 多 GPU 并行推理
- **吞吐量**: 比 HuggingFace Transformers 高 24 倍

**Docker 部署**:
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    command: >
      --model meta-llama/Llama-3-70b-Instruct
      --tensor-parallel-size 2
      --max-model-len 8192
      --gpu-memory-utilization 0.95
      --served-model-name necorag-llm
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']
              capabilities: [gpu]
```

**OpenAI 兼容 API**:
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # vLLM 不需要 API key
)

response = client.chat.completions.create(
    model="necorag-llm",
    messages=[
        {"role": "user", "content": "什么是深度学习？"}
    ],
    max_tokens=2048,
    temperature=0.7
)

print(response.choices[0].message.content)
```

---

#### 1.3 云端 LLM（可选 - 简化部署）

**支持的服务商**:

| 服务商 | 模型 | 价格 | 延迟 | 适用场景 |
|-------|------|------|------|---------|
| **OpenAI** | GPT-4/GPT-3.5 | $0.03/1K tokens | ~500ms | 高质量生成、海外部署 |
| **Anthropic** | Claude 3 | $0.025/1K tokens | ~600ms | 长文本、安全性要求高 |
| **智谱 AI** | GLM-4 | ¥0.05/1K tokens | ~300ms | 中文优化、国内部署 |
| **通义千问** | Qwen-Max | ¥0.04/1K tokens | ~350ms | 阿里生态集成 |

**配置示例**:
```yaml
llm:
  provider: openai
  api_key: ${OPENAI_API_KEY}
  model: gpt-4-turbo-preview
  base_url: https://api.openai.com/v1
  rate_limit:
    rpm: 1000  # 每分钟请求数
    tpm: 100000  # 每分钟 token 数
```

---

### 2. BGE-M3 向量化服务

**功能定位**: 将文本转换为高维向量表示，支持语义检索。

**技术特性**:
- **多维度量**: 稠密向量 (1024 维) + 稀疏向量 + 实体三元组
- **多语言**: 支持 100+ 语言
- **长文本**: 原生支持 8192 长度
- **高性能**: GPU 加速下 ~1000 docs/s

**模型信息**:
```python
# src/perception/encoder.py
from FlagEmbedding import BGEM3FlagModel

class BGE_M3_Encoder:
    def __init__(self, model_path="BAAI/bge-m3", device="cuda"):
        self.model = BGEM3FlagModel(model_path, use_fp16=True)
        self.device = device
    
    def encode(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """
        生成三种向量表示
        
        Returns:
            {
                'dense': np.ndarray,      # [batch_size, 1024]
                'sparse': np.ndarray,     # [batch_size, vocab_size]
                'colbert_vecs': List      # Colbert 风格向量
            }
        """
        result = self.model.encode(
            texts,
            batch_size=16,
            max_length=8192,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True
        )
        return result
```

**Docker 部署**:
```yaml
services:
  bge-m3:
    image: xhluca/bge-m3:latest
    container_name: bge-m3
    ports:
      - "8001:8000"
    volumes:
      - ./models:/app/models
    environment:
      - MODEL_NAME=BAAI/bge-m3
      - DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**RESTful API 调用**:
```bash
# 向量化 API
curl -X POST http://localhost:8001/encode \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["深度学习是机器学习的一个分支"],
    "return_dense": true,
    "return_sparse": true
  }'

# 响应
{
  "dense_embedding": [0.023, -0.045, ...],  # 1024 维
  "lexical_weights": {"深度": 0.85, "学习": 0.72, ...}
}
```

**性能优化配置**:
```yaml
embedding:
  model: BAAI/bge-m3
  device: cuda  # cpu/cuda/mps
  fp16: true    # 半精度推理，速度提升 2 倍
  
  # 批处理优化
  batching:
    enabled: true
    max_batch_size: 32
    dynamic_batching: true
  
  # 缓存策略
  cache:
    enabled: true
    backend: redis  # redis/memory
    ttl: 86400      # 24 小时缓存
    max_size: 10000 # 最大缓存条目
```

---

### 3. BGE-Reranker-v2 重排序服务

**功能定位**: 对检索结果进行精排序，提升最终相关性。

**技术特性**:
- **Cross-Encoder 架构**: 查询 - 文档联合编码
- **高精度**: 在 C-MTEB 榜单排名第一
- **多语言**: 中英双语优化
- **输入长度**: 支持 512/1024 token

**集成代码**:
```python
# src/retrieval/reranker.py
from FlagEmbedding import FlagReranker

class BGE_Reranker:
    def __init__(self, model_path="BAAI/bge-reranker-v2-m3"):
        self.reranker = FlagReranker(model_path, use_fp16=True)
    
    def rerank(self, query: str, passages: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        重排序
        
        Args:
            query: 查询文本
            passages: 候选段落列表
            top_k: 返回数量
            
        Returns:
            [(passage_1, score_1), (passage_2, score_2), ...]
        """
        # 构建配对
        pairs = [[query, passage] for passage in passages]
        
        # 计算分数
        scores = self.reranker.compute_score(pairs)
        
        # 排序并返回 Top-K
        ranked = sorted(zip(passages, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
```

**Docker 部署**:
```yaml
services:
  reranker:
    image: flagembedding/bge-reranker:latest
    container_name: bge-reranker
    ports:
      - "8002:8000"
    volumes:
      - ./models:/app/models
    environment:
      - MODEL_NAME=BAAI/bge-reranker-v2-m3
      - DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**API 调用示例**:
```bash
curl -X POST http://localhost:8002/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "深度学习的原理",
    "passages": [
      "深度学习使用神经网络...",
      "机器学习包括监督学习...",
      "卷积神经网络应用于图像..."
    ],
    "top_k": 2
  }'

# 响应
{
  "results": [
    {"passage": "深度学习使用神经网络...", "score": 0.92},
    {"passage": "卷积神经网络应用于图像...", "score": 0.87}
  ]
}
```

---

### 4. Rasa NLU 意图识别

**功能定位**: 用户查询意图分类与实体提取。

**技术特性**:
- **轻量级**: 无需 GPU，CPU 即可高效运行
- **可训练**: 支持自定义领域数据微调
- **多意图**: 支持复合意图识别
- **实体抽取**: 内置命名实体识别

**模型训练**:
```yaml
# intent/config.yml
language: zh

pipeline:
  - name: JiebaTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: DIETClassifier
    epochs: 100
    constrain_similarities: true
  - name: EntitySynonymMapper

intents:
  - factual_query       # 事实查询
  - comparative_analysis # 比较分析
  - reasoning_inference  # 推理演绎
  - concept_explanation  # 概念解释
  - summarization        # 摘要总结
  - procedural_howto     # 操作指导
  - exploratory          # 探索发散

entities:
  - technology
  - product
  - person
  - organization
  - date
  - version
```

**训练数据示例** (`data/nlu.yml`):
```yaml
version: "3.1"

nlu:
- intent: factual_query
  examples: |
    - Python 3.12 发布了什么新特性？
    - Redis 的持久化机制有哪些？
    - Transformer 架构是哪年提出的？

- intent: comparative_analysis
  examples: |
    - Redis 和 Memcached 有什么区别？
    - PyTorch 和 TensorFlow 哪个更好用？
    - MySQL 和 PostgreSQL 对比一下

- intent: reasoning_inference
  examples: |
    - 为什么微服务架构更适合大规模系统？
    - 深度学习为什么需要大量数据？
    - 量子计算会对密码学产生什么影响？
```

**Docker 部署**:
```yaml
services:
  rasa:
    image: rasa/rasa:latest
    container_name: rasa-nlu
    ports:
      - "5005:5005"
    volumes:
      - ./intent:/app/intent
      - ./models/rasa:/app/models
    command: run --enable-api --cors "*"
    environment:
      - PYTHONPATH=/app
```

**集成调用**:
```python
# src/intent/classifier.py
import requests

class RasaIntentClassifier:
    def __init__(self, endpoint="http://localhost:5005/model/parse"):
        self.endpoint = endpoint
    
    def classify(self, text: str) -> IntentResult:
        """
        意图分类
        
        Returns:
            IntentResult {
                primary_intent: IntentType,
                confidence: float,
                entities: List[Entity],
                secondary_intents: List[IntentWithConfidence]
            }
        """
        response = requests.post(
            self.endpoint,
            json={"text": text}
        )
        data = response.json()
        
        return IntentResult(
            primary_intent=self._map_intent(data['intent']['name']),
            confidence=data['intent']['confidence'],
            entities=data.get('entities', []),
            secondary_intents=[
                {"intent": i['name'], "confidence": i['confidence']}
                for i in data.get('intent_ranking', [])[1:]
            ]
        )
```

---

### 5. spaCy + jieba 中文 NLP

**功能定位**: 中文分词、词性标注、命名实体识别。

**技术栈组合**:
- **spaCy**: 工业级 NLP 流水线
- **jieba**: 中文分词优化
- **spacy-pkuseg**: 北大中文分词扩展

**集成代码**:
```python
# src/perception/tagger.py
import spacy
import jieba
from spacy.zh import LanguageZh

class ChineseNLPProcessor:
    def __init__(self):
        # 加载中文模型
        self.nlp = spacy.load("zh_core_web_sm")
        
        # 自定义分词器
        self.nlp.tokenizer = jieba_spacy_tokenizer
        
        # 添加自定义实体识别
        self._setup_entity_recognition()
    
    def process(self, text: str) -> ProcessedDocument:
        """
        NLP 处理流水线
        
        处理步骤:
        1. 分词
        2. 词性标注
        3. 命名实体识别
        4. 依存句法分析
        5. 关键词提取
        """
        doc = self.nlp(text)
        
        return ProcessedDocument(
            tokens=[token.text for token in doc],
            pos_tags=[(token.text, token.pos_) for token in doc],
            entities=[(ent.text, ent.label_) for ent in doc.ents],
            noun_chunks=[chunk.text for chunk in doc.noun_chunks],
            keywords=self._extract_keywords(doc)
        )
    
    def _extract_keywords(self, doc) -> List[str]:
        """基于 TF-IDF 和 TextRank 提取关键词"""
        # 实现略
        pass

def jieba_spacy_tokenizer(nlp):
    """jieba 与 spaCy 集成"""
    def tokenize(text):
        words = jieba.cut(text)
        # 转换为 spaCy 格式
        return spacy.tokens.Doc(nlp.vocab, words=list(words))
    return tokenize
```

**依赖安装**:
```bash
pip install spacy jieba spacy-pkuseg
python -m spacy download zh_core_web_sm
```

---

### 6. OCR 服务（可选）

**功能定位**: 从图片、PDF 中提取文字。

**推荐方案**:

#### 6.1 PaddleOCR（推荐 - 中文优化）

**Docker 部署**:
```yaml
services:
  paddleocr:
    image: paddlepaddle/paddleocr:latest
    container_name: paddleocr
    ports:
      - "8003:8866"
    volumes:
      - ./uploads:/app/uploads
    environment:
      - LANG=ch
      - DET=true
      - REC=true
      - TYPE=ocr
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**API 调用**:
```python
import requests
import base64

class PaddleOCRClient:
    def __init__(self, endpoint="http://localhost:8003/ocr"):
        self.endpoint = endpoint
    
    def recognize(self, image_path: str) -> List[OCRResult]:
        """
        OCR 文字识别
        
        Returns:
            [
                {
                    "text": "识别的文字内容",
                    "confidence": 0.95,
                    "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                },
                ...
            ]
        """
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = requests.post(
            self.endpoint,
            json={"images": [image_data]}
        )
        
        return response.json()["results"][0]
```

**性能指标**:
- **中文识别准确率**: 96%+
- **处理速度**: ~100ms/张 (GPU)
- **支持语言**: 中/英/日/韩等 80+ 语言

---

## 💾 数据存储系统

### 1. Redis - L1 工作记忆

**功能定位**: 高速缓存与会话上下文存储。

**技术特性**:
- **超低延迟**: < 1ms 读写
- **数据结构丰富**: String, Hash, List, Set, Sorted Set
- **TTL 自动过期**: 模拟工作记忆遗忘
- **持久化选项**: RDB/AOF

**Docker 部署**:
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: redis-memory
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    deploy:
      resources:
        limits:
          memory: 2G

volumes:
  redis_data:
```

**Redis 配置** (`redis.conf`):
```conf
# 内存管理
maxmemory 2gb
maxmemory-policy allkeys-lru  # LRU 淘汰策略

# 持久化
appendonly yes
appendfsync everysec

# 网络
bind 0.0.0.0
protected-mode no

# 日志
loglevel notice

# 客户端
timeout 300
tcp-keepalive 60
```

**NecoRAG 集成**:
```python
# src/memory/backends/redis_backend.py
import redis
from typing import Optional, Any, Dict

class RedisWorkingMemory:
    def __init__(self, host="localhost", port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.default_ttl = 3600  # 1 小时 TTL
    
    def store(self, key: str, value: Any, ttl: Optional[int] = None):
        """存储到工作记忆"""
        ttl = ttl or self.default_ttl
        self.redis.setex(key, ttl, json.dumps(value))
    
    def retrieve(self, key: str) -> Optional[Any]:
        """从工作记忆检索"""
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def get_session_context(self, session_id: str) -> Dict:
        """获取会话上下文"""
        pattern = f"session:{session_id}:*"
        keys = self.redis.keys(pattern)
        
        context = {}
        for key in keys:
            context[key] = self.retrieve(key)
        
        return context
    
    def refresh(self, key: str):
        """刷新 TTL（访问时续期）"""
        ttl = self.redis.ttl(key)
        if ttl > 0:
            self.redis.expire(key, ttl)
```

**数据结构设计**:
```
# Key 命名规范
session:{session_id}:query:{query_id}     # 查询历史
session:{session_id}:context              # 会话上下文
working:hot:{entity_id}                   # 热点实体
working:recent:{user_id}                  # 最近访问
```

**性能监控**:
```bash
# 查看内存使用
redis-cli INFO memory

# 查看命中率
redis-cli INFO stats | grep keyspace

# 慢查询日志
redis-cli --latency-history
```

---

### 2. Qdrant - L2 语义记忆

**功能定位**: 高维向量相似度检索。

**技术特性**:
- **HNSW 索引**: 近似最近邻搜索
- **过滤查询**: 向量 + 元数据混合查询
- **分布式**: 支持集群部署
- **持久化**: WAL 日志保证数据安全

**Docker 部署**:
```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-vector-db
    ports:
      - "6333:6333"   # REST API
      - "6334:6334"   # gRPC
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 8G

volumes:
  qdrant_storage:
```

**NecoRAG 集成**:
```python
# src/memory/backends/qdrant_backend.py
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
)

class QdrantSemanticMemory:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "semantic_memory"
        
        # 初始化集合
        self._init_collection()
    
    def _init_collection(self):
        """创建向量集合"""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1024,          # BGE-M3 向量维度
                    distance=Distance.COSINE
                ),
                hnsw_config={
                    "m": 16,            # 连接数
                    "ef_construct": 100 # 构建精度
                }
            )
    
    def store(self, chunk_id: str, vector: np.ndarray, metadata: Dict):
        """存储向量"""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=hash(chunk_id) % (2**63),
                    vector=vector.tolist(),
                    payload=metadata
                )
            ]
        )
    
    def retrieve(self, query_vector: np.ndarray, top_k: int = 10, 
                 filter_conditions: Optional[Dict] = None) -> List[RetrievalResult]:
        """向量检索"""
        query_filter = self._build_filter(filter_conditions) if filter_conditions else None
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            query_filter=query_filter,
            limit=top_k
        )
        
        return [
            RetrievalResult(
                memory_id=str(r.id),
                content=r.payload["content"],
                score=r.score,
                source=r.payload.get("source", "unknown")
            )
            for r in results
        ]
    
    def hybrid_search(self, query_vector: np.ndarray, keyword_filter: Dict) -> List:
        """向量 + 关键词混合搜索"""
        # 实现 BGE-M3 的稀疏向量检索
        pass
```

**性能调优配置**:
```yaml
qdrant:
  # 连接配置
  host: localhost
  port: 6333
  grpc_port: 6334
  
  # 集合配置
  collection:
    name: semantic_memory
    vector_size: 1024
    distance: cosine
    
  # HNSW 索引优化
  hnsw:
    m: 16              # 连接数 (4-64, 越大越精确但越慢)
    ef_construct: 100  # 构建时候选集大小
    full_scan_threshold: 10000
  
  # 查询优化
  search:
    exact_threshold: 1000  # 小数据集使用精确搜索
    quantization: scalar   # 标量量化，减少内存
  
  # 批量操作
  batch:
    size: 256
    parallel: 4
```

**集群部署** (生产环境):
```yaml
version: '3.8'

services:
  qdrant-node-1:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
    ports:
      - "6333:6333"
      - "6335:6335"
    volumes:
      - ./qdrant/node1:/qdrant/storage
  
  qdrant-node-2:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
    depends_on:
      - qdrant-node-1
  
  qdrant-node-3:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__P2P__PORT=6335
    depends_on:
      - qdrant-node-2
```

---

### 3. Neo4j - L3 情景图谱

**功能定位**: 知识图谱存储与多跳推理。

**技术特性**:
- **属性图模型**: 节点 + 关系 + 属性
- **Cypher 查询语言**: 声明式图查询
- **多跳遍历**: 高效的图遍历算法
- **图算法库**: PageRank、社区发现等

**Docker 部署**:
```yaml
services:
  neo4j:
    image: neo4j:5-community
    container_name: neo4j-graph-db
    ports:
      - "7687:7687"  # Bolt 协议
      - "7474:7474"  # Browser UI
    environment:
      - NEO4J_AUTH=neo4j/necorag_password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=2G
      - NEO4J_dbms_memory_heap_max__size=4G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    deploy:
      resources:
        limits:
          memory: 4G

volumes:
  neo4j_data:
  neo4j_logs:
```

**Neo4j 配置** (`neo4j.conf`):
```conf
# 内存配置
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# 网络配置
server.default_listen_address=0.0.0.0

# 插件配置
dbms.security.auth_enabled=true
dbms.plugins=apoc

# 日志
dbms.logs.http.enabled=true
dbms.logs.query.enabled=true
```

**NecoRAG 集成**:
```python
# src/memory/episodic_graph.py
from neo4j import GraphDatabase

class EpisodicGraph:
    def __init__(self, uri="bolt://localhost:7687", 
                 user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_schema()
    
    def _init_schema(self):
        """初始化图谱索引"""
        with self.driver.session() as session:
            # 创建实体索引
            session.run("CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.id)")
            session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
            
            # 创建关系类型索引
            session.run("CREATE INDEX rel_type IF NOT EXISTS FOR ()-[r:RELATIONSHIP]-() ON (r.type)")
    
    def add_entity(self, entity_id: str, entity_type: str, properties: Dict):
        """添加实体节点"""
        with self.driver.session() as session:
            session.run("""
                MERGE (e:Entity {id: $id})
                SET e.type = $type,
                    e.name = $properties.name,
                    e.created_at = datetime()
                SET e += $properties
            """, id=entity_id, type=entity_type, properties=properties)
    
    def add_relationship(self, source_id: str, target_id: str, 
                        rel_type: str, properties: Dict = None):
        """添加关系边"""
        with self.driver.session() as session:
            session.run("""
                MATCH (source:Entity {id: $source_id})
                MATCH (target:Entity {id: $target_id})
                MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
                SET r += $properties
            """, source_id=source_id, target_id=target_id, 
                rel_type=rel_type, properties=properties or {})
    
    def multi_hop_retrieve(self, start_entity: str, hops: int = 2, 
                          relationship_types: List[str] = None) -> List[GraphPath]:
        """
        多跳检索
        
        Args:
            start_entity: 起始实体 ID
            hops: 跳跃次数
            relationship_types: 关系类型过滤
            
        Returns:
            路径列表，每条路径包含实体序列和关系序列
        """
        with self.driver.session() as session:
            rel_filter = f":{'|'.join(relationship_types)}" if relationship_types else ""
            
            query = f"""
                MATCH path = (start:Entity {{id: $start_id}})-[{rel_filter}*..{hops}]-(end)
                RETURN path
                ORDER BY length(path) DESC
                LIMIT 50
            """
            
            result = session.run(query, start_id=start_entity)
            
            paths = []
            for record in result:
                path = record["path"]
                paths.append(self._parse_path(path))
            
            return paths
    
    def _parse_path(self, path) -> GraphPath:
        """解析 Cypher 路径结果为 Python 对象"""
        nodes = list(path.nodes)
        relationships = list(path.relationships)
        
        return GraphPath(
            entities=[dict(n) for n in nodes],
            relationships=[dict(r) for r in relationships]
        )
```

**图谱模式设计**:
```cypher
// 实体类型
(:Entity {
    id: String,           // 唯一标识
    type: String,         // 实体类型：Concept/Person/Organization/Event
    name: String,         // 显示名称
    description: String,  // 描述
    created_at: DateTime, // 创建时间
    updated_at: DateTime, // 更新时间
    weight: Float         // 权重分数
})

// 关系类型
(:Entity)-[:RELATIONSHIP {
    type: String,         // 关系类型：is_a/part_of/caused_by/related_to
    strength: Float,      // 关系强度 0-1
    frequency: Integer,   // 共现频率
    last_accessed: DateTime
}]->(:Entity)

// 索引优化
CREATE INDEX FOR (e:Entity) ON (e.type)
CREATE INDEX FOR ()-[r:RELATIONSHIP]-() ON (r.type)
```

**性能优化**:
```yaml
neo4j:
  # 连接池
  connection_pool:
    max_size: 50
    min_idle: 10
    max_lifetime: 3600
  
  # 查询优化
  query:
    plan_cache: true
    runtime: interpreted  # pipelined/interpreted
    timeout: 30          # 查询超时 (秒)
  
  # 缓存策略
  cache:
    node_cache: true
    relationship_cache: true
    query_plan_cache: true
```

---

## 📄 文档处理系统

### RAGFlow 深度文档解析

**功能定位**: 多格式文档的深度解析与结构化提取。

**技术特性**:
- **多格式支持**: PDF/Word/Excel/PPT/Markdown/HTML
- **OCR 集成**: 扫描件文字识别
- **表格还原**: 复杂表格结构提取
- **层级分析**: 标题 - 段落 - 列表层级关系
- **公式识别**: LaTeX 公式提取

**Docker 部署**:
```yaml
services:
  ragflow:
    image: infiniflow/ragflow:latest
    container_name: ragflow-parser
    ports:
      - "9380:9380"
    volumes:
      - ./ragflow_data:/var/lib/ragflow
      - ./uploads:/app/uploads
    environment:
      - RAGFLOW_HOST=0.0.0.0
      - RAGFLOW_PORT=9380
      - MYSQL_URL=mysql://root:password@mysql:3306/ragflow
      - MINIO_URL=http://minio:9000
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mysql
      - minio
      - redis
  
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ragflow
    volumes:
      - mysql_data:/var/lib/mysql
  
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  ragflow_data:
  mysql_data:
  minio_data:
```

**API 集成**:
```python
# src/perception/parser.py
import requests
from typing import List, Dict

class RAGFlowParser:
    def __init__(self, endpoint="http://localhost:9380/api/v1"):
        self.endpoint = endpoint
        self.api_key = "your_api_key"
    
    def parse_document(self, file_path: str) -> ParsedDocument:
        """
        解析文档
        
        Returns:
            ParsedDocument {
                sections: List[Section],
                tables: List[Table],
                images: List[Image],
                metadata: DocumentMetadata
            }
        """
        # 1. 上传文件
        upload_response = self._upload_file(file_path)
        document_id = upload_response["document_id"]
        
        # 2. 触发解析
        parse_response = self._trigger_parsing(document_id)
        
        # 3. 等待解析完成
        status = self._wait_for_completion(document_id)
        
        # 4. 获取解析结果
        result = self._get_parsed_result(document_id)
        
        return result
    
    def _upload_file(self, file_path: str) -> Dict:
        """上传文件到 RAGFlow"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.endpoint}/documents/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return response.json()
    
    def _trigger_parsing(self, document_id: str) -> Dict:
        """触发解析任务"""
        response = requests.post(
            f"{self.endpoint}/documents/{document_id}/parse",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def _wait_for_completion(self, document_id: str, timeout: int = 300) -> bool:
        """等待解析完成"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_response = requests.get(
                f"{self.endpoint}/documents/{document_id}/status",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            status = status_response.json()["status"]
            
            if status == "SUCCESS":
                return True
            elif status in ["FAILED", "TIMEOUT"]:
                return False
            
            time.sleep(2)
        
        return False
    
    def _get_parsed_result(self, document_id: str) -> ParsedDocument:
        """获取解析结果"""
        response = requests.get(
            f"{self.endpoint}/documents/{document_id}/parsed_content",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        data = response.json()
        
        return ParsedDocument.from_dict(data)
```

**解析结果示例**:
```python
@dataclass
class ParsedDocument:
    """解析后的文档结构"""
    sections: List[Section]
    tables: List[Table]
    images: List[Image]
    metadata: DocumentMetadata

@dataclass
class Section:
    """文档章节"""
    title: str              # 章节标题
    level: int              # 层级 (1=一级标题，2=二级标题...)
    content: str            # 正文内容
    page_number: int        # 页码
    bounding_box: Box       # 位置信息
    
@dataclass
class Table:
    """表格"""
    caption: str            # 表格标题
    headers: List[str]      # 表头
    rows: List[List[str]]   # 数据行
    page_number: int        # 所在页
    markdown: str           # Markdown 表示

@dataclass
class Image:
    """图片"""
    caption: str            # 图片说明
    ocr_text: str           # OCR 识别文字
    format: str             # 图片格式
    path: str               # 存储路径
```

**性能指标**:
- **PDF 解析速度**: 10-20 页/秒
- **表格识别准确率**: 92%+
- **OCR 识别准确率**: 96%+ (中文)
- **并发处理**: 支持 10+ 文档并行解析

---

## ⚙️ 任务调度系统

### APScheduler 定时任务

**功能定位**: 周期性任务调度（知识更新、记忆清理等）。

**技术特性**:
- **多种触发器**: Cron、Interval、Date
- **持久化**: 支持数据库存储任务状态
- **分布式**: 支持多节点任务协调
- **错误重试**: 失败任务自动重试

**集成代码**:
```python
# src/knowledge_evolution/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging

class KnowledgeUpdateScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            job_defaults={
                'coalesce': False,      # 不合并执行
                'max_instances': 1,     # 单实例执行
                'misfire_grace_time': 60  # 错过执行的容忍时间
            }
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_default_tasks(self):
        """设置默认调度任务"""
        
        # 任务 1: 每日凌晨 3 点执行批量知识更新
        self.scheduler.add_job(
            func=self.batch_update_knowledge,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_batch_update',
            name='每日批量知识更新',
            replace_existing=True
        )
        
        # 任务 2: 每 6 小时执行记忆衰减计算
        self.scheduler.add_job(
            func=self.calculate_memory_decay,
            trigger=IntervalTrigger(hours=6),
            id='memory_decay_calculation',
            name='记忆衰减计算',
            replace_existing=True
        )
        
        # 任务 3: 每小时执行热点知识归档
        self.scheduler.add_job(
            func=self.archive_hot_knowledge,
            trigger=IntervalTrigger(hours=1),
            id='hourly_archive',
            name='每小时归档',
            replace_existing=True
        )
        
        # 任务 4: 每周日凌晨 2 点执行图谱维护
        self.scheduler.add_job(
            func=self.maintain_knowledge_graph,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_graph_maintenance',
            name='每周图谱维护',
            replace_existing=True
        )
    
    def batch_update_knowledge(self):
        """批量知识更新任务"""
        self.logger.info("Starting batch knowledge update...")
        # 实现逻辑
        pass
    
    def calculate_memory_decay(self):
        """记忆衰减计算"""
        self.logger.info("Calculating memory decay...")
        # 实现逻辑
        pass
    
    def start(self):
        """启动调度器"""
        self.scheduler.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown(wait=True)
        self.logger.info("Scheduler stopped")
```

**任务监控**:
```python
# 查看任务状态
for job in scheduler.get_jobs():
    print(f"Job: {job.name}")
    print(f"Next run: {job.next_run_time}")
    print(f"Trigger: {job.trigger}")
```

---

### Celery 分布式任务队列（可选 - 大规模部署）

**功能定位**: 异步任务处理与分布式任务队列。

**Docker 部署**:
```yaml
services:
  celery-worker:
    build: .
    command: celery -A src.tasks worker --loglevel=info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    volumes:
      - .:/app
    depends_on:
      - redis
  
  celery-beat:
    build: .
    command: celery -A src.tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      - redis
```

**任务定义**:
```python
# src/tasks.py
from celery import Celery
from celery.schedules import crontab

app = Celery('necorag', broker='redis://localhost:6379/0')

# 定时任务配置
app.conf.beat_schedule = {
    'daily-knowledge-update': {
        'task': 'src.tasks.batch_update_knowledge',
        'schedule': crontab(hour=3, minute=0),
    },
    'hourly-memory-cleanup': {
        'task': 'src.tasks.cleanup_memory',
        'schedule': crontab(minute=0),  # 每小时
    },
}

@app.task(bind=True, max_retries=3)
def batch_update_knowledge(self):
    """批量知识更新任务"""
    try:
        # 业务逻辑
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)  # 5 分钟后重试

@app.task
def cleanup_memory():
    """记忆清理任务"""
    pass
```

---

## 📊 监控与运维

### Prometheus 指标采集

**功能定位**: 系统性能指标采集与存储。

**Docker 部署**:
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'

volumes:
  prometheus_data:
```

**配置文件** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'necorag'
    static_configs:
      - targets: ['necorag-app:8000']
    metrics_path: '/metrics'
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
  
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j-exporter:9122']
```

**NecoRAG 指标暴露**:
```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# 指标定义
QUERY_COUNTER = Counter(
    'necorag_queries_total',
    'Total number of queries processed'
)

QUERY_LATENCY = Histogram(
    'necorag_query_latency_seconds',
    'Query processing latency',
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

MEMORY_USAGE = Gauge(
    'necorag_memory_usage_bytes',
    'Current memory usage'
)

RETRIEVAL_ACCURACY = Gauge(
    'necorag_retrieval_accuracy',
    'Retrieval accuracy metric'
)

# FastAPI 集成
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()

@app.middleware("http")
async def track_metrics(request, call_next):
    if request.url.path == "/query":
        start_time = time.time()
        QUERY_COUNTER.inc()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        QUERY_LATENCY.observe(duration)
        
        return response
    
    return await call_next(request)

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

---

### Grafana 可视化面板

**功能定位**: 监控数据可视化展示。

**Docker 部署**:
```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: grafana-dashboard
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    depends_on:
      - prometheus

volumes:
  grafana_data:
```

**Dashboard 配置**:
```json
{
  "dashboard": {
    "title": "NecoRAG System Monitor",
    "panels": [
      {
        "title": "Query Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(necorag_queries_total[1m])",
            "legendFormat": "Queries/sec"
          }
        ]
      },
      {
        "title": "Query Latency Percentile",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(necorag_query_latency_seconds_bucket[5m]))",
            "legendFormat": "P95 Latency"
          },
          {
            "expr": "histogram_quantile(0.50, rate(necorag_query_latency_seconds_bucket[5m]))",
            "legendFormat": "P50 Latency"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "necorag_memory_usage_bytes",
            "legendFormat": "Memory (bytes)"
          }
        ]
      },
      {
        "title": "Retrieval Accuracy",
        "type": "stat",
        "targets": [
          {
            "expr": "necorag_retrieval_accuracy",
            "legendFormat": "Accuracy"
          }
        ]
      }
    ]
  }
}
```

---

## 🏗️ 集成架构图

### 完整第三方系统集成视图

```mermaid
graph TB
    subgraph "用户接入层"
        USER[用户/客户端]
        NGINX[Nginx 负载均衡]
    end
    
    subgraph "应用服务层"
        FASTAPI[FastAPI :8000<br/>NecoRAG Core]
        WORKER[Celery Worker<br/>异步任务]
        SCHED[APScheduler<br/>定时调度]
    end
    
    subgraph "AI 模型服务层"
        OLLAMA[Ollama :11434<br/>LLM 推理]
        BGE_M3[BGE-M3 :8001<br/>向量化]
        RERANK[BGE-Reranker :8002<br/>重排序]
        RASA[Rasa :5005<br/>意图识别]
        PADDLE[PaddleOCR :8003<br/>文字识别]
    end
    
    subgraph "数据处理层"
        RAGFLOW[RAGFlow :9380<br/>文档解析]
        SPACY[spaCy<br/>NLP 处理]
        JIEBA[jieba<br/>中文分词]
    end
    
    subgraph "数据存储层"
        REDIS[Redis :6379<br/>L1 工作记忆]
        QDRANT[Qdrant :6333<br/>L2 语义记忆]
        NEO4J[Neo4j :7687<br/>L3 情景图谱]
        MYSQL[MySQL :3306<br/>元数据存储]
        MINIO[MinIO :9000<br/>文件存储]
    end
    
    subgraph "监控运维层"
        PROM[Prometheus :9090<br/>指标采集]
        GRAFANA[Grafana :3000<br/>可视化]
    end
    
    USER --> NGINX
    NGINX --> FASTAPI
    FASTAPI --> WORKER & SCHED
    
    FASTAPI --> OLLAMA & BGE_M3 & RERANK & RASA
    FASTAPI --> RAGFLOW & SPACY & JIEBA
    FASTAPI --> REDIS & QDRANT & NEO4J & MYSQL
    FASTAPI --> MINIO
    
    PROM --> FASTAPI & REDIS & QDRANT & NEO4J
    GRAFANA --> PROM
    
    style FASTAPI fill:#ffcc80,stroke:#e65100,stroke-width:3px
    style REDIS fill:#ffe0b2
    style QDRANT fill:#f8bbd9
    style NEO4J fill:#ce93d8
```

---

## ⚙️ 配置指南

### 统一配置文件

**环境变量配置** (`.env`):
```bash
# ==================== LLM 配置 ====================
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# OpenAI (可选)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxx
# OPENAI_MODEL=gpt-4-turbo-preview

# ==================== 向量模型配置 ====================
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=16

# ==================== 重排序模型配置 ====================
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=cuda

# ==================== 存储配置 ====================
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=3600

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=semantic_memory

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=necorag_password

# MySQL (RAGFlow 依赖)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# ==================== 意图识别配置 ====================
INTENT_PROVIDER=rasa
RASA_ENDPOINT=http://localhost:5005/model/parse

# ==================== 文档解析配置 ====================
RAGFLOW_ENDPOINT=http://localhost:9380/api/v1
RAGFLOW_API_KEY=your_api_key

# ==================== OCR 配置 ====================
OCR_ENABLED=true
OCR_PROVIDER=paddleocr
PADDLEOCR_ENDPOINT=http://localhost:8003/ocr

# ==================== 任务调度配置 ====================
SCHEDULER_TYPE=apscheduler
CELERY_BROKER=redis://localhost:6379/0
CELERY_BACKEND=redis://localhost:6379/1

# ==================== 监控配置 ====================
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
GRAFANA_URL=http://localhost:3000

# ==================== 性能调优配置 ====================
MAX_CONCURRENT_QUERIES=100
QUERY_TIMEOUT=30
EMBEDDING_CACHE_SIZE=10000
RERANK_TOP_K=5
```

### Docker Compose 一键启动

**完整开发环境** (`docker-compose.dev.yml`):
```yaml
version: '3.8'

services:
  # NecoRAG 核心服务
  necorag:
    build: .
    container_name: necorag-core
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - .:/app
      - ./logs:/app/logs
    depends_on:
      - redis
      - qdrant
      - neo4j
      - ollama
      - bge-m3
      - reranker
      - rasa
      - ragflow
  
  # AI 模型服务
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  bge-m3:
    image: xhluca/bge-m3:latest
    ports:
      - "8001:8000"
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  reranker:
    image: flagembedding/bge-reranker:latest
    ports:
      - "8002:8000"
    volumes:
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  rasa:
    image: rasa/rasa:latest
    ports:
      - "5005:5005"
    volumes:
      - ./intent:/app/intent
      - ./models/rasa:/app/models
    command: run --enable-api --cors "*"
  
  # 文档处理
  ragflow:
    image: infiniflow/ragflow:latest
    ports:
      - "9380:9380"
    volumes:
      - ./ragflow_data:/var/lib/ragflow
    environment:
      - MYSQL_URL=mysql://root:password@mysql:3306/ragflow
      - MINIO_URL=http://minio:9000
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mysql
      - minio
      - redis
  
  # 存储服务
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 2gb
    volumes:
      - redis_data:/data
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
  
  neo4j:
    image: neo4j:5-community
    ports:
      - "7687:7687"
      - "7474:7474"
    environment:
      - NEO4J_AUTH=neo4j/necorag_password
    volumes:
      - neo4j_data:/data
  
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ragflow
    volumes:
      - mysql_data:/var/lib/mysql
  
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
  
  # 监控
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus

volumes:
  ollama_data:
  redis_data:
  qdrant_storage:
  neo4j_data:
  mysql_data:
  minio_data:
  prometheus_data:
  grafana_data:
  ragflow_data:
```

---

## 📊 性能基准与资源规划

### 最小资源配置（开发测试）

| 组件 | CPU | 内存 | GPU | 磁盘 |
|-----|-----|------|-----|------|
| NecoRAG Core | 2 核 | 4GB | - | 10GB |
| Ollama (Llama 3 8B) | 4 核 | 8GB | 可选 | 20GB |
| Redis | 1 核 | 2GB | - | 5GB |
| Qdrant | 2 核 | 4GB | - | 20GB |
| Neo4j | 2 核 | 4GB | - | 10GB |
| **总计** | **11 核** | **22GB** | **0-1** | **65GB** |

### 生产环境配置（1000 QPS）

| 组件 | CPU | 内存 | GPU | 磁盘 | 副本数 |
|-----|-----|------|-----|------|--------|
| NecoRAG Core | 8 核 | 16GB | - | 50GB | 3 |
| Ollama (70B) | 16 核 | 64GB | A100×2 | 200GB | 2 |
| BGE-M3 | 4 核 | 8GB | A10×1 | 50GB | 2 |
| Redis Cluster | 8 核 | 32GB | - | 100GB | 3 |
| Qdrant Cluster | 16 核 | 64GB | - | 500GB | 3 |
| Neo4j Cluster | 16 核 | 64GB | - | 200GB | 3 |
| **总计** | **~200 核** | **~600GB** | **6GPU** | **~2TB** | **-** |

---

## 🔧 故障排查指南

### 常见问题与解决方案

#### 1. Ollama 连接超时

**症状**: `Connection refused` 或 `Timeout error`

**排查步骤**:
```bash
# 1. 检查容器状态
docker ps | grep ollama

# 2. 查看日志
docker logs ollama

# 3. 测试端口连通性
nc -zv localhost 11434

# 4. 检查模型是否加载
curl http://localhost:11434/api/tags
```

**解决方案**:
```bash
# 重启 Ollama
docker restart ollama

# 重新拉取模型
docker exec -it ollama ollama pull llama3
```

---

#### 2. Qdrant 向量检索慢

**症状**: 检索延迟 > 100ms

**排查步骤**:
```bash
# 查看集合统计
curl http://localhost:6333/collections/semantic_memory

# 检查 HNSW 索引状态
curl http://localhost:6333/collections/semantic_memory/index
```

**优化方案**:
```yaml
# 调整 HNSW 参数
hnsw_config:
  m: 8              # 减小连接数，提升速度
  ef_construct: 50  # 降低构建精度
  
# 启用标量量化
quantization_config:
  scalar:
    type: int8
    quantile: 0.99
```

---

#### 3. Neo4j 内存溢出

**症状**: `OutOfMemoryError`

**解决方案**:
```conf
# 调整 neo4j.conf
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=4G

# 限制查询复杂度
dbms.security.procedures.unrestricted=apoc.*
dbms.transaction.timeout=60
```

---

## 📚 总结

本文档详细介绍了 NecoRAG 集成的 **14+ 第三方系统**，涵盖：

✅ **AI 模型层** (6 个): LLM 推理、向量化、重排序、意图识别、NLP 处理、OCR  
✅ **数据存储层** (3 个): Redis、Qdrant、Neo4j  
✅ **文档处理层** (1 个): RAGFlow  
✅ **中间件层** (2 个): APScheduler、Celery  
✅ **监控层** (2 个): Prometheus、Grafana  

每个系统都提供了：
- 📋 **功能定位** 与 **技术特性**
- 🐳 **Docker 部署** 配置
- 💻 **代码集成** 示例
- ⚙️ **性能调优** 参数
- 🔧 **故障排查** 指南

通过本指南，您可以：
1. **快速搭建** 完整的 NecoRAG 系统
2. **灵活替换** 各层的第三方组件
3. **性能调优** 以满足生产环境需求
4. **故障诊断** 快速定位和解决问题

---

<div align="center">

**Let's make AI think like a brain!** 🧠

[NecoRAG Team](https://github.com/NecoRAG)

</div>
