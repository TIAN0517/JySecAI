#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时攻击状态监控器
监控所有SQLMap攻击进程的状态和进度
"""

import subprocess
import json
import time
import datetime
import os
import threading
from typing import Dict, List, Any

class AttackStatusMonitor:
    def __init__(self):
        self.attack_processes = {}
        self.start_time = datetime.datetime.now()
        self.status_log = []

    def get_running_sqlmap_processes(self) -> List[Dict]:
        """获取所有运行中的SQLMap进程"""
        try:
            # 获取所有Python进程
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                                  capture_output=True, text=True, timeout=10)

            processes = []
            lines = result.stdout.split('\n')

            for line in lines:
                if 'python.exe' in line and 'sqlmap' in line.lower():
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[1]
                        memory = parts[4] if len(parts) > 4 else 'Unknown'
                        processes.append({
                            'pid': pid,
                            'memory': memory,
                            'command': line
                        })

            return processes

        except Exception as e:
            print(f"获取进程列表失败: {e}")
            return []

    def check_sqlmap_output_files(self) -> Dict[str, Any]:
        """检查SQLMap输出文件"""
        output_dirs = []

        # 查找可能的输出目录
        for item in os.listdir('.'):
            if item.startswith('extract_') and os.path.isdir(item):
                output_dirs.append(item)

        results = {}
        for output_dir in output_dirs:
            try:
                files = os.listdir(output_dir)
                results[output_dir] = {
                    'files': files,
                    'file_count': len(files),
                    'size': sum(os.path.getsize(os.path.join(output_dir, f)) for f in files)
                }
            except:
                pass

        return results

    def analyze_attack_patterns(self) -> Dict[str, Any]:
        """分析攻击模式"""
        running_processes = self.get_running_sqlmap_processes()

        targets = {
            'QuickCash.in.th': 0,
            'NgoenMun.com': 0,
            'Peacoop.or.th': 0,
            'MoneyCat.co.th': 0,
            'Mula-X.com': 0,
            'Rocket-Cash.com': 0,
            'KLoan.co.th': 0,
            'NgernTidlor.com': 0,
            'testphp.vulnweb.com': 0,
            'Other': 0
        }

        for process in running_processes:
            command = process['command'].lower()
            if 'quickcash' in command:
                targets['QuickCash.in.th'] += 1
            elif 'ngoenmun' in command:
                targets['NgoenMun.com'] += 1
            elif 'peacoop' in command:
                targets['Peacoop.or.th'] += 1
            elif 'moneycat' in command:
                targets['MoneyCat.co.th'] += 1
            elif 'mula-x' in command:
                targets['Mula-X.com'] += 1
            elif 'rocket-cash' in command:
                targets['Rocket-Cash.com'] += 1
            elif 'kloan' in command:
                targets['KLoan.co.th'] += 1
            elif 'ngerntidlor' in command:
                targets['NgernTidlor.com'] += 1
            elif 'testphp' in command:
                targets['testphp.vulnweb.com'] += 1
            else:
                targets['Other'] += 1

        return {
            'total_processes': len(running_processes),
            'targets': targets,
            'process_details': running_processes
        }

    def generate_status_report(self) -> Dict[str, Any]:
        """生成状态报告"""
        current_time = datetime.datetime.now()
        elapsed_time = current_time - self.start_time

        attack_analysis = self.analyze_attack_patterns()
        output_files = self.check_sqlmap_output_files()

        report = {
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_time': str(elapsed_time).split('.')[0],
            'attack_status': attack_analysis,
            'output_files': output_files,
            'memory_usage': sum(int(p['memory'].replace('K', '').replace(',', ''))
                              for p in attack_analysis['process_details']
                              if p['memory'].replace('K', '').replace(',', '').isdigit()),
            'quickcash_focus': attack_analysis['targets']['QuickCash.in.th'],
            'total_attacks': attack_analysis['total_processes']
        }

        return report

    def display_status(self):
        """显示状态"""
        report = self.generate_status_report()

        print("=" * 80)
        print(f"🎯 实时攻击状态监控 - {report['timestamp']}")
        print(f"⏱️ 运行时间: {report['elapsed_time']}")
        print(f"🔥 总攻击进程: {report['total_attacks']}")
        print(f"💾 内存使用: {report['memory_usage']:,} KB")
        print("=" * 80)

        print("\n📊 攻击目标分布:")
        for target, count in report['attack_status']['targets'].items():
            if count > 0:
                print(f"  🎯 {target}: {count} 个进程")

        print(f"\n🔥 QuickCash.in.th 专攻状态: {report['quickcash_focus']} 个进程")

        if report['output_files']:
            print(f"\n📁 输出文件: {len(report['output_files'])} 个目录")
            for directory, info in report['output_files'].items():
                print(f"  📂 {directory}: {info['file_count']} 个文件, {info['size']} 字节")

        print("\n" + "=" * 80)

    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"attack_status_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = self.generate_status_report()

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📊 报告已保存: {filename}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

    def monitor_loop(self, interval: int = 30):
        """监控循环"""
        print("🚀 启动实时攻击状态监控...")

        try:
            while True:
                self.display_status()
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⏹️ 监控已停止")
            self.save_report()

def main():
    """主函数"""
    monitor = AttackStatusMonitor()

    print("选择监控模式:")
    print("1. 实时监控 (每30秒更新)")
    print("2. 单次状态检查")
    print("3. 保存状态报告")

    choice = input("请选择 (1-3): ").strip()

    if choice == '1':
        monitor.monitor_loop()
    elif choice == '2':
        monitor.display_status()
    elif choice == '3':
        monitor.save_report()
        monitor.display_status()
    else:
        print("无效选择，执行单次检查")
        monitor.display_status()

if __name__ == "__main__":
    main()