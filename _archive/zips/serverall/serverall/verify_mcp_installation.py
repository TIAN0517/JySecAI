#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证MCP服务器安装
"""

import os
import json
import sys

def verify_installation():
    """验证MCP安装状态"""
    print("=== MCP服务器安装验证 ===\n")

    # 检查配置文件
    config_path = os.path.expanduser("~/.claude/mcp_client_config.json")
    print(f"1. 检查配置文件: {config_path}")

    if os.path.exists(config_path):
        print("   [OK] 配置文件存在")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("   [OK] 配置文件格式正确")
            if 'mcpServers' in config:
                print(f"   [OK] 配置了 {len(config['mcpServers'])} 个MCP服务器")
        except Exception as e:
            print(f"   [ERROR] 配置文件读取失败: {e}")
    else:
        print("   [ERROR] 配置文件不存在")

    # 检查Python依赖
    print("\n2. 检查Python依赖")
    try:
        import aiohttp
        print("   [OK] aiohttp 已安装")
    except ImportError:
        print("   [WARN] aiohttp 未安装，运行: pip install aiohttp")

    try:
        import asyncio
        print("   [OK] asyncio 已安装")
    except ImportError:
        print("   [ERROR] asyncio 未安装")

    # 检查MCP服务器文件
    print("\n3. 检查MCP服务器文件")
    server_files = [
        "mcp_penetration_server.py",
        "mcp_exploit_database.py",
        "mcp_payloads_database.py"
    ]

    for file in server_files:
        if os.path.exists(file):
            print(f"   [OK] {file} 存在")
        else:
            print(f"   [ERROR] {file} 不存在")

    # 检查环境变量
    print("\n4. 检查环境变量")
    current_dir = os.getcwd()
    print(f"   当前工作目录: {current_dir}")

    # 测试服务器启动
    print("\n5. 测试服务器启动")
    try:
        # 导入服务器模块
        sys.path.append(current_dir)
        from mcp_penetration_server import server
        import asyncio

        async def quick_test():
            await server.initialize()
            exploits = await server.search_exploits("test")
            return True

        result = asyncio.run(quick_test())
        if result:
            print("   [OK] 服务器启动测试成功")
    except Exception as e:
        print(f"   [ERROR] 服务器启动测试失败: {e}")

    print("\n=== 安装验证完成 ===")
    print("\n下一步操作:")
    print("1. 重启Claude Code以加载MCP配置")
    print("2. 在Claude Code中使用 /mcp 命令")
    print("3. 或直接运行: python mcp_penetration_server.py")

if __name__ == "__main__":
    verify_installation()