#!/bin/bash
# NecoRAG 第三方 Docker 镜像一键导入脚本
# Third-Party Docker Images Import Script
# 
# 功能：从 Docker Hub 拉取所有需要的第三方镜像
# Usage: ./import_docker_images.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 镜像源配置
docker_hub_registry="docker.io"  # Docker Hub 官方
aliyun_registry="registry.cn-hangzhou.aliyuncs.com"  # 阿里云容器镜像服务

# 镜像大小信息（MB）
declare -A IMAGE_SIZES=(
    ["redis:7-alpine"]=25
    ["qdrant/qdrant:latest"]=500
    ["neo4j:5-community"]=1200
    ["ollama/ollama:latest"]=2000
    ["grafana/grafana:latest"]=300
    ["milvusdb/milvus:v2.3.0"]=707
    ["memgraph/memgraph:latest"]=203
    ["prom/prometheus:latest"]=146
    ["apache/superset:latest"]=643
)

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 标题
echo "============================================================"
echo "  NecoRAG 第三方 Docker 镜像导入工具"
echo "  Third-Party Docker Images Import Tool"
echo "============================================================"
echo ""

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装！请先安装 Docker。"
        echo "安装指南：https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行！请启动 Docker 服务。"
        exit 1
    fi
    
    log_success "Docker 检查通过"
}

# 检测网络环境，选择合适的镜像源
detect_network_and_select_registry() {
    log_info "正在检测网络环境..."
    
    # 使用多个检测点提高准确性
    local test_urls=(
        "https://www.baidu.com"
        "https://www.taobao.com"
        "https://registry.cn-hangzhou.aliyuncs.com"
    )
    
    local is_china=false
    local timeout=5
    
    # 尝试访问国内网站
    for url in "${test_urls[@]}"; do
        if curl --connect-timeout $timeout --max-time $((timeout*2)) -s -o /dev/null -w "%{http_code}" "$url" | grep -qE "^[23]"; then
            is_china=true
            break
        fi
    done
    
    # 根据检测结果选择镜像源
    if [ "$is_china" = true ]; then
        log_success "检测到中国大陆网络环境，使用阿里云镜像加速器"
        SELECTED_REGISTRY="$aliyun_registry"
        USE_ALIYUN=true
    else
        log_info "检测到海外网络环境，使用 Docker Hub 官方镜像源"
        SELECTED_REGISTRY="$docker_hub_registry"
        USE_ALIYUN=false
    fi
    
    echo ""
}

# 计算镜像总大小
calculate_total_size() {
    local total_mb=0
    local images=("$@")
    
    for image in "${images[@]}"; do
        if [[ -n "${IMAGE_SIZES[$image]}" ]]; then
            ((total_mb += ${IMAGE_SIZES[$image]}))
        fi
    done
    
    echo $total_mb
}

# 格式化大小显示
format_size() {
    local size_mb=$1
    if [ $size_mb -ge 1024 ]; then
        printf "%.2f GB" $(echo "scale=2; $size_mb / 1024" | bc)
    else
        printf "%d MB" $size_mb
    fi
}

# 检查磁盘空间
check_disk_space() {
    local required_mb=$1
    local docker_data_dir="/var/lib/docker"
    
    # 获取可用空间（MB）
    local available_mb=$(df -m "$docker_data_dir" 2>/dev/null | tail -1 | awk '{print $4}')
    
    # 如果无法获取，尝试其他方法
    if [ -z "$available_mb" ] || [ "$available_mb" -eq 0 ]; then
        available_mb=$(df -m / | tail -1 | awk '{print $4}')
    fi
    
    # 建议预留 20% 的额外空间
    local recommended_mb=$((required_mb * 120 / 100))
    
    echo ""
    log_info "磁盘空间检查"
    echo "   需要空间：$(format_size $required_mb)"
    echo "   建议预留：$(format_size $recommended_mb) (包含 20% 余量)"
    echo "   可用空间：$(format_size $available_mb)"
    
    if [ $available_mb -lt $required_mb ]; then
        log_error "磁盘空间不足！"
        echo "   缺口：$(format_size $((required_mb - available_mb)))"
        echo ""
        echo "💡 建议:"
        echo "   1. 清理未使用的 Docker 镜像：docker image prune -a"
        echo "   2. 清理停止的容器：docker container prune"
        echo "   3. 清理构建缓存：docker builder prune"
        echo "   4. 选择下载较少的镜像组合"
        return 1
    elif [ $available_mb -lt $recommended_mb ]; then
        log_warning "磁盘空间紧张，但勉强够用"
        echo "   剩余：$(format_size $((available_mb - required_mb)))"
        echo ""
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    else
        log_success "磁盘空间充足"
        echo "   剩余：$(format_size $((available_mb - required_mb)))"
    fi
    
    return 0
}

