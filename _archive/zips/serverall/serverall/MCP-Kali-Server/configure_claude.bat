@echo off
chcp 65001 >nul
echo.
echo ========================================
echo     Claude Desktop MCP 配置脚本
echo ========================================
echo.

set "CLAUDE_CONFIG_DIR=%APPDATA%\Claude"
set "CONFIG_FILE=%CLAUDE_CONFIG_DIR%\claude_desktop_config.json"
set "SOURCE_CONFIG=%~dp0claude_desktop_config.json"

REM 检查Claude配置目录是否存在
echo 📁 检查Claude Desktop配置目录...
if not exist "%CLAUDE_CONFIG_DIR%" (
    echo 📂 创建Claude配置目录...
    mkdir "%CLAUDE_CONFIG_DIR%"
    if errorlevel 1 (
        echo ❌ 无法创建配置目录: %CLAUDE_CONFIG_DIR%
        echo   请手动创建目录并复制配置文件
        pause
        exit /b 1
    )
    echo ✅ 配置目录创建成功
) else (
    echo ✅ 配置目录已存在
)

REM 检查源配置文件
echo 📄 检查源配置文件...
if not exist "%SOURCE_CONFIG%" (
    echo ❌ 源配置文件不存在: %SOURCE_CONFIG%
    echo   请确保claude_desktop_config.json文件存在
    pause
    exit /b 1
)

echo ✅ 源配置文件存在

REM 备份现有配置（如果存在）
if exist "%CONFIG_FILE%" (
    echo 📋 备份现有配置文件...
    copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%" >nul
    if errorlevel 1 (
        echo ⚠️  备份失败，继续配置...
    ) else (
        echo ✅ 配置文件已备份
    )
)

REM 复制配置文件
echo 📝 配置Claude Desktop MCP...
copy "%SOURCE_CONFIG%" "%CONFIG_FILE%" >nul
if errorlevel 1 (
    echo ❌ 配置文件复制失败
    echo   请手动复制: %SOURCE_CONFIG% 到 %CONFIG_FILE%
    pause
    exit /b 1
)

echo ✅ Claude Desktop MCP配置完成！
echo.
echo 📋 配置信息：
echo   配置文件位置: %CONFIG_FILE%
echo   MCP服务器: %~dp0mcp_server.py
echo   API服务器: http://localhost:5000
echo.
echo ⚠️  重要：需要重启Claude Desktop应用才能使配置生效！
echo.
echo 📖 验证步骤：
echo   1. 完全关闭Claude Desktop
echo   2. 重新启动Claude Desktop
echo   3. 在Claude中测试MCP功能
echo.
pause