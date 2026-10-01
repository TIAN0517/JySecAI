#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
符合MCP协议的渗透测试服务器
MCP Protocol Compliant Penetration Testing Server for Claude Code
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys
import os

# 导入MCP库
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_exploit_database import MCPExploitDatabase
from mcp_payloads_database import MCPPayloadsDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_penetration_server")

# 创建MCP服务器实例
app = Server("penetration-server")

# 初始化数据库
exploit_db = MCPExploitDatabase()
payloads_db = MCPPayloadsDatabase()
scan_results = {}

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出所有可用工具"""
    return [
        types.Tool(
            name="search_exploits",
            description="搜索漏洞利用数据库",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            }
        ),
        types.Tool(
            name="get_exploit_details",
            description="获取漏洞详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "cve_id": {
                        "type": "string",
                        "description": "CVE编号"
                    }
                },
                "required": ["cve_id"]
            }
        ),
        types.Tool(
            name="generate_payload",
            description="生成渗透载荷",
            inputSchema={
                "type": "object",
                "properties": {
                    "cve_id": {
                        "type": "string",
                        "description": "CVE编号"
                    },
                    "payload_type": {
                        "type": "string",
                        "description": "载荷类型 (reverse_shell, web_shell, sql_injection)",
                        "enum": ["reverse_shell", "web_shell", "sql_injection", "xss"]
                    },
                    "attacker_ip": {
                        "type": "string",
                        "description": "攻击者IP地址",
                        "default": "127.0.0.1"
                    },
                    "attacker_port": {
                        "type": "integer",
                        "description": "攻击者端口",
                        "default": 4444
                    }
                },
                "required": ["cve_id", "payload_type"]
            }
        ),
        types.Tool(
            name="search_payloads",
            description="搜索载荷数据库",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            }
        ),
        types.Tool(
            name="port_scan",
            description="端口扫描",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "目标地址"
                    },
                    "ports": {
                        "type": "string",
                        "description": "端口范围 (如: 1-1000, 80,443,22)",
                        "default": "1-1000"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="vulnerability_scan",
            description="漏洞扫描",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "目标地址"
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="get_payload_stats",
            description="获取载荷统计信息",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    logger.info(f"调用工具: {name}, 参数: {arguments}")

    try:
        if name == "search_exploits":
            keyword = arguments.get("keyword", "")
            results = exploit_db.search_exploits(keyword)
            return [types.TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

        elif name == "get_exploit_details":
            cve_id = arguments.get("cve_id", "")
            details = exploit_db.get_exploit_by_cve(cve_id)
            return [types.TextContent(type="text", text=json.dumps(details, ensure_ascii=False, indent=2))]

        elif name == "generate_payload":
            cve_id = arguments.get("cve_id", "")
            payload_type = arguments.get("payload_type", "reverse_shell")
            attacker_ip = arguments.get("attacker_ip", "127.0.0.1")
            attacker_port = arguments.get("attacker_port", 4444)

            payload = exploit_db.generate_exploit_payload(
                cve_id, payload_type, attacker_ip, attacker_port
            )
            return [types.TextContent(type="text", text=payload)]

        elif name == "search_payloads":
            keyword = arguments.get("keyword", "")
            results = payloads_db.search_payloads(keyword)
            return [types.TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

        elif name == "port_scan":
            target = arguments.get("target", "")
            ports = arguments.get("ports", "1-1000")

            try:
                cmd = f"nmap -sS -p {ports} {target}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                scan_results[scan_id] = {
                    'target': target,
                    'ports': ports,
                    'output': result.stdout,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }

                response = {
                    'scan_id': scan_id,
                    'target': target,
                    'ports': ports,
                    'output': result.stdout,
                    'error': result.stderr,
                    'success': result.returncode == 0
                }
                return [types.TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]

            except Exception as e:
                error_response = {
                    'error': str(e),
                    'success': False
                }
                return [types.TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

        elif name == "vulnerability_scan":
            target = arguments.get("target", "")

            try:
                cmd = f"nmap --script vuln {target}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                scan_id = f"vuln_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                scan_results[scan_id] = {
                    'target': target,
                    'type': 'vulnerability',
                    'output': result.stdout,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }

                response = {
                    'scan_id': scan_id,
                    'target': target,
                    'output': result.stdout,
                    'error': result.stderr,
                    'success': result.returncode == 0
                }
                return [types.TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]

            except Exception as e:
                error_response = {
                    'error': str(e),
                    'success': False
                }
                return [types.TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

        elif name == "get_payload_stats":
            stats = payloads_db.get_all_payloads_count()
            return [types.TextContent(type="text", text=json.dumps(stats, ensure_ascii=False, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        logger.error(f"工具调用错误: {e}")
        return [types.TextContent(type="text", text=f"工具调用失败: {str(e)}")]

async def main():
    """MCP服务器主函数"""
    logger.info("启动符合MCP协议的渗透测试服务器...")
    logger.info(f"漏洞数据库已加载: {len(exploit_db.exploits)} 个分类")
    logger.info(f"载荷数据库已加载: {payloads_db.get_all_payloads_count()['total']} 个载荷")

    # 运行MCP服务器
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())