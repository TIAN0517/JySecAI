#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 DRAGON-V 一键启动系统
完全自动化启动 + 依赖检查 + 状态监控
"""

import os
import sys
import time
import subprocess
import json
import socket
from pathlib import Path
from datetime import datetime

# ==================== 配置 ====================
BOT_CONFIG = {
    "bot_1": {
        "file": "bot_ultimate_with_waf_bypass.py",
        "name": "Bot #1 (三太子/ntp_nezhabot)",
        "token": "YOUR_TELEGRAM_BOT_TOKEN_1",
        "id": "8314772330"
    },
    "bot_3": {
        "file": "bot_3_ultimate_with_waf_bypass.py", 
        "name": "Bot #3 (哮天犬/lstjks_jy_bot)",
        "token": "YOUR_TELEGRAM_BOT_TOKEN_2",
        "id": "8344575992"
    }
}

REQUIRED_MODULES = [
    "telegram",
    "requests"
]

# ==================== 颜色输出 ====================
class Colors:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """打印欢迎标题"""
    print("\n" + "="*80)
    print(Colors.BOLD + Colors.CYAN + "🚀 DRAGON-V 企业级漏洞扫描系统 - 一键启动" + Colors.END)
    print("="*80)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def check_python_version():
    """检查 Python 版本"""
    print(f"[*] 检查 Python 版本...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(Colors.GREEN + f"✓ {version.major}.{version.minor}.{version.micro}" + Colors.END)
        return True
    else:
        print(Colors.RED + f"✗ 需要 Python 3.7+，当前: {version.major}.{version.minor}" + Colors.END)
        return False

def check_internet():
    """检查网络连接"""
    print(f"[*] 检查网络连接...", end=" ")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print(Colors.GREEN + "✓ 连接正常" + Colors.END)
        return True
    except:
        print(Colors.RED + "✗ 网络连接失败" + Colors.END)
        return False

def check_module(module_name):
    """检查单个模块"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def check_dependencies():
    """检查依赖"""
    print(f"\n[*] 检查依赖库...\n")
    missing = []
    
    for module in REQUIRED_MODULES:
        status = "✓" if check_module(module) else "✗"
        status_color = Colors.GREEN if check_module(module) else Colors.RED
        print(f"    {status_color}{status}{Colors.END} {module}")
        if not check_module(module):
            missing.append(module)
    
    if missing:
        print(f"\n{Colors.YELLOW}[!] 缺少依赖: {', '.join(missing)}{Colors.END}")
        print(f"{Colors.YELLOW}[!] 自动安装中...{Colors.END}\n")
        
        for module in missing:
            print(f"    [*] 安装 {module}...", end=" ")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-q", module],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(Colors.GREEN + "✓" + Colors.END)
            except:
                print(Colors.RED + "✗ 安装失败" + Colors.END)
                print(f"{Colors.RED}请手动运行: pip install {module}{Colors.END}")
                return False
    
    print(f"{Colors.GREEN}[+] 所有依赖检查完成！{Colors.END}\n")
    return True

