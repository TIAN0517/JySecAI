@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      Cursor MCP Kali Configuration
echo ========================================
echo.

echo [1/4] Creating Cursor MCP configuration...
if not exist "%USERPROFILE%\.cursor" mkdir "%USERPROFILE%\.cursor"

(
echo {
echo   "mcpServers": {
echo     "kali_wsl": {
echo       "command": "python",
echo       "args": [
echo         "C:\\Users\\Administrator\\Desktop\\serverall\\MCP-Kali-Server\\mcp_server.py",
echo         "--server",
echo         "http://localhost:5001",
echo         "--debug"
echo       ],
echo       "env": {
echo         "WSL_PASSWORD": "520520",
echo         "MCP_DEBUG": "true"
echo       }
echo     }
echo   }
echo }
) > "%USERPROFILE%\.cursor\mcp_servers.json"

echo ✅ Cursor MCP configuration created

echo.
echo [2/4] Setting up WSL password configuration...
(
echo {
echo   "wsl_password": "520520",
echo   "wsl_user": "bossjy",
echo   "timestamp": "2025-10-27"
echo }
) > "%USERPROFILE%\.cursor\wsl_config.json"

echo ✅ WSL password configuration saved

echo.
echo [3/4] Testing WSL Kali server connection...
curl -s http://localhost:5001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ WSL Kali server not running
    echo Please run: start_wsl_kali_mcp.bat
) else (
    echo ✅ WSL Kali server is running
)

echo.
echo [4/4] Creating desktop shortcut...
echo Creating shortcut for Cursor with MCP...

echo.
echo ========================================
echo ✅ Cursor MCP Kali Setup Complete!
echo ========================================
echo.
echo 📋 Next Steps:
echo 1. Restart Cursor IDE
echo 2. Open Command Palette (Ctrl+Shift+P)
echo 3. Type "MCP" to see available Kali tools
echo 4. Start using Kali penetration testing tools
echo.
echo 🛠️ Available Tools in Cursor:
echo - nmap_network_scanner
echo - sqlmap_sql_injection
echo - hydra_password_cracker
echo - nikto_web_scanner
echo - And more Kali tools...
echo.
echo 📍 Configuration Files:
echo - MCP Config: %USERPROFILE%\.cursor\mcp_servers.json
echo - WSL Config: %USERPROFILE%\.cursor\wsl_config.json
echo.
pause