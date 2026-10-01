#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP渗透测试服务器启动器
独立启动MCP服务器以供系统集成
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_penetration_server import PenetrationMCPServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_launcher")

class MCPServerLauncher:
    """MCP服务器启动器"""

    def __init__(self):
        self.server = None
        self.is_running = False

    async def start_server(self):
        """启动MCP服务器"""
        try:
            print("启动MCP渗透测试服务器...")

            # 创建服务器实例
            self.server = PenetrationMCPServer()

            # 初始化服务器
            await self.server.initialize()

            # 设置服务器为运行状态
            self.is_running = True

            print("MCP服务器启动成功!")
            print("服务状态:")
            print("  漏洞数据库: 已加载")
            print("  载荷数据库: 已加载")
            print("  渗透测试模块: 已就绪")

            # 显示可用功能
            await self._display_available_functions()

            # 保持服务器运行
            print("\nMCP服务器正在运行...")
            print("按 Ctrl+C 停止服务器")

            # 模拟服务运行
            while self.is_running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n正在停止MCP服务器...")
            self.is_running = False
            print("MCP服务器已停止")

        except Exception as e:
            print(f"MCP服务器启动失败: {str(e)}")
            logger.error(f"MCP服务器错误: {e}")

    async def _display_available_functions(self):
        """显示可用功能"""
        print("\n可用功能:")
        print("  1. 搜索漏洞利用 (search_exploits)")
        print("  2. 获取漏洞详情 (get_exploit_details)")
        print("  3. 生成攻击载荷 (generate_payload)")
        print("  4. 搜索载荷 (search_payloads)")
        print("  5. 端口扫描 (port_scan)")
        print("  6. 漏洞扫描 (vulnerability_scan)")
        print("  7. 获取载荷统计 (get_payload_stats)")

        # 显示数据库统计
        if self.server:
            exploit_count = len(self.server.exploit_db.exploits)
            payload_stats = self.server.payloads_db.get_all_payloads_count()

            print(f"\n数据库统计:")
            print(f"  漏洞分类: {exploit_count} 个")
            print(f"  攻击载荷: {payload_stats.get('total', 0)} 个")

async def main():
    """主函数"""
    print("MCP渗透测试服务器启动器")
    print("=" * 40)

    launcher = MCPServerLauncher()
    await launcher.start_server()

if __name__ == "__main__":
    asyncio.run(main())