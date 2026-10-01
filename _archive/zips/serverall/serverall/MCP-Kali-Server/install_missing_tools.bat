@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      安装缺失的Kali工具
echo ========================================
echo.

echo 🔄 正在安装缺失的Kali渗透测试工具...
echo.

echo [1/8] 更新软件包列表...
wsl bash -c "echo '520520' | sudo -S apt update" 2>nul
if errorlevel 1 echo ⚠️ 软件包列表更新失败

echo.
echo [2/8] 安装nikto (Web漏洞扫描器)...
wsl bash -c "echo '520520' | sudo -S apt install -y nikto" 2>nul
if errorlevel 1 echo ⚠️ nikto安装失败

echo.
echo [3/8] 安装gobuster (目录爆破工具)...
wsl bash -c "echo '520520' | sudo -S apt install -y gobuster" 2>nul
if errorlevel 1 echo ⚠️ gobuster安装失败

echo.
echo [4/8] 安装dirb (目录扫描工具)...
wsl bash -c "echo '520520' | sudo -S apt install -y dirb" 2>nul
if errorlevel 1 echo ⚠️ dirb安装失败

echo.
echo [5/8] 安装wpscan (WordPress安全扫描器)...
wsl bash -c "echo '520520' | sudo -S apt install -y wpscan" 2>nul
if errorlevel 1 echo ⚠️ wpscan安装失败

echo.
echo [6/8] 安装enum4linux (SMB枚举工具)...
wsl bash -c "echo '520520' | sudo -S apt install -y enum4linux" 2>nul
if errorlevel 1 echo ⚠️ enum4linux安装失败

echo.
echo [7/8] 安装john (密码哈希破解工具)...
wsl bash -c "echo '520520' | sudo -S apt install -y john" 2>nul
if errorlevel 1 echo ⚠️ john安装失败

echo.
echo [8/8] 安装hydra (密码破解工具)...
wsl bash -c "echo '520520' | sudo -S apt install -y hydra" 2>nul
if errorlevel 1 echo ⚠️ hydra安装失败

echo.
echo ✅ 工具安装完成！正在验证安装状态...

echo.
echo 🔍 检查工具安装状态...
wsl bash -c "
echo '=== 工具安装状态检查 ==='
echo -n 'nikto: '; command -v nikto >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'gobuster: '; command -v gobuster >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'dirb: '; command -v dirb >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'wpscan: '; command -v wpscan >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'enum4linux: '; command -v enum4linux >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'john: '; command -v john >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'hydra: '; command -v hydra >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'nmap: '; command -v nmap >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
echo -n 'sqlmap: '; command -v sqlmap >/dev/null 2>&1 && echo '✅ 已安装' || echo '❌ 未安装'
"

echo.
echo 🔄 重启WSL Kali服务器以更新工具状态...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq*WSL Kali API Server*" >nul 2>&1
timeout /t 3 /nobreak > nul

echo 🚀 重新启动WSL Kali服务器...
start "WSL Kali API Server" /min wsl bash -c "cd /tmp/mcp-kali-server && source venv/bin/activate && python kali_server.py"

timeout /t 5 /nobreak > nul

echo.
echo ✅ 工具安装和配置完成！
echo.
echo 📋 下一步操作：
echo 1. 重启Cursor IDE
echo 2. 检查MCP工具连接状态
echo 3. 开始使用完整的Kali渗透测试工具集
echo.
echo 🛠️ 现在可用的工具：
echo    • nmap - 网络扫描
echo    • sqlmap - SQL注入测试
echo    • nikto - Web漏洞扫描
echo    • gobuster - 目录爆破
echo    • dirb - 目录扫描
echo    • wpscan - WordPress安全扫描
echo    • enum4linux - SMB枚举
echo    • john - 密码破解
echo    • hydra - 在线密码攻击
echo.
pause