# 🚀 NecoRAG 部署与运维目录

## 📋 目录说明

本目录包含 NecoRAG 项目的部署配置、运维脚本和 DevOps 相关资源。

## 📁 文件结构

```
devops/
├── docker-compose.yml           # Docker Compose 主配置文件
├── docker-compose.dev.yml       # 开发环境配置
├── docker-compose.minimal.yml   # 最小化部署配置
├── Dockerfile                   # Docker 镜像构建文件
├── .env.example                 # 环境变量示例
├── .dockerignore                # Docker 忽略文件
├── configs/                     # 配置文件目录
│   ├── grafana/                 # Grafana 监控配置
│   └── redis/                   # Redis 配置
└── scripts/                     # 运维脚本
    ├── start.sh                 # 启动脚本
    ├── stop.sh                  # 停止脚本
    ├── status.sh                # 状态检查
    └── pull-model.sh            # 模型拉取脚本
```

## 🔧 配置文件

### Docker Compose 配置

#### 1. [docker-compose.yml](./docker-compose.yml) - 生产环境配置
**用途**: 完整的生产环境部署配置

**包含服务**:
- `necorag-app`: NecoRAG 应用服务
- `qdrant`: 向量数据库
- `neo4j`: 图数据库
- `redis`: 缓存和工作记忆
- `grafana`: 监控仪表盘
- `prometheus`: 指标收集

**启动命令**:
```bash
docker-compose up -d
```

#### 2. [docker-compose.dev.yml](./docker-compose.dev.yml) - 开发环境配置
**用途**: 本地开发和测试

**特性**:
- 代码热重载
- 详细日志输出
- 调试端口开放

**启动命令**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### 3. [docker-compose.minimal.yml](./docker-compose.minimal.yml) - 最小化配置
**用途**: 资源受限环境或快速测试

**包含服务**:
- 仅包含核心服务（App + Qdrant + Redis）
- 不包含图数据库和监控系统

**启动命令**:
```bash
docker-compose -f docker-compose.minimal.yml up -d
```

### Dockerfile

**基础镜像**: Python 3.11-slim  
**大小**: ~1.2GB（完整依赖）

**构建阶段**:
1. 安装系统依赖
2. 创建虚拟环境
3. 安装 Python 依赖
4. 复制项目文件
5. 配置入口点

**构建命令**:
```bash
docker build -t necorag:latest -f Dockerfile .
```

### 环境变量

#### [.env.example](./.env.example)
**用途**: 环境变量模板

**关键变量**:
```bash
# 应用配置
APP_ENV=production
APP_PORT=8000
LOG_LEVEL=INFO

# 数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
NEO4J_URI=bolt://localhost:7687
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM 配置
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-3.5-turbo

# 安全配置
JWT_SECRET=your-secret-key
AUTH_ENABLED=true
```

**使用方法**:
```bash
cp .env.example .env
# 编辑 .env 文件填入实际值
```

## 🛠️ 运维脚本

### [scripts/start.sh](./scripts/start.sh)
**功能**: 一键启动所有服务

**用法**:
```bash
./devops/scripts/start.sh
# 或指定环境
./devops/scripts/start.sh dev
```

### [scripts/stop.sh](./scripts/stop.sh)
**功能**: 优雅停止所有服务

**用法**:
```bash
./devops/scripts/stop.sh
```

### [scripts/status.sh](./scripts/status.sh)
**功能**: 检查服务运行状态

**输出**:
- 容器状态
- 端口占用情况
- 健康检查状态

**用法**:
```bash
./devops/scripts/status.sh
```

### [scripts/pull-model.sh](./scripts/pull-model.sh)
**功能**: 拉取 AI 模型

**支持的模型**:
- BGE-M3（向量化模型）
- BGE-Reranker-v2（重排序模型）
- 其他开源模型

**用法**:
```bash
./devops/scripts/pull-model.sh bge-m3
```

## 📊 监控配置

### Grafana 配置

**位置**: `configs/grafana/provisioning/datasources/`

**预置仪表盘**:
1. **系统监控**: CPU、内存、磁盘使用率
2. **应用性能**: 请求延迟、吞吐量、错误率
3. **知识库健康**: 健康分数、增长趋势、更新频率
4. **用户行为**: 查询分布、活跃时段、满意度

**访问**: `http://localhost:3000`

### Prometheus 配置

**指标收集**:
- HTTP 请求指标
- 数据库查询性能
- 缓存命中率
- 队列长度
- 自定义业务指标

**端点**: `/metrics`

## 🔐 安全配置

### 网络安全
- 容器网络隔离
- 端口暴露控制
- HTTPS/TLS 支持

### 认证授权
- JWT Token 认证
- RBAC 权限管理
- API Key 管理

### 数据安全
- 敏感数据加密存储
- 传输层加密
- 备份策略

## 📦 部署模式

### 1. 单机部署
**适用**: 开发测试、小规模使用

**配置**:
```bash
docker-compose -f docker-compose.yml up -d
```

### 2. 集群部署
**适用**: 生产环境、高可用需求

**工具**: 
- Kubernetes
- Docker Swarm

**配置**: 参考 `k8s/` 目录（单独维护）

### 3. 云部署
**适用**: 弹性扩展需求

**支持平台**:
- AWS ECS/EKS
- Azure Container Instances
- 阿里云 ACK

## 🔧 故障排查

### 常见问题

#### 1. 容器无法启动
```bash
# 查看日志
docker-compose logs -f app

# 检查配置
docker-compose config
```

#### 2. 端口冲突
```bash
# 查看端口占用
lsof -i :8000

# 修改端口
export APP_PORT=8080
```

#### 3. 数据库连接失败
```bash
# 检查网络
docker network ls

# 测试连接
docker-compose exec app python -c "from src.core import protocols; print('OK')"
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f app

# 最近 100 行
docker-compose logs --tail=100 app
```

## 📈 性能优化

### 1. 资源限制
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### 2. 缓存优化
- Redis 缓存热点数据
- HNSW 索引加速检索
- CDN 静态资源

### 3. 数据库调优
- Qdrant 分片配置
- Neo4j 内存优化
- Redis 持久化策略

## 🔄 持续集成

### GitHub Actions
**位置**: `.github/workflows/`

**工作流**:
- CI 测试
- Docker 镜像构建
- 自动部署

### 构建流水线
```
代码提交 → 单元测试 → 集成测试 → 镜像构建 → 推送仓库 → 自动部署
```

## 📞 维护信息

**负责人**: DevOps Team  
**最后更新**: 2026-03-19  
**文档状态**: ✅ 持续维护中

## 🔗 相关链接

- [项目主文档](../README.md)
- [部署指南](../docs/wiki/部署与运维/快速开始.md)
- [监控手册](../docs/wiki/部署与运维/监控告警系统.md)

---

*良好的部署和运维是系统稳定运行的保障。请定期检查和更新此目录下的配置文件。*
