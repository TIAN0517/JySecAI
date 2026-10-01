@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      MCP Kali Server 全局启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 检查依赖
python -c "import flask; import requests; import fastmcp" >nul 2>&1
if errorlevel 1 (
    echo 📦 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
)

echo.
echo 🚀 启动MCP Kali Server系统...
echo.

REM 启动Kali API服务器
echo 📡 启动Kali API服务器 (端口: 5000)...
start "MCP Kali Server" /min cmd /c "cd /d "%~dp0" && python kali_server.py --debug"

REM 等待服务器启动
echo ⏳ 等待服务器启动...
timeout /t 5 /nobreak > nul

REM 检查服务器状态
echo 🔍 检查服务器状态...
python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=5); print('✅ 服务器状态:', r.json().get('status', 'unknown')) if r.status_code == 200 else print('❌ 服务器未响应')" 2>nul
if errorlevel 1 (
    echo ⚠️  服务器启动可能需要更多时间，请稍后手动检查
)

echo.
echo 🤖 启动MCP客户端...
start "MCP Client" /min cmd /c "cd /d "%~dp0" && python mcp_server.py --server http://localhost:5000 --debug"

echo.
echo ========================================
echo ✅ MCP Kali Server 系统已启动！
echo ========================================
echo.
echo 📍 服务信息：
echo    • Kali API服务器: http://localhost:5000
echo    • MCP客户端: 后台运行中
echo    • 健康检查: http://localhost:5000/health
echo.
echo 📋 下一步操作：
echo   1. 配置Claude Desktop (参考 GLOBAL_MCP_CONFIG.md)
echo   2. 重启Claude Desktop应用
echo   3. 开始使用MCP工具
echo.
echo ⏹️  要停止服务，请关闭对应的命令窗口
echo.
pause