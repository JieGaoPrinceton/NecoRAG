#!/usr/bin/env bash
# Ollama 模型拉取脚本

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODEL="${1:-qwen2:7b}"

echo -e "${CYAN}🤖 拉取 LLM 模型: $MODEL${NC}"

if ! docker ps --format '{{.Names}}' | grep -q necorag-ollama; then
    echo -e "${YELLOW}[INFO] Ollama 容器未运行，尝试启动...${NC}"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$(dirname "$SCRIPT_DIR")"
    docker compose --profile llm up -d ollama
    sleep 5
fi

docker exec -it necorag-ollama ollama pull "$MODEL"
echo -e "${GREEN}[OK] 模型 $MODEL 拉取完成${NC}"
echo ""
echo "可用模型列表:"
docker exec necorag-ollama ollama list
