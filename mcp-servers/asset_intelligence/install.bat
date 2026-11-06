@echo off
rem JySecAI Asset Intelligence MCP — 安裝腳本 (Windows)
rem 用途: 建立資料目錄、複製範範、顯示驗證指引
rem 回滾: 執行 rollback.bat

setlocal enabledelayedexpansion

echo ============================================================
echo JySecAI Asset Intelligence MCP - Install
echo ============================================================

rem 1. 建立資料庫目錄
if not exist "%LOCALAPPDATA%\JySecAI\assets" (
    mkdir "%LOCALAPPDATA%\JySecAI\assets"
    echo [OK] 建立目錄 %LOCALAPPDATA%\JySecAI\assets
)

rem 2. 若 scope.json 不存在, 從範範複製
set "SCOPE_SRC=%~dp0scope.example.json"
set "SCOPE_DST=%~dp0scope.json"
if not exist "%SCOPE_DST%" (
    copy "%SCOPE_SRC%" "%SCOPE_DST%"
    echo [OK] 建立 scope.json (請編輯填入你的授權範圍)
) else (
    echo [SKIP] scope.json 已存在
)

rem 3. 驗證 Python 與 mcp SDK
"C:\Program Files\Python311\python.exe" -c "import mcp; print('[OK] mcp SDK:', mcp.__file__)" 2>&1
if errorlevel 1 (
    echo [ERROR] mcp SDK 未安裝, 請執行: "C:\Program Files\Python311\python.exe" -m pip install -r %~dp0requirements.txt
    exit /b 1
)

rem 4. 驗證入口腳本可啟動
"C:\Program Files\Python311\python.exe" -c "import sys; sys.path.insert(0, '%~dp0..'); from asset_intelligence.server import create_app; print('[OK] create_app 可載入')" 2>&1

echo.
echo ============================================================
echo 下一步:
echo   1. 編輯 scope.json 填入你的授權 CIDR / 域名 / IP
echo   2. 設定環境變數 FOFA_API_KEY / ZOOMEYE_API_KEY
echo   3. 將 cursor_mcp_snippet.json / hermes_mcp_snippet.json /
echo      claude_code_snippet.json 加入對應客戶端的設定
echo   4. 執行測試: "C:\Program Files\Python311\python.exe" -m pytest %~dp0tests\
echo ============================================================
endlocal