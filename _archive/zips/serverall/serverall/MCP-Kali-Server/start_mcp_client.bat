@echo off
echo Starting MCP Client for Kali Server...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo Checking dependencies...
python -c "import flask; import requests; import fastmcp" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Starting MCP Client...
echo Server URL: http://localhost:5000
echo.

REM 启动MCP客户端
python mcp_server.py --server http://localhost:5000