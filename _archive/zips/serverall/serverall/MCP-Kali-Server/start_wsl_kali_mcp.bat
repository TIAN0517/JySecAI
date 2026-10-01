@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      MCP Kali WSL Server 启动脚本
echo ========================================
echo.

echo 🚀 启动基于WSL的MCP Kali Server系统...
echo.

REM 检查WSL是否可用
wsl --list --verbose >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: WSL未安装或未启用
    echo 请先安装WSL并确保Kali Linux已安装
    pause
    exit /b 1
)

echo ✅ WSL环境检查通过
echo.

REM 检查Kali Linux是否运行
wsl -e bash -c "echo 'Kali Linux is running'" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Kali Linux未运行或不可访问
    pause
    exit /b 1
)

echo ✅ Kali Linux运行正常
echo.

REM 复制文件到WSL
echo 📁 准备WSL环境...
wsl bash -c "mkdir -p /tmp/mcp-kali-server && cp -rf /mnt/c/Users/Administrator/desktop/serverall/MCP-Kali-Server/* /tmp/mcp-kali-server/" >nul 2>&1

REM 检查虚拟环境
echo 🔧 检查Python虚拟环境...
wsl bash -c "cd /tmp/mcp-kali-server && if [ ! -d 'venv' ]; then python3 -m venv venv; fi"

REM 安装依赖
echo 📦 检查并安装依赖...
wsl bash -c "cd /tmp/mcp-kali-server && source venv/bin/activate && pip install -q -r requirements.txt"

REM 停止现有的服务
echo 🔄 停止现有服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq*MCP Kali API Server*" >nul 2>&1
timeout /t 2 /nobreak > nul

REM 启动WSL Kali API服务器
echo 🐉 启动WSL Kali API服务器 (端口: 5001)...
start "WSL Kali API Server" /min wsl bash -c "cd /tmp/mcp-kali-server && source venv/bin/activate && python kali_server.py"

REM 等待服务器启动
echo ⏳ 等待服务器启动...
timeout /t 5 /nobreak > nul

REM 检查服务器状态
echo 🔍 检查服务器状态...
curl -s http://localhost:5001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  服务器启动可能需要更多时间
) else (
    echo ✅ WSL Kali API服务器运行正常
)

echo.
echo ========================================
echo ✅ MCP Kali WSL Server 系统已启动！
echo ========================================
echo.
echo 📍 服务信息：
echo    • WSL Kali API服务器: http://localhost:5001
echo    • 健康检查: http://localhost:5001/health
echo    • MCP客户端: 需要通过Claude Desktop启动
echo.
echo 🛠️  可用工具：
echo    • nmap - 网络扫描工具 ✅
echo    • sqlmap - SQL注入测试 ✅
echo    • 其他Kali工具需要额外安装
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
echo ⏹️  要停止服务，请关闭 "WSL Kali API Server" 窗口
echo.
pause