#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP渗透测试服务器功能测试
直接测试MCP服务器功能，无需完整启动
"""

import asyncio
import json
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_penetration_server import PenetrationMCPServer

async def test_mcp_functions():
    """测试MCP服务器功能"""
    print("MCP渗透测试服务器功能测试")
    print("=" * 40)

    try:
        # 创建服务器实例
        server = PenetrationMCPServer()

        # 初始化服务器
        await server.initialize()

        print("[OK] MCP服务器初始化成功")

        # 测试漏洞搜索
        print("\n[测试] 漏洞搜索功能...")
        search_results = await server.search_exploits("chuanhugpt")
        print(f"搜索 'chuanhugpt' 结果: {len(search_results)} 个")
        for result in search_results[:2]:  # 显示前2个结果
            print(f"  - {result.get('cve', 'N/A')}: {result.get('summary', 'N/A')[:50]}...")

        # 测试载荷生成
        print("\n💣 测试载荷生成功能...")
        try:
            payload = await server.generate_payload(
                cve_id="CVE-2024-3234",
                payload_type="reverse_shell",
                attacker_ip="192.168.1.100",
                attacker_port=4444
            )
            print(f"生成载荷长度: {len(payload)} 字符")
            print(f"载荷预览: {payload[:100]}...")
        except Exception as e:
            print(f"载荷生成失败: {str(e)}")

        # 测试端口扫描
        print("\n🔌 测试端口扫描功能...")
        try:
            scan_result = await server.port_scan(
                target="localhost",
                ports="22,80,443"
            )
            print(f"扫描结果ID: {scan_result.get('scan_id', 'N/A')}")
            print(f"扫描目标: {scan_result.get('target', 'N/A')}")
        except Exception as e:
            print(f"端口扫描失败: {str(e)}")

        # 测试载荷统计
        print("\n📊 测试载荷统计功能...")
        payload_stats = await server.get_payload_stats()
        print("载荷统计:")
        for category, count in payload_stats.items():
            print(f"  {category}: {count}")

        # 测试漏洞详情
        print("\n📋 测试漏洞详情功能...")
        try:
            cve_details = await server.get_exploit_details("CVE-2024-3234")
            print(f"CVE详情:")
            print(f"  CVE编号: {cve_details.get('cve', 'N/A')}")
            print(f"  严重性: {cve_details.get('severity', 'N/A')}")
            print(f"  CVSS评分: {cve_details.get('cvss', 'N/A')}")
        except Exception as e:
            print(f"获取漏洞详情失败: {str(e)}")

        print("\n✅ 所有MCP功能测试完成")
        print("MCP服务器已就绪，可以开始使用!")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_functions())