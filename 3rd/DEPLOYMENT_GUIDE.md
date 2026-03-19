# NecoRAG 部署指南

**Quick Reference: Deployment Configuration**

版本：v3.3.0-alpha  
更新日期：2026-03-19

---

## 📋 目录

- [快速开始](#快速开始)
- [一键启动脚本](#一键启动脚本)
- [各组件独立部署](#各组件独立部署)
- [配置文件模板](#配置文件模板)
- [端口速查](#端口速查)
- [故障排查](#故障排查)

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
chmod +x verify_docker_images.sh
./verify_docker_images.sh
```

### Docker Compose 快速启动

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f necorag
```

---

## 🎛️ 一键启动脚本

### 开发环境（全部组件）

```bash
#!/bin/bash
# scripts/start-dev.sh

set -e

echo "🚀 Starting NecoRAG Development Environment..."

# 创建必要目录
mkdir -p data/{redis,qdrant,neo4j,ollama,ragflow}
mkdir -p logs/{necorag,ollama,qdrant,neo4j}
mkdir -p models/{bge-m3,reranker,rasa}

# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 等待服务就绪
echo "⏳ Waiting for services to be ready..."
sleep 30

# 检查服务状态
echo "📊 Service Status:"
docker-compose -f docker-compose.dev.yml ps

# 拉取 Ollama 模型
echo "📥 Pulling Ollama model..."
docker exec ollama ollama pull llama3

echo "✅ All services started successfully!"
echo ""
echo "📍 Access Points:"
echo "   - NecoRAG API:    http://localhost:8000"
echo "   - Ollama:         http://localhost:11434"
echo "   - Qdrant:         http://localhost:6333"
echo "   - Neo4j Browser:  http://localhost:7474"
echo "   - Grafana:        http://localhost:3000 (admin/admin)"
echo "   - Prometheus:     http://localhost:9090"
```

### 生产环境（优化配置）

```bash
#!/bin/bash
# scripts/start-prod.sh

set -e

echo "🚀 Starting NecoRAG Production Environment..."

# 设置资源限制
export OLLAMA_NUM_GPU=1
export OLLAMA_MAX_VRAM=24GB
export QDRANT_MAX_MEMORY=8GB
export NEO4J_HEAP_MAX=4G

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 健康检查
echo "🏥 Running health checks..."

check_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Checking $name..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            echo " ✅"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo " ❌"
    return 1
}

check_service "NecoRAG" "http://localhost:8000/health"
check_service "Ollama" "http://localhost:11434/api/tags"
check_service "Qdrant" "http://localhost:6333/"
check_service "Neo4j" "bolt://localhost:7687"

echo "✅ Production environment started!"
```

### 最小化部署（资源受限）

```bash
#!/bin/bash
# scripts/start-minimal.sh

echo "🪶 Starting NecoRAG Minimal Environment..."

# 仅启动必要服务
docker-compose -f docker-compose.minimal.yml up -d

# 使用 CPU 模式（无 GPU）
export OLLAMA_NUM_GPU=0

echo "✅ Minimal environment started (CPU-only mode)"
echo ""
echo "⚠️  Note: Performance will be limited"
echo "   Recommended for: Development & Testing only"
```

---

## 💾 各组件独立部署

### 1. Ollama（LLM 推理）

#### Docker 部署

```bash
# 基础部署
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest

# GPU 加速（NVIDIA）
docker run -d \
  --gpus all \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  -e OLLAMA_KEEP_ALIVE=24h \
  ollama/ollama:latest

# 拉取模型
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull nomic-embed-text  # 嵌入模型

# 查看模型列表
docker exec -it ollama ollama list
```

#### Kubernetes 部署

```yaml
# k8s/ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: 24Gi
          requests:
            nvidia.com/gpu: 1
            memory: 16Gi
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ollama-service
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
  type: ClusterIP
```

### 2. Qdrant（向量数据库）

#### Docker 部署

```bash
# 单机版
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  -v qdrant_logs:/qdrant/logs \
  -e QDRANT__SERVICE__GRPC_PORT=6334 \
  qdrant/qdrant:latest

# 集群版（3 节点）
# 节点 1
docker run -d \
  --name qdrant-node-1 \
  -p 6333:6333 \
  -p 6335:6335 \
  -v ./node1:/qdrant/storage \
  -e QDRANT__CLUSTER__ENABLED=true \
  -e QDRANT__CLUSTER__P2P__PORT=6335 \
  qdrant/qdrant:latest

# 加入集群
curl -X POST http://localhost:6336/cluster/raft/join \
  -H "Content-Type: application/json" \
  -d '{"peer_id": 2, "uri": "http://qdrant-node-2:6335"}'
```

#### 性能调优

```yaml
# qdrant_config.yaml
log_level: INFO

storage:
  storage_path: /qdrant/storage
  
  # 性能优化
  performance:
    max_search_threads: 8
    max_optimization_threads: 4
  
  # HNSW 索引
  hnsw_index:
    m: 16
    ef_construct: 100
    full_scan_threshold: 10000

service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334
```

### 3. Neo4j（图数据库）

#### Docker 部署

```bash
# 社区版
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  -e NEO4J_AUTH=neo4j/necorag_password \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  -e NEO4J_dbms_memory_pagecache_size=2G \
  neo4j:5-community
```

#### APOC 插件安装

```bash
# 下载 APOC 插件
wget https://github.com/neo4j/apoc/releases/download/5.x/apoc-5.x.jar \
  -P $(docker inspect neo4j --format='{{range .Mounts}}{{if eq .Destination "/plugins"}}{{.Source}}{{end}}{{end}}')

# 启用 APOC
docker exec neo4j sh -c 'echo "dbms.security.procedures.unrestricted=apoc.*" >> /var/lib/neo4j/conf/neo4j.conf'

# 重启容器
docker restart neo4j

# 验证安装
cypher-shell -u neo4j -p necorag_password \
  "RETURN apoc.version()"
```

### 4. Redis（工作记忆）

#### Docker 部署

```bash
# 基础部署
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --maxmemory 2gb

# 高可用部署（Sentinel）
# Master
docker run -d \
  --name redis-master \
  -p 6379:6379 \
  redis:7-alpine

# Slave
docker run -d \
  --name redis-slave \
  -p 6380:6379 \
  --link redis-master:redis-master \
  redis:7-alpine \
  redis-server --slaveof redis-master 6379
```

### 5. RAGFlow（文档解析）

#### Docker 部署

```bash
# 完整部署（依赖 MySQL + MinIO）
docker-compose up -d ragflow mysql minio

# 单独部署 RAGFlow（已有后端存储）
docker run -d \
  --name ragflow \
  -p 9380:9380 \
  -v ragflow_data:/var/lib/ragflow \
  -e RAGFLOW_HOST=0.0.0.0 \
  -e MYSQL_URL=mysql://user:pass@mysql:3306/ragflow \
  -e MINIO_URL=http://minio:9000 \
  infiniflow/ragflow:latest
```

### 6. Rasa NLU（意图识别）

#### Docker 部署

```bash
# 训练模型
docker run -it \
  --name rasa-train \
  -v $(pwd)/intent:/app/intent \
  -v $(pwd)/models:/app/models \
  rasa/rasa:latest train

# 运行服务
docker run -d \
  --name rasa \
  -p 5005:5005 \
  -v $(pwd)/models:/app/models \
  rasa/rasa:latest run \
    --enable-api \
    --cors "*" \
    --model /app/models/latest.tar.gz

# 测试意图识别
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "什么是深度学习？"}'
```

---

## ⚙️ 配置文件模板

### .env 完整配置

```bash
# ==================== 全局配置 ====================
ENVIRONMENT=development  # development/production
LOG_LEVEL=INFO           # DEBUG/INFO/WARNING/ERROR
DEBUG=false

# ==================== LLM 配置 ====================
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# OpenAI 备用
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-api-key
# OPENAI_MODEL=gpt-4-turbo-preview

# vLLM 配置
# LLM_PROVIDER=vllm
# VLLM_BASE_URL=http://localhost:8000/v1
# VLLM_MODEL=meta-llama/Llama-3-70b-Instruct

# ==================== 向量模型配置 ====================
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda       # cpu/cuda/mps
EMBEDDING_BATCH_SIZE=16
EMBEDDING_FP16=true

# ==================== 重排序配置 ====================
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=cuda
RERANK_TOP_K=5

# ==================== Redis 配置 ====================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_TTL=3600              # 秒
REDIS_MAXMEMORY=2gb

# ==================== Qdrant 配置 ====================
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_COLLECTION=semantic_memory
QDRANT_VECTOR_SIZE=1024
QDRANT_DISTANCE=Cosine

# ==================== Neo4j 配置 ====================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=necorag_password
NEO4J_DATABASE=neo4j

# ==================== MySQL 配置 ====================
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=ragflow

# ==================== MinIO 配置 ====================
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents

# ==================== Rasa 配置 ====================
INTENT_PROVIDER=rasa
RASA_ENDPOINT=http://localhost:5005/model/parse
RASA_CONFIDENCE_THRESHOLD=0.7

# ==================== RAGFlow 配置 ====================
RAGFLOW_ENABLED=true
RAGFLOW_ENDPOINT=http://localhost:9380/api/v1
RAGFLOW_API_KEY=your_api_key_here

# ==================== OCR 配置 ====================
OCR_ENABLED=true
OCR_PROVIDER=paddleocr
PADDLEOCR_ENDPOINT=http://localhost:8003/ocr

# ==================== 任务调度配置 ====================
SCHEDULER_TYPE=apscheduler    # apscheduler/celery
CELERY_BROKER=redis://localhost:6379/0
CELERY_BACKEND=redis://localhost:6379/1

# ==================== 监控配置 ====================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_URL=http://localhost:3000
GRAFANA_ADMIN_PASSWORD=admin

# ==================== 性能调优配置 ====================
MAX_CONCURRENT_QUERIES=100
QUERY_TIMEOUT_SECONDS=30
EMBEDDING_CACHE_SIZE=10000
EMBEDDING_CACHE_TTL=86400

# ==================== 安全配置 ====================
API_KEY_HEADER=X-API-Key
API_KEY=your_secret_api_key
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
ALLOWED_HOSTS=["*"]
```

### Docker Compose 模板

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ==================== NecoRAG Core ====================
  necorag:
    build:
      context: .
      dockerfile: Dockerfile
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
    networks:
      - necorag-network
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  # ==================== AI Services ====================
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
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
    networks:
      - necorag-network

  bge-m3:
    image: xhluca/bge-m3:latest
    container_name: bge-m3
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
    networks:
      - necorag-network

  reranker:
    image: flagembedding/bge-reranker:latest
    container_name: reranker
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
    networks:
      - necorag-network

  rasa:
    image: rasa/rasa:latest
    container_name: rasa
    ports:
      - "5005:5005"
    volumes:
      - ./intent:/app/intent
      - ./models/rasa:/app/models
    command: run --enable-api --cors "*"
    networks:
      - necorag-network

  # ==================== Storage Services ====================
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - necorag-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    networks:
      - necorag-network

  neo4j:
    image: neo4j:5-community
    container_name: neo4j
    ports:
      - "7687:7687"
      - "7474:7474"
    environment:
      - NEO4J_AUTH=neo4j/necorag_password
      - NEO4J_dbms_memory_heap_max__size=4G
      - NEO4J_dbms_memory_pagecache_size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - necorag-network

  # ==================== Monitoring ====================
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
    networks:
      - necorag-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - necorag-network

networks:
  necorag-network:
    driver: bridge

volumes:
  ollama_data:
  redis_data:
  qdrant_storage:
  neo4j_data:
  neo4j_logs:
  prometheus_data:
  grafana_data:
```

---

## 🔌 端口速查表

| 服务 | 端口 | 协议 | 说明 |
|-----|------|------|------|
| **NecoRAG** | 8000 | HTTP | RESTful API |
| **Ollama** | 11434 | HTTP | LLM 推理 API |
| **BGE-M3** | 8001 | HTTP | 向量化 API |
| **Reranker** | 8002 | HTTP | 重排序 API |
| **Rasa** | 5005 | HTTP | 意图识别 API |
| **PaddleOCR** | 8003 | HTTP | OCR API |
| **Redis** | 6379 | TCP | 工作记忆 |
| **Qdrant** | 6333 | HTTP | REST API |
| **Qdrant gRPC** | 6334 | gRPC | gRPC API |
| **Neo4j Bolt** | 7687 | Bolt | Cypher 查询 |
| **Neo4j Browser** | 7474 | HTTP | Web UI |
| **MySQL** | 3306 | TCP | 元数据存储 |
| **MinIO** | 9000 | HTTP | S3 兼容对象存储 |
| **MinIO Console** | 9001 | HTTP | 管理控制台 |
| **Prometheus** | 9090 | HTTP | 指标采集 |
| **Grafana** | 3000 | HTTP | 可视化面板 |
| **RAGFlow** | 9380 | HTTP | 文档解析 API |

---

## 🌍 环境变量速查表

### LLM 相关
```bash
LLM_PROVIDER=ollama|openai|vllm
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4-turbo-preview
VLLM_BASE_URL=http://localhost:8000/v1
```

### 存储相关
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 模型相关
```bash
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cuda
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=cuda
```

### 性能相关
```bash
MAX_CONCURRENT_QUERIES=100
QUERY_TIMEOUT=30
EMBEDDING_CACHE_SIZE=10000
REDIS_MAXMEMORY=2gb
```

---

## 🔧 故障排查命令

### Docker 相关
```bash
# 查看所有容器状态
docker ps -a

# 查看容器日志
docker logs <container_name>
docker logs -f <container_name>  # 实时查看

# 进入容器调试
docker exec -it <container_name> bash

# 重启容器
docker restart <container_name>

# 查看容器资源使用
docker stats

# 清理未使用的容器
docker system prune -a
```

### Redis 诊断
```bash
# 连接 Redis
redis-cli -h localhost -p 6379

# 查看内存使用
INFO memory

# 查看命中率
INFO stats | grep keyspace

# 查看所有 Key
KEYS *

# 查看某个 Key 的 TTL
TTL <key_name>

# 慢查询监控
SLOWLOG GET 10
```

### Qdrant 诊断
```bash
# 查看集合列表
curl http://localhost:6333/collections

# 查看集合信息
curl http://localhost:6333/collections/semantic_memory

# 查看集群状态
curl http://localhost:6333/cluster

# 测试检索
curl -X POST http://localhost:6333/collections/semantic_memory/query \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 10
  }'
```

### Neo4j 诊断
```bash
# 连接 Neo4j
cypher-shell -u neo4j -p password

# 查看节点数量
MATCH (n) RETURN count(n);

# 查看关系数量
MATCH ()-[r]->() RETURN count(r);

# 查看数据库大小
CALL dbms.overview();

# 查看慢查询
SHOW TRANSACTIONS;

# 清空数据库（慎用！）
MATCH (n) DETACH DELETE n;
```

### Ollama 诊断
```bash
# 查看模型列表
curl http://localhost:11434/api/tags

# 测试生成
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3", "prompt": "Hello"}'

# 测试嵌入
curl http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "Hello"}'

# 查看日志
docker logs ollama
```

### 性能监控
```bash
# 查看系统负载
top
htop

# 查看 GPU 使用
nvidia-smi

# 查看磁盘 IO
iotop

# 查看网络流量
iftop

# 查看端口占用
netstat -tulpn | grep <port>
lsof -i :<port>
```

---

## 🏥 健康检查脚本

```bash
#!/bin/bash
# scripts/health-check.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_http() {
    local name=$1
    local url=$2
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is DOWN"
        return 1
    fi
}

check_tcp() {
    local name=$1
    local port=$2
    
    if nc -zv localhost $port 2>&1 | grep -q "succeeded"; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is DOWN"
        return 1
    fi
}

echo "🏥 NecoRAG Health Check"
echo "======================"
echo ""

# HTTP 检查
check_http "NecoRAG API" "http://localhost:8000/health"
check_http "Ollama" "http://localhost:11434/api/tags"
check_http "Qdrant" "http://localhost:6333/"
check_http "Neo4j Browser" "http://localhost:7474"
check_http "Grafana" "http://localhost:3000"
check_http "Prometheus" "http://localhost:9090"

# TCP 检查
check_tcp "Redis" 6379
check_tcp "Neo4j Bolt" 7687
check_tcp "MySQL" 3306
check_tcp "MinIO" 9000

echo ""
echo "Health check completed!"
```

---

## 📚 总结

本部署指南提供了 NecoRAG 第三方系统部署的**快速参考**:

✅ **一键启动脚本**: 开发/生产/最小化三种模式  
✅ **独立部署指南**: 每个组件的详细部署步骤  
✅ **配置文件模板**: .env 和 docker-compose.yml 完整示例  
✅ **端口速查表**: 所有服务的端口号一览  
✅ **环境变量速查**: 常用配置参数快速查找  
✅ **故障排查命令**: Docker/Redis/Qdrant/Neo4j 诊断命令  

建议将此文档保存为 PDF，方便运维时快速查阅!

---

<div align="center">

**Let's make AI think like a brain!** 🧠

[NecoRAG Team](https://github.com/NecoRAG)

</div>
