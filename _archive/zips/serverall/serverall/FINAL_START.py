#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Launcher - Direct Bot Execution
直接启动 Bot，不使用后台进程
"""

import subprocess
import time
import os
import sys

print("\n" + "="*70)
print("DRAGON-V ENTERPRISE SYSTEM")
print("="*70)
print("\n[*] Killing old processes...")
os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)

print("[+] Clean! Now starting bots...\n")

script_dir = os.path.dirname(os.path.abspath(__file__))

bots = [
    ("bot_1_working.py", "Bot #1"),
    ("bot_3_working.py", "Bot #3")
]

print("[*] Launching in separate windows:")

for bot_file, bot_name in bots:
    bot_path = os.path.join(script_dir, bot_file)
    if os.path.exists(bot_path):
        print(f"    [+] {bot_name}: {bot_file}")
        # Use subprocess to start in new window
        subprocess.Popen(f'start "Dragon-V {bot_name}" python "{bot_path}"', shell=True)
        time.sleep(1)

print("\n[+] Both bots launched!")
print("[*] Check: You should see 2 new console windows appearing")
print("[*] Each should show: '[+] BOT IS NOW ONLINE'\n")

print("="*70)
print("[✓] SYSTEM STARTED")
print("="*70)
print("\n[Next] Open Telegram and:")
print("       1. Find @ntp_nezhabot or @lstjks_jy_bot")
print("       2. Send: /start")
print("       3. Click: 🔍 完整扫描")
print("       4. Enter: hanshin.com.tw\n")
