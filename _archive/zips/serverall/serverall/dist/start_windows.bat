@echo off
echo 🐉 Dragon-V Triple Bot 启动脚本
echo =================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

REM 安装依赖
echo 📦 安装依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo ✅ 依赖安装完成

REM 启动系统
echo 🚀 启动Dragon-V Triple Bot...
python dragon_triple_bot_unified_manager.py interactive

pause
