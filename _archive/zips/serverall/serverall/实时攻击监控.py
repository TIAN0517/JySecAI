#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时攻击监控器 - 监控所有SQLMap攻击进展
Real-time Attack Monitor - Monitor All SQLMap Attack Progress
"""

import subprocess
import time
import os
import json
from datetime import datetime

class RealTimeAttackMonitor:
    def __init__(self):
        self.running_attacks = []
        self.successful_attacks = []
        self.failed_attacks = []
        self.output_dir = f"attack_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)

    def monitor_attacks(self):
        """监控所有攻击"""
        print("=" * 80)
        print("[监控] 实时攻击监控器启动")
        print("=" * 80)
        print(f"监控目录: {self.output_dir}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        while True:
            try:
                # 获取所有运行的SQLMap进程
                sqlmap_processes = self.get_sqlmap_processes()

                if sqlmap_processes:
                    print(f"\n[监控] 发现 {len(sqlmap_processes)} 个活跃SQLMap攻击:")
                    for i, process in enumerate(sqlmap_processes, 1):
                        print(f"  {i}. PID: {process['pid']} - {process['cmd'][:100]}...")

                        # 检查是否有新的输出
                        self.check_process_output(process)
                else:
                    print(f"\n[监控] 未发现活跃的SQLMap攻击进程")

                # 检查是否有新的SQLMap攻击启动
                self.check_new_attacks()

                # 生成状态报告
                self.generate_status_report()

                # 等待30秒再次检查
                time.sleep(30)

            except KeyboardInterrupt:
                print("\n[监控] 监控器停止")
                break
            except Exception as e:
                print(f"[错误] 监控异常: {e}")
                time.sleep(10)

    def get_sqlmap_processes(self):
        """获取所有SQLMap进程"""
        try:
            # 使用tasklist获取所有进程
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                                  capture_output=True, text=True)

            sqlmap_processes = []
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行

            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')

                        # 检查这个进程是否是SQLMap
                        cmd_result = subprocess.run(['wmic', 'process', 'where', f'processid={pid}', 'get', 'commandline', '/value'],
                                                  capture_output=True, text=True)

                        if 'sqlmap' in cmd_result.stdout.lower():
                            sqlmap_processes.append({
                                'pid': pid,
                                'cmd': cmd_result.stdout.strip()
                            })

            return sqlmap_processes

        except Exception as e:
            print(f"[错误] 获取SQLMap进程失败: {e}")
            return []

    def check_process_output(self, process):
        """检查进程输出（这里简化处理）"""
        pid = process['pid']

        # 检查是否有临时输出文件
        temp_files = []
        for file in os.listdir('.'):
            if file.startswith('sqlmap') and file.endswith('.txt'):
                temp_files.append(file)

        if temp_files:
            print(f"    [发现] 临时输出文件: {temp_files}")

    def check_new_attacks(self):
        """检查新的攻击"""
        # 检查新的SQLMap输出目录
        for item in os.listdir('.'):
            if item.startswith('advanced_penetration_') and os.path.isdir(item):
                if item not in [attack['dir'] for attack in self.running_attacks]:
                    print(f"\n[发现] 新的高级渗透攻击目录: {item}")
                    self.running_attacks.append({
                        'dir': item,
                        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'running'
                    })

    def generate_status_report(self):
        """生成状态报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, f"attack_status_{timestamp}.json")

        report = {
            "monitoring_session": {
                "timestamp": timestamp,
                "total_running_attacks": len(self.running_attacks),
                "successful_attacks": len(self.successful_attacks),
                "failed_attacks": len(self.failed_attacks)
            },
            "running_attacks": self.running_attacks,
            "successful_attacks": self.successful_attacks,
            "failed_attacks": self.failed_attacks,
            "system_info": {
                "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "monitor_duration": "监控进行中..."
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[报告] 状态报告已生成: {report_file}")

def main():
    """主函数"""
    print("=" * 50)
    print("实时攻击监控器 v1.0")
    print("Real-time Attack Monitor v1.0")
    print("=" * 50)
    print("监控所有SQLMap攻击进展")
    print("按 Ctrl+C 停止监控")
    print("=" * 50)

    monitor = RealTimeAttackMonitor()
    monitor.monitor_attacks()

if __name__ == "__main__":
    main()