def check_bot_files():
    """检查 Bot 文件是否存在"""
    print(f"[*] 检查 Bot 文件...\n")
    all_exist = True
    
    for bot_key, config in BOT_CONFIG.items():
        bot_file = config["file"]
        exists = os.path.exists(bot_file)
        status = "✓" if exists else "✗"
        status_color = Colors.GREEN if exists else Colors.RED
        
        print(f"    {status_color}{status}{Colors.END} {bot_file}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print(f"\n{Colors.RED}[!] 部分 Bot 文件缺失！{Colors.END}\n")
        return False
    
    print(f"{Colors.GREEN}[+] Bot 文件检查完成！{Colors.END}\n")
    return True

def cleanup_processes():
    """清理旧进程"""
    print(f"[*] 清理旧进程...", end=" ")
    try:
        if sys.platform == "win32":
            os.system("taskkill /IM python.exe /F 2>nul >nul 2>&1")
        else:
            os.system("pkill -f 'python.*bot_' 2>/dev/null")
        time.sleep(1)
        print(Colors.GREEN + "✓" + Colors.END)
        return True
    except:
        print(Colors.YELLOW + "⚠" + Colors.END)
        return True

def start_bot(bot_key, config):
    """启动单个 Bot"""
    bot_file = config["file"]
    bot_name = config["name"]
    
    print(f"[*] 启动 {bot_name}...", end=" ")
    
    try:
        if sys.platform == "win32":
            # Windows: 在新窗口中启动
            proc = subprocess.Popen(
                [sys.executable, bot_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac
            proc = subprocess.Popen(
                [sys.executable, bot_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        time.sleep(2)
        print(Colors.GREEN + f"✓ (PID: {proc.pid})" + Colors.END)
        return proc
    except Exception as e:
        print(Colors.RED + f"✗ {str(e)[:30]}" + Colors.END)
        return None

def start_all_bots():
    """启动所有 Bot"""
    print(f"\n[*] 启动 Bot 系统...\n")
    processes = {}
    
    for bot_key, config in BOT_CONFIG.items():
        proc = start_bot(bot_key, config)
        if proc:
            processes[bot_key] = proc
    
    if processes:
        print(f"\n{Colors.GREEN}[+] {len(processes)} 个 Bot 已启动！{Colors.END}\n")
        return processes
    else:
        print(f"\n{Colors.RED}[!] 没有 Bot 成功启动！{Colors.END}\n")
        return {}

def print_status(processes):
    """打印系统状态"""
    print("="*80)
    print(Colors.BOLD + Colors.GREEN + "✅ 系统已启动" + Colors.END)
    print("="*80)
    print()
    
    print(Colors.BOLD + "【主要功能】" + Colors.END)
    print("  ✓ SQL 注入利用 (真实数据提取)")
    print("  ✓ XSS 会话劫持 (Cookie 盗取)")
    print("  ✓ API 泄露检测 (端点枚举)")
    print("  ✓ WAF 绕过 (10 种方法)")
    print("  ✓ 企业级报告 (HTML + JSON)")
    print()
    
    print(Colors.BOLD + "【运行中的 Bot】" + Colors.END)
    for bot_key, config in BOT_CONFIG.items():
        if bot_key in processes:
            print(f"  ✓ {config['name']} (活跃)")
        else:
            print(f"  ✗ {config['name']} (未启动)")
    print()
    
    print(Colors.BOLD + "【在 Telegram 中使用】" + Colors.END)
    print("  1. 搜索并打开:")
    print("     • @ntp_nezhabot (Bot #1)")
    print("     • @lstjks_jy_bot (Bot #3)")
    print("  2. 发送命令: /start")
    print("  3. 选择: 🔥 开始扫描")
    print("  4. 输入目标: hanshin.com.tw")
    print("  5. 等待结果 (5-15 分钟)")
    print()
    
    print(Colors.BOLD + "【测试目标】" + Colors.END)
    print("  ✓ hanshin.com.tw (金融服务)")
    print("  ✓ thisshop.com (电商平台)")
    print("  ✓ netpost.vn (物流系统)")
    print()
    
    print("="*80)
    print(Colors.CYAN + "系统运行中... 按 Ctrl+C 停止" + Colors.END)
    print("="*80 + "\n")

def monitor_processes(processes):
    """监控进程运行"""
    try:
        while True:
            # 检查进程状态
            active = 0
            for bot_key, proc in processes.items():
                if proc.poll() is None:
                    active += 1
                else:
                    print(f"\n{Colors.YELLOW}[!] {BOT_CONFIG[bot_key]['name']} 已停止{Colors.END}")
            
            if active == 0:
                print(f"\n{Colors.RED}[!] 所有 Bot 已停止{Colors.END}")
                break
            
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n\n[*] 收到停止信号...")
        print(f"[*] 关闭 Bot 进程...\n")
        
        for bot_key, proc in processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"    ✓ {BOT_CONFIG[bot_key]['name']} 已关闭")
            except:
                proc.kill()
                print(f"    ✓ {BOT_CONFIG[bot_key]['name']} (强制关闭)")
        
        print(f"\n{Colors.GREEN}[+] 系统已关闭{Colors.END}\n")

def main():
    """主函数"""
    print_header()
    
    # 检查 Python 版本
    if not check_python_version():
        return False
    
    # 检查网络
    if not check_internet():
        print(f"{Colors.YELLOW}[!] 没有网络连接，部分功能可能无法使用{Colors.END}\n")
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 检查 Bot 文件
    if not check_bot_files():
        return False
    
    # 清理旧进程
    cleanup_processes()
    
    # 启动所有 Bot
    processes = start_all_bots()
    
    if not processes:
        print(f"{Colors.RED}[!] 启动失败，请检查错误信息{Colors.END}\n")
        return False
    
    # 打印状态
    print_status(processes)
    
    # 监控进程
    monitor_processes(processes)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n{Colors.RED}[!] 错误: {str(e)}{Colors.END}\n")
        sys.exit(1)
