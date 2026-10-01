#!/bin/bash
echo "🐉 Dragon-V Triple Bot 启动脚本"
echo "================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python环境检查通过"

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装完成"

# 启动系统
echo "🚀 启动Dragon-V Triple Bot..."
python3 dragon_triple_bot_unified_manager.py interactive
