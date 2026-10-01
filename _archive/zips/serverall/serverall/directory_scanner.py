#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录扫描器 - 使用白名单进行安全扫描
用于扫描指定目录并统计文件类型分布
"""

import os
import yaml
import glob
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class DirectoryScanner:
    def __init__(self, whitelist_path='file_whitelist.yaml'):
        """初始化扫描器，加载白名单配置"""
        self.whitelist = self.load_whitelist(whitelist_path)
        self.scan_results = defaultdict(lambda: defaultdict(int))
        
    def load_whitelist(self, whitelist_path):
        """加载白名单配置文件"""
        try:
            with open(whitelist_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载白名单失败: {e}")
            return {}
    
    def is_allowed_file(self, file_path):
        """检查文件是否在白名单中"""
        if not self.whitelist:
            return True
            
        filename = os.path.basename(file_path)
        
        # 检查排除模式
        for pattern in self.whitelist.get('exclude_patterns', []):
            if glob.fnmatch.fnmatch(filename, pattern):
                return False
        
        # 检查文件类型是否在允许列表中
        for file_type, patterns in self.whitelist.items():
            if file_type.endswith('_files'):
                for pattern in patterns:
                    if glob.fnmatch.fnmatch(filename, pattern):
                        return True
        
        return False
    
    def scan_directory(self, directory_path, max_depth=None):
        """扫描目录并统计文件信息"""
        if max_depth is None:
            max_depth = self.whitelist.get('scan_config', {}).get('max_depth', 5)
        
        scan_time = datetime.now()
        total_files = 0
        allowed_files = 0
        
        for root, dirs, files in os.walk(directory_path):
            # 计算当前深度
            current_depth = root.replace(directory_path, '').count(os.sep)
            if current_depth > max_depth:
                continue
            
            for file in files:
                total_files += 1
                file_path = os.path.join(root, file)
                
                if self.is_allowed_file(file_path):
                    allowed_files += 1
                    
                    # 统计文件类型
                    file_ext = Path(file).suffix.lower()
                    if not file_ext:
                        file_ext = '无扩展名'
                    
                    self.scan_results['file_types'][file_ext] += 1
                    
                    # 统计目录分布
                    relative_path = os.path.relpath(root, directory_path)
                    if relative_path == '.':
                        relative_path = '根目录'
                    self.scan_results['directories'][relative_path] += 1
                    
                    # 统计文件大小范围
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size < 1024:
                            size_range = '<1KB'
                        elif file_size < 1024 * 1024:
                            size_range = '1KB-1MB'
                        elif file_size < 1024 * 1024 * 10:
                            size_range = '1MB-10MB'
                        else:
                            size_range = '>10MB'
                        self.scan_results['sizes'][size_range] += 1
                    except OSError:
                        self.scan_results['sizes']['无法访问'] += 1
        
        self.scan_results['summary'] = {
            'scan_time': scan_time.isoformat(),
            'total_files': total_files,
            'allowed_files': allowed_files,
            'blocked_files': total_files - allowed_files,
            'scan_duration': (datetime.now() - scan_time).total_seconds(),
            'directory_path': directory_path
        }
        
        return self.scan_results
    
    def generate_report(self):
        """生成扫描报告"""
        if not self.scan_results:
            return "没有扫描数据可用"
        
        report = []
        summary = self.scan_results['summary']
        
        report.append("=" * 60)
        report.append("目录扫描报告")
        report.append("=" * 60)
        report.append(f"扫描时间: {summary['scan_time']}")
        report.append(f"扫描目录: {summary['directory_path']}")
        report.append(f"扫描耗时: {summary['scan_duration']:.2f} 秒")
        report.append(f"总文件数: {summary['total_files']}")
        report.append(f"允许文件: {summary['allowed_files']}")
        report.append(f"阻止文件: {summary['blocked_files']}")
        report.append("")
        
        # 文件类型统计
        if 'file_types' in self.scan_results:
            report.append("文件类型统计:")
            report.append("-" * 30)
            for ext, count in sorted(self.scan_results['file_types'].items(), 
                                   key=lambda x: x[1], reverse=True):
                report.append(f"  {ext}: {count} 个")
            report.append("")
        
        # 目录分布统计
        if 'directories' in self.scan_results:
            report.append("目录分布统计 (前10):")
            report.append("-" * 30)
            for dir_path, count in sorted(self.scan_results['directories'].items(), 
                                        key=lambda x: x[1], reverse=True)[:10]:
                report.append(f"  {dir_path}: {count} 个")
            report.append("")
        
        # 文件大小统计
        if 'sizes' in self.scan_results:
            report.append("文件大小分布:")
            report.append("-" * 30)
            for size_range, count in sorted(self.scan_results['sizes'].items()):
                report.append(f"  {size_range}: {count} 个")
        
        return '\n'.join(report)
    
    def save_report(self, output_path='scan_report.txt'):
        """保存扫描报告到文件"""
        report = self.generate_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        return output_path

def main():
    """主函数"""
    scanner = DirectoryScanner()
    
    # 扫描当前目录
    current_dir = os.getcwd()
    print(f"开始扫描目录: {current_dir}")
    
    results = scanner.scan_directory(current_dir)
    
    # 生成并显示报告
    report = scanner.generate_report()
    print(report)
    
    # 保存报告
    report_file = scanner.save_report()
    print(f"\n扫描报告已保存到: {report_file}")
    
    return results

if __name__ == "__main__":
    main()