#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版自动化报告生成系统 - 兼容Windows控制台
Final Automated Report Generation System - Windows Console Compatible
"""

import json
import time
import os
import glob
from datetime import datetime
import requests
import re
import csv
from pathlib import Path

class FinalReportGenerator:
    """最终版报告生成器"""

    def __init__(self):
        self.report_data = {
            "generation_time": datetime.now().isoformat(),
            "summary": {},
            "targets": [],
            "recommendations": []
        }

        # 泰国贷款目标数据库
        self.thai_targets = {
            "MoneyCat Thailand": {
                "url": "https://www.moneycat.co.th",
                "type": "在线贷款平台",
                "priority": "高"
            },
            "Mula-X": {
                "url": "https://mula-x.com",
                "type": "私人贷款平台",
                "priority": "高"
            },
            "Rocket Cash": {
                "url": "https://www.rocket-cash.com",
                "type": "微型贷款平台",
                "priority": "中"
            },
            "KLoan Thailand": {
                "url": "https://kloan.co.th",
                "type": "个人贷款平台",
                "priority": "高"
            },
            "NgoenMun Finance": {
                "url": "https://ngoenmun.com",
                "type": "金融科技公司",
                "priority": "高"
            },
            "Peacoop Credit Union": {
                "url": "https://peacoop.or.th",
                "type": "信用合作社",
                "priority": "中"
            },
            "Ngern Tid Lor": {
                "url": "https://www.ngerntidlor.com",
                "type": "汽车抵押贷款",
                "priority": "中"
            }
        }

    def check_target_accessibility(self):
        """检查目标可访问性"""
        print("检查泰国贷款目标可访问性...")

        results = []
        for name, info in self.thai_targets.items():
            target_data = {
                "name": name,
                "url": info["url"],
                "type": info["type"],
                "priority": info["priority"],
                "accessible": False,
                "status_code": None,
                "response_time": None,
                "vulnerability_count": 0
            }

            try:
                response = requests.get(info["url"], timeout=10, verify=False)
                target_data["accessible"] = True
                target_data["status_code"] = response.status_code
                target_data["response_time"] = round(response.elapsed.total_seconds(), 2)

                print(f"  [OK] {name} - 可访问 (状态码: {response.status_code})")
            except Exception as e:
                print(f"  [FAIL] {name} - 不可访问 ({str(e)[:50]})")

            results.append(target_data)

        return results

    def scan_for_reports(self):
        """扫描现有的报告文件"""
        print("扫描现有攻击报告...")

        reports = {}

        # 扫描JSON报告
        json_files = glob.glob("*report*.json")
        json_files.extend(glob.glob("thai_loan_quick_test_report_*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports[json_file] = data
                    print(f"  [OK] 找到报告: {json_file}")
            except Exception as e:
                print(f"  [FAIL] 读取报告失败 {json_file}: {e}")

        return reports

    def analyze_vulnerabilities(self, reports, targets):
        """分析漏洞信息"""
        print("分析漏洞信息...")

        for target in targets:
            for report_file, report_data in reports.items():
                if "results" in report_data:
                    for result in report_data["results"]:
                        if isinstance(result, dict) and "url" in result:
                            if target["url"] in result["url"] or target["name"].lower() in report_file.lower():
                                if "vulnerability_count" in result:
                                    target["vulnerability_count"] = result["vulnerability_count"]
                                elif "vulnerabilities" in result:
                                    target["vulnerability_count"] += len(result["vulnerabilities"])

                if "scan_results" in report_data:
                    for scan_result in report_data["scan_results"]:
                        if isinstance(scan_result, dict) and "target" in scan_result:
                            if target["url"] in scan_result["target"] or target["name"] == scan_result.get("name", ""):
                                if "vulnerabilities" in scan_result:
                                    target["vulnerability_count"] += len(scan_result["vulnerabilities"])

        return targets

    def generate_recommendations(self):
        """生成安全建议"""
        return [
            {
                "category": "SQL注入防护",
                "priority": "高",
                "recommendation": "实施参数化查询和输入验证",
                "description": "所有用户输入必须进行严格验证，使用参数化查询防止SQL注入攻击"
            },
            {
                "category": "WAF部署",
                "priority": "高",
                "recommendation": "部署Web应用防火墙",
                "description": "建议部署Cloudflare或ModSecurity等WAF解决方案"
            },
            {
                "category": "API安全",
                "priority": "中",
                "recommendation": "加强API端点安全",
                "description": "实施API密钥认证、速率限制和输入验证"
            },
            {
                "category": "数据加密",
                "priority": "高",
                "recommendation": "敏感数据加密存储",
                "description": "用户个人信息和财务数据必须使用强加密算法存储"
            }
        ]

    def calculate_summary(self, targets):
        """计算汇总信息"""
        total_targets = len(targets)
        accessible_targets = sum(1 for t in targets if t["accessible"])
        vulnerable_targets = sum(1 for t in targets if t["vulnerability_count"] > 0)
        high_priority_targets = sum(1 for t in targets if t["priority"] == "高")

        security_score = 0
        if total_targets > 0:
            security_score = round((1 - vulnerable_targets / total_targets) * 100, 2)

        return {
            "total_targets": total_targets,
            "accessible_targets": accessible_targets,
            "vulnerable_targets": vulnerable_targets,
            "high_priority_targets": high_priority_targets,
            "security_score": security_score
        }

    def generate_html_report(self, targets, summary, recommendations, filename="thai_loan_security_report.html"):
        """生成HTML报告"""

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>泰国贷款平台安全评估报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -30px -30px 30px -30px;
            border-radius: 10px 10px 0 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .target-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 15px 0;
            overflow: hidden;
        }}
        .target-header {{
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .target-body {{
            padding: 15px;
        }}
        .status-accessible {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-inaccessible {{
            color: #dc3545;
            font-weight: bold;
        }}
        .priority-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        .priority-medium {{
            color: #ffc107;
            font-weight: bold;
        }}
        .vulnerability-badge {{
            background: #dc3545;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .recommendation-card {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }}
        .recommendation-high {{
            border-left: 4px solid #dc3545;
        }}
        .recommendation-medium {{
            border-left: 4px solid #ffc107;
        }}
        .footer {{
            margin-top: 50px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>泰国贷款平台安全评估报告</h1>
            <p>自动化安全测试结果综合分析</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>总测试目标</h3>
                <div class="number">{summary['total_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>可访问目标</h3>
                <div class="number">{summary['accessible_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>高优先级目标</h3>
                <div class="number">{summary['high_priority_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>发现漏洞目标</h3>
                <div class="number">{summary['vulnerable_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>安全评分</h3>
                <div class="number">{summary['security_score']}%</div>
            </div>
        </div>

        <h2>目标安全分析</h2>
        {self._generate_targets_html(targets)}

        <h2>安全建议</h2>
        {self._generate_recommendations_html(recommendations)}

        <div class="footer">
            <p>本报告由自动化安全测试系统生成</p>
            <p>测试范围: 泰国主要在线贷款平台</p>
            <p>测试目的: 安全评估和漏洞发现</p>
        </div>
    </div>
</body>
</html>
        """

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filename

    def _generate_targets_html(self, targets):
        """生成目标HTML"""
        html = ""
        for target in targets:
            status_class = "status-accessible" if target["accessible"] else "status-inaccessible"
            priority_class = "priority-high" if target["priority"] == "高" else "priority-medium"

            vuln_badge = ""
            if target["vulnerability_count"] > 0:
                vuln_badge = f'<span class="vulnerability-badge">{target["vulnerability_count"]} 漏洞</span>'

            response_info = ""
            if target["status_code"]:
                response_info = f'<p><strong>状态码:</strong> {target["status_code"]}</p>'
            if target["response_time"]:
                response_info += f'<p><strong>响应时间:</strong> {target["response_time"]}秒</p>'

            html += f"""
            <div class="target-card">
                <div class="target-header">
                    <div>
                        <h4>{target['name']}</h4>
                        <p>{target['type']} - {target['url']}</p>
                    </div>
                    <div>
                        {vuln_badge}
                        <span class="{priority_class}">{target['priority']}优先级</span>
                    </div>
                </div>
                <div class="target-body">
                    <p><strong>可访问性:</strong> <span class="{status_class}">{'可访问' if target['accessible'] else '不可访问'}</span></p>
                    {response_info}
                    <p><strong>漏洞数量:</strong> {target['vulnerability_count']}</p>
                </div>
            </div>
            """
        return html

    def _generate_recommendations_html(self, recommendations):
        """生成建议HTML"""
        html = ""
        for rec in recommendations:
            priority_class = f"recommendation-{rec['priority'].lower() if rec['priority'] in ['high', 'medium'] else 'medium'}"

            html += f"""
            <div class="recommendation-card {priority_class}">
                <h4>{rec['category']} - {rec['priority']}优先级</h4>
                <h5>{rec['recommendation']}</h5>
                <p>{rec['description']}</p>
            </div>
            """
        return html

    def generate_csv_report(self, targets, filename="thai_loan_security_summary.csv"):
        """生成CSV报告"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['目标名称', 'URL', '类型', '优先级', '可访问性', '漏洞数量', '状态码', '响应时间']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for target in targets:
                writer.writerow({
                    '目标名称': target['name'],
                    'URL': target['url'],
                    '类型': target['type'],
                    '优先级': target['priority'],
                    '可访问性': '可访问' if target['accessible'] else '不可访问',
                    '漏洞数量': target['vulnerability_count'],
                    '状态码': target.get('status_code', 'N/A'),
                    '响应时间': f"{target.get('response_time', 'N/A')}秒"
                })

        return filename

    def generate_all_reports(self):
        """生成所有报告"""
        print("正在生成自动化安全评估报告...")

        # 检查目标可访问性
        targets = self.check_target_accessibility()

        # 扫描现有报告
        reports = self.scan_for_reports()

        # 分析漏洞
        targets = self.analyze_vulnerabilities(reports, targets)

        # 计算汇总
        summary = self.calculate_summary(targets)

        # 生成建议
        recommendations = self.generate_recommendations()

        # 生成HTML报告
        html_file = self.generate_html_report(targets, summary, recommendations)
        print(f"HTML报告已生成: {html_file}")

        # 生成CSV报告
        csv_file = self.generate_csv_report(targets)
        print(f"CSV报告已生成: {csv_file}")

        # 生成JSON报告
        json_file = "thai_loan_security_report.json"
        self.report_data.update({
            "summary": summary,
            "targets": targets,
            "recommendations": recommendations,
            "existing_reports": list(reports.keys())
        })

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)
        print(f"JSON报告已生成: {json_file}")

        # 打印摘要
        print(f"\n=== 报告摘要 ===")
        print(f"总测试目标: {summary['total_targets']}")
        print(f"可访问目标: {summary['accessible_targets']}")
        print(f"高优先级目标: {summary['high_priority_targets']}")
        print(f"发现漏洞目标: {summary['vulnerable_targets']}")
        print(f"整体安全评分: {summary['security_score']}%")

        return {
            'html': html_file,
            'csv': csv_file,
            'json': json_file
        }

def main():
    """主函数"""
    generator = FinalReportGenerator()

    try:
        reports = generator.generate_all_reports()
        print(f"\n所有报告生成完成！")
        print(f"报告文件:")
        for format_type, file_path in reports.items():
            print(f"  {format_type.upper()}: {file_path}")

    except KeyboardInterrupt:
        print("\n报告生成已取消")
    except Exception as e:
        print(f"报告生成错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()