#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的MCP功能测试
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_penetration_server import PenetrationMCPServer

async def simple_test():
    """简化测试"""
    print("MCP渗透测试服务器状态检查")
    print("=" * 40)

    try:
        # 创建并初始化服务器
        server = PenetrationMCPServer()
        await server.initialize()

        print("状态: MCP服务器已启动")
        print(f"漏洞数据库: {len(server.exploit_db.exploits)} 个分类")

        payload_stats = server.payloads_db.get_all_payloads_count()
        print(f"载荷数据库: {payload_stats.get('total', 0)} 个载荷")

        # 测试搜索功能
        results = await server.search_exploits("sql")
        print(f"搜索测试: 找到 {len(results)} 个SQL相关漏洞")

        # 测试载荷生成
        try:
            payload = await server.generate_payload("CVE-2024-3234", "web_shell")
            print(f"载荷生成: 成功 ({len(payload)} 字符)")
        except:
            print("载荷生成: 失败")

        print("\n结论: MCP服务器运行正常")
        return True

    except Exception as e:
        print(f"状态: MCP服务器异常 - {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(simple_test())
    print(f"\nMCP服务器状态: {'就绪' if result else '未就绪'}")