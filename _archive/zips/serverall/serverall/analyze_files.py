#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件分析脚本 - 统计白名单目录下的文件信息
"""

import os
import glob
from pathlib import Path

# 要扫描的目录
dirs = ['eval', 'fingerprints', 'mcp', 'vuln', 'vuln_en']
allowed_extensions = ['.md', '.txt', '.json', '.yaml', '.yml', '.csv', '.py', '.js', '.ts', '.sql', '.ini', '.conf', '.log']

# 存储文件统计信息
file_stats = []
total_files = 0
total_size = 0

print("📁 文件白名单扫描结果\n")

for dir_path in dirs:
    if os.path.exists(dir_path):
        print(f"📂 扫描目录: {dir_path}")
        dir_file_count = 0
        dir_size = 0
        
        for root, dirs_list, files in os.walk(dir_path):
            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    file_stats.append({
                        'path': file_path,
                        'size': file_size,
                        'dir': dir_path
                    })
                    total_files += 1
                    dir_file_count += 1
                    total_size += file_size
                    dir_size += file_size
        
        print(f"  文件数: {dir_file_count}")
        print(f"  大小: {dir_size:,} bytes\n")
    else:
        print(f"❌ 目录不存在: {dir_path}\n")

print("=" * 50)
print(f"📊 总计: {total_files} 个文件, {total_size:,} bytes")
print(f"📁 目录数: {len(dirs)}")

# 按目录统计
print("\n📋 按目录统计:")
dir_summary = {}
for stat in file_stats:
    dir_name = stat['dir']
    if dir_name not in dir_summary:
        dir_summary[dir_name] = {'count': 0, 'size': 0}
    dir_summary[dir_name]['count'] += 1
    dir_summary[dir_name]['size'] += stat['size']

for dir_name, info in dir_summary.items():
    print(f"  {dir_name}: {info['count']} 文件, {info['size']:,} bytes")

# 按文件类型统计
print("\n📋 按文件类型统计:")
extension_summary = {}
for stat in file_stats:
    ext = Path(stat['path']).suffix.lower()
    if ext not in extension_summary:
        extension_summary[ext] = {'count': 0, 'size': 0}
    extension_summary[ext]['count'] += 1
    extension_summary[ext]['size'] += stat['size']

for ext, info in sorted(extension_summary.items()):
    print(f"  {ext}: {info['count']} 文件, {info['size']:,} bytes")

# 显示前10个最大文件
print("\n📏 前10个最大文件:")
sorted_files = sorted(file_stats, key=lambda x: x['size'], reverse=True)
for i, stat in enumerate(sorted_files[:10]):
    size_mb = stat['size'] / 1024 / 1024
    print(f"  {i+1}. {stat['path']} - {stat['size']:,} bytes ({size_mb:.2f} MB)")

print("\n✅ 扫描完成")