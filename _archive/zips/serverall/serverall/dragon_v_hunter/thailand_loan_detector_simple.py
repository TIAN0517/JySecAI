#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的泰国贷款系统漏洞检测工具
Simplified Thai Loan System Vulnerability Detector
"""

import requests
import json
import time
from datetime import datetime

class SimpleThailandLoanDetector:
    def __init__(self):
        self.targets = [
            {
                "name": "Kasikornbank",
                "url": "https://www.kasikornbank.com",
                "category": "commercial_bank"
            },
            {
                "name": "Bangkok Bank",
                "url": "https://www.bangkokbank.com",
                "category": "commercial_bank"
            },
            {
                "name": "SCB",
                "url": "https://www.scb.co.th",
                "category": "commercial_bank"
            }
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.results = []

    def detect_thai_keywords(self, content: str) -> bool:
        """检测泰语关键词"""
        thai_keywords = [
            "สินเชื่อ", "personal loan", "home loan", "credit card",
            "ผ่อนชำระ", "กู้ยืน", "บัตรเครดิต", "ธนาคาร"
        ]
        return any(keyword.lower() in content.lower() for keyword in thai_keywords)

    def basic_security_check(self, url: str) -> dict:
        """基本安全检查"""
        try:
            response = self.session.get(url, timeout=10, verify=False)

            # 基本信息收集
            result = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.text),
                "server": response.headers.get('Server', ''),
                "content_type": response.headers.get('Content-Type', ''),
                "thai_keywords_detected": self.detect_thai_keywords(response.text),
                "response_time": response.elapsed.total_seconds()
            }

            # 检测常见漏洞迹象
            security_indicators = {
                "information_disclosure": [
                    "server:", "apache", "nginx", "microsoft-iis",
                    "php/", "asp/", "jsp/"
                ],
                "error_handling": [
                    "error", "exception", "fatal", "warning",
                    "ora-", "mysql", "postgresql", "sql"
                ],
                "potential_vulnerabilities": [
                    "index of", "directory listing", "phpmyadmin",
                    "wp-content", "admin/login", "login.php"
                ]
            }

            for category, indicators in security_indicators.items():
                matches = [indicator for indicator in indicators
                          if indicator.lower() in response.text.lower()]
                if matches:
                    result[category] = matches

            return result

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status_code": None,
                "thai_keywords_detected": False
            }

    def scan_targets(self):
        """扫描所有目标"""
        print("开始泰国贷款系统安全扫描...")
        print(f"扫描目标数量: {len(self.targets)}")

        for target in self.targets:
            print(f"\n扫描目标: {target['name']} ({target['url']})")

            result = self.basic_security_check(target['url'])
            result['name'] = target['name']
            result['category'] = target['category']
            result['timestamp'] = datetime.now().isoformat()

            # 分析风险等级
            risk_score = 0
            vulnerabilities = []

            if result['thai_keywords_detected']:
                risk_score += 2
                vulnerabilities.append("检测到贷款相关关键词")

            if 'information_disclosure' in result:
                risk_score += 3
                vulnerabilities.extend(result['information_disclosure'])

            if 'error_handling' in result:
                risk_score += 2
                vulnerabilities.extend(result['error_handling'])

            if 'potential_vulnerabilities' in result:
                risk_score += 5
                vulnerabilities.extend(result['potential_vulnerabilities'])

            # 确定风险等级
            if risk_score >= 8:
                risk_level = "HIGH"
            elif risk_score >= 5:
                risk_level = "MEDIUM"
            elif risk_score >= 2:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"

            result['risk_level'] = risk_level
            result['risk_score'] = risk_score
            result['vulnerabilities'] = vulnerabilities

            self.results.append(result)

            print(f"风险等级: {risk_level}")
            print(f"风险分数: {risk_score}")
            if vulnerabilities:
                print("发现的问题:")
                for vuln in vulnerabilities[:3]:  # 只显示前3个问题
                    print(f"  - {vuln}")

    def generate_report(self):
        """生成报告"""
        if not self.results:
            return "没有扫描结果"

        report = []
        report.append("=" * 80)
        report.append("泰国贷款系统漏洞检测报告")
        report.append("Thai Loan System Vulnerability Detection Report")
        report.append("=" * 80)
        report.append(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"扫描目标总数: {len(self.targets)}")
        report.append("")

        # 统计汇总
        risk_levels = {}
        for result in self.results:
            level = result['risk_level']
            risk_levels[level] = risk_levels.get(level, 0) + 1

        report.append("风险分布统计:")
        for level, count in sorted(risk_levels.items()):
            report.append(f"- {level}: {count}")
        report.append("")

        # 详细结果
        for result in self.results:
            report.append(f"[{result['risk_level']}] {result['name']} ({result['url']})")
            report.append(f"  状态码: {result['status_code']}")
            report.append(f"  响应时间: {result['response_time']:.2f}秒")
            report.append(f"  内容长度: {result['content_length']}")
            report.append(f"  服务器信息: {result['server']}")
            report.append(f"  泰语关键词: {'是' if result['thai_keywords_detected'] else '否'}")
            report.append(f"  风险分数: {result['risk_score']}")

            if result.get('vulnerabilities'):
                report.append("  发现的漏洞:")
                for vuln in result['vulnerabilities']:
                    report.append(f"    - {vuln}")

            report.append("")

        return "\n".join(report)

    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"thailand_loan_scan_simple_{timestamp}.json"
        txt_filename = f"thailand_loan_scan_simple_{timestamp}.txt"

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
    print("Dragon-V Simplified Thai Loan System Detector")
    print("简化版泰国贷款系统检测工具")
    print("=" * 50)

    detector = SimpleThailandLoanDetector()
    detector.scan_targets()

    print("\n" + "=" * 50)
    report = detector.generate_report()
    print(report)

    detector.save_results()

if __name__ == "__main__":
    main()