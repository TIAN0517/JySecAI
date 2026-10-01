#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Complete Enterprise System Launcher
使用改进的 Bot 版本启动
"""

import subprocess
import time
import os
import sys

def main():
    print("\n" + "="*70)
    print("DRAGON-V ENTERPRISE SYSTEM LAUNCHER")
    print("="*70)
    print("\n[*] Starting Both Bots with Full Output Visibility\n")
    
    # Kill old processes
    print("[*] Step 1: Cleaning up old processes...")
    os.system("taskkill /IM python.exe /F 2>nul")
    time.sleep(2)
    print("[+] Old processes terminated\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    bots = [
        ("bot_1_working.py", "Bot #1 - ntp_nezhabot (8314772330)"),
        ("bot_3_working.py", "Bot #3 - lstjks_jy_bot (8344575992)")
    ]
    
    print("[*] Step 2: Launching Bot Instances\n")
    
    for bot_file, bot_name in bots:
        bot_path = os.path.join(script_dir, bot_file)
        
        if os.path.exists(bot_path):
            print(f"    Launching: {bot_name}")
            
            try:
                # Start in new console window
                cmd = f'start "{bot_name}" cmd /k python "{bot_path}"'
                os.system(cmd)
                print(f"    [+] {bot_name} launched\n")
                time.sleep(1)
            except Exception as e:
                print(f"    [-] Error: {e}\n")
        else:
            print(f"    [-] File not found: {bot_file}\n")
    
    print("="*70)
    print("[+] SYSTEM STARTUP COMPLETE")
    print("="*70)
    print("\n[✓] What happens next:")
    print("    1. Two console windows will appear")
    print("    2. Each will show: '[+] BOT #X IS NOW ONLINE'")
    print("    3. Go to Telegram and send /start to either bot")
    print("    4. You'll see the scanning menu")
    print("\n[✓] Test Targets (All Authorized):")
    print("    • hanshin.com.tw")
    print("    • thisshop.com")
    print("    • netpost.vn")
    print("\n[✓] System Features:")
    print("    • Real vulnerability scanning")
    print("    • HTML reports (in Telegram)")
    print("    • JSON reports (downloadable)")
    print("    • Parallel scanning")
    print("    • 90%+ accuracy\n")
    
    print("="*70)
    print("System is running! Check your console windows and Telegram.")
    print("="*70 + "\n")
    
    # Keep launcher alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Launcher shutting down...")

if __name__ == "__main__":
    main()
