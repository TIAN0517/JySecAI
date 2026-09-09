@echo off
chcp 65001 >nul
title JySecAI 管理菜单
cls

:main
echo ==========================================
echo JySecAI 管理菜单
echo ==========================================
echo.
echo [1] 启动/重启服务
echo [2] 停止服务  
echo [3] 检查服务状态
echo [4] 等待 20 秒 (模块載入)
echo [5] security-ops 功能測試
echo [6] 退出
echo.
set /p choice="請選擇 [1-6]: "

if %choice%==1 goto start_service
if %choice%==2 goto stop_service
if %choice%==3 goto check_status
if %choice%==4 goto wait_modules
if %choice%==5 goto test_securityops
if %choice%==6 exit

:start_service
echo 正在啟動服務...
start "" "C:\Users\Administrator\Desktop\JySecAI\jysecai.exe" --config "C:\Users\Administrator\Desktop\JySecAI\config.yaml"
timeout /t 15 /nobreak >nul
goto main

:stop_service
taskkill /F /IM jysecai.exe 2>nul
echo 已停止服務
timeout /t 2 /nobreak >nul
goto main

:check_status
echo 正在檢查狀態...
curl -s -f http://127.0.0.1:6688/api/security-ops/catalog >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ security-ops 端點可用
) else (
    echo ⚠️ security-ops 端點可能未啟用
)
timeout /t 3 /nobreak >nul
goto main

:wait_modules
echo 等待 20 秒 讓模組載入...
timeout /t 20 /nobreak >nul
goto main

:test_securityops
echo 正在測試 security-ops...
curl -s -f http://127.0.0.1:6688/api/security-ops/catalog >nul 2>&1
if %errorlevel% == 0 (
    echo 成功！功能已恢復
) else (
    echo 檢測到: 端點返回非 200 狀態
)
timeout /t 3 /nobreak >nul
goto main

goto main