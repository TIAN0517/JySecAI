@echo off
rem JySecAI Asset Intelligence MCP — 回滾腳本 (Windows)
rem 用途: 移除安裝時建立的資料庫與 scope.json (不影響原始 JySecAI)
rem 注意: 此腳本不移除原始 fofo/zoomeye 功能

setlocal

echo ============================================================
echo JySecAI Asset Intelligence MCP - Rollback
echo ============================================================

rem 1. 移除資料庫
if exist "%LOCALAPPDATA%\JySecAI\assets\assets.db" (
    del "%LOCALAPPDATA%\JySecAI\assets\assets.db"
    del "%LOCALAPPDATA%\JySecAI\assets\assets.db-wal" 2>nul
    del "%LOCALAPPDATA%\JySecAI\assets\assets.db-shm" 2>nul
    echo [OK] 移除 assets.db
)

rem 2. 移除 scope.json (保留範範)
if exist "%~dp0scope.json" (
    del "%~dp0scope.json"
    echo [OK] 移除 scope.json
)

echo.
echo 手動回滾步驟:
echo   1. 從 Cursor / Hermes / Claude Code 設定中移除 jysecai-assets 區塊
echo   2. 移除環境變數 FOFA_API_KEY / ZOOMEYE_API_KEY (若專為此 MCP 設定)
echo   3. 重新啟動對應客戶端
echo.
echo 原始 FOFA / ZoomEye 功能不受此回滾影響
echo ============================================================
endlocal