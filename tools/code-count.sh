#!/bin/bash
# NecoRAG 代码统计工具 - 快速启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${SCRIPT_DIR}/.."

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   NecoRAG 代码行数统计工具                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Python 版本
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ 错误：找不到 Python${NC}"
    exit 1
fi

# 检查 Python 版本是否 >= 3.7
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓${NC} Python 版本：${PYTHON_VERSION}"

# 切换到 tools 目录
cd "$SCRIPT_DIR"

# 解析命令行参数
OUTPUT_FLAG=""
VERBOSE_FLAG=""
TARGET_PATH="$PROJECT_ROOT"

# 检查是否有 -o 参数（不带值表示自动生成文件名）
if [[ "$*" == *"-o"* ]]; then
    # 查找 -o 后面的参数
    args=("$@")
    for i in "${!args[@]}"; do
        if [[ "${args[$i]}" == "-o" ]]; then
            next_idx=$((i+1))
            if [[ $next_idx -lt ${#args[@]} ]] && [[ ! "${args[$next_idx]}" =~ ^- ]]; then
                OUTPUT_FLAG="-o ${args[$next_idx]}"
            else
                OUTPUT_FLAG="-o"
            fi
            break
        fi
    done
fi

# 检查是否有 -v 参数
if [[ "$*" == *"-v"* ]]; then
    VERBOSE_FLAG="-v"
fi

# 检查是否有 -p 参数
if [[ "$*" == *"-p"* ]]; then
    # 查找 -p 后面的参数
    args=("$@")
    for i in "${!args[@]}"; do
        if [[ "${args[$i]}" == "-p" ]]; then
            next_idx=$((i+1))
            if [[ $next_idx -lt ${#args[@]} ]] && [[ ! "${args[$next_idx]}" =~ ^- ]]; then
                TARGET_PATH="${args[$next_idx]}"
            fi
            break
        fi
    done
fi

# 显示帮助
if [[ "$*" == *"-h"* ]]; then
    echo "用法：$0 [-p 路径] [-o 输出文件] [-v]"
    echo ""
    echo "选项:"
    echo "  -p PATH    项目根目录路径 (默认：..)"
    echo "  -o FILE    导出 Markdown 报告文件名 (不加参数则自动生成)"
    echo "  -v         显示详细信息"
    echo "  -h         显示帮助信息"
    exit 0
fi

# 执行统计
echo -e "${GREEN}✓${NC} 目标路径：${TARGET_PATH}"
echo ""
echo -e "${YELLOW}📊 开始统计...${NC}"
echo ""

$PYTHON_CMD code-count.py -p "$TARGET_PATH" $OUTPUT_FLAG $VERBOSE_FLAG

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 统计完成！${NC}"
else
    echo -e "${RED}❌ 统计失败，退出码：$EXIT_CODE${NC}"
fi

exit $EXIT_CODE