# 显示镜像选择菜单
show_image_selection_menu() {
    echo "============================================================"
    echo "  镜像选择"
    echo "============================================================"
    echo ""
    
    # 显示必需镜像
    echo "【必需镜像】(必须下载)"
    printf "  %-5s %-35s %10s\n" "序号" "镜像名称" "大小"
    echo "  ------------------------------------------------------------"
    local index=1
    for image in "${IMAGES[@]}"; do
        local size="${IMAGE_SIZES[$image]:-unknown}"
        printf "  %-5d %-35s %10s\n" $index "$image" "$(format_size $size)MB"
        ((index++))
    done
    
    # 显示可选镜像
    echo ""
    echo "【可选镜像】(可选择下载)"
    printf "  %-5s %-35s %10s\n" "序号" "镜像名称" "用途"
    echo "  ------------------------------------------------------------"
    index=1
    for image in "${OPTIONAL_IMAGES[@]}"; do
        local size="${IMAGE_SIZES[$image]:-unknown}"
        printf "  %-5d %-35s %10s\n" $index "$image" "$(format_size $size)MB"
        ((index++))
    done
    echo ""
}

# 获取用户下载选择
get_user_selection() {
    echo "============================================================"
    echo "  下载选项"
    echo "============================================================"
    echo ""
    echo "请选择要下载的镜像:"
    echo "  1) 仅下载必需镜像 (~4.03GB)"
    echo "  2) 下载全部镜像 (必需 + 可选，~5.68GB)"
    echo "  3) 自定义选择"
    echo ""
    read -p "请输入选项 (1/2/3): " download_choice
    
    case $download_choice in
        1)
            # 仅下载必需镜像
            DOWNLOAD_REQUIRED=true
            DOWNLOAD_OPTIONAL=false
            SELECTED_IMAGES=("${IMAGES[@]}")
            ;;
        2)
            # 下载全部镜像
            DOWNLOAD_REQUIRED=true
            DOWNLOAD_OPTIONAL=true
            SELECTED_IMAGES=("${IMAGES[@]}" "${OPTIONAL_IMAGES[@]}")
            ;;
        3)
            # 自定义选择
            DOWNLOAD_REQUIRED=true
            echo ""
            echo "请选择要下载的可选镜像 (可多选，用空格分隔):"
            echo ""
            local index=1
            for image in "${OPTIONAL_IMAGES[@]}"; do
                local size="${IMAGE_SIZES[$image]:-unknown}"
                printf "  %d) %-35s %10s\n" $index "$image" "$(format_size $size)MB"
                ((index++))
            done
            echo "  0) 不下载任何可选镜像"
            echo ""
            read -p "请选择 (例如：1 3 或 0): " optional_selection
            
            # 解析选择
            CUSTOM_OPTIONAL=()
            for selection in $optional_selection; do
                if [ "$selection" -ge 1 ] && [ "$selection" -le "${#OPTIONAL_IMAGES[@]}" ]; then
                    CUSTOM_OPTIONAL+=("${OPTIONAL_IMAGES[$((selection-1))]}")
                fi
            done
            
            if [ ${#CUSTOM_OPTIONAL[@]} -gt 0 ]; then
                DOWNLOAD_OPTIONAL=true
                SELECTED_IMAGES=("${IMAGES[@]}" "${CUSTOM_OPTIONAL[@]}")
            else
                DOWNLOAD_OPTIONAL=false
                SELECTED_IMAGES=("${IMAGES[@]}")
            fi
            ;;
        *)
            log_error "无效选项，默认仅下载必需镜像"
            DOWNLOAD_REQUIRED=true
            DOWNLOAD_OPTIONAL=false
            SELECTED_IMAGES=("${IMAGES[@]}")
            ;;
    esac
    
    # 计算总大小
    TOTAL_SIZE_MB=$(calculate_total_size "${SELECTED_IMAGES[@]}")
    
    echo ""
    log_info "已选择的镜像"
    echo "   必需镜像：${#IMAGES[@]} 个"
    if [ "$DOWNLOAD_OPTIONAL" = true ]; then
        echo "   可选镜像：${#SELECTED_IMAGES[@]} - ${#IMAGES[@]} = $((${#SELECTED_IMAGES[@]} - ${#IMAGES[@]}) 个"
    else
        echo "   可选镜像：0 个"
    fi
    echo "   总计：${#SELECTED_IMAGES[@]} 个镜像"
    echo "   总大小：$(format_size $TOTAL_SIZE_MB)"
    echo ""
}

