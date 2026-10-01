#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作网站扫描测试工具
Working Website Scanner Test Tool

测试完全可访问的网站，确保工具正常工作
"""

import requests
import json
import time
from datetime import datetime

class WorkingTestScanner:
    def __init__(self):
        self.targets = [
            {
                "name": "GitHub",
                "url": "https://github.com",
                "category": "development"
            },
            {
                "name": "Stack Overflow",
                "url": "https://stackoverflow.com",
                "category": "qa"
            },
            {
                "name": "Wikipedia",
                "url": "https://wikipedia.org",
                "category": "information"
            },
            {
                "name": "Google",
                "url": "https://google.com",
                "category": "search"
            }
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.results = []

    def basic_security_check(self, url: str) -> dict:
        """基本安全检查"""
        try:
            response = self.session.get(url, timeout=15, verify=False)

            # 基本信息收集
            result = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.text),
                "server": response.headers.get('Server', ''),
                "content_type": response.headers.get('Content-Type', ''),
                "response_time": response.elapsed.total_seconds(),
                "title": "",
                "technologies": [],
                "potential_issues": []
            }

            # 提取标题
            if response.text:
                import re
                title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
                if title_match:
                    result["title"] = title_match.group(1).strip()

            # 检测技术栈
            tech_indicators = {
                "php": ["php", "php/", ".php"],
                "asp": ["asp", "aspx", "asp.net"],
                "jsp": ["jsp", "servlet"],
                "node.js": ["node.js", "express"],
                "python": ["python", "django", "flask"],
                "ruby": ["ruby", "rails"],
                "wordpress": ["wp-content", "wp-includes"],
                "drupal": ["drupal"],
                "joomla": ["joomla"],
                "apache": ["apache", "apache/", "mod_"],
                "nginx": ["nginx", "nginx/"],
                "iis": ["microsoft-iis", "iis"]
            }

            for tech, indicators in tech_indicators.items():
                if any(indicator.lower() in response.text.lower() for indicator in indicators):
                    result["technologies"].append(tech)

            # 检测潜在安全问题
            security_checks = {
                "directory_listing": ["index of", "parent directory", "directory listing"],
                "error_disclosure": ["error", "exception", "fatal error", "traceback"],
                "version_disclosure": ["/wp-content/", "/wp-includes/", "/phpmyadmin/", "powered by"],
                "exposed_services": [".git/", ".svn/", "backup", "config"]
            }

            for issue_type, indicators in security_checks.items():
                matches = [indicator for indicator in indicators
                          if indicator.lower() in response.text.lower()]
                if matches:
                    result["potential_issues"].append({
                        "type": issue_type,
                        "indicators": matches
                    })

            return result

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status_code": None,
                "accessibility": "failed"
            }

    def scan_targets(self):
        """扫描所有目标"""
        print("=== 工作网站扫描测试 ===")
        print("开始扫描完全可访问的测试网站...")
        print(f"扫描目标数量: {len(self.targets)}")

        accessible_count = 0
        failed_count = 0

        for target in self.targets:
            print(f"\n扫描目标: {target['name']} ({target['url']})")

            result = self.basic_security_check(target['url'])
            result['name'] = target['name']
            result['category'] = target['category']
            result['timestamp'] = datetime.now().isoformat()

            if result['status_code'] == 200:
                accessible_count += 1
                print(f"[OK] 状态码: {result['status_code']}")
                print(f"[OK] 响应时间: {result['response_time']:.2f}秒")
                print(f"[OK] 内容长度: {result['content_length']}")
                print(f"[OK] 标题: {result['title'][:50]}..." if result['title'] else "[OK] 标题: 无")
                print(f"[OK] 服务器信息: {result['server']}")

                if result['technologies']:
                    print(f"[OK] 检测到的技术: {', '.join(result['technologies'])}")

                if result['potential_issues']:
                    print("[WARNING] 潜在问题:")
                    for issue in result['potential_issues']:
                        print(f"  - {issue['type']}: {', '.join(issue['indicators'][:2])}")

            else:
                failed_count += 1
                print(f"[ERROR] 访问失败: {result.get('error', 'Unknown error')}")

            self.results.append(result)

        print(f"\n=== 扫描完成 ===")
        print(f"可访问: {accessible_count}")
        print(f"失败: {failed_count}")
        print(f"成功率: {accessible_count/len(self.targets)*100:.1f}%")

    def generate_report(self):
        """生成报告"""
        if not self.results:
            return "没有扫描结果"

        report = []
        report.append("=" * 60)
        report.append("工作网站扫描测试报告")
        report.append("Working Website Scan Test Report")
        report.append("=" * 60)
        report.append(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"扫描目标总数: {len(self.targets)}")
        report.append("")

        # 统计信息
        accessible = len([r for r in self.results if r['status_code'] == 200])
        failed = len([r for r in self.results if r['status_code'] != 200])

        report.append("访问统计:")
        report.append(f"- 成功访问: {accessible}")
        report.append(f"- 访问失败: {failed}")
        report.append(f"- 成功率: {accessible/len(self.results)*100:.1f}%")
        report.append("")

        # 详细结果
        for result in self.results:
            status_icon = "[OK]" if result['status_code'] == 200 else "[ERROR]"
            report.append(f"[{status_icon}] {result['name']} ({result['url']})")
            report.append(f"  状态码: {result['status_code']}")
            report.append(f"  响应时间: {result['response_time']:.2f}秒")
            report.append(f"  内容长度: {result['content_length']}")
            report.append(f"  服务器: {result['server']}")
            report.append(f"  标题: {result['title'][:50]}..." if result['title'] else "  标题: 无")

            if result.get('technologies'):
                report.append(f"  技术栈: {', '.join(result['technologies'])}")

            if result.get('potential_issues'):
                report.append("  潜在问题:")
                for issue in result['potential_issues']:
                    report.append(f"    - {issue['type']}: {', '.join(issue['indicators'][:2])}")

            if result.get('error'):
                report.append(f"  错误: {result['error']}")

            report.append("")

        return "\n".join(report)

    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"working_test_scan_{timestamp}.json"
        txt_filename = f"working_test_scan_{timestamp}.txt"

        # 保存JSON格式
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            # 保存文本报告
            report = self.generate_report()
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\n[SUCCESS] 结果已保存:")
            print(f"  JSON格式: {json_filename}")
            print(f"  文本报告: {txt_filename}")

            return json_filename, txt_filename

        except Exception as e:
            print(f"[ERROR] 保存结果失败: {e}")
            return None, None

def main():
    """主函数"""
    print("Dragon-V Working Website Test Scanner")
    print("工作网站测试扫描工具")
    print("=" * 40)

    scanner = WorkingTestScanner()
    scanner.scan_targets()

    print("\n" + "=" * 40)
    report = scanner.generate_report()
    print(report)

    scanner.save_results()

if __name__ == "__main__":
    main()