#!/usr/bin/env bash
# NecoRAG 服务状态检查

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPDEV_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OPDEV_DIR"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║     🧠 NecoRAG 服务状态检查              ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 服务检测函数
check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✔${NC} $name"
    else
        echo -e "  ${RED}✘${NC} $name"
    fi
}

echo "Docker 容器状态:"
docker compose ps 2>/dev/null || echo "  (无运行中的容器)"

echo ""
echo "服务连通性检查:"
check_service "Redis        (localhost:6379)" "redis://localhost:6379" 2>/dev/null || \
    (redis-cli -p 6379 ping > /dev/null 2>&1 && echo -e "  ${GREEN}✔${NC} Redis        (localhost:6379)" || echo -e "  ${RED}✘${NC} Redis        (localhost:6379)")
check_service "Qdrant       (localhost:6334)" "http://localhost:6334/"
check_service "Neo4j        (localhost:7474)" "http://localhost:7474/"
check_service "Ollama       (localhost:11434)" "http://localhost:11434/api/tags"
check_service "Grafana      (localhost:3000)" "http://localhost:3000/"
check_service "NecoRAG App  (localhost:8000)" "http://localhost:8000/api/stats"

echo ""
echo "数据卷:"
docker volume ls --filter name=necorag 2>/dev/null | tail -n +2 || echo "  (无数据卷)"
