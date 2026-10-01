#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 READMAP.md 文件索引脚本
扫描指定目录下的文本文件，生成路径、大小和预览信息
"""

import os
import sys
from pathlib import Path
import json
import yaml
import csv
from datetime import datetime

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

# 排除的目录
EXCLUDE_DIRS = ['cache']

# 最大文件大小 (256KB)
MAX_FILE_SIZE = 256 * 1024

def get_file_info(file_path):
    """获取文件信息：大小、修改时间、前200行预览"""
    try:
        stat = file_path.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime)

        # 检查文件大小
        if size > MAX_FILE_SIZE:
            return None

        # 读取文件前200行预览
        preview_lines = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= 200:
                        break
                    preview_lines.append(line.rstrip())
        except:
            # 如果UTF-8读取失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if i >= 200:
                            break
                        preview_lines.append(line.rstrip())
            except:
                preview_lines = ["无法读取文件内容"]

        preview = '\n'.join(preview_lines[:10])  # 只显示前10行作为预览

        return {
            'path': str(file_path),
            'size': size,
            'size_human': format_size(size),
            'mtime': mtime.strftime('%Y-%m-%d %H:%M:%S'),
            'preview': preview,
            'line_count': len(preview_lines)
        }
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return None

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def scan_directories():
    """扫描指定目录下的文本文件"""
    all_files = []

    for scan_dir in SCAN_DIRS:
        if not Path(scan_dir).exists():
            print(f"警告: 目录 {scan_dir} 不存在")
            continue

        print(f"扫描目录: {scan_dir}")

        for file_path in Path(scan_dir).rglob('*'):
            # 跳过目录
            if not file_path.is_file():
                continue

            # 检查文件扩展名
            if file_path.suffix.lower() not in TEXT_EXTENSIONS:
                continue

            # 检查排除目录
            if any(exclude in str(file_path) for exclude in EXCLUDE_DIRS):
                continue

            # 获取文件信息
            file_info = get_file_info(file_path)
            if file_info:
                all_files.append(file_info)

    return all_files

def generate_readmap_md(files):
    """生成 READMAP.md 内容"""
    content = ["# READMAP - 文件索引目录\n"]
    content.append("\n## 概述\n")
    content.append(f"- **扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"- **扫描目录**: {', '.join(SCAN_DIRS)}")
    content.append(f"- **文件总数**: {len(files)}")
    content.append(f"- **文件类型**: {', '.join(sorted(TEXT_EXTENSIONS))}")
    content.append("\n---\n")

    # 按目录分组
    files_by_dir = {}
    for file_info in files:
        dir_path = str(Path(file_info['path']).parent)
        if dir_path not in files_by_dir:
            files_by_dir[dir_path] = []
        files_by_dir[dir_path].append(file_info)

    # 按目录排序
    for dir_path in sorted(files_by_dir.keys()):
        content.append(f"\n## {dir_path}\n")

        for file_info in sorted(files_by_dir[dir_path], key=lambda x: x['path']):
            content.append(f"\n### {Path(file_info['path']).name}\n")
            content.append(f"- **路径**: `{file_info['path']}`")
            content.append(f"- **大小**: {file_info['size_human']}")
            content.append(f"- **修改时间**: {file_info['mtime']}")
            content.append(f"- **行数**: {file_info['line_count']}")

            if file_info['preview']:
                content.append(f"- **预览**:\n```\n{file_info['preview']}\n```")

            content.append("")

    return '\n'.join(content)

def main():
    """主函数"""
    print("开始扫描目录...")

    # 扫描文件
    files = scan_directories()
    print(f"找到 {len(files)} 个文本文件")

    # 生成 READMAP.md
    readmap_content = generate_readmap_md(files)

    # 保存到文件
    output_path = Path('README.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readmap_content)

    print(f"已生成 READMAP.md，包含 {len(files)} 个文件的索引")

    # 同时生成JSON格式的索引（用于机器读取）
    json_data = {
        'scan_time': datetime.now().isoformat(),
        'scan_dirs': SCAN_DIRS,
        'total_files': len(files),
        'files': files
    }

    with open('file_index.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print("已生成 file_index.json (机器可读格式)")

if __name__ == "__main__":
    main()