# 镜像列表（根据项目需求）
# 来源：基于 requirements.txt 和 docker-compose.yml 分析
declare -a IMAGES=(
    # === 核心存储服务 ===
    "redis:7-alpine"                          # L1 工作记忆与缓存
    "qdrant/qdrant:latest"                    # L2 语义向量数据库
    "neo4j:5-community"                       # L3 情景图谱数据库
    
    # === AI/ML 模型服务 ===
    "ollama/ollama:latest"                    # 本地 LLM 推理服务器
    
    # === 监控可视化 ===
    "grafana/grafana:latest"                  # 监控仪表盘
    
    # === 备选方案（可选）===
    # "milvusdb/milvus:v2.3.0"               # Milvus 向量数据库（备选）
    # "memgraph/memgraph:latest"              # Memgraph 图数据库（备选）
    # "prom/prometheus:latest"                # Prometheus 指标收集
    # "apache/superset:latest"                # Superset 数据可视化
)

# 可选镜像（根据需求选择）
declare -a OPTIONAL_IMAGES=(
    # === 文档处理 ===
    # "ragflow/ragflow:latest"                # RAGFlow 深度文档解析
    
    # === 其他监控工具 ===
    # "prom/prometheus:latest"                # Prometheus
    # "grafana/loki:latest"                   # Loki 日志聚合
    # "jaegertracing/all-in-one:latest"       # Jaeger 链路追踪
)

# 拉取镜像函数
pull_image() {
    local image=$1
    local is_optional=${2:-false}
    local pull_image_name="$image"
    
    # 如果使用阿里云镜像，需要转换镜像名称格式
    if [ "$USE_ALIYUN" = true ] && [[ "$image" == *"/"* ]]; then
        # 将 docker.io/library/image:tag 转换为 registry.cn-hangzhou.aliyuncs.com/library/image:tag
        # 将 qdrant/qdrant:latest 转换为 registry.cn-hangzhou.aliyuncs.com/qdrant/qdrant:latest
        pull_image_name="${SELECTED_REGISTRY}/${image}"
    fi
    
    log_info "正在拉取镜像：$image"
    if [ "$USE_ALIYUN" = true ] && [[ "$image" == *"/"* ]]; then
        log_info "镜像源：${pull_image_name} (阿里云加速)"
    fi
    
    # 检查镜像是否已存在
    if docker image inspect "$image" &> /dev/null; then
        log_warning "镜像已存在：$image"
        
        # 询问是否重新拉取
        read -p "是否重新拉取？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    # 拉取镜像
    if docker pull "$image"; then
        log_success "镜像拉取成功：$image"
        return 0
    else
        if [ "$is_optional" = true ]; then
            log_warning "可选镜像拉取失败（可跳过）: $image"
            return 1
        else
            log_error "镜像拉取失败：$image"
            return 1
        fi
    fi
}

# 显示镜像信息
show_image_info() {
    local image=$1
    echo ""
    echo "镜像信息："
    docker images "$image" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
}

