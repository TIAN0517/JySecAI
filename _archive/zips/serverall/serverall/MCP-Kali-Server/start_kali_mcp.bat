@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      MCP Kali Server 启动脚本 v2.0
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

REM 检查端口5001是否被占用
netstat -an | findstr :5001 >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  端口5001已被占用，尝试终止现有进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001') do (
        echo 终止进程 PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak > nul
)

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
echo 📡 启动Kali API服务器 (端口: 5001)...
start "MCP Kali API Server" /min cmd /c "cd /d "%~dp0" && python kali_server.py"

REM 等待服务器启动
echo ⏳ 等待服务器启动...
timeout /t 3 /nobreak > nul

REM 检查服务器状态
echo 🔍 检查服务器状态...
curl -s http://localhost:5001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  服务器启动可能需要更多时间，请稍后手动检查
) else (
    echo ✅ Kali API服务器运行正常
)

echo.
echo ========================================
echo ✅ MCP Kali Server 系统已启动！
echo ========================================
echo.
echo 📍 服务信息：
echo    • Kali API服务器: http://localhost:5001
echo    • 健康检查: http://localhost:5001/health
echo    • MCP客户端: 需要通过Claude Desktop启动
echo.
echo 📋 Claude Desktop配置：
echo    将以下内容添加到Claude Desktop配置文件：
echo    {
echo        "mcpServers": {
echo            "kali_mcp": {
echo                "command": "python",
echo                "args": [
echo                    "C:\\Users\\Administrator\\Desktop\\serverall\\MCP-Kali-Server\\mcp_server.py",
echo                    "--server",
echo                    "http://localhost:5001"
echo                ]
echo            }
echo        }
echo    }
echo.
echo 📝 配置文件位置：
echo    Windows: %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo ⏹️  要停止服务，请关闭 "MCP Kali API Server" 窗口
echo.
pause