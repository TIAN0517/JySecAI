#!/usr/bin/env python3

# 测试服务器模块
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

try:
    import kali_server
    print("✅ Kali server module loaded successfully")
    
    # 测试配置
    from kali_server import app, API_PORT
    print(f"✅ Flask app configured on port {API_PORT}")
    
    # 测试命令执行功能
    from kali_server import execute_command
    result = execute_command("echo 'Hello MCP'")
    print(f"✅ Command execution test: {result.get('success', False)}")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()