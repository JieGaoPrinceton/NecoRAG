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

### 必需镜像（5 个）

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| **redis** | `7-alpine` | ~25MB | L1 工作记忆与缓存 | [链接](https://hub.docker.com/_/redis) |
| **qdrant/qdrant** | `latest` | ~500MB | L2 语义向量数据库 | [链接](https://hub.docker.com/r/qdrant/qdrant) |
| **neo4j** | `5-community` | ~1.2GB | L3 情景图谱数据库 | [链接](https://hub.docker.com/_/neo4j) |
| **ollama/ollama** | `latest` | ~2GB | 本地 LLM 推理服务器 | [链接](https://hub.docker.com/r/ollama/ollama) |
| **grafana/grafana** | `latest` | ~300MB | 监控仪表盘 | [链接](https://hub.docker.com/r/grafana/grafana) |

**总计大小**: ~4.2GB

### 可选镜像（按需选择）

| 镜像名称 | 版本 | 大小 | 用途 | Docker Hub |
|---------|------|------|------|-----------|
| milvusdb/milvus | `v3.0.0-alpha` | ~707MB | Milvus 向量数据库（备选） | [链接](https://hub.docker.com/r/milvusdb/milvus) |
| memgraph/memgraph | `latest` | ~203MB | Memgraph 图数据库（备选） | [链接](https://hub.docker.com/r/memgraph/memgraph) |
| prom/prometheus | `latest` | ~146MB | Prometheus 指标收集 | [链接](https://hub.docker.com/_/prometheus) |
| apache/superset | `latest` | ~643MB | Superset 数据可视化 | [链接](https://hub.docker.com/r/apache/superset) |

**可选镜像总计**: ~1.7GB

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
    "redis:3.0.0-alpha"           # 锁定具体版本
    "qdrant/qdrant:v3.0.0-alpha"         # 锁定具体版本
    "neo4j:3.0.0-alpha"       # 锁定具体版本
    "ollama/ollama:3.0.0-alpha"         # 锁定具体版本
    "grafana/grafana:3.0.0-alpha"       # 锁定具体版本
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
**版本**: v3.0.0-alpha  
**兼容性**: Docker 20.10+, Docker Compose 2.0+

---

## ✨ 总结

通过本指南提供的脚本和文档，您可以：

✅ **一键导入** - 自动拉取所有必需的第三方镜像  
✅ **智能验证** - 快速检查镜像是否就绪  
✅ **灵活配置** - 支持必需和可选镜像选择  
✅ **故障排查** - 详细的错误处理和解决方案  
✅ **最佳实践** - 遵循业界标准的操作流程  

**下一步**: 运行 `./import_docker_images.sh` 开始导入！🚀
