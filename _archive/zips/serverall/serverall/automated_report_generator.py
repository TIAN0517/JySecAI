#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化报告生成系统
Automated Report Generation System

整合所有攻击结果，生成综合性漏洞报告
支持多格式输出：HTML、JSON、CSV
"""

import sqlite3
import json
import time
import os
import glob
from datetime import datetime
import requests
import re
from pathlib import Path
import csv
import html

class AutomatedReportGenerator:
    """自动化报告生成器"""

    def __init__(self):
        self.report_data = {
            "generation_time": datetime.now().isoformat(),
            "scan_summary": {},
            "target_results": [],
            "vulnerability_analysis": {},
            "exploitation_results": {},
            "recommendations": []
        }

        # 泰国贷款目标数据库
        self.thai_targets = {
            "MoneyCat Thailand": {
                "url": "https://www.moneycat.co.th",
                "type": "在线贷款平台",
                "priority": "高",
                "description": "面向个人消费者的快速贷款服务"
            },
            "Mula-X": {
                "url": "https://mula-x.com",
                "type": "私人贷款平台",
                "priority": "高",
                "description": "无抵押个人贷款服务提供商"
            },
            "Rocket Cash": {
                "url": "https://www.rocket-cash.com",
                "type": "微型贷款平台",
                "priority": "中",
                "description": "小额短期贷款服务"
            },
            "KLoan Thailand": {
                "url": "https://kloan.co.th",
                "type": "个人贷款平台",
                "priority": "高",
                "description": "个人消费贷款服务"
            },
            "NgoenMun Finance": {
                "url": "https://ngoenmun.com",
                "type": "金融科技公司",
                "priority": "高",
                "description": "数字金融服务平台"
            },
            "Peacoop Credit Union": {
                "url": "https://peacoop.or.th",
                "type": "信用合作社",
                "priority": "中",
                "description": "会员制金融服务机构"
            },
            "Ngern Tid Lor": {
                "url": "https://www.ngerntidlor.com",
                "type": "汽车抵押贷款",
                "priority": "中",
                "description": "汽车抵押贷款服务"
            }
        }

    def collect_sqlmap_results(self):
        """收集SQLMap攻击结果"""
        sqlmap_results = {}

        # 扫描SQLMap输出目录
        sqlmap_output_dir = os.path.expanduser("~/AppData/Local/sqlmap/output")
        if os.path.exists(sqlmap_output_dir):
            for target_dir in os.listdir(sqlmap_output_dir):
                target_path = os.path.join(sqlmap_output_dir, target_dir)
                if os.path.isdir(target_path):
                    # 读取log文件
                    log_file = os.path.join(target_path, "log")
                    if os.path.exists(log_file):
                        try:
                            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                log_content = f.read()

                            # 解析SQLMap结果
                            sqlmap_results[target_dir] = {
                                "vulnerabilities_found": [],
                                "database_info": {},
                                "tables": [],
                                "injection_points": []
                            }

                            # 检测注入点
                            if "injection point(s) from stored session" in log_content:
                                sqlmap_results[target_dir]["injection_points"].append("发现SQL注入点")

                            # 检测数据库信息
                            if "back-end DBMS is MySQL" in log_content:
                                sqlmap_results[target_dir]["database_info"]["dbms"] = "MySQL"
                            if "banner:" in log_content:
                                banner_match = re.search(r"banner: '([^']+)'", log_content)
                                if banner_match:
                                    sqlmap_results[target_dir]["database_info"]["version"] = banner_match.group(1)

                            # 检测数据库名
                            if "available databases" in log_content:
                                db_match = re.findall(r"\[([^\]]+)\]", log_content)
                                sqlmap_results[target_dir]["database_info"]["databases"] = db_match

                        except Exception as e:
                            print(f"读取SQLMap结果失败 {target_dir}: {e}")

        return sqlmap_results

    def collect_monitoring_results(self):
        """收集实时监控结果"""
        monitoring_results = {}

        # 检查监控数据库
        db_files = [
            'real_time_exploit_monitor.db',
            'real_time_exploit_monitor_simple.db',
            'thai_loan_exploits.db',
            'dragon_triple_functional.db'
        ]

        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()

                    # 获取表信息
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()

                    monitoring_results[db_file] = {
                        "tables": [table[0] for table in tables],
                        "total_records": 0
                    }

                    # 统计记录数
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                            count = cursor.fetchone()[0]
                            monitoring_results[db_file]["total_records"] += count
                        except:
                            pass

                    conn.close()
                except Exception as e:
                    print(f"读取监控数据库失败 {db_file}: {e}")

        return monitoring_results

    def collect_json_reports(self):
        """收集JSON格式的攻击报告"""
        json_reports = {}

        # 扫描JSON报告文件
        json_files = glob.glob("*.json")
        json_files.extend(glob.glob("*_report_*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    json_reports[json_file] = data
            except Exception as e:
                print(f"读取JSON报告失败 {json_file}: {e}")

        return json_reports

    def analyze_thai_loan_security(self):
        """分析泰国贷款平台安全状况"""
        security_analysis = {
            "total_targets": len(self.thai_targets),
            "high_priority_targets": 0,
            "vulnerable_targets": 0,
            "security_score": 0,
            "target_analysis": []
        }

        for name, info in self.thai_targets.items():
            target_analysis = {
                "name": name,
                "url": info["url"],
                "type": info["type"],
                "priority": info["priority"],
                "vulnerability_count": 0,
                "critical_vulnerabilities": [],
                "accessibility": "unknown"
            }

            # 检查可访问性
            try:
                response = requests.get(info["url"], timeout=10, verify=False)
                target_analysis["accessibility"] = "accessible" if response.status_code == 200 else "error"
                target_analysis["status_code"] = response.status_code
            except:
                target_analysis["accessibility"] = "inaccessible"

            # 检查相关报告文件
            json_reports = self.collect_json_reports()
            for report_file, report_data in json_reports.items():
                if name.lower() in report_file.lower() or info["url"] in str(report_data):
                    if "vulnerabilities" in report_data:
                        target_analysis["vulnerability_count"] += len(report_data["vulnerabilities"])
                    if "results" in report_data:
                        for result in report_data["results"]:
                            if isinstance(result, dict) and "vulnerabilities" in result:
                                target_analysis["vulnerability_count"] += len(result["vulnerabilities"])

            if target_analysis["vulnerability_count"] > 0:
                security_analysis["vulnerable_targets"] += 1

            if info["priority"] == "高":
                security_analysis["high_priority_targets"] += 1

            security_analysis["target_analysis"].append(target_analysis)

        # 计算安全评分
        if security_analysis["total_targets"] > 0:
            security_analysis["security_score"] = round(
                (1 - security_analysis["vulnerable_targets"] / security_analysis["total_targets"]) * 100, 2
            )

        return security_analysis

    def generate_recommendations(self):
        """生成安全建议"""
        recommendations = [
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
            },
            {
                "category": "安全监控",
                "priority": "中",
                "recommendation": "建立实时安全监控系统",
                "description": "部署入侵检测系统和异常流量监控"
            }
        ]

        return recommendations

    def generate_html_report(self, output_file="thai_loan_security_report.html"):
        """生成HTML格式报告"""

        # 收集所有数据
        sqlmap_results = self.collect_sqlmap_results()
        monitoring_results = self.collect_monitoring_results()
        json_reports = self.collect_json_reports()
        security_analysis = self.analyze_thai_loan_security()
        recommendations = self.generate_recommendations()

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>泰国贷款平台安全评估报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .summary-card .number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .target-section {{
            margin: 30px 0;
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
        .vulnerability-count {{
            background: #dc3545;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .recommendations {{
            margin: 30px 0;
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
        .methodology {{
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
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
                <div class="number">{security_analysis['total_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>高优先级目标</h3>
                <div class="number">{security_analysis['high_priority_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>发现漏洞目标</h3>
                <div class="number">{security_analysis['vulnerable_targets']}</div>
            </div>
            <div class="summary-card">
                <h3>安全评分</h3>
                <div class="number">{security_analysis['security_score']}%</div>
            </div>
        </div>

        <div class="methodology">
            <h2>测试方法论</h2>
            <ul>
                <li><strong>SQL注入测试:</strong> 使用SQLMap进行自动化SQL注入检测</li>
                <li><strong>XSS检测:</strong> 跨站脚本漏洞扫描和验证</li>
                <li><strong>API安全测试:</strong> REST API端点安全性评估</li>
                <li><strong>业务逻辑测试:</strong> 贷款申请流程逻辑漏洞检测</li>
                <li><strong>实时监控:</strong> 攻击进程监控和结果收集</li>
            </ul>
        </div>

        <div class="target-section">
            <h2>目标安全分析</h2>
            {self._generate_target_html(security_analysis['target_analysis'])}
        </div>

        <div class="recommendations">
            <h2>安全建议</h2>
            {self._generate_recommendations_html(recommendations)}
        </div>

        <div class="footer">
            <p>本报告由自动化安全测试系统生成</p>
            <p>测试范围: 泰国主要在线贷款平台</p>
            <p>测试目的: 安全评估和漏洞发现</p>
        </div>
    </div>
</body>
</html>
        """

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        return output_file

    def _generate_target_html(self, target_analysis):
        """生成目标分析HTML"""
        html = ""
        for target in target_analysis:
            status_class = "status-accessible" if target["accessibility"] == "accessible" else "status-inaccessible"
            priority_class = "priority-high" if target["priority"] == "高" else "priority-medium"

            vuln_badge = ""
            if target["vulnerability_count"] > 0:
                vuln_badge = f'<span class="vulnerability-count">{target["vulnerability_count"]} 漏洞</span>'

            html += f"""
            <div class="target-card">
                <div class="target-header">
                    <div>
                        <h4>{html.escape(target['name'])}</h4>
                        <p>{html.escape(target['type'])} - {html.escape(target['url'])}</p>
                    </div>
                    <div>
                        {vuln_badge}
                        <span class="{priority_class}">{html.escape(target['priority'])}优先级</span>
                    </div>
                </div>
                <div class="target-body">
                    <p><strong>可访问性:</strong> <span class="{status_class}">{html.escape(target['accessibility'])}</span></p>
                    <p><strong>描述:</strong> {html.escape(self.thai_targets[target['name']]['description'])}</p>
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
                <h4>{html.escape(rec['category'])} - {html.escape(rec['priority'])}优先级</h4>
                <h5>{html.escape(rec['recommendation'])}</h5>
                <p>{html.escape(rec['description'])}</p>
            </div>
            """
        return html

    def generate_json_report(self, output_file="thai_loan_security_report.json"):
        """生成JSON格式报告"""
        # 收集所有数据
        self.report_data.update({
            "sqlmap_results": self.collect_sqlmap_results(),
            "monitoring_results": self.collect_monitoring_results(),
            "json_reports": self.collect_json_reports(),
            "security_analysis": self.analyze_thai_loan_security(),
            "recommendations": self.generate_recommendations()
        })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)

        return output_file

    def generate_csv_report(self, output_file="thai_loan_security_summary.csv"):
        """生成CSV格式摘要报告"""
        security_analysis = self.analyze_thai_loan_security()

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['目标名称', 'URL', '类型', '优先级', '可访问性', '漏洞数量', '状态码']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for target in security_analysis['target_analysis']:
                writer.writerow({
                    '目标名称': target['name'],
                    'URL': target['url'],
                    '类型': target['type'],
                    '优先级': target['priority'],
                    '可访问性': target['accessibility'],
                    '漏洞数量': target['vulnerability_count'],
                    '状态码': target.get('status_code', 'N/A')
                })

        return output_file

    def generate_all_reports(self):
        """生成所有格式的报告"""
        reports = {}

        print("正在生成自动化安全评估报告...")

        # 生成HTML报告
        html_file = self.generate_html_report()
        reports['html'] = html_file
        print(f"HTML报告已生成: {html_file}")

        # 生成JSON报告
        json_file = self.generate_json_report()
        reports['json'] = json_file
        print(f"JSON报告已生成: {json_file}")

        # 生成CSV报告
        csv_file = self.generate_csv_report()
        reports['csv'] = csv_file
        print(f"CSV报告已生成: {csv_file}")

        # 打印摘要
        security_analysis = self.analyze_thai_loan_security()
        print(f"\n=== 报告摘要 ===")
        print(f"总测试目标: {security_analysis['total_targets']}")
        print(f"高优先级目标: {security_analysis['high_priority_targets']}")
        print(f"发现漏洞目标: {security_analysis['vulnerable_targets']}")
        print(f"整体安全评分: {security_analysis['security_score']}%")

        return reports

def main():
    """主函数"""
    generator = AutomatedReportGenerator()

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

if __name__ == "__main__":
    main()