#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾 Hanshin 网站验证工具
Taiwan Hanshin Website Validation Tool

专门验证 https://www.hanshin.com.tw/ 的可访问性和安全状态
"""

import requests
import json
import time
from datetime import datetime
import re

class HanshinValidator:
    def __init__(self):
        self.target = {
            "name": "Hanshin",
            "url": "https://www.hanshin.com.tw/",
            "category": "taiwan_business"
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.result = {}

    def validate_website(self):
        """验证网站可访问性和安全性"""
        print("=== Hanshin Website Validator ===")
        print(f"验证目标: {self.target['name']} ({self.target['url']})")
        print("开始验证过程...")
        print("-" * 50)

        try:
            # 基本访问验证
            print("[STEP 1] 基本可访问性验证...")
            response = self.session.get(self.target['url'], timeout=15, verify=False)
            self.result['basic_access'] = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'content_length': len(response.text),
                'headers': dict(response.headers),
                'success': response.status_code == 200
            }

            if response.status_code == 200:
                print(f"[OK] 状态码: {response.status_code}")
                print(f"[OK] 响应时间: {response.elapsed.total_seconds():.2f}秒")
                print(f"[OK] 内容长度: {len(response.text)} 字符")

                # 详细安全分析
                self.detailed_security_analysis(response)
            else:
                print(f"[ERROR] 访问失败: HTTP {response.status_code}")
                self.result['error'] = f"HTTP {response.status_code}"

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] 连接失败: {error_msg}")
            self.result['error'] = error_msg
            self.result['success'] = False

        return self.result

    def detailed_security_analysis(self, response):
        """详细安全分析"""
        print("\n[STEP 2] 详细安全分析...")

        # 提取基本信息
        content = response.text

        # 提取标题
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "无标题"
        print(f"[INFO] 网站标题: {title}")
        self.result['title'] = title

        # 服务器信息
        server = response.headers.get('Server', '未知')
        print(f"[INFO] 服务器: {server}")
        self.result['server'] = server

        # 技术栈检测
        print("[STEP 3] 技术栈检测...")
        technologies = self.detect_technologies(content)
        if technologies:
            print(f"[INFO] 检测到技术: {', '.join(technologies)}")
        else:
            print("[INFO] 未检测到特定技术栈")
        self.result['technologies'] = technologies

        # 安全漏洞检测
        print("[STEP 4] 安全漏洞检测...")
        security_issues = self.detect_security_issues(content)
        if security_issues:
            print("[WARNING] 发现潜在安全问题:")
            for issue in security_issues:
                print(f"  - {issue['type']}: {', '.join(issue['indicators'][:2])}")
        else:
            print("[INFO] 未发现明显安全问题")
        self.result['security_issues'] = security_issues

        # 台湾网站特定检测
        print("[STEP 5] 台湾网站特定检测...")
        taiwan_issues = self.detect_taiwan_specific_issues(content)
        if taiwan_issues:
            print("[INFO] 台湾网站特性:")
            for issue in taiwan_issues:
                print(f"  - {issue['type']}: {issue['description']}")
        self.result['taiwan_issues'] = taiwan_issues

        # 性能分析
        print("[STEP 6] 性能分析...")
        performance = self.analyze_performance(response)
        print(f"[INFO] 性能评估: {performance['status']}")
        self.result['performance'] = performance

        self.result['success'] = True
        self.result['overall_risk'] = self.calculate_risk_level(security_issues, performance)

    def detect_technologies(self, content):
        """检测技术栈"""
        tech_indicators = {
            "wordpress": ["wp-content", "wp-includes", "wp-admin", "/wp-"],
            "php": [".php", "php/", "php version", "x-powered-by"],
            "asp": [".asp", ".aspx", "asp.net", "microsoft-iis"],
            "joomla": ["joomla", "/administrator/", "com_joomla"],
            "drupal": ["drupal", "sites/default", "drupal.settings"],
            "apache": ["apache/", "server:", "apache/"],
            "nginx": ["nginx/", "server: nginx", "x-powered-by nginx"],
            "iis": ["microsoft-iis", "iis/", "x-aspnet-version"],
            "cloudflare": ["cloudflare", "cf-ray", "cdn-cgi"],
            "shopify": ["shopify", "cdn.shopify"],
            "wix": ["wix", "wixstatic"],
            "tawk": ["tawk.to", "tawkchat"],
            "google_analytics": ["google-analytics.com", "ga.js", "gtag.js"],
            "facebook_pixel": ["facebook.com/tr", "fbq"],
            "hotjar": ["hotjar", "hj.j"]
        }

        detected = []
        content_lower = content.lower()

        for tech, indicators in tech_indicators.items():
            if any(indicator.lower() in content_lower for indicator in indicators):
                detected.append(tech)

        return detected

    def detect_security_issues(self, content):
        """检测安全问题"""
        security_checks = {
            "error_disclosure": [
                "error", "exception", "fatal error", "traceback", "stack trace",
                "mysql", "microsoft ole db", "sql server", "oracle"
            ],
            "version_disclosure": [
                "version", "revision", "build", "powered by", "running on"
            ],
            "exposed_paths": [
                "/admin", "/administrator", "/phpmyadmin", "/wp-admin",
                "/.git/", "/.svn/", "/backup", "/config"
            ],
            "directory_listing": [
                "index of", "parent directory", "directory listing"
            ],
            "forms_analysis": [
                "form", "input", "password", "email", "submit"
            ],
            "javascript_files": [
                ".js", "javascript", "jquery", "bootstrap"
            ],
            "css_files": [".css", "stylesheet"],
            "iframe_content": ["<iframe", "<frame", "iframe"],
            "third_party_services": [
                "googleapis", "amazonaws", "azure", "cloudfront"
            ]
        }

        issues = []
        content_lower = content.lower()

        for issue_type, indicators in security_checks.items():
            matches = [indicator for indicator in indicators
                      if indicator.lower() in content_lower]
            if matches:
                issues.append({
                    'type': issue_type,
                    'indicators': matches[:5]  # 限制显示前5个
                })

        return issues

    def detect_taiwan_specific_issues(self, content):
        """台湾网站特定检测"""
        taiwan_checks = {
            "taiwan_content": {
                "indicators": ["台灣", "台灣", "中華民國", "taiwan"],
                "description": "包含繁体中文台湾相关内容"
            },
            "business_registration": {
                "indicators": ["統一編號", "營業登記", "公司登記", "商業登記"],
                "description": "可能包含商业登记信息"
            },
            "payment_methods": {
                "indicators": ["信用卡", "銀行轉帳", "atm", "webatm"],
                "description": "支持台湾本地支付方式"
            },
            "contact_info": {
                "indicators": ["tel:", "電話", "聯絡電話", "服務電話"],
                "description": "提供台湾电话号码"
            }
        }

        taiwan_issues = []
        content_lower = content.lower()

        for check_type, check_data in taiwan_checks.items():
            if any(indicator.lower() in content_lower for indicator in check_data["indicators"]):
                taiwan_issues.append({
                    'type': check_type,
                    'description': check_data["description"]
                })

        return taiwan_issues

    def analyze_performance(self, response):
        """性能分析"""
        response_time = response.elapsed.total_seconds()
        content_length = len(response.text)

        # 性能评估
        if response_time < 1.0 and content_length < 500000:
            status = "优秀"
            score = 10
        elif response_time < 2.0 and content_length < 1000000:
            status = "良好"
            score = 8
        elif response_time < 3.0:
            status = "一般"
            score = 6
        else:
            status = "较慢"
            score = 4

        return {
            'status': status,
            'response_time': response_time,
            'content_length': content_length,
            'score': score
        }

    def calculate_risk_level(self, security_issues, performance):
        """计算风险等级"""
        risk_score = 0

        # 安全问题权重
        security_weights = {
            "error_disclosure": 3,
            "version_disclosure": 2,
            "exposed_paths": 4,
            "directory_listing": 5,
            "forms_analysis": 1,
            "javascript_files": 0,
            "css_files": 0,
            "iframe_content": 1,
            "third_party_services": 0
        }

        for issue in security_issues:
            weight = security_weights.get(issue['type'], 1)
            risk_score += weight * len(issue['indicators'])

        # 性能调整
        risk_score += (10 - performance['score']) // 2

        # 风险等级评定
        if risk_score >= 15:
            return "HIGH"
        elif risk_score >= 8:
            return "MEDIUM"
        elif risk_score >= 3:
            return "LOW"
        else:
            return "MINIMAL"

    def generate_report(self):
        """生成验证报告"""
        if not self.result:
            return "没有验证结果"

        report = []
        report.append("=" * 60)
        report.append("台湾 Hanshin 网站验证报告")
        report.append("Taiwan Hanshin Website Validation Report")
        report.append("=" * 60)
        report.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"验证目标: {self.target['name']} ({self.target['url']})")
        report.append("")

        if self.result.get('success'):
            # 基本信息
            basic = self.result['basic_access']
            report.append("基本信息:")
            report.append(f"  状态码: {basic['status_code']}")
            report.append(f"  响应时间: {basic['response_time']:.2f}秒")
            report.append(f"  内容长度: {basic['content_length']} 字符")
            report.append("")

            # 详细信息
            if 'title' in self.result:
                report.append(f"网站标题: {self.result['title']}")

            if 'server' in self.result:
                report.append(f"服务器信息: {self.result['server']}")

            report.append(f"综合风险等级: {self.result['overall_risk']}")
            report.append("")

            # 技术栈
            if 'technologies' in self.result and self.result['technologies']:
                report.append(f"检测到的技术栈: {', '.join(self.result['technologies'])}")
                report.append("")

            # 安全问题
            if 'security_issues' in self.result and self.result['security_issues']:
                report.append("安全发现:")
                for issue in self.result['security_issues']:
                    report.append(f"  - {issue['type']}: {', '.join(issue['indicators'][:2])}")
                report.append("")

            # 台湾特性
            if 'taiwan_issues' in self.result and self.result['taiwan_issues']:
                report.append("台湾网站特性:")
                for issue in self.result['taiwan_issues']:
                    report.append(f"  - {issue['type']}: {issue['description']}")
                report.append("")

            # 性能
            if 'performance' in self.result:
                perf = self.result['performance']
                report.append(f"性能评估: {perf['status']}")
                report.append(f"  响应时间: {perf['response_time']:.2f}秒")
                report.append(f"  内容长度: {perf['content_length']} 字符")

        else:
            if 'error' in self.result:
                report.append(f"验证失败: {self.result['error']}")

        return "\n".join(report)

    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"hanshin_validation_{timestamp}.json"
        txt_filename = f"hanshin_validation_{timestamp}.txt"

        # 保存JSON格式
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.result, f, ensure_ascii=False, indent=2)

            # 保存文本报告
            report = self.generate_report()
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\n[SUCCESS] 验证结果已保存:")
            print(f"  JSON格式: {json_filename}")
            print(f"  文本报告: {txt_filename}")

            return json_filename, txt_filename

        except Exception as e:
            print(f"[ERROR] 保存结果失败: {e}")
            return None, None

def main():
    """主函数"""
    print("Dragon-V Hanshin Website Validator")
    print("台湾 Hanshin 网站验证工具")
    print("=" * 40)

    validator = HanshinValidator()
    result = validator.validate_website()

    print("\n" + "=" * 40)
    report = validator.generate_report()
    print(report)

    validator.save_results()

if __name__ == "__main__":
    main()