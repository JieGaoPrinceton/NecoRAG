#!/bin/bash
# NecoRAG Dashboard 快速启动脚本
# 自动打开知识库健康仪表盘

echo "======================================================================"
echo "  NecoRAG Dashboard - 知识库健康仪表盘"
echo "======================================================================"
echo ""

# 设置默认端口
PORT=${1:-8000}

echo "🚀 启动 Dashboard 服务器..."
echo "   端口：$PORT"
echo "   访问地址：http://localhost:$PORT/knowledge-health"
echo ""
echo "📌 提示:"
echo "   - 按 Ctrl+C 停止服务器"
echo "   - 在浏览器中打开上述地址查看仪表盘"
echo ""
echo "======================================================================"
echo ""

# 启动服务器并自动打开浏览器
python src/dashboard/dashboard.py --port $PORT &
SERVER_PID=$!

# 等待服务器启动
sleep 3

# 尝试打开默认浏览器
case "$(uname -s)" in
    Darwin)
        # macOS
        open "http://localhost:$PORT/knowledge-health"
        ;;
    Linux)
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:$PORT/knowledge-health"
        elif command -v gnome-open &> /dev/null; then
            gnome-open "http://localhost:$PORT/knowledge-health"
        fi
        ;;
    MINGW*|CYGWIN*|MSYS*)
        # Windows
        start "http://localhost:$PORT/knowledge-health"
        ;;
esac

echo ""
echo "✅ Dashboard 已启动！"
echo "   如果浏览器没有自动打开，请手动访问：http://localhost:$PORT/knowledge-health"
echo ""

# 捕获退出信号
trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Dashboard 已停止'; exit" INT TERM EXIT

# 保持运行
wait