# 主流程
main() {
    # 检查 Docker
    check_docker
    
    # 检测网络并选择镜像源
    detect_network_and_select_registry
    
    # 显示镜像选择菜单并获取用户选择
    show_image_selection_menu
    get_user_selection
    
    # 检查磁盘空间
    if ! check_disk_space $TOTAL_SIZE_MB; then
        log_error "磁盘空间检查失败，终止操作"
        exit 1
    fi
    
    echo ""
    
    # 确认开始下载
    read -p "是否开始下载选中的镜像？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "已取消下载操作"
        exit 0
    fi
    
    echo ""
    
    # 统计
    total=0
    success=0
    failed=0
    skipped=0
    
    # 下载选中的镜像
    log_info "开始下载选中的镜像..."
    echo ""
    
    for image in "${SELECTED_IMAGES[@]}"; do
        ((total++))
        
        # 判断是否为可选镜像
        is_optional=false
        for opt_image in "${OPTIONAL_IMAGES[@]}"; do
            if [ "$image" == "$opt_image" ]; then
                is_optional=true
                break
            fi
        done
        
        if pull_image "$image" $is_optional; then
            ((success++))
            show_image_info "$image"
        else
            ((failed++))
            if [ "$is_optional" = true ]; then
                log_warning "可选镜像拉取失败（已跳过）: $image"
            else
                log_error "必需镜像拉取失败，可能影响系统运行！"
                
                # 询问是否继续
                read -p "是否继续拉取其他镜像？(y/n): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    break
                fi
            fi
        fi
    done
    
    echo ""
    log_info "镜像拉取完成"
    echo ""
    
    # 汇总报告
    
    # 不再询问是否拉取可选镜像，因为已经在前面选择过了
    echo ""
    echo "============================================================"
    echo "  镜像导入完成报告"
    echo "============================================================"
    echo ""
    log_info "总计尝试：$total 个镜像"
    log_success "成功：$success 个"
    
    if [ $failed -gt 0 ]; then
        log_error "失败：$failed 个"
    fi
    
    log_info "实际下载：$success 个镜像 ($(format_size $TOTAL_SIZE_MB))"
    echo ""
    
    # 显示所有已拉取的镜像
    log_info "当前所有 NecoRAG 相关镜像："
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | grep -E "(redis|qdrant|neo4j|ollama|grafana|mivlus|prom)" || echo "无相关镜像"
    echo ""
    
    # 下一步指引
    echo "============================================================"
    echo "  下一步操作"
    echo "============================================================"
    echo ""
    echo "1. 验证镜像："
    echo "   docker images"
    echo ""
    echo "2. 启动服务："
    echo "   cd devops && docker-compose up -d"
    echo ""
    echo "3. 查看状态："
    echo "   docker-compose ps"
    echo ""
    echo "4. 查看日志："
    echo "   docker-compose logs -f"
    echo ""
    echo "详细文档：3rd/deployment_quickref.md"
    echo "============================================================"
    echo ""
    
    # 退出码
    if [ $failed -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 显示帮助
show_help() {
    echo "用法：./import_docker_images.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -l, --list      列出所有需要拉取的镜像"
    echo "  -o, --optional  仅拉取可选镜像"
    echo "  -v, --verbose   显示详细信息"
    echo ""
    echo "示例:"
    echo "  ./import_docker_images.sh           # 拉取所有必需镜像"
    echo "  ./import_docker_images.sh -l        # 列出镜像列表"
    echo "  ./import_docker_images.sh -o        # 拉取可选镜像"
    echo ""
}

# 列出镜像列表
list_images() {
    echo "============================================================"
    echo "  NecoRAG 需要的 Docker 镜像列表"
    echo "============================================================"
    echo ""
    echo "【必需镜像】"
    printf "%-30s %s\n" "镜像名称" "用途"
    echo "------------------------------------------------------------"
    printf "%-30s %s\n" "redis:7-alpine" "L1 工作记忆与缓存 (~25MB)"
    printf "%-30s %s\n" "qdrant/qdrant:latest" "L2 语义向量数据库 (~500MB)"
    printf "%-30s %s\n" "neo4j:5-community" "L3 情景图谱数据库 (~1.2GB)"
    printf "%-30s %s\n" "ollama/ollama:latest" "本地 LLM 推理服务器 (~2GB)"
    printf "%-30s %s\n" "grafana/grafana:latest" "监控仪表盘 (~300MB)"
    echo ""
    echo "【可选镜像】"
    printf "%-30s %s\n" "镜像名称" "用途"
    echo "------------------------------------------------------------"
    printf "%-30s %s\n" "milvusdb/milvus:v2.3.0" "Milvus 向量数据库（备选）(~707MB)"
    printf "%-30s %s\n" "memgraph/memgraph:latest" "Memgraph 图数据库（备选）(~203MB)"
    printf "%-30s %s\n" "prom/prometheus:latest" "Prometheus 指标收集 (~146MB)"
    printf "%-30s %s\n" "apache/superset:latest" "Superset 数据可视化 (~643MB)"
    echo ""
    echo "💡 提示：脚本会自动检测网络并选择最优镜像源"
    echo "   - 中国大陆：阿里云镜像加速器"
    echo "   - 海外地区：Docker Hub 官方"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -l|--list)
            list_images
            exit 0
            ;;
        -o|--optional)
            check_docker
            for image in "${OPTIONAL_IMAGES[@]}"; do
                pull_image "$image" true
            done
            exit 0
            ;;
        -v|--verbose)
            set -x
            shift
            ;;
        *)
            log_error "未知选项：$1"
            show_help
            exit 1
            ;;
    esac
done

# 执行主流程
main
