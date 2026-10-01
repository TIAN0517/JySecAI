#!/usr/bin/env python3
import os
import json
from pathlib import Path

def scan_directory(directory_path, file_extensions=None, max_size_kb=256):
    """扫描目录并返回文件信息"""
    results = []
    total_size = 0
    file_count = 0
    
    if file_extensions:
        file_extensions = [ext.lower() for ext in file_extensions]
    
    for root, dirs, files in os.walk(directory_path):
        # 跳过cache目录
        if 'cache' in root.lower():
            continue
            
        for file in files:
            file_path = Path(root) / file
            
            # 检查文件扩展名
            if file_extensions:
                file_ext = file_path.suffix.lower()
                if file_ext and file_ext[1:] not in file_extensions:
                    continue
            
            # 获取文件大小
            file_size = file_path.stat().st_size
            size_kb = file_size / 1024
            total_size += file_size
            file_count += 1
            
            # 读取文件内容预览
            preview = ""
            if size_kb <= max_size_kb:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= 200:  # 最多读取200行
                                break
                            lines.append(line.rstrip())
                        preview = "\n".join(lines[:50])  # 显示前50行
                except:
                    preview = "[无法读取文件内容]"
            else:
                preview = f"[文件过大: {size_kb:.1f}KB > {max_size_kb}KB，仅显示路径]"
            
            results.append({
                'path': str(file_path.relative_to(directory_path.parent)),
                'size_kb': round(size_kb, 2),
                'preview': preview
            })
    
    return {
        'directory': str(directory_path),
        'total_files': file_count,
        'total_size_kb': round(total_size / 1024, 2),
        'files': results
    }

def main():
    # 目标目录
    directories = [
        'eval',
        'fingerprints', 
        'mcp',
        'vuln',
        'vuln_en'
    ]
    
    # 允许的文件扩展名
    allowed_extensions = ['md', 'txt', 'json', 'yaml', 'yml', 'csv', 'py', 'js', 'ts', 'sql', 'ini', 'conf', 'log']
    
    all_results = {}
    
    for dir_name in directories:
        dir_path = Path.cwd() / dir_name
        if dir_path.exists():
            print(f"扫描目录: {dir_name}")
            result = scan_directory(dir_path, allowed_extensions)
            all_results[dir_name] = result
        else:
            print(f"目录不存在: {dir_name}")
            all_results[dir_name] = {'error': '目录不存在'}
    
    # 保存结果
    with open('scan_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print("扫描完成，结果已保存到 scan_results.json")

if __name__ == "__main__":
    main()