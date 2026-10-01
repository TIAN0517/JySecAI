#!/usr/bin/env python3
"""
Xray MCP客户端
为Cursor提供Xray扫描能力
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

class MCPXrayClient:
    def __init__(self, server_url: str = "http://localhost:5002"):
        self.server_url = server_url
        self.tools = self._register_tools()

    def _register_tools(self):
        """注册MCP工具"""
        return {
            "xray_scan": {
                "name": "xray_scan",
                "description": "启动Xray安全扫描，支持多种漏洞类型检测",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "目标URL，例如: https://example.com"
                        },
                        "scan_type": {
                            "type": "string",
                            "enum": ["web", "basic_crawler", "services"],
                            "description": "扫描类型",
                            "default": "web"
                        },
                        "plugins": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "启用的插件列表，例如: ['xss', 'sql', 'cmd-injection']"
                        },
                        "options": {
                            "type": "object",
                            "description": "额外扫描选项",
                            "properties": {
                                "max_depth": {"type": "integer", "default": 5},
                                "timeout": {"type": "integer", "default": 30},
                                "max_concurrency": {"type": "integer", "default": 50}
                            }
                        }
                    },
                    "required": ["target"]
                }
            },
            "xray_status": {
                "name": "xray_status",
                "description": "查询Xray扫描状态和结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "扫描ID"
                        }
                    },
                    "required": ["scan_id"]
                }
            },
            "xray_results": {
                "name": "xray_results",
                "description": "获取详细的扫描结果和漏洞信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "扫描ID"
                        },
                        "severity_filter": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["high", "medium", "low", "info"]},
                            "description": "严重程度过滤器"
                        },
                        "vuln_type_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "漏洞类型过滤器"
                        }
                    },
                    "required": ["scan_id"]
                }
            },
            "xray_burp_integration": {
                "name": "xray_burp_integration",
                "description": "与Burp Suite集成，将Burp请求转换为Xray测试用例",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_url": {
                            "type": "string",
                            "description": "目标URL"
                        },
                        "request": {
                            "type": "string",
                            "description": "HTTP请求内容"
                        },
                        "headers": {
                            "type": "object",
                            "description": "请求头信息"
                        },
                        "auto_scan": {
                            "type": "boolean",
                            "description": "是否自动启动扫描",
                            "default": false
                        }
                    },
                    "required": ["target_url", "request"]
                }
            },
            "xray_export_report": {
                "name": "xray_export_report",
                "description": "导出扫描报告，支持HTML和JSON格式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "扫描ID"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["html", "json", "markdown"],
                            "description": "报告格式",
                            "default": "json"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "输出文件路径（可选）"
                        }
                    },
                    "required": ["scan_id"]
                }
            },
            "xray_info": {
                "name": "xray_info",
                "description": "获取Xray工具信息和配置状态",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具方法"""
        import aiohttp
        import urllib.parse

        async with aiohttp.ClientSession() as session:
            try:
                if tool_name == "xray_scan":
                    url = f"{self.server_url}/api/xray/scan"
                    async with session.post(url, json=arguments) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                elif tool_name == "xray_status":
                    scan_id = arguments.get("scan_id")
                    url = f"{self.server_url}/api/xray/scan/{scan_id}/status"
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                elif tool_name == "xray_results":
                    scan_id = arguments.get("scan_id")
                    params = {}
                    if "severity_filter" in arguments:
                        params["severity"] = ",".join(arguments["severity_filter"])
                    if "vuln_type_filter" in arguments:
                        params["type"] = ",".join(arguments["vuln_type_filter"])

                    url = f"{self.server_url}/api/xray/scan/{scan_id}/results"
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                elif tool_name == "xray_burp_integration":
                    url = f"{self.server_url}/api/xray/burp/integration"
                    async with session.post(url, json=arguments) as response:
                        if response.status == 200:
                            result = await response.json()

                            # 如果设置了自动扫描，立即启动扫描
                            if arguments.get("auto_scan", False):
                                scan_args = {
                                    "target": arguments["target_url"],
                                    "scan_type": "web",
                                    "plugins": ["xss", "sql", "cmd-injection", "path-traversal"]
                                }
                                scan_result = await self.call_tool("xray_scan", scan_args)
                                result["auto_scan"] = scan_result

                            return result
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                elif tool_name == "xray_export_report":
                    scan_id = arguments.get("scan_id")
                    format_type = arguments.get("format", "json")
                    url = f"{self.server_url}/api/xray/export/{scan_id}?format={format_type}"

                    async with session.get(url) as response:
                        if response.status == 200:
                            if format_type == "json":
                                return await response.json()
                            else:
                                return {"report": await response.text()}
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                elif tool_name == "xray_info":
                    url = f"{self.server_url}/api/xray/info"
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}

                else:
                    return {"error": f"Unknown tool: {tool_name}"}

            except aiohttp.ClientError as e:
                return {"error": f"Connection error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected error: {str(e)}"}

async def main():
    """主函数 - 处理stdin/stdout通信"""
    client = MCPXrayClient()

    # 发送初始化消息
    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": "xray-mcp-client",
                "version": "1.0.0"
            }
        }
    }
    print(json.dumps(init_message), flush=True)

    # 处理请求
    async for line in sys.stdin:
        try:
            message = json.loads(line.strip())

            if message.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "tools": list(client.tools.values())
                    }
                }
                print(json.dumps(response), flush=True)

            elif message.get("method") == "tools/call":
                params = message.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                result = await client.call_tool(tool_name, arguments)

                response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result, indent=2, ensure_ascii=False)
                        }]
                    }
                }
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id") if 'message' in locals() else None,
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())