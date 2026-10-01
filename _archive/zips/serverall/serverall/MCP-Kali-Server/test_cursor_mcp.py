#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor MCP测试脚本 - 验证MCP工具功能
"""

import requests
import json
import time
from typing import Dict, Any

class CursorMCPTester:
    def __init__(self):
        self.server_url = "http://localhost:5001"
        self.test_results = []

    def log_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")

    def test_server_health(self):
        """测试服务器健康状态"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "服务器健康检查",
                    True,
                    f"状态: {data.get('status')}, 工具可用: {list(data.get('tools_status', {}).keys())}",
                    data
                )
                return True
            else:
                self.log_result("服务器健康检查", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("服务器健康检查", False, f"连接失败: {str(e)}")
            return False

    def test_nmap_tool(self):
        """测试nmap工具"""
        try:
            payload = {
                "target": "127.0.0.1",
                "options": "-p 22,80,443,5001"
            }

            response = requests.post(
                f"{self.server_url}/api/tools/nmap",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Nmap工具测试",
                    data.get("success", False),
                    f"返回码: {data.get('return_code')}, 超时: {data.get('timed_out')}",
                    data.get("stdout", "")[:200] + "..." if data.get("stdout") else None
                )
                return data.get("success", False)
            else:
                self.log_result("Nmap工具测试", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Nmap工具测试", False, f"请求失败: {str(e)}")
            return False

    def test_sqlmap_tool(self):
        """测试sqlmap工具"""
        try:
            # 使用sqlmap的help命令进行测试
            payload = {
                "url": "--help",
                "options": "--batch"
            }

            response = requests.post(
                f"{self.server_url}/api/tools/sqlmap",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "SQLMap工具测试",
                    data.get("success", False),
                    f"返回码: {data.get('return_code')}",
                    "SQLMap help信息已获取" if data.get("success") else data.get("error", "未知错误")
                )
                return data.get("success", False)
            else:
                self.log_result("SQLMap工具测试", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("SQLMap工具测试", False, f"请求失败: {str(e)}")
            return False

    def test_general_command(self):
        """测试通用命令执行"""
        try:
            payload = {
                "command": "whoami",
                "args": [],
                "timeout": 10
            }

            response = requests.post(
                f"{self.server_url}/api/command",
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "通用命令测试",
                    data.get("success", False),
                    f"用户: {data.get('stdout', '').strip()}, 返回码: {data.get('return_code')}",
                    data
                )
                return data.get("success", False)
            else:
                self.log_result("通用命令测试", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("通用命令测试", False, f"请求失败: {str(e)}")
            return False

    def test_mcp_capabilities(self):
        """测试MCP能力端点"""
        try:
            response = requests.get(f"{self.server_url}/mcp/capabilities", timeout=5)

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "MCP能力测试",
                    True,
                    f"服务器能力: {list(data.keys()) if isinstance(data, dict) else '获取成功'}",
                    data
                )
                return True
            else:
                self.log_result("MCP能力测试", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("MCP能力测试", False, f"请求失败: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始Cursor MCP功能测试")
        print("=" * 50)

        tests = [
            self.test_server_health,
            self.test_mcp_capabilities,
            self.test_general_command,
            self.test_nmap_tool,
            self.test_sqlmap_tool,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # 测试间隔

        print("\n" + "=" * 50)
        print(f"📊 测试完成: {passed}/{total} 通过")

        # 生成测试报告
        self.generate_report()

        return passed == total

    def generate_report(self):
        """生成测试报告"""
        report = {
            "测试时间": time.strftime("%Y-%m-%d %H:%M:%S"),
            "服务器地址": self.server_url,
            "测试结果": self.test_results,
            "总结": {
                "总测试数": len(self.test_results),
                "通过数": sum(1 for r in self.test_results if r["success"]),
                "失败数": sum(1 for r in self.test_results if not r["success"])
            }
        }

        # 保存报告
        report_file = f"cursor_mcp_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 测试报告已保存: {report_file}")

        # 显示详细结果
        print("\n📋 详细测试结果:")
        for result in self.test_results:
            status = "✅ 通过" if result["success"] else "❌ 失败"
            print(f"  {status} {result['test']}")
            if not result["success"]:
                print(f"    错误: {result['message']}")

def main():
    """主函数"""
    print("Cursor MCP Kali系统测试工具")
    print("请确保WSL Kali服务器正在运行...")
    print()

    tester = CursorMCPTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 所有测试通过！Cursor MCP系统可以正常使用。")
        print("\n📋 下一步:")
        print("1. 重启Cursor IDE")
        print("2. 在Cursor中使用MCP工具")
        print("3. 查看使用指南: CURSOR_MCP_GUIDE.md")
    else:
        print("\n⚠️ 部分测试失败，请检查系统配置。")
        print("📋 故障排除:")
        print("1. 确认WSL Kali服务器运行状态")
        print("2. 检查端口5001是否被占用")
        print("3. 重启相关服务")

if __name__ == "__main__":
    main()