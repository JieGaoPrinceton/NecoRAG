#!/usr/bin/env bash
# NecoRAG Docker 环境停止脚本
# 用法:
#   ./scripts/stop.sh              # 停止所有服务
#   ./scripts/stop.sh --clean      # 停止并清理数据卷

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OPDEV_DIR="$(dirname "$SCRIPT_DIR")"
cd "$OPDEV_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🛑 停止 NecoRAG Docker 环境...${NC}"

if [ "$1" = "--clean" ]; then
    echo -e "${YELLOW}[WARNING] 将清理所有数据卷，此操作不可恢复！${NC}"
    read -p "确认继续？(y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker compose down -v --remove-orphans 2>/dev/null || true
        docker compose -f docker-compose.minimal.yml down -v --remove-orphans 2>/dev/null || true
        echo -e "${GREEN}[OK] 所有服务已停止，数据卷已清理${NC}"
    else
        echo -e "${YELLOW}[取消] 操作已取消${NC}"
    fi
else
    docker compose down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.minimal.yml down --remove-orphans 2>/dev/null || true
    echo -e "${GREEN}[OK] 所有服务已停止（数据卷已保留）${NC}"
fi
