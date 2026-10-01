#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Bots with Visible Output
启动 Bot 并显示输出
"""

import subprocess
import time
import os
import sys

def main():
    print("[*] Dragon-V Complete Enterprise System")
    print("[*] Starting Both Bots with Visible Output\n")
    
    # Kill old processes
    print("[*] Cleaning up old processes...")
    os.system("taskkill /IM python.exe /F 2>nul")
    time.sleep(2)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Bot configurations
    bots = [
        ("bot_1_complete.py", "Bot #1 (ntp_nezhabot - 8314772330)"),
        ("bot_3_complete.py", "Bot #3 (lstjks_jy_bot - 8344575992)")
    ]
    
    print("\n" + "="*70)
    print("STARTING BOTS WITH CONTINUOUS OUTPUT")
    print("="*70 + "\n")
    
    for bot_file, bot_name in bots:
        bot_path = os.path.join(script_dir, bot_file)
        
        if os.path.exists(bot_path):
            print(f"[*] Launching: {bot_name}")
            print(f"    File: {bot_file}")
            print(f"    Path: {bot_path}\n")
            
            try:
                # Start in new console window with output visible
                cmd = f'start "Dragon-V {bot_name}" python "{bot_path}"'
                os.system(cmd)
                print(f"[+] {bot_name} launched successfully\n")
                time.sleep(1)
            except Exception as e:
                print(f"[-] Failed to start {bot_name}: {e}\n")
        else:
            print(f"[-] {bot_file} not found!\n")
    
    print("="*70)
    print("✅ BOTH BOTS STARTED")
    print("="*70)
    print("\n[*] Important:")
    print("    • Both bots are running in separate windows")
    print("    • You should see console windows for each bot")
    print("    • Bot output will show: '[*] Bot starting...'")
    print("    • Check Telegram to verify bots are online")
    print("\n[*] To verify bots are working:")
    print("    1. Open Telegram")
    print("    2. Find @ntp_nezhabot and @lstjks_jy_bot")
    print("    3. Send: /start")
    print("    4. You should see the menu\n")
    
    print("[*] Keeping launcher alive...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down launcher...")

if __name__ == "__main__":
    main()
