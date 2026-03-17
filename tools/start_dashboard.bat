@echo off
REM NecoRAG Dashboard 启动脚本 (Windows)

echo.
echo ========================================
echo   NecoRAG Dashboard
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 启动 Dashboard
echo 正在启动 Dashboard...
echo.
echo 访问地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务器
echo.

python start_dashboard.py

pause
