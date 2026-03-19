# 🐳 NecoRAG Docker 镜像导入指南

## 📋 目录

- [快速开始](#快速开始)
- [镜像列表](#镜像列表)
- [使用说明](#使用说明)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 一键导入所有镜像

```bash
# 进入 3rd 目录
cd 3rd

# 赋予执行权限
chmod +x import_docker_images.sh

# 运行导入脚本（自动检测网络并选择最优镜像源）
./import_docker_images.sh
```

### 验证镜像

```bash
# 验证脚本
chmod +x verify_docker_images.sh
./verify_docker_images.sh
```

---

## 📦 镜像列表

### 必需镜像（9 个）

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| **redis** | `7-alpine` | ~25MB | L1 工作记忆与缓存 | [链接](https://hub.docker.com/_/redis) |
| **qdrant/qdrant** | `latest` | ~500MB | L2 语义向量数据库 | [链接](https://hub.docker.com/r/qdrant/qdrant) |
| **neo4j** | `5-community` | ~1.2GB | L3 情景图谱数据库 | [链接](https://hub.docker.com/_/neo4j) |
| **ollama/ollama** | `latest` | ~2GB | 本地 LLM 推理服务器 | [链接](https://hub.docker.com/r/ollama/ollama) |
| **vllm/vllm-openai** | `latest` | ~3GB | 高吞吐 LLM 推理服务 | [链接](https://hub.docker.com/r/vllm/vllm-openai) |
| **infiniflow/ragflow** | `latest` | ~1.5GB | 深度文档解析引擎 | [链接](https://hub.docker.com/r/infiniflow/ragflow) |
| **langchain/langgraph** | `latest` | ~800MB | 编排引擎（状态机） | [链接](https://hub.docker.com/r/langchain/langgraph) |
| **streamlit/streamlit** | `latest` | ~600MB | 前端/可视化界面 | [链接](https://hub.docker.com/r/streamlit/streamlit) |
| **grafana/grafana** | `latest` | ~300MB | 监控仪表盘 | [链接](https://hub.docker.com/r/grafana/grafana) |

**总计大小**: ~9.9GB

### 可选镜像（按需选择）

#### 数据库与监控

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| milvusdb/milvus | `v3.2.0-alpha` | ~707MB | Milvus 向量数据库（备选） | [链接](https://hub.docker.com/r/milvusdb/milvus) |
| memgraph/memgraph | `latest` | ~203MB | Memgraph 图数据库（备选） | [链接](https://hub.docker.com/r/memgraph/memgraph) |
| prom/prometheus | `latest` | ~146MB | Prometheus 指标收集 | [链接](https://hub.docker.com/_/prometheus) |
| apache/superset | `latest` | ~643MB | Superset 数据可视化 | [链接](https://hub.docker.com/r/apache/superset) |

#### OCR 文档扫描

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| **ocrmypdf/ocrmypdf** | `latest` | ~400MB | PDF OCR 扫描与优化 | [链接](https://hub.docker.com/r/ocrmypdf/ocrmypdf) |
| **tesseractshadow/tesseract4re** | `latest` | ~1.2GB | Tesseract OCR 引擎（图片/文档） | [链接](https://hub.docker.com/r/tesseractshadow/tesseract4re) |
| **paddlepaddle/paddleocr** | `latest` | ~1.5GB | PaddleOCR 多语言 OCR | [链接](https://hub.docker.com/r/paddlepaddle/paddleocr) |

**OCR 功能说明：**
- **OCRmyPDF**: 专为 PDF 设计，支持扫描版 PDF 转可搜索 PDF
- **Tesseract OCR**: 通用 OCR 引擎，支持 100+ 种语言
- **PaddleOCR**: 百度开源，支持中英文等多语言，精度高

#### 全文搜索引擎

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| **elasticsearch/elasticsearch** | `3.2.0-alpha` | ~1.8GB | Elasticsearch 分布式搜索引擎 | [链接](https://hub.docker.com/r/elasticsearch/elasticsearch) |
| **kibana/kibana** | `3.2.0-alpha` | ~1.2GB | Kibana 可视化仪表盘 | [链接](https://hub.docker.com/r/kibana/kibana) |
| **docker.elastic.co/apm/apm-server** | `3.2.0-alpha` | ~300MB | APM Server 应用性能监控 | [链接](https://www.docker.elastic.co/) |

**Elasticsearch 功能说明：**
- **Elasticsearch**: 分布式全文搜索引擎，支持海量数据实时检索
- **Kibana**: 数据可视化平台，提供丰富的图表和仪表盘
- **APM Server**: 应用性能监控，收集和分析应用指标

#### AI 意图与情感分析

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| **huggingface/text-generation-inference** | `2.0` | ~2.5GB | Hugging Face 文本推理服务 | [链接](https://hub.docker.com/r/huggingface/text-generation-inference) |
| **textblob/textblob** | `latest` | ~800MB | TextBlob 情感分析（英文） | [链接](https://hub.docker.com/r/textblob/textblob) |
| **snowflake/snowpark-python** | `latest` | ~1.2GB | Snowflake NLP 情感分析 | [链接](https://hub.docker.com/r/snowflake/snowpark-python) |
| **bert-base-uncased** | `latest` | ~1.5GB | BERT 意图分类模型 | [链接](https://hub.docker.com/r/huggingface/bert-base-uncased) |

**AI 意图与情感分析功能说明：**
- **Hugging Face TGI**: 高性能文本推理服务，支持多种预训练模型
- **TextBlob**: 简单易用的情感分析工具（英文优化）
- **Snowflake NLP**: 企业级 NLP 服务，支持多语言情感分析
- **BERT**: 深度学习的意图分类和文本理解

**可选镜像总计**: ~16.5GB

---

## 📖 使用说明

### 脚本功能

#### 1. `import_docker_images.sh` - 镜像导入脚本

**功能**:
- ✅ 自动检测 Docker 环境
- ✅ **智能网络检测** - 自动识别中国大陆/海外网络环境
- ✅ **镜像源自动切换** - 国内使用阿里云镜像，海外使用 Docker Hub 官方
- ✅ 智能拉取所有必需镜像
- ✅ 支持可选镜像选择
- ✅ 显示镜像详细信息
- ✅ 错误处理和重试机制

**参数**:
```bash
./import_docker_images.sh [选项]

选项:
  -h, --help      显示帮助信息
  -l, --list      列出所有需要的镜像
  -o, --optional  仅拉取可选镜像
  -v, --verbose   显示详细信息
```

**使用示例**:
```bash
# 拉取所有必需镜像
./import_docker_images.sh

# 查看镜像列表
./import_docker_images.sh -l

# 拉取可选镜像
./import_docker_images.sh -o

# 显示详细信息
./import_docker_images.sh -v
```

#### 2. `verify_docker_images.sh` - 镜像验证脚本

**功能**:
- ✅ 检查所有必需镜像是否存在
- ✅ 显示镜像大小和创建时间
- ✅ 生成验证报告
- ✅ 提供下一步指引

**使用示例**:
```bash
# 验证所有镜像
./verify_docker_images.sh

# 静默验证（用于脚本中）
./verify_docker_images.sh > /dev/null 2>&1 && echo "验证通过"
```

---

## 🔧 故障排查

### 问题 1: Docker 未安装或未运行

**症状**:
```
[ERROR] Docker 未安装！请先安装 Docker。
```

**解决方案**:
```bash
# macOS (使用 Homebrew)
brew install --cask docker

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# CentOS/RHEL
sudo yum install docker docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 问题 2: 网络检测失败

**症状**:
```
[INFO] 正在检测网络环境...
[WARNING] 无法访问测试站点，将使用默认镜像源
```

**解决方案**:

#### 方案 1: 手动指定镜像源

```bash
# 强制使用阿里云镜像（国内用户）
export USE_ALIYUN=true
./import_docker_images.sh

# 强制使用 Docker Hub（海外用户）
export USE_ALIYUN=false
./import_docker_images.sh
```

#### 方案 2: 检查网络连接

```bash
# 测试网络连接
curl -I https://www.baidu.com
curl -I https://registry.cn-hangzhou.aliyuncs.com

# 如果无法访问，请检查防火墙或代理设置
```

### 问题 3: 镜像拉取失败

**症状**:
```
[ERROR] 镜像拉取失败：qdrant/qdrant:latest
Error response from daemon: Get https://registry-1.docker.io/v2/: dial tcp: lookup registry-1.docker.io on 8.8.8.8:53: read udp: i/o timeout
```

**解决方案**:

#### 方案 1: 配置 Docker 镜像加速器（中国大陆推荐）

```bash
# 编辑 Docker 配置文件
sudo vi /etc/docker/daemon.json

# 添加以下内容（使用阿里云加速器）
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 方案 2: 镜像拉取超时或失败

```bash
# 如果脚本拉取失败，可以手动拉取
docker pull redis:7-alpine
docker pull qdrant/qdrant:latest
docker pull neo4j:5-community
docker pull ollama/ollama:latest
docker pull grafana/grafana:latest
```

### 问题 3: 磁盘空间不足

**症状**:
```
Error response from daemon: no space left on device
```

**解决方案**:

```bash
# 1. 清理未使用的镜像
docker image prune -a

# 2. 清理停止的容器
docker container prune

# 3. 清理构建缓存
docker builder prune

# 4. 查看磁盘使用情况
docker system df
```

### 问题 4: 网络超时

**症状**:
```
context deadline exceeded
```

**解决方案**:

```bash
# 增加 Docker 拉取超时时间
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300

# 使用国内镜像源
# 参考问题 2 的配置
```

---

## 🎯 最佳实践

### 1. 定期更新镜像

```bash
# 每月检查一次镜像更新
./import_docker_images.sh

# 查看哪些镜像有过时版本
docker images --format "{{.Repository}}:{{.Tag}} - {{.CreatedAt}}"
```

### 2. 镜像备份

```bash
# 保存镜像到本地文件
docker save -o necorag-images.tar \
  redis:7-alpine \
  qdrant/qdrant:latest \
  neo4j:5-community \
  ollama/ollama:latest \
  grafana/grafana:latest

# 从备份恢复
docker load -i necorag-images.tar
```

### 3. 离线环境部署

```bash
# 在有网络的机器上导出镜像
docker save redis:7-alpine > redis-7-alpine.tar
docker save qdrant/qdrant:latest > qdrant-latest.tar
# ... 其他镜像

# 复制到离线机器
scp *.tar user@offline-server:/tmp/

# 在离线机器上加载
docker load -i redis-7-alpine.tar
docker load -i qdrant-latest.tar
# ... 其他镜像
```

### 4. 版本锁定（生产环境推荐）

```bash
# 使用具体版本号而非 latest
# 修改 import_docker_images.sh 中的镜像列表

declare -a IMAGES=(
    "redis:3.2.0-alpha"           # 锁定具体版本
    "qdrant/qdrant:v3.2.0-alpha"         # 锁定具体版本
    "neo4j:3.2.0-alpha"       # 锁定具体版本
    "ollama/ollama:3.2.0-alpha"         # 锁定具体版本
    "grafana/grafana:3.2.0-alpha"       # 锁定具体版本
)
```

### 5. 多环境管理

```bash
# 开发环境
./import_docker_images.sh

# 生产环境（使用特定版本）
./import_docker_images_production.sh

# 测试环境（最小化配置）
./import_docker_images_minimal.sh
```

---

## 🔧 NecoRAG 核心架构镜像

### 完整技术栈对比

| 模块 | 推荐开源组件 | Docker 镜像 | 状态 |
|------|-------------|-----------|------|
| **编排引擎** | LangGraph | `langchain/langgraph` | ✅ 已添加 |
| **文档解析** | RAGFlow | `infiniflow/ragflow` | ✅ 已添加 |
| **向量数据库** | Qdrant | `qdrant/qdrant` | ✅ 已有 |
| **图数据库** | Neo4j (社区版) | `neo4j:5-community` | ✅ 已有 |
| **缓存/工作记忆** | Redis | `redis:7-alpine` | ✅ 已有 |
| **嵌入模型** | BGE-M3 | HuggingFace 模型 | 📝 配置说明 |
| **重排序模型** | BGE-Reranker-v2 | HuggingFace 模型 | 📝 配置说明 |
| **LLM 推理** | vLLM / Ollama | `vllm/vllm-openai` + `ollama/ollama` | ✅ 已添加 |
| **前端/可视化** | Streamlit | `streamlit/streamlit` | ✅ 已添加 |
| **监控仪表盘** | Grafana | `grafana/grafana` | ✅ 已有 |

### 快速启动 - 核心组件

#### 1. RAGFlow 深度文档解析

```yaml
# docker-compose.yml
version: '3.8'
services:
  ragflow:
    image: infiniflow/ragflow:latest
    container_name: ragflow
    ports:
      - "9380:9380"
    volumes:
      - ./ragflow_data:/var/lib/ragflow
    environment:
      - RAGFLOW_PORT=9380
      - LOG_LEVEL=INFO
```

```bash
# 启动服务
docker-compose up -d ragflow

# 访问 Web 界面
# http://localhost:9380

# API 测试
curl http://localhost:9380/api/v1/parser \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/data/document.pdf",
    "parser_type": "deep"
  }'
```

**RAGFlow 核心能力：**
- ✅ 深度文档解析（支持复杂布局）
- ✅ 表格识别与还原
- ✅ 公式和图表提取
- ✅ 多栏排版处理
- ✅ OCR 集成

#### 2. LangGraph 编排引擎

```yaml
# docker-compose.yml
version: '3.8'
services:
  langgraph:
    image: langchain/langgraph:latest
    container_name: langgraph
    ports:
      - "8123:8123"
    volumes:
      - ./graphs:/app/graphs
    environment:
      - LANGCHAIN_API_KEY=your_api_key
      - LANGGRAPH_DEBUG=true
```

```bash
# 启动服务
docker-compose up -d langgraph

# 创建状态机图
curl http://localhost:8123/graphs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rag_workflow",
    "nodes": [
      {"id": "retrieve", "type": "retriever"},
      {"id": "reflect", "type": "reflector"},
      {"id": "generate", "type": "generator"}
    ],
    "edges": [
      {"from": "retrieve", "to": "reflect"},
      {"from": "reflect", "to": "generate"}
    ]
  }'
```

**LangGraph 核心能力：**
- ✅ 复杂循环状态机
- ✅ "检索 - 反思 - 校正"闭环
- ✅ 多 Agent 协作
- ✅ 条件分支和循环
- ✅ 状态持久化

#### 3. vLLM 高吞吐推理

```yaml
# docker-compose.yml
version: '3.8'
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    ports:
      - "8000:8000"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=/models/Qwen-7B-Chat
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```bash
# 启动服务
docker-compose up -d vllm

# OpenAI 兼容 API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen-7B-Chat",
    "messages": [
      {"role": "user", "content": "什么是 RAG？"}
    ]
  }'
```

**vLLM 核心优势：**
- ✅ 高吞吐量（比 HuggingFace 快 24 倍）
- ✅ PagedAttention 内存优化
- ✅ 连续批处理
- ✅ OpenAI API 兼容
- ✅ 支持多种模型

#### 4. Streamlit 前端界面

```yaml
# docker-compose.yml
version: '3.8'
services:
  streamlit:
    image: streamlit/streamlit:latest
    container_name: streamlit
    ports:
      - "8501:8501"
    volumes:
      - ./app:/app
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

```python
# app/app.py
import streamlit as st

st.title("NecoRAG 智能问答系统")

# 用户输入
query = st.text_input("请输入问题：")

if st.button("提交"):
    # 调用后端 API
    response = call_backend(query)
    st.write(response)
    
    # 显示置信度
    st.metric("置信度", f"{response['confidence']:.2%}")
```

```bash
# 启动应用
docker-compose up -d streamlit

# 访问界面
# http://localhost:8501
```

**Streamlit 核心能力：**
- ✅ 快速构建 Demo
- ✅ 交互式组件
- ✅ 实时数据展示
- ✅ 文件上传下载
- ✅ 图表可视化

### 完整系统启动

```yaml
# docker-compose.full.yml
version: '3.8'
services:
  # 数据存储层
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
  
  # 文档解析层
  ragflow:
    image: infiniflow/ragflow:latest
    ports:
      - "9380:9380"
    depends_on:
      - redis
      - qdrant
  
  # 模型服务层
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    volumes:
      - models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  # 编排层
  langgraph:
    image: langchain/langgraph:latest
    ports:
      - "8123:8123"
    depends_on:
      - vllm
      - ragflow
  
  # 应用层
  streamlit:
    image: streamlit/streamlit:latest
    ports:
      - "8501:8501"
    volumes:
      - ./app:/app
    depends_on:
      - langgraph
  
  # 监控层
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  qdrant_data:
  models:
```

```bash
# 一键启动所有服务
docker-compose -f docker-compose.full.yml up -d

# 查看状态
docker-compose -f docker-compose.full.yml ps

# 停止所有服务
docker-compose -f docker-compose.full.yml down
```

### 模型配置指南

#### 1. BGE-M3 嵌入模型

```python
from sentence_transformers import SentenceTransformer

# 加载模型
model = SentenceTransformer('BAAI/bge-m3', device='cuda')

# 编码文本
texts = ["这是第一个句子", "这是第二个句子"]
embeddings = model.encode(texts, normalize_embeddings=True)

# 存储到 Qdrant
qdrant.upsert(
    collection_name="documents",
    points=[{
        "id": i,
        "vector": embedding.tolist(),
        "payload": {"text": text}
    }]
)
```

**Docker 部署：**
```yaml
services:
  embedding-service:
    image: pytorch/pytorch:2.0-cuda11.7
    volumes:
      - ./models:/models
      - ./embedding_service.py:/app/app.py
    command: python /app/app.py
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### 2. BGE-Reranker-v2 重排序模型

```python
from FlagEmbedding import FlagReranker

# 加载模型
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=False)

# 重排序
pairs = [
    ("查询：什么是 RAG", "文档 1：RAG 是检索增强生成..."),
    ("查询：什么是 RAG", "文档 2：深度学习是一种..."),
]

scores = reranker.compute_score(pairs)

# 按分数排序
ranked = sorted(zip(pairs, scores), key=lambda x: x[1], reverse=True)
```

**Docker 部署：**
```yaml
services:
  reranker-service:
    image: pytorch/pytorch:2.0-cuda11.7
    volumes:
      - ./models:/models
      - ./reranker_service.py:/app/app.py
    ports:
      - "8888:8888"
    command: python /app/app.py
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 性能优化建议

#### 1. GPU 资源分配

```yaml
# 为不同服务分配 GPU
services:
  vllm:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']  # GPU 0
              capabilities: [gpu]
  
  embedding-service:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']  # GPU 1
              capabilities: [gpu]
```

#### 2. 内存管理

```yaml
services:
  vllm:
    environment:
      - VLLM_MAX_MODEL_LEN=8192
      - VLLM_GPU_MEMORY_UTILIZATION=0.9
  
  qdrant:
    environment:
      - QDRANT_MEM_LIMIT_GB=4
```

#### 3. 自动扩缩容

```yaml
services:
  vllm:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      rollback_config:
        parallelism: 1
        delay: 10s
```

---

## 🧠 AI 意图分析与情感分析功能

### 核心组件对比

| 方案 | 语言支持 | 模型类型 | 大小 | 精度 | 速度 |
|------|---------|---------|------|------|------|
| **Hugging Face TGI** | 多语言 | Transformer | ~2.5GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **TextBlob** | 英文为主 | 规则 + 统计 | ~800MB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Snowflake NLP** | 多语言 | 深度学习 | ~1.2GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **BERT** | 多语言 | Transformer | ~1.5GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 快速启动

#### 1. Hugging Face Text Generation Inference

```yaml
# docker-compose.yml
version: '3.8'
services:
  tgi:
    image: huggingface/text-generation-inference:2.0
    container_name: tgi
    ports:
      - "8080:80"
    volumes:
      - ./models:/data
    environment:
      - MODEL_ID=/data/bert-base-uncased
      - MAX_INPUT_LENGTH=512
      - MAX_TOTAL_TOKENS=1024
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```bash
# 启动服务
docker-compose up -d

# 检查状态
curl http://localhost:8080/health

# 情感分析示例
curl http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "I love this product!",
    "parameters": {
      "max_new_tokens": 10
    }
  }'
```

#### 2. TextBlob 情感分析（英文）

```bash
# 拉取镜像
docker pull textblob/textblob:latest

# 运行容器
docker run -it --rm textblob/textblob python3

# Python 代码测试
from textblob import TextBlob

# 情感分析
text = "I absolutely love this! It's amazing."
blob = TextBlob(text)
sentiment = blob.sentiment

print(f"Polarity: {sentiment.polarity}")  # -1 (负面) 到 1 (正面)
print(f"Subjectivity: {sentiment.subjectivity}")  # 0 (客观) 到 1 (主观)

# 中文需要使用翻译
from textblob.translate import Translator
translator = Translator()

chinese_text = "我很喜欢这个产品"
translated = translator.translate(chinese_text, from_lang='zh-CN', to='en')
blob = TextBlob(translated)
print(f"Sentiment: {blob.sentiment}")
```

#### 3. BERT 意图分类

```bash
# 拉取镜像
docker pull huggingface/bert-base-uncased:latest

# 运行容器
docker run -it --rm \
  -v $(pwd)/models:/models \
  huggingface/bert-base-uncased \
  python3 << EOF
from transformers import pipeline

# 加载情感分析管道
classifier = pipeline("sentiment-analysis", model="bert-base-uncased")

# 测试
texts = [
    "I love this product!",
    "This is terrible.",
    "It's okay, nothing special."
]

for text in texts:
    result = classifier(text)[0]
    print(f"Text: {text}")
    print(f"Label: {result['label']}, Score: {result['score']:.4f}\n")
EOF
```

### 基本使用

#### 1. 情感分析（中英文）

```python
from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self, model_name="nlptown/bert-base-multilingual-unicode-sentiment"):
        """
        初始化情感分析器
        :param model_name: 模型名称，支持多语言
        """
        self.classifier = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=0  # GPU
        )
    
    def analyze(self, text: str) -> dict:
        """
        分析文本情感
        :param text: 输入文本
        :return: 情感分析结果
        """
        result = self.classifier(text)[0]
        
        return {
            "label": result["label"],
            "score": result["score"],
            "sentiment": "positive" if "5" in result["label"] or "POS" in result["label"] else "negative",
            "confidence": result["score"]
        }

# 使用示例
analyzer = SentimentAnalyzer()

# 英文测试
en_texts = [
    "I absolutely love this product!",
    "This is the worst thing ever.",
    "It's okay, nothing special."
]

for text in en_texts:
    result = analyzer.analyze(text)
    print(f"EN: {text}")
    print(f"   Sentiment: {result['sentiment']} ({result['confidence']:.2%})\n")

# 中文测试
zh_texts = [
    "这个产品太棒了，我非常喜欢！",
    "质量很差，我很失望。",
    "还可以吧，没什么特别的。"
]

for text in zh_texts:
    result = analyzer.analyze(text)
    print(f"ZH: {text}")
    print(f"   Sentiment: {result['sentiment']} ({result['confidence']:.2%})\n")
```

#### 2. 意图分类

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class IntentClassifier:
    def __init__(self, model_name="bhadresh-savani/bert-base-uncased-emotion"):
        """
        初始化意图分类器
        :param model_name: 预训练模型
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    def classify(self, text: str, labels: list = None) -> dict:
        """
        分类文本意图
        :param text: 输入文本
        :param labels: 自定义标签列表（可选）
        :return: 分类结果
        """
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # 获取概率最高的类别
        top_prob, top_class = torch.max(predictions, 1)
        
        return {
            "intent": labels[top_class.item()] if labels else top_class.item(),
            "confidence": top_prob.item(),
            "all_scores": predictions[0].tolist()
        }

# 使用示例
classifier = IntentClassifier()

# 定义意图标签
intent_labels = ["joy", "sadness", "anger", "fear", "surprise", "disgust"]

texts = [
    "I'm so excited about the news!",
    "I'm feeling really down today.",
    "This makes me so angry!",
    "我很害怕明天的考试。",
    "这个消息让我很惊讶！"
]

for text in texts:
    result = classifier.classify(text, intent_labels)
    print(f"Text: {text}")
    print(f"Intent: {result['intent']} ({result['confidence']:.2%})\n")
```

#### 3. 多语言混合分析

```python
from langdetect import detect
from transformers import pipeline

class MultiLingualAnalyzer:
    def __init__(self):
        """初始化多语言分析器"""
        # 英文情感分析
        self.en_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # 中文情感分析
        self.zh_analyzer = pipeline(
            "sentiment-analysis",
            model="uer/roberta-base-finetuned-jd-binary-chinese"
        )
    
    def detect_language(self, text: str) -> str:
        """检测语言类型"""
        try:
            lang = detect(text)
            return 'zh' if lang == 'zh-cn' else lang
        except:
            return 'unknown'
    
    def analyze(self, text: str) -> dict:
        """
        自动检测语言并分析情感
        :param text: 输入文本
        :return: 分析结果
        """
        lang = self.detect_language(text)
        
        if lang == 'en':
            result = self.en_analyzer(text)[0]
            sentiment = "positive" if result["label"] == "POSITIVE" else "negative"
        elif lang == 'zh':
            result = self.zh_analyzer(text)[0]
            sentiment = "positive" if result["label"] == "pos" else "negative"
        else:
            # 默认使用多语言模型
            multilingual = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-unicode-sentiment"
            )
            result = multilingual(text)[0]
            sentiment = "positive" if "5" in result["label"] else "negative"
        
        return {
            "language": lang,
            "sentiment": sentiment,
            "confidence": result["score"],
            "label": result["label"]
        }

# 使用示例
analyzer = MultiLingualAnalyzer()

mixed_texts = [
    "This is amazing!",  # English positive
    "I hate this.",  # English negative
    "这个产品太好了！",  # Chinese positive
    "质量很差，不喜欢。",  # Chinese negative
    "The quality is good but expensive."  # Mixed
]

for text in mixed_texts:
    result = analyzer.analyze(text)
    print(f"Text: {text}")
    print(f"Language: {result['language']}")
    print(f"Sentiment: {result['sentiment']} ({result['confidence']:.2%})\n")
```

### 集成到 NecoRAG

#### 方案 1：用户查询意图分析

```python
from enum import Enum
from typing import List, Dict

class QueryIntent(Enum):
    """查询意图类型"""
    INFORMATION_SEEKING = "information_seeking"  # 寻求信息
    PROBLEM_SOLVING = "problem_solving"  # 解决问题
    OPINION_REQUEST = "opinion_request"  # 征求意见
    CHAT = "chat"  # 闲聊
    COMMAND = "command"  # 指令
    NEGATIVE_FEEDBACK = "negative_feedback"  # 负面反馈
    POSITIVE_FEEDBACK = "positive_feedback"  # 正面反馈

class QueryAnalyzer:
    def __init__(self):
        """初始化查询分析器"""
        from transformers import pipeline
        
        # 意图分类
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # 情感分析
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        # 定义意图候选
        self.intent_candidates = [
            "information seeking",
            "problem solving",
            "opinion request",
            "casual chat",
            "command",
            "complaint",
            "praise"
        ]
    
    def analyze_query(self, query: str) -> Dict:
        """
        分析用户查询
        :param query: 用户输入
        :return: 分析结果
        """
        # 1. 意图识别
        intent_result = self.intent_classifier(
            query,
            self.intent_candidates,
            multi_label=False
        )
        
        # 2. 情感分析
        sentiment_result = self.sentiment_analyzer(query)[0]
        
        # 3. 映射到枚举
        intent_mapping = {
            "information seeking": QueryIntent.INFORMATION_SEEKING,
            "problem solving": QueryIntent.PROBLEM_SOLVING,
            "opinion request": QueryIntent.OPINION_REQUEST,
            "casual chat": QueryIntent.CHAT,
            "command": QueryIntent.COMMAND,
            "complaint": QueryIntent.NEGATIVE_FEEDBACK,
            "praise": QueryIntent.POSITIVE_FEEDBACK
        }
        
        primary_intent = intent_mapping.get(
            intent_result["labels"][0],
            QueryIntent.CHAT
        )
        
        return {
            "query": query,
            "intent": primary_intent.value,
            "intent_confidence": intent_result["scores"][0],
            "sentiment": "positive" if sentiment_result["label"] == "POSITIVE" else "negative",
            "sentiment_score": sentiment_result["score"],
            "all_intents": list(zip(
                intent_result["labels"],
                intent_result["scores"]
            ))
        }

# 在 NecoRAG 中使用
analyzer = QueryAnalyzer()

queries = [
    "How do I install NecoRAG?",
    "This system is not working properly!",
    "What do you think about AI ethics?",
    "Hello, how are you today?",
    "Show me the documentation.",
    "I love this feature! It's so useful!"
]

for query in queries:
    result = analyzer.analyze_query(query)
    print(f"Query: {query}")
    print(f"Intent: {result['intent']} ({result['intent_confidence']:.2%})")
    print(f"Sentiment: {result['sentiment']} ({result['sentiment_score']:.2%})\n")
```

#### 方案 2：实时情感监控

```python
import asyncio
from datetime import datetime
from collections import deque

class RealTimeSentimentMonitor:
    def __init__(self, window_size: int = 100):
        """
        实时情感监控器
        :param window_size: 时间窗口大小
        """
        self.window_size = window_size
        self.sentiment_history = deque(maxlen=window_size)
        self.analyzer = MultiLingualAnalyzer()
    
    async def add_observation(self, text: str, metadata: dict = None):
        """添加观察记录"""
        result = self.analyzer.analyze(text)
        
        observation = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "language": result["language"],
            "metadata": metadata or {}
        }
        
        self.sentiment_history.append(observation)
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        if not self.sentiment_history:
            return {"count": 0}
        
        sentiments = [o["sentiment"] for o in self.sentiment_history]
        confidences = [o["confidence"] for o in self.sentiment_history]
        
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")
        total = len(sentiments)
        
        return {
            "count": total,
            "positive_ratio": positive_count / total,
            "negative_ratio": negative_count / total,
            "avg_confidence": sum(confidences) / len(confidences),
            "trend": self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """计算情感趋势"""
        if len(self.sentiment_history) < 10:
            return "insufficient_data"
        
        recent = list(self.sentiment_history)[-10:]
        recent_positive = sum(1 for o in recent if o["sentiment"] == "positive")
        
        if recent_positive >= 7:
            return "improving"
        elif recent_positive <= 3:
            return "declining"
        else:
            return "stable"

# 在 NecoRAG 中使用
monitor = RealTimeSentimentMonitor(window_size=50)

# 模拟用户反馈
async def simulate_feedback():
    feedbacks = [
        ("Great system!", {"user_id": "u1"}),
        ("Not bad", {"user_id": "u2"}),
        ("非常好用", {"user_id": "u3"}),
        ("有点慢", {"user_id": "u4"}),
        ("Perfect!", {"user_id": "u5"})
    ]
    
    for text, meta in feedbacks:
        await monitor.add_observation(text, meta)
    
    stats = monitor.get_statistics()
    print(f"Statistics: {stats}")

asyncio.run(simulate_feedback())
```

#### 方案 3：智能路由决策

```python
class IntelligentRouter:
    def __init__(self):
        """智能路由器：基于意图和情感路由查询"""
        self.analyzer = QueryAnalyzer()
    
    def route_query(self, query: str) -> str:
        """
        根据意图和情感路由查询
        :param query: 用户输入
        :return: 路由目标
        """
        analysis = self.analyzer.analyze_query(query)
        
        intent = analysis["intent"]
        sentiment = analysis["sentiment"]
        
        # 路由规则
        routing_rules = {
            QueryIntent.NEGATIVE_FEEDBACK.value: "escalation",  # 负面反馈 → 人工客服
            QueryIntent.PROBLEM_SOLVING.value: "troubleshooting",  # 问题解决 → 技术支持
            QueryIntent.INFORMATION_SEEKING.value: "knowledge_base",  # 信息查询 → 知识库
            QueryIntent.COMMAND.value: "action_executor",  # 指令 → 执行器
            QueryIntent.POSITIVE_FEEDBACK.value: "feedback_collector",  # 正面反馈 → 收集器
        }
        
        # 默认路由
        default_route = "general_chat"
        
        # 如果情感非常负面，升级到人工
        if sentiment == "negative" and analysis["sentiment_score"] > 0.9:
            return "urgent_escalation"
        
        return routing_rules.get(intent, default_route)

# 在 NecoRAG 中使用
router = IntelligentRouter()

test_queries = [
    "This is broken! Fix it now!",
    "How do I configure the system?",
    "I need help with installation.",
    "Your product is amazing!",
    "Execute the backup command."
]

for query in test_queries:
    route = router.route_query(query)
    print(f"Query: {query}")
    print(f"Route: {route}\n")
```

### 性能优化建议

#### 1. 模型量化

```python
import torch
from transformers import AutoModelForSequenceClassification

def quantize_model(model_name: str):
    """量化模型以减少内存占用"""
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # 动态量化
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8
    )
    
    return quantized_model

# 使用量化模型
quantized = quantize_model("bert-base-uncased")
```

#### 2. 批量处理

```python
def batch_analyze(texts: List[str], batch_size: int = 32):
    """批量分析文本"""
    from transformers import pipeline
    
    analyzer = pipeline("sentiment-analysis")
    
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = analyzer(batch)
        results.extend(batch_results)
    
    return results
```

#### 3. 缓存机制

```python
from functools import lru_cache
import hashlib

class CachedAnalyzer:
    @lru_cache(maxsize=1000)
    def analyze_with_cache(self, text_hash: str, text: str):
        """带缓存的分析"""
        return self.analyzer.analyze(text)
    
    def analyze(self, text: str):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.analyze_with_cache(text_hash, text)
```

### 常见问题

#### Q1: 中文识别效果不好？

**解决方案：**
1. 使用专门针对中文训练的模型
2. 增加训练数据
3. 微调预训练模型

```python
# 使用中文专用模型
model = pipeline(
    "sentiment-analysis",
    model="uer/roberta-base-finetuned-jd-binary-chinese"
)
```

#### Q2: 推理速度慢？

**解决方案：**
1. 使用更小的模型（如 DistilBERT）
2. 启用 GPU 加速
3. 批量处理请求
4. 模型量化

```bash
# 使用 TensorRT 加速
docker run --gpus all \
  -p 8080:80 \
  nvcr.io/nvidia/tensorrt:21.09-py3
```

#### Q3: 多语言支持不足？

**解决方案：**
1. 使用 XLM-RoBERTa 等多语言模型
2. 为不同语言配置不同的模型
3. 实现语言检测和自动切换

```python
# 使用 XLM-RoBERTa
model = pipeline(
    "sentiment-analysis",
    model="xlm-roberta-large-finetuned-offensive-language"
)
```

---

## 🔍 Elasticsearch 全文搜索功能

### 核心组件

| 组件 | 作用 | 端口 |
|------|------|------|
| **Elasticsearch** | 搜索引擎核心，存储和检索数据 | 9200 (HTTP), 9300 (Transport) |
| **Kibana** | 可视化界面，管理和分析数据 | 5601 |
| **APM Server** | 应用性能监控，收集指标 | 8200 |

### 快速启动

#### 1. Docker Compose 一键启动

```yaml
# docker-compose.yml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch/elasticsearch:3.2.0-alpha
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - elastic-network

  kibana:
    image: kibana/kibana:3.2.0-alpha
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - elastic-network

volumes:
  es_data:
    driver: local

networks:
  elastic-network:
    driver: bridge
```

```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 检查 Elasticsearch
curl http://localhost:9200

# 访问 Kibana
# 浏览器打开：http://localhost:5601
```

#### 2. 手动启动单个容器

```bash
# 拉取镜像
docker pull elasticsearch/elasticsearch:3.2.0-alpha
docker pull kibana/kibana:3.2.0-alpha

# 启动 Elasticsearch
docker run -d --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  -v es_data:/usr/share/elasticsearch/data \
  elasticsearch/elasticsearch:3.2.0-alpha

# 启动 Kibana
docker run -d --name kibana \
  -p 5601:5601 \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  --link elasticsearch:elasticsearch \
  kibana/kibana:3.2.0-alpha
```

### 基本使用

#### 1. 创建索引

```bash
# 创建文档索引
curl -X PUT "localhost:9200/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    },
    "mappings": {
      "properties": {
        "title": { "type": "text", "analyzer": "standard" },
        "content": { "type": "text", "analyzer": "standard" },
        "author": { "type": "keyword" },
        "created_at": { "type": "date" },
        "tags": { "type": "keyword" }
      }
    }
  }'

# 查看索引信息
curl "localhost:9200/documents/_mapping"
```

#### 2. 添加文档

```bash
# 插入单条文档
curl -X POST "localhost:9200/documents/_doc" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "NecoRAG 项目文档",
    "content": "NecoRAG 是一个智能 RAG 系统...",
    "author": "admin",
    "created_at": "2026-03-19",
    "tags": ["rag", "ai", "nlp"]
  }'

# 批量插入文档
curl -X POST "localhost:9200/documents/_bulk" \
  -H "Content-Type: application/json" \
  -d '"index":{}}
{"title":"知识库管理","content":"支持多种知识源...","author":"user1","tags":["knowledge"]}
{"index":{}}
{"title":"语义检索","content":"基于向量相似度...","author":"user2","tags":["retrieval","semantic"]}
```

#### 3. 全文搜索

```bash
# 简单匹配查询
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "content": "RAG 系统"
      }
    }
  }'

# 多字段查询
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "multi_match": {
        "query": "智能检索",
        "fields": ["title", "content"]
      }
    }
  }'

# 精确短语查询
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match_phrase": {
        "content": "向量相似度"
      }
    }
  }'

# 布尔组合查询
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [
          { "match": { "content": "检索" }}
        ],
        "filter": [
          { "term": { "author": "admin" }},
          { "range": { "created_at": { "gte": "2026-01-01" }}}
        ]
      }
    }
  }'
```

#### 4. 高亮显示

```bash
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "match": {
        "content": "RAG"
      }
    },
    "highlight": {
      "fields": {
        "content": {}
      }
    }
  }'
```

#### 5. 聚合统计

```bash
# 按作者统计文档数量
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "authors": {
        "terms": {
          "field": "author"
        }
      }
    }
  }'

# 按标签统计
curl -X GET "localhost:9200/documents/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "tags": {
        "terms": {
          "field": "tags"
        }
      }
    }
  }'
```

### 集成到 NecoRAG

#### 方案 1：使用 Python 客户端

```python
from elasticsearch import Elasticsearch

class ElasticSearchService:
    def __init__(self, host="localhost", port=9200):
        self.es = Elasticsearch([f"http://{host}:{port}"])
    
    def index_document(self, index, doc_id, document):
        """索引文档"""
        return self.es.index(index=index, id=doc_id, document=document)
    
    def search(self, index, query, fields=None, size=10):
        """全文搜索"""
        if fields:
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": fields
                    }
                },
                "size": size
            }
        else:
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content"]  # title 权重更高
                    }
                },
                "size": size
            }
        
        return self.es.search(index=index, body=body)
    
    def delete_index(self, index):
        """删除索引"""
        return self.es.indices.delete(index=index, ignore=[400, 404])

# 在 NecoRAG 中使用
es_service = ElasticSearchService()

# 索引文档
es_service.index_document(
    index="documents",
    doc_id="doc_001",
    document={
        "title": "NecoRAG 使用指南",
        "content": "本文介绍如何使用 NecoRAG...",
        "author": "admin",
        "tags": ["guide", "tutorial"]
    }
)

# 搜索
results = es_service.search(
    index="documents",
    query="RAG 系统使用",
    fields=["title", "content"],
    size=5
)

for hit in results["hits"]["hits"]:
    print(f"Score: {hit['_score']}, Title: {hit['_source']['title']}")
```

#### 方案 2：与 Qdrant 联合使用

```python
from qdrant_client import QdrantClient
from elasticsearch import Elasticsearch

class HybridSearchEngine:
    def __init__(self):
        # 向量数据库（语义搜索）
        self.qdrant = QdrantClient(host="localhost", port=6333)
        # 全文搜索引擎（关键词搜索）
        self.es = Elasticsearch(host="localhost", port=9200)
    
    def hybrid_search(self, query_text, query_vector, top_k=10):
        """混合搜索：结合语义和关键词"""
        
        # 1. 语义搜索（Qdrant）
        semantic_results = self.qdrant.search(
            collection_name="documents",
            query_vector=query_vector,
            limit=top_k
        )
        
        # 2. 全文搜索（Elasticsearch）
        keyword_results = self.es.search(
            index="documents",
            body={
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["title", "content"]
                    }
                },
                "size": top_k
            }
        )
        
        # 3. 融合结果（加权排序）
        fused_results = self._fuse_results(
            semantic_results, 
            keyword_results,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        
        return fused_results
    
    def _fuse_results(self, semantic, keyword, semantic_weight, keyword_weight):
        """结果融合算法"""
        score_map = {}
        
        # 语义搜索结果
        for i, result in enumerate(semantic):
            doc_id = result.id
            score = (top_k - i) / top_k  # 归一化
            score_map[doc_id] = score * semantic_weight
        
        # 关键词搜索结果
        for hit in keyword["hits"]["hits"]:
            doc_id = hit["_id"]
            score = hit["_score"] / 10.0  # 归一化
            if doc_id in score_map:
                score_map[doc_id] += score * keyword_weight
            else:
                score_map[doc_id] = score * keyword_weight
        
        # 按总分排序
        sorted_results = sorted(
            score_map.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_results[:top_k]

# 在 NecoRAG 中使用
hybrid_engine = HybridSearchEngine()
results = hybrid_engine.hybrid_search(
    query_text="RAG 系统架构",
    query_vector=[0.1, 0.2, ...],  # 向量嵌入
    top_k=10
)
```

#### 方案 3：自动同步机制

```python
import asyncio
from datetime import datetime

class KnowledgeSyncService:
    """知识库同步服务：同时写入 Qdrant 和 Elasticsearch"""
    
    def __init__(self):
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.es = Elasticsearch(host="localhost", port=9200)
    
    async def sync_knowledge(self, knowledge_item):
        """同步知识项到多个存储"""
        
        # 1. 写入 Qdrant（向量检索）
        await self._sync_to_qdrant(knowledge_item)
        
        # 2. 写入 Elasticsearch（全文搜索）
        await self._sync_to_elastic(knowledge_item)
        
        # 3. 记录日志
        print(f"✓ 知识项已同步：{knowledge_item['id']}")
    
    async def _sync_to_qdrant(self, item):
        """同步到 Qdrant"""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('BAAI/bge-m3')
        
        # 生成向量嵌入
        text = f"{item['title']} {item['content']}"
        vector = model.encode(text)
        
        # 存储到 Qdrant
        self.qdrant.upsert(
            collection_name="knowledge",
            points=[{
                "id": item["id"],
                "vector": vector.tolist(),
                "payload": {
                    "title": item["title"],
                    "content": item["content"],
                    "metadata": item.get("metadata", {})
                }
            }]
        )
    
    async def _sync_to_elastic(self, item):
        """同步到 Elasticsearch"""
        self.es.index(
            index="knowledge",
            id=item["id"],
            document={
                "title": item["title"],
                "content": item["content"],
                "author": item.get("author", "unknown"),
                "created_at": item.get("created_at", datetime.now().isoformat()),
                "tags": item.get("tags", []),
                "metadata": item.get("metadata", {})
            }
        )

# 在 NecoRAG 中使用
sync_service = KnowledgeSyncService()

# 添加新知识
await sync_service.sync_knowledge({
    "id": "know_001",
    "title": "RAG 基础概念",
    "content": "Retrieval-Augmented Generation...",
    "author": "admin",
    "tags": ["rag", "ai"]
})
```

### 性能优化建议

#### 1. 分词器配置

```bash
# 自定义分析器（支持中文）
curl -X PUT "localhost:9200/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "analysis": {
        "analyzer": {
          "my_analyzer": {
            "type": "custom",
            "tokenizer": "ik_max_word",
            "filter": ["lowercase"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "title": { "type": "text", "analyzer": "my_analyzer" },
        "content": { "type": "text", "analyzer": "my_analyzer" }
      }
    }
  }'
```

#### 2. 索引优化

```python
# 批量索引操作
from elasticsearch.helpers import bulk

def bulk_index_documents(es_client, documents, index_name):
    """批量索引文档"""
    actions = []
    for doc in documents:
        action = {
            "_index": index_name,
            "_id": doc["id"],
            "_source": doc
        }
        actions.append(action)
    
    success, failed = bulk(es_client, actions)
    print(f"成功：{success}, 失败：{failed}")
```

#### 3. 缓存策略

```python
from functools import lru_cache
import hashlib
import json

class CachedElasticSearch:
    def __init__(self, es_client):
        self.es = es_client
    
    @lru_cache(maxsize=1000)
    def cached_search(self, index, query_key, query_json):
        """带缓存的搜索"""
        query = json.loads(query_json)
        return self.es.search(index=index, body=query)
    
    def search(self, index, query):
        """搜索接口"""
        # 生成缓存键
        cache_key = hashlib.md5(
            json.dumps(query, sort_keys=True).encode()
        ).hexdigest()
        
        return self.cached_search(
            index=index,
            query_key=cache_key,
            query_json=json.dumps(query)
        )
```

### 常见问题

#### Q1: Elasticsearch 启动失败？

**解决方案：**
```bash
# 增加虚拟内存
sudo sysctl -w vm.max_map_count=262144

# 永久生效
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 调整 JVM 堆大小
-e "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

#### Q2: 中文分词效果不好？

**解决方案：**
1. 安装 IK 分词插件
2. 使用自定义词典
3. 调整分词器参数

```bash
# 进入容器安装插件
docker exec -it elasticsearch bin/elasticsearch-plugin install \
  https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v3.2.0-alpha/elasticsearch-analysis-ik-8.11.0.zip
```

#### Q3: 如何提高搜索性能？

**解决方案：**
1. 使用过滤器代替查询
2. 合理设置副本数
3. 使用路由优化
4. 定期清理旧数据

```bash
# 删除旧索引
curl -X DELETE "localhost:9200/documents_2025"

# 优化索引
curl -X POST "localhost:9200/documents/_forcemerge?max_num_segments=1"
```

---

## 📄 OCR 文档扫描功能

### 支持的文件格式

| 文件类型 | 格式 | OCR 支持 | 推荐工具 |
|---------|------|----------|---------|
| **图片** | PNG, JPG, JPEG, TIFF, BMP, GIF | ✅ | Tesseract OCR, PaddleOCR |
| **PDF** | PDF (扫描版/文本版) | ✅ | OCRmyPDF |
| **文档** | DOC, DOCX | ⚠️ 需转换 | 先转 PDF 再 OCR |
| **其他** | DjVu, XPS, OXPS | ✅ | OCRmyPDF |

### OCR 工具对比

| 特性 | OCRmyPDF | Tesseract OCR | PaddleOCR |
|------|----------|---------------|-----------|
| **PDF 处理** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **图片 OCR** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **中文支持** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **多语言** | 100+ 语言 | 100+ 语言 | 80+ 语言 |
| **速度** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **精度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **部署难度** | 简单 | 简单 | 中等 |

### 使用示例

#### 1. OCRmyPDF - PDF OCR 扫描

```bash
# 拉取镜像
docker pull ocrmypdf/ocrmypdf:latest

# 基本用法：为扫描版 PDF 添加 OCR 文本层
docker run --rm -i ocrmypdf/ocrmypdf -- - input.pdf output.pdf < input.pdf

# 从本地文件处理
docker run --rm -v $(pwd):/data ocrmypdf/ocrmypdf \
  --language chi_sim+eng \
  --deskew \
  --clean \
  /data/input.pdf \
  /data/output.pdf

# 参数说明：
# --language chi_sim+eng  支持中文+英文
# --deskew                 自动矫正倾斜
# --clean                  清理噪点
# --force-ocr              强制重新 OCR（即使已有文本层）
```

**OCRmyPDF 常用参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--language` | 指定语言 | `chi_sim+eng` (中英文) |
| `--deskew` | 矫正倾斜 | 自动检测并旋转 |
| `--clean` | 清理噪点 | 提高扫描质量 |
| `--force-ocr` | 强制 OCR | 重新处理已有文本 |
| `--skip-text` | 跳过文本页 | 仅处理扫描页 |
| `--jobs` | 并行处理 | `--jobs 4` |

#### 2. Tesseract OCR - 通用 OCR 引擎

```bash
# 拉取镜像
docker pull tesseractshadow/tesseract4re:latest

# 识别图片中的文字
docker run --rm -v $(pwd):/data tesseractshadow/tesseract4re \
  tesseract /data/image.png /data/output -l chi_sim+eng

# 输出格式
docker run --rm -v $(pwd):/data tesseractshadow/tesseract4re \
  tesseract /data/image.png /data/output \
  -l chi_sim+eng \
  --oem 1 \
  --psm 3

# 参数说明：
# -l chi_sim+eng    语言：中文简体+英文
# --oem 1           OCR Engine Mode: Neural net LSTM
# --psm 3           Page Segmentation Mode: 全自动分页
```

**Tesseract PSM 模式：**

| PSM | 模式说明 | 适用场景 |
|-----|---------|---------|
| 0 | 仅方向和脚本检测 | 检测文字方向 |
| 3 | 全自动分页 | 一般文档 |
| 6 | 单块文本 | 简单文本块 |
| 11 | 稀疏文本 | 随机分布文字 |
| 12 | 带 OSD 的稀疏文本 | 带方向检测 |

#### 3. PaddleOCR - 高精度中文 OCR

```bash
# 拉取镜像
docker pull paddlepaddle/paddleocr:latest

# 运行 PaddleOCR（需要进入容器）
docker run --rm -it -v $(pwd):/data paddlepaddle/paddleocr /bin/bash

# 在容器内执行
cd /data
python3 -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr('image.jpg', cls=True)
for idx in range(len(result)):
    res = result[idx]
    for line in res:
        print(line)
"

# 或使用命令行工具
paddleocr --image_dir /data/image.jpg \
  --use_angle_cls true \
  --lang ch \
  --use_gpu false
```

**PaddleOCR 优势：**
- ✅ 中文识别精度最高
- ✅ 支持倾斜文字检测
- ✅ 支持表格识别
- ✅ 支持印章检测
- ✅ 轻量级模型部署

### 集成到 NecoRAG

#### 方案 1：使用 OCRmyPDF 预处理

```python
import subprocess

def ocr_pdf(input_path: str, output_path: str):
    """使用 OCRmyPDF 处理 PDF"""
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.path.dirname(input_path)}:/data",
        "ocrmypdf/ocrmypdf",
        "--language", "chi_sim+eng",
        "--deskew",
        "--clean",
        f"/data/{os.path.basename(input_path)}",
        f"/data/{os.path.basename(output_path)}"
    ]
    subprocess.run(cmd, check=True)

# 在 NecoRAG 中使用
from src.perception import PerceptionEngine

engine = PerceptionEngine()

# 先 OCR 处理
ocr_pdf("scanned.pdf", "searchable.pdf")

# 再导入
engine.process_file("searchable.pdf")
```

#### 方案 2：使用 Tesseract 处理图片

```python
import docker

def ocr_image(image_path: str) -> str:
    """使用 Tesseract OCR 识别图片"""
    client = docker.from_env()
    
    output = client.containers.run(
        "tesseractshadow/tesseract4re",
        f"tesseract /data/{image_path} stdout -l chi_sim+eng",
        volumes={os.path.dirname(image_path): {'bind': '/data', 'mode': 'ro'}},
        remove=True
    )
    
    return output.decode('utf-8')

# 在 NecoRAG 中使用
text = ocr_image("document.png")
engine.process_text(text)
```

#### 方案 3：PaddleOCR 高精度识别

```python
from paddleocr import PaddleOCR

class PaddleOCRProcessor:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=False
        )
    
    def process_image(self, image_path: str) -> str:
        """处理图片并返回文本"""
        result = self.ocr.ocr(image_path, cls=True)
        
        # 提取所有文本
        text_lines = []
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                text_lines.append(line[1][0])
        
        return '\n'.join(text_lines)

# 在 NecoRAG 中使用
processor = PaddleOCRProcessor()
text = processor.process_image("document.jpg")
engine.process_text(text)
```

### 性能优化建议

#### 1. 批量处理

```bash
# OCRmyPDF 批量处理
for file in *.pdf; do
  docker run --rm -v $(pwd):/data ocrmypdf/ocrmypdf \
    --language chi_sim+eng \
    --jobs 4 \
    "/data/$file" "/data/ocr_$file"
done
```

#### 2. 并行处理

```python
from concurrent.futures import ThreadPoolExecutor

def batch_ocr(files: list, max_workers: int = 4):
    """并行 OCR 处理"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(ocr_image, files))
    return results
```

#### 3. 缓存机制

```python
import hashlib
import pickle

def ocr_with_cache(image_path: str, cache_dir: str = ".ocr_cache"):
    """带缓存的 OCR"""
    # 计算文件哈希
    with open(image_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    cache_file = f"{cache_dir}/{file_hash}.pkl"
    
    # 检查缓存
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    # 执行 OCR
    text = ocr_image(image_path)
    
    # 保存缓存
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'wb') as f:
        pickle.dump(text, f)
    
    return text
```

### 常见问题

#### Q1: OCR 识别率低怎么办？

**解决方案：**
1. 提高扫描分辨率（300 DPI 以上）
2. 使用图像预处理（去噪、二值化）
3. 选择合适的语言模型
4. 尝试不同的 OCR 引擎

```bash
# OCRmyPDF 图像增强
docker run --rm -v $(pwd):/data ocrmypdf/ocrmypdf \
  --clean --deskew --remove-background \
  /data/input.pdf /data/output.pdf
```

#### Q2: 处理速度慢怎么办？

**解决方案：**
1. 使用 `--jobs` 参数并行处理
2. 启用 GPU 加速（PaddleOCR）
3. 使用轻量级模型
4. 实现批量处理

#### Q3: 中文识别不准确？

**解决方案：**
1. 使用 PaddleOCR（中文精度最高）
2. 确保安装了中文语言包
3. 检查字体是否支持
4. 尝试不同的 PSM 模式

---

## 📊 镜像信息管理

### 查看所有镜像

```bash
# 列出所有相关镜像
docker images | grep -E "(redis|qdrant|neo4j|ollama|grafana)"
```

### 查看镜像详情

```bash
# 查看镜像详细信息
docker inspect redis:7-alpine

# 查看镜像历史层
docker history qdrant/qdrant:latest
```

### 镜像标签管理

```bash
# 给镜像打标签
docker tag redis:7-alpine necorag/redis:latest

# 删除标签
docker rmi necorag/redis:latest
```

---

## 🔗 相关资源

### 官方文档

- [Docker Hub](https://hub.docker.com/)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [Qdrant Docker](https://qdrant.tech/documentation/quickstart/)
- [Neo4j Docker](https://neo4j.com/docs/operations-manual/current/docker/)
- [Ollama Docker](https://github.com/ollama/ollama/blob/main/docs/docker.md)
- [Grafana Docker](https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/)

### 项目文档

- [部署快速参考](./deployment_quickref.md)
- [第三方系统详解](./third_party_systems.md)
- [选型指南](./selection_guide.md)
- [架构结构](./STRUCTURE.md)

---

## 📞 维护信息

**脚本作者**: NecoRAG DevOps Team  
**最后更新**: 2026-03-19  
**版本**: v3.2.0-alpha  
**兼容性**: Docker 20.10+, Docker Compose 2.0+

---

## ✨ 总结

通过本指南提供的脚本和文档，您可以：

✅ **一键导入** - 自动拉取所有必需的第三方镜像  
✅ **智能验证** - 快速检查镜像是否就绪  
✅ **灵活配置** - 支持必需和可选镜像选择  
✅ **故障排查** - 详细的错误处理和解决方案  
✅ **最佳实践** - 遵循业界标准的操作流程  
✅ **OCR 支持** - 支持图片、PDF、文档的 OCR 扫描识别  
✅ **全文搜索** - Elasticsearch 分布式搜索引擎与 Kibana 可视化  
✅ **AI 意图情感分析** - Hugging Face、BERT、TextBlob 多语言智能分析  
✅ **核心架构** - NecoRAG 完整技术栈 Docker 化  

### 核心能力

**必需镜像** (~9.9GB):
- Redis - L1 工作记忆与缓存
- Qdrant - L2 语义向量数据库
- Neo4j - L3 情景图谱数据库
- Ollama / vLLM - 本地 LLM 推理服务器（双引擎）
- RAGFlow - 深度文档解析引擎
- LangGraph - 编排引擎（状态机）
- Streamlit - 前端/可视化界面
- Grafana - 监控仪表盘

**可选镜像** (~20.5GB):
- **数据库备选** - Milvus, Memgraph
- **监控可视化** - Prometheus, Superset
- **OCR 文档扫描** - OCRmyPDF, Tesseract, PaddleOCR
- **全文搜索引擎** - Elasticsearch + Kibana + APM
- **AI 意图情感分析** - Hugging Face TGI + BERT + TextBlob

**NecoRAG 核心架构亮点**:
- 🔧 **完整技术栈** - 100% 覆盖官方推荐组件
- 📄 **RAGFlow** - 业界最强深度文档解析
- 🔄 **LangGraph** - 复杂循环状态机编排
- ⚡ **vLLM** - 高吞吐 LLM 推理（24 倍加速）
- 🎨 **Streamlit** - 快速构建演示界面
- 📊 **BGE-M3** - 多语言长文本嵌入
- 🎯 **BGE-Reranker** - 中文优化重排序
- 🐛 **一键启动** - Docker Compose 完整配置

**OCR 功能亮点**:
- 📄 支持 PDF、图片、文档 OCR
- 🌏 中英文多语言支持
- 🚀 三种 OCR 引擎可选
- 🔧 完整的集成示例
- 💡 性能优化建议

**Elasticsearch 功能亮点**:
- 🔍 分布式全文搜索引擎
- 📊 Kibana 数据可视化
- 📈 APM 应用性能监控
- 🐍 Python 客户端集成
- 🎯 混合搜索（语义 + 关键词）

**AI 意图情感分析功能亮点**:
- 🧠 Hugging Face 高性能推理服务
- 😊 中英文情感分析（正面/负面）
- 🎯 智能意图识别（6+ 种意图类型）
- 🌍 多语言自动检测和切换
- ⚡ 实时情感监控和趋势分析
- 🔀 基于意图的智能路由决策
- 🐛 完整的集成示例和优化建议

**下一步**: 运行 `./import_docker_images.sh` 开始导入！🚀
