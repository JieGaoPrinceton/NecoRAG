# NecoRAG Docker 脚本

**Docker Image Management Scripts**

版本：v3.2.0-alpha  
更新日期：2026-03-19

---

## 📋 目录

- [快速开始](#快速开始)
- [脚本说明](#脚本说明)
- [镜像列表](#镜像列表)
- [故障排查](#故障排查)

---

## 🚀 快速开始

### 一键导入所有镜像

```bash
# 进入 docker_scripts 目录
cd 3rd/docker_scripts

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

---

## 📜 脚本说明

### 1. import_docker_images.sh

**功能**: 一键导入所有必需和可选的 Docker 镜像

**特性**:
- ✅ 自动检测网络环境，选择最优镜像源
- ✅ 支持交互式选择镜像组合
- ✅ 精确计算所需磁盘空间
- ✅ 详细的进度条和状态提示
- ✅ 错误重试机制

**使用方法**:
```bash
./import_docker_images.sh

# 输出示例:
# ============================================================
#   NecoRAG Docker 镜像导入工具
# ============================================================
# 
# 请选择要下载的镜像:
#   1) 仅下载必需镜像 (~4.03GB)
#   2) 下载全部镜像 (必需 + 可选，~5.68GB)
#   3) 自定义选择
# 
# 请输入选项 (1/2/3): _
```

**镜像列表**:

#### 必需镜像（9 个，~9.9GB）

| 镜像名称 | 版本 | 大小 | 用途 |
|---------|------|------|------|
| redis | 7-alpine | ~25MB | L1 工作记忆与缓存 |
| qdrant/qdrant | latest | ~500MB | L2 语义向量数据库 |
| neo4j | 5-community | ~1.2GB | L3 情景图谱数据库 |
| ollama/ollama | latest | ~2GB | 本地 LLM 推理服务器 |
| vllm/vllm-openai | latest | ~3GB | 高吞吐 LLM 推理服务 |
| infiniflow/ragflow | latest | ~1.5GB | 深度文档解析引擎 |
| langchain/langgraph | latest | ~800MB | 编排引擎（状态机） |
| streamlit/streamlit | latest | ~600MB | 前端可视化界面 |
| grafana/grafana | latest | ~300MB | 监控可视化面板 |

#### 可选镜像（6 个，~3.5GB）

| 镜像名称 | 版本 | 大小 | 用途 |
|---------|------|------|------|
| milvusdb/milvus | v3.2.0-alpha | ~707MB | Milvus 向量数据库（备选） |
| memgraph/memgraph | latest | ~203MB | Memgraph 图数据库（备选） |
| prom/prometheus | latest | ~146MB | Prometheus 指标收集 |
| apache/superset | latest | ~643MB | Superset 数据可视化 |
| elasticsearch/elasticsearch | 8.11.0 | ~1.8GB | Elasticsearch 全文搜索 |
| kibana/kibana | 8.11.0 | ~1.2GB | Kibana 可视化仪表盘 |

**总计**:
- 必需镜像：~9.9GB
- 可选镜像：~3.5GB
- 全部镜像：~13.4GB

### 2. verify_docker_images.sh

**功能**: 验证已下载镜像的完整性和版本

**检查项目**:
- ✅ 镜像是否存在
- ✅ 镜像版本号是否正确
- ✅ 镜像大小是否在合理范围
- ✅ 镜像架构是否匹配

**使用方法**:
```bash
./verify_docker_images.sh

# 输出示例:
# ============================================================
#   NecoRAG Docker 镜像验证工具
# ============================================================
# 
# ✅ redis:7-alpine - 存在且版本正确 (25 MB)
# ✅ qdrant/qdrant:latest - 存在 (500 MB)
# ⚠️  neo4j:5-community - 版本不匹配 (期望：5-community, 实际：latest)
# ❌ ollama/ollama:latest - 镜像不存在
# 
# 验证完成：8/10 通过
```

---

## 🔧 故障排查

### Q1: 下载速度慢

**解决方案**: 使用国内镜像源

```bash
# 编辑脚本，修改 DOCKER_REGISTRY 变量
export DOCKER_REGISTRY="registry.cn-hangzhou.aliyuncs.com"

# 或者手动指定镜像源
./import_docker_images.sh --registry registry.cn-hangzhou.aliyuncs.com
```

### Q2: 磁盘空间不足

**检查磁盘空间**:
```bash
df -h /var/lib/docker
```

**清理未使用的镜像**:
```bash
docker image prune -a --filter "until=24h"
```

**选择性下载**:
```bash
# 只下载必需镜像
./import_docker_images.sh --minimal
```

### Q3: 架构不匹配

**查看当前系统架构**:
```bash
uname -m
# x86_64 = AMD64
# arm64 = Apple Silicon (M1/M2)
```

**指定平台下载**:
```bash
docker pull --platform linux/amd64 redis:7-alpine
```

### Q4: 验证失败

**查看详细错误**:
```bash
./verify_docker_images.sh --verbose
```

**手动验证单个镜像**:
```bash
docker inspect redis:7-alpine
docker history redis:7-alpine
```

---

## 📊 镜像大小查询历史

### 第一次查询（2026-03-19）

**查询结果**:
- redis:7-alpine: ~25MB
- qdrant/qdrant:latest: ~500MB
- neo4j:5-community: ~1.2GB
- ollama/ollama:latest: ~2GB
- grafana/grafana:latest: ~300MB

**总计**: ~4.03GB（必需镜像）

### 第二次查询（2026-03-19）

**新增查询**:
- milvusdb/milvus:v3.2.0-alpha: ~707MB
- memgraph/memgraph:latest: ~203MB
- prom/prometheus:latest: ~146MB
- apache/superset:latest: ~643MB

**更新后总计**: ~5.68GB（全部镜像）

---

## 📚 相关文档

- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Docker 部署详细指南
- [TECH_STACK.md](../TECH_STACK.md) - 技术栈详解
- [README.md](../README.md) - 文档索引

---

## 🔄 更新日志

### v3.2.0-alpha (2026-03-19)

**新增功能**:
- ✅ 交互式镜像选择菜单
- ✅ 精确的容量计算
- ✅ 磁盘空间检查
- ✅ 智能镜像源路由

**改进**:
- ✅ 优化下载速度（自动选择最优镜像源）
- ✅ 增强错误处理（重试机制）
- ✅ 改善用户体验（进度条、颜色提示）

---

<div align="center">

**Let's make AI think like a brain!** 🧠

[NecoRAG Team](https://github.com/NecoRAG)

</div>
