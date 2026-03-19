#!/bin/bash
# NecoRAG Docker 镜像验证脚本
# Docker Images Verification Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo "============================================================"
echo "  NecoRAG Docker 镜像验证工具"
echo "============================================================"
echo ""

# 必需镜像列表
declare -A REQUIRED_IMAGES=(
    ["redis:7-alpine"]="L1 工作记忆与缓存"
    ["qdrant/qdrant:latest"]="L2 语义向量数据库"
    ["neo4j:5-community"]="L3 情景图谱数据库"
    ["ollama/ollama:latest"]="本地 LLM 推理服务器"
    ["grafana/grafana:latest"]="监控仪表盘"
)

# 统计
total=0
passed=0
failed=0

# 检查每个镜像
for image in "${!REQUIRED_IMAGES[@]}"; do
    ((total++))
    purpose="${REQUIRED_IMAGES[$image]}"
    
    if docker image inspect "$image" &> /dev/null; then
        # 获取镜像大小
        size=$(docker images --format "{{.Size}}" "$image" | head -n1)
        created=$(docker images --format "{{.CreatedAt}}" "$image" | head -n1)
        
        log_success "$image"
        printf "  %-40s %s\n" "用途：" "$purpose"
        printf "  %-40s %s\n" "大小：" "$size"
        printf "  %-40s %s\n" "创建时间：" "$created"
        echo ""
        ((passed++))
    else
        log_error "$image"
        printf "  %-40s %s\n" "用途：" "$purpose"
        printf "  %-40s %s\n" "状态：" "未找到"
        echo ""
        ((failed++))
    fi
done

# 汇总
echo "============================================================"
echo "  验证结果"
echo "============================================================"
echo ""
log_info "总计：$total 个镜像"
log_success "通过：$passed 个"

if [ $failed -gt 0 ]; then
    log_error "失败：$failed 个"
    echo ""
    log_warning "请运行以下命令拉取缺失的镜像："
    echo "  cd 3rd && ./import_docker_images.sh"
    exit 1
else
    log_success "所有镜像已就绪！"
    echo ""
    log_info "下一步操作："
    echo "  cd devops && docker-compose up -d"
    exit 0
fi
