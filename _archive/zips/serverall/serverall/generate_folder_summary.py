#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 FOLDER_SUMMARY.md 文件夹摘要脚本
分析每个目录的结构、文件类型分布和内容摘要
"""

import os
import sys
from pathlib import Path
import json
import yaml
from datetime import datetime
from collections import Counter

# 扫描的目录列表
SCAN_DIRS = [
    './eval',
    './fingerprints',
    './mcp',
    './vuln',
    './vuln_en'
]

# 支持的文件扩展名
TEXT_EXTENSIONS = {
    '.md', '.txt', '.json', '.yaml', '.yml', '.csv',
    '.py', '.js', '.ts', '.sql', '.ini', '.conf', '.log'
}

def analyze_directory(dir_path):
    """分析单个目录的结构和内容"""
    dir_info = {
        'path': str(dir_path),
        'exists': dir_path.exists(),
        'total_files': 0,
        'file_types': Counter(),
        'subdirectories': [],
        'largest_files': [],
        'recent_files': [],
        'content_summary': {}
    }

    if not dir_path.exists():
        return dir_info

    # 收集文件信息
    all_files = []
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            # 检查文件扩展名
            if file_path.suffix.lower() in TEXT_EXTENSIONS:
                try:
                    stat = file_path.stat()
                    file_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': stat.st_size,
                        'mtime': datetime.fromtimestamp(stat.st_mtime),
                        'extension': file_path.suffix.lower()
                    }
                    all_files.append(file_info)
                    dir_info['file_types'][file_path.suffix.lower()] += 1
                except:
                    continue

    dir_info['total_files'] = len(all_files)

    # 分析子目录
    for subdir in dir_path.iterdir():
        if subdir.is_dir():
            subdir_info = {
                'name': subdir.name,
                'file_count': len([f for f in subdir.rglob('*') if f.is_file() and f.suffix.lower() in TEXT_EXTENSIONS])
            }
            dir_info['subdirectories'].append(subdir_info)

    # 最大文件
    dir_info['largest_files'] = sorted(all_files, key=lambda x: x['size'], reverse=True)[:5]

    # 最近修改的文件
    dir_info['recent_files'] = sorted(all_files, key=lambda x: x['mtime'], reverse=True)[:5]

    # 内容摘要
    dir_info['content_summary'] = generate_content_summary(dir_path, all_files)

    return dir_info

def generate_content_summary(dir_path, files):
    """生成目录内容摘要"""
    summary = {
        'description': '',
        'key_files': [],
        'file_patterns': [],
        'data_types': set()
    }

    # 根据目录名推断内容类型
    dir_name = dir_path.name.lower()
    if 'eval' in dir_name:
        summary['description'] = '评估数据集和测试用例'
        summary['data_types'].add('evaluation')
    elif 'fingerprint' in dir_name:
        summary['description'] = '指纹识别和特征检测规则'
        summary['data_types'].add('fingerprinting')
    elif 'mcp' in dir_name:
        summary['description'] = 'MCP (Model Context Protocol) 相关配置和工具'
        summary['data_types'].add('mcp')
    elif 'vuln' in dir_name:
        summary['description'] = '漏洞信息和利用代码'
        summary['data_types'].add('vulnerability')

    # 分析文件模式
    extensions = [f['extension'] for f in files]
    ext_counter = Counter(extensions)
    summary['file_patterns'] = [f"{ext}: {count}" for ext, count in ext_counter.most_common(5)]

    # 识别关键文件
    for file_info in files:
        file_name = file_info['name'].lower()
        if any(keyword in file_name for keyword in ['readme', 'index', 'main', 'config']):
            summary['key_files'].append(file_info['name'])

    return summary

def generate_folder_summary_md(directories_info):
    """生成 FOLDER_SUMMARY.md 内容"""
    content = ["# FOLDER_SUMMARY - 文件夹摘要\n"]
    content.append("\n## 概述\n")
    content.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"- **扫描目录数**: {len(directories_info)}")
    content.append(f"- **总文件数**: {sum(d['total_files'] for d in directories_info)}")
    content.append("\n---\n")

    # 总体统计
    content.append("\n## 总体统计\n")

    total_files = sum(d['total_files'] for d in directories_info)
    all_file_types = Counter()
    for dir_info in directories_info:
        all_file_types.update(dir_info['file_types'])

    content.append(f"- **总文件数**: {total_files}")
    content.append(f"- **文件类型分布**:")
    for ext, count in all_file_types.most_common():
        percentage = (count / total_files) * 100
        content.append(f"  - `{ext}`: {count} 个 ({percentage:.1f}%)")

    # 各目录详细分析
    for dir_info in directories_info:
        content.append(f"\n## {dir_info['path']}\n")

        if not dir_info['exists']:
            content.append("*目录不存在*\n")
            continue

        content.append(f"- **描述**: {dir_info['content_summary']['description']}")
        content.append(f"- **文件总数**: {dir_info['total_files']}")
        content.append(f"- **子目录数**: {len(dir_info['subdirectories'])}")

        # 文件类型分布
        if dir_info['file_types']:
            content.append(f"- **文件类型分布**:")
            for ext, count in dir_info['file_types'].most_common(5):
                percentage = (count / dir_info['total_files']) * 100
                content.append(f"  - `{ext}`: {count} 个 ({percentage:.1f}%)")

        # 子目录
        if dir_info['subdirectories']:
            content.append(f"- **主要子目录**:")
            for subdir in sorted(dir_info['subdirectories'], key=lambda x: x['file_count'], reverse=True)[:10]:
                content.append(f"  - `{subdir['name']}`: {subdir['file_count']} 个文件")

        # 关键文件
        if dir_info['content_summary']['key_files']:
            content.append(f"- **关键文件**:")
            for key_file in dir_info['content_summary']['key_files'][:5]:
                content.append(f"  - `{key_file}`")

        # 最大文件
        if dir_info['largest_files']:
            content.append(f"- **最大文件**:")
            for file_info in dir_info['largest_files']:
                size_mb = file_info['size'] / (1024 * 1024)
                content.append(f"  - `{file_info['name']}`: {size_mb:.2f} MB")

        # 最近修改的文件
        if dir_info['recent_files']:
            content.append(f"- **最近修改的文件**:")
            for file_info in dir_info['recent_files']:
                content.append(f"  - `{file_info['name']}` ({file_info['mtime'].strftime('%Y-%m-%d')})")

        # 数据分类
        if dir_info['content_summary']['data_types']:
            content.append(f"- **数据分类**: {', '.join(sorted(dir_info['content_summary']['data_types']))}")

    return '\n'.join(content)

def main():
    """主函数"""
    print("开始分析目录结构...")

    # 分析每个目录
    directories_info = []
    for scan_dir in SCAN_DIRS:
        print(f"分析目录: {scan_dir}")
        dir_info = analyze_directory(Path(scan_dir))
        directories_info.append(dir_info)

    # 生成 FOLDER_SUMMARY.md
    summary_content = generate_folder_summary_md(directories_info)

    # 保存到文件
    output_path = Path('FOLDER_SUMMARY.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)

    print(f"已生成 FOLDER_SUMMARY.md")

    # 同时生成JSON格式的摘要
    json_data = {
        'generated_time': datetime.now().isoformat(),
        'directories': directories_info
    }

    with open('folder_summary.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

    print("已生成 folder_summary.json")

if __name__ == "__main__":
    main()