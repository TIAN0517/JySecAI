#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速状态检查脚本
"""

import subprocess
import json
import time
import datetime
import os

def get_running_sqlmap_processes():
    """获取所有运行中的SQLMap进程"""
    try:
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

def analyze_attack_patterns():
    """分析攻击模式"""
    running_processes = get_running_sqlmap_processes()

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

def main():
    """主函数"""
    current_time = datetime.datetime.now()
    attack_analysis = analyze_attack_patterns()

    print("=" * 80)
    print(f"🎯 渗透攻击状态报告 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"🔥 总攻击进程: {attack_analysis['total_processes']}")

    # 计算总内存使用
    total_memory = 0
    for p in attack_analysis['process_details']:
        try:
            mem_str = p['memory'].replace('K', '').replace(',', '')
            if mem_str.isdigit():
                total_memory += int(mem_str)
        except:
            pass

    print(f"💾 总内存使用: {total_memory:,} KB ({total_memory/1024:.1f} MB)")
    print("=" * 80)

    print("\n📊 攻击目标分布:")
    for target, count in attack_analysis['targets'].items():
        if count > 0:
            print(f"  🎯 {target}: {count} 个进程")

    print(f"\n🔥 QuickCash.in.th 专攻状态: {attack_analysis['targets']['QuickCash.in.th']} 个进程")

    if attack_analysis['targets']['QuickCash.in.th'] > 0:
        print("✅ QuickCash.in.th 攻击正在进行中")
    else:
        print("⚠️ QuickCash.in.th 攻击可能已完成或暂停")

    # 检查输出目录
    output_dirs = []
    for item in os.listdir('.'):
        if item.startswith('extract_') and os.path.isdir(item):
            output_dirs.append(item)

    if output_dirs:
        print(f"\n📁 输出目录: {len(output_dirs)} 个")
        for directory in output_dirs[:5]:  # 只显示前5个
            try:
                files = os.listdir(directory)
                print(f"  📂 {directory}: {len(files)} 个文件")
            except:
                print(f"  📂 {directory}: 无法访问")

    print("\n" + "=" * 80)

    # 保存报告
    report = {
        'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'attack_status': attack_analysis,
        'total_memory_kb': total_memory,
        'quickcash_attacks': attack_analysis['targets']['QuickCash.in.th'],
        'output_directories': len(output_dirs)
    }

    try:
        with open(f"attack_status_{current_time.strftime('%Y%m%d_%H%M%S')}.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📊 报告已保存")
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")

if __name__ == "__main__":
    main()