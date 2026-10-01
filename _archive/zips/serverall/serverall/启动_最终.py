#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRAGON-V 终极企业级系统启动器 - 改进版
直接启动 Bot，保持在前台
"""
import sys
import os
import time

# 设置编码
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*70)
print("🔥 DRAGON-V 终极企业级漏洞扫描系统")
print("="*70)

print("\n[*] 清理旧进程...")
os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)
print("[+] 完成!")

print("\n[*] 选择要启动的 Bot:")
print("  1. Bot #1 (8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw)")
print("  2. Bot #3 (8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA)")
print("  3. 两个都启动")
print()

choice = input("[?] 请选择 (输入 1, 2 或 3): ").strip()

if choice == "1":
    print("\n[*] 启动 Bot #1...")
    os.system("python bot_ultimate.py")
elif choice == "2":
    print("\n[*] 启动 Bot #3...")
    os.system("python bot_3_ultimate.py")
elif choice == "3":
    print("\n[*] 启动 Bot #1...")
    import subprocess
    subprocess.Popen("start python bot_ultimate.py", shell=True)
    time.sleep(2)
    print("[*] 启动 Bot #3...")
    subprocess.Popen("start python bot_3_ultimate.py", shell=True)
    print("\n[+] 两个 Bot 已在单独的窗口启动!")
    time.sleep(2)
else:
    print("❌ 无效选择!")
