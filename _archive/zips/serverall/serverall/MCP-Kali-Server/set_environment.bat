@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      MCP Kali Server 环境变量配置
echo ========================================
echo.

REM 设置MCP环境变量
echo 📝 设置MCP环境变量...

REM 设置项目路径
setx MCP_KALI_SERVER "C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server"
if errorlevel 1 (
    echo ❌ 设置MCP_KALI_SERVER环境变量失败
) else (
    echo ✅ MCP_KALI_SERVER环境变量设置成功
)

REM 设置服务器URL
setx MCP_SERVER_URL "http://localhost:5000"
if errorlevel 1 (
    echo ❌ 设置MCP_SERVER_URL环境变量失败
) else (
    echo ✅ MCP_SERVER_URL环境变量设置成功
)

echo.
echo 📋 已设置的环境变量：
echo    MCP_KALI_SERVER=%MCP_KALI_SERVER%
echo    MCP_SERVER_URL=%MCP_SERVER_URL%

echo.
echo ⚠️  注意：新环境变量需要重启命令行或系统才能生效
echo.
echo 📖 使用方法：
echo   在命令行中可以使用 %%MCP_KALI_SERVER%% 和 %%MCP_SERVER_URL%%
echo.
pause