#!/bin/bash
# NecoRAG Dashboard 启动脚本 (Linux/Mac)

echo ""
echo "========================================"
echo "  NecoRAG Dashboard"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.9+"
    exit 1
fi

# 启动 Dashboard
echo "正在启动 Dashboard..."
echo ""
echo "访问地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python3 start_dashboard.py
