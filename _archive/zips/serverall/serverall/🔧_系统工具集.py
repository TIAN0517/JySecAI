#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 DRAGON-V 系统工具集
系统诊断、管理、和优化工具
"""

import os
import sys
import time
import subprocess
import json
import psutil
import platform
from datetime import datetime
from pathlib import Path

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

class SystemTools:
    """系统工具类"""
    
    @staticmethod
    def print_header(title):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    @staticmethod
    def check_system_health():
        """检查系统健康状态"""
        SystemTools.print_header("🏥 系统健康检查")
        
        checks_passed = 0
        checks_total = 0
        
        # 1. Python 版本
        checks_total += 1
        version = sys.version_info
        status = "✓" if version.major >= 3 and version.minor >= 7 else "✗"
        status_color = Colors.GREEN if status == "✓" else Colors.RED
        print(f"{status_color}{status}{Colors.END} Python 版本: {version.major}.{version.minor}.{version.micro}")
        if status == "✓":
            checks_passed += 1
        
        # 2. 操作系统
        checks_total += 1
        os_name = platform.system()
        print(f"{Colors.GREEN}✓{Colors.END} 操作系统: {os_name}")
        checks_passed += 1
        
        # 3. CPU 使用率
        checks_total += 1
        cpu_percent = psutil.cpu_percent(interval=1)
        status = "✓" if cpu_percent < 80 else "⚠"
        status_color = Colors.GREEN if cpu_percent < 80 else Colors.YELLOW
        print(f"{status_color}{status}{Colors.END} CPU 使用率: {cpu_percent}%")
        if cpu_percent < 80:
            checks_passed += 1
        
        # 4. 内存使用率
        checks_total += 1
        memory = psutil.virtual_memory()
        status = "✓" if memory.percent < 80 else "⚠"
        status_color = Colors.GREEN if memory.percent < 80 else Colors.YELLOW
        print(f"{status_color}{status}{Colors.END} 内存使用率: {memory.percent}% ({memory.available // (1024**3)}GB 可用)")
        if memory.percent < 80:
            checks_passed += 1
        
        # 5. 磁盘空间
        checks_total += 1
        disk = psutil.disk_usage('/')
        status = "✓" if disk.percent < 80 else "⚠"
        status_color = Colors.GREEN if disk.percent < 80 else Colors.YELLOW
        print(f"{status_color}{status}{Colors.END} 磁盘使用率: {disk.percent}% ({disk.free // (1024**3)}GB 可用)")
        if disk.percent < 80:
            checks_passed += 1
        
        # 6. 网络连接
        checks_total += 1
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print(f"{Colors.GREEN}✓{Colors.END} 网络连接: 正常")
            checks_passed += 1
        except:
            print(f"{Colors.RED}✗{Colors.END} 网络连接: 失败")
        
        print(f"\n{Colors.BOLD}检查结果: {checks_passed}/{checks_total} 通过{Colors.END}\n")
        return checks_passed == checks_total
    
    @staticmethod
    def check_bot_status():
        """检查 Bot 运行状态"""
        SystemTools.print_header("🤖 Bot 状态检查")
        
        # 查找 Python 进程
        print("[*] 搜索运行中的 Bot 进程...\n")
        
        bot_files = [
            "bot_ultimate_with_waf_bypass.py",
            "bot_3_ultimate_with_waf_bypass.py"
        ]
        
        found_any = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                for bot_file in bot_files:
                    if bot_file in cmdline:
                        found_any = True
                        memory = proc.memory_info().rss / 1024 / 1024
                        cpu = proc.cpu_percent(interval=0.1)
                        print(f"{Colors.GREEN}✓{Colors.END} {bot_file}")
                        print(f"   PID: {proc.info['pid']}")
                        print(f"   CPU: {cpu}%")
                        print(f"    内存: {memory:.1f} MB\n")
            except:
                pass
        
        if not found_any:
            print(f"{Colors.YELLOW}[!] 未找到运行中的 Bot 进程{Colors.END}")
            print(f"{Colors.CYAN}[*] 提示: 运行 🚀_一键启动.bat 来启动系统{Colors.END}\n")
        
        return found_any
    
    @staticmethod
    def check_dependencies():
        """检查依赖库"""
        SystemTools.print_header("📦 依赖库检查")
        
        required_modules = {
            "telegram": "python-telegram-bot",
            "requests": "requests"
        }
        
        all_ok = True
        for module, package_name in required_modules.items():
            try:
                __import__(module)
                print(f"{Colors.GREEN}✓{Colors.END} {module}")
            except ImportError:
                print(f"{Colors.RED}✗{Colors.END} {module} (缺失)")
                print(f"   {Colors.YELLOW}安装: pip install {package_name}{Colors.END}")
                all_ok = False
        
        print()
        return all_ok
    
    @staticmethod
    def check_files():
        """检查关键文件"""
        SystemTools.print_header("📁 关键文件检查")
        
        required_files = [
            "🚀_一键启动.py",
            "🚀_一键启动.bat",
            "bot_ultimate_with_waf_bypass.py",
            "bot_3_ultimate_with_waf_bypass.py",
            "CVE_POC_database.py",
            "exploitation_module.py",
            "report_generator.py"
        ]
        
        all_ok = True
        total_size = 0
        
        for filename in required_files:
            if os.path.exists(filename):
                size = os.path.getsize(filename) / 1024
                total_size += size
                print(f"{Colors.GREEN}✓{Colors.END} {filename} ({size:.1f} KB)")
            else:
                print(f"{Colors.RED}✗{Colors.END} {filename} (缺失)")
                all_ok = False
        
        print(f"\n{Colors.BLUE}总大小: {total_size:.1f} KB{Colors.END}\n")
        return all_ok
    
    @staticmethod
    def cleanup_temp_files():
        """清理临时文件"""
        SystemTools.print_header("🗑️  清理临时文件")
        
        # 要删除的文件模式
        patterns = [
            ".pyc",
            "__pycache__",
            ".log",
            "*.json",
            ".db"
        ]
        
        print("[*] 扫描临时文件...\n")
        
        deleted_count = 0
        freed_space = 0
        
        # 简单清理 .pyc 文件
        for root, dirs, files in os.walk("."):
            # 清理 __pycache__
            if "__pycache__" in dirs:
                try:
                    import shutil
                    size = sum(
                        os.path.getsize(os.path.join(root, "__pycache__", f))
                        for f in os.listdir(os.path.join(root, "__pycache__"))
                    ) / 1024
                    shutil.rmtree(os.path.join(root, "__pycache__"))
                    freed_space += size
                    deleted_count += 1
                    print(f"{Colors.GREEN}✓{Colors.END} 删除: __pycache__ ({size:.1f} KB)")
                except:
                    pass
        
        print(f"\n{Colors.GREEN}[+] 清理完成{Colors.END}")
        print(f"   删除: {deleted_count} 项")
        print(f"   释放空间: {freed_space:.1f} KB\n")
    
    @staticmethod
    def generate_report():
        """生成系统报告"""
        SystemTools.print_header("📊 生成系统报告")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_used_percent": psutil.virtual_memory().percent,
            "disk_used_percent": psutil.disk_usage('/').percent,
            "file_checks": {},
            "dependency_checks": {}
        }
        
        # 检查文件
        for filename in [
            "bot_ultimate_with_waf_bypass.py",
            "CVE_POC_database.py"
        ]:
            report["file_checks"][filename] = os.path.exists(filename)
        
        # 检查依赖
        for module in ["telegram", "requests"]:
            try:
                __import__(module)
                report["dependency_checks"][module] = True
            except:
                report["dependency_checks"][module] = False
        
        # 保存报告
        report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"{Colors.GREEN}✓{Colors.END} 报告已生成: {report_file}\n")
        
        # 打印摘要
        print(f"系统信息:")
        print(f"  • 平台: {report['platform']}")
        print(f"  • Python: {report['python_version']}")
        print(f"  • CPU: {report['cpu_percent']}% / {report['cpu_count']} 核心")
        print(f"  • 内存: {report['memory_used_percent']}% / {report['memory_total_gb']:.1f} GB")
        print(f"  • 磁盘: {report['disk_used_percent']}%\n")
    
    @staticmethod
    def show_menu():
        """显示菜单"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}DRAGON-V 系统工具集{Colors.END}\n")
        print("1. 系统健康检查")
        print("2. Bot 状态检查")
        print("3. 依赖库检查")
        print("4. 关键文件检查")
        print("5. 清理临时文件")
        print("6. 生成系统报告")
        print("7. 全部检查")
        print("0. 退出\n")
    
    @staticmethod
    def run_full_check():
        """运行完整检查"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}🔧 DRAGON-V 系统完整诊断{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
        
        start_time = time.time()
        
        SystemTools.check_system_health()
        SystemTools.check_dependencies()
        SystemTools.check_files()
        SystemTools.check_bot_status()
        
        elapsed = time.time() - start_time
        
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}✅ 诊断完成 (耗时: {elapsed:.2f} 秒){Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def main():
    """主菜单"""
    SystemTools.print_header("🔧 DRAGON-V 系统工具集")
    
    while True:
        SystemTools.show_menu()
        choice = input(f"{Colors.CYAN}选择操作 [0-7]: {Colors.END}").strip()
        
        if choice == "1":
            SystemTools.check_system_health()
        elif choice == "2":
            SystemTools.check_bot_status()
        elif choice == "3":
            SystemTools.check_dependencies()
        elif choice == "4":
            SystemTools.check_files()
        elif choice == "5":
            SystemTools.cleanup_temp_files()
        elif choice == "6":
            SystemTools.generate_report()
        elif choice == "7":
            SystemTools.run_full_check()
        elif choice == "0":
            print(f"{Colors.CYAN}再见！{Colors.END}\n")
            break
        else:
            print(f"{Colors.RED}[!] 无效选择{Colors.END}\n")
        
        input(f"\n{Colors.CYAN}按 Enter 继续...{Colors.END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}已中断{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[!] 错误: {str(e)}{Colors.END}\n")
        sys.exit(1)
