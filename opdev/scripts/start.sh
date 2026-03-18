#!/usr/bin/env bash
# NecoRAG Docker 环境启动脚本
# 用法:
#   ./scripts/start.sh              # 启动全部服务
#   ./scripts/start.sh dev          # 仅启动后台服务（开发模式）
#   ./scripts/start.sh minimal      # 仅启动核心存储（Redis + Qdrant）
#   ./scripts/start.sh --with-llm   # 全部服务 + LLM

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPDEV_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OPDEV_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║     🧠 NecoRAG Docker 环境管理器         ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}[INFO] 未找到 .env 文件，从模板创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}[OK] .env 文件已创建，请根据需要修改配置${NC}"
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] 未检测到 Docker，请先安装 Docker Desktop${NC}"
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker 服务未运行，请启动 Docker Desktop${NC}"
    exit 1
fi

MODE="${1:-full}"

case "$MODE" in
    dev)
        echo -e "${GREEN}[启动模式] 开发模式 - 仅后台服务${NC}"
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        echo ""
        echo -e "${GREEN}后台服务已启动:${NC}"
        echo "  Redis:    localhost:${REDIS_PORT:-6379}"
        echo "  Qdrant:   localhost:${QDRANT_HTTP_PORT:-6334}"
        echo "  Neo4j:    localhost:${NEO4J_HTTP_PORT:-7474} (Browser)"
        echo "            localhost:${NEO4J_BOLT_PORT:-7687} (Bolt)"
        echo ""
        echo -e "${YELLOW}请在本地运行 NecoRAG 应用:${NC}"
        echo "  cd .. && python tools/start_dashboard.py"
        ;;
    minimal)
        echo -e "${GREEN}[启动模式] 最小模式 - Redis + Qdrant${NC}"
        docker compose -f docker-compose.minimal.yml up -d
        echo ""
        echo -e "${GREEN}核心服务已启动:${NC}"
        echo "  Redis:    localhost:6379"
        echo "  Qdrant:   localhost:6334"
        ;;
    --with-llm|llm)
        echo -e "${GREEN}[启动模式] 全部服务 + LLM${NC}"
        docker compose --profile llm up -d
        echo ""
        echo -e "${GREEN}所有服务已启动（含 Ollama LLM）${NC}"
        echo ""
        echo -e "${YELLOW}[提示] 请拉取 LLM 模型:${NC}"
        echo "  docker exec -it necorag-ollama ollama pull qwen2:7b"
        ;;
    full|"")
        echo -e "${GREEN}[启动模式] 完整模式 - 全部服务${NC}"
        docker compose up -d
        echo ""
        echo -e "${GREEN}所有服务已启动:${NC}"
        echo "  NecoRAG:  http://localhost:${NECORAG_PORT:-8000}"
        echo "  Redis:    localhost:${REDIS_PORT:-6379}"
        echo "  Qdrant:   localhost:${QDRANT_HTTP_PORT:-6334}"
        echo "  Neo4j:    http://localhost:${NEO4J_HTTP_PORT:-7474}"
        echo "  Grafana:  http://localhost:${GRAFANA_PORT:-3000}"
        ;;
    *)
        echo -e "${RED}未知模式: $MODE${NC}"
        echo "用法: $0 [dev|minimal|full|--with-llm]"
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}查看服务状态: docker compose ps${NC}"
echo -e "${CYAN}查看日志:     docker compose logs -f [服务名]${NC}"
echo -e "${CYAN}停止服务:     ./scripts/stop.sh${NC}"
