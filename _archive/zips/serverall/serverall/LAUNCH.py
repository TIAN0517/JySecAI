#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Launcher for Complete Enterprise System
"""

import subprocess
import time
import os
import sys

def main():
    print("[*] Dragon-V Complete Enterprise System Launcher")
    print("[*] Real Exploitation + HTML & JSON Reports\n")
    
    # Kill old processes
    print("[*] Cleaning up old processes...")
    os.system("taskkill /IM python.exe /F 2>nul")
    time.sleep(2)
    
    # Get the directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    bot_files = [
        ("bot_1_complete.py", "Bot #1 (ntp_nezhabot)"),
        ("bot_3_complete.py", "Bot #3 (lstjks_jy_bot)")
    ]
    
    processes = []
    
    for bot_file, bot_name in bot_files:
        bot_path = os.path.join(script_dir, bot_file)
        
        if os.path.exists(bot_path):
            print(f"[*] Starting {bot_name}...")
            
            try:
                # Launch in new console window
                proc = subprocess.Popen(
                    [sys.executable, bot_path],
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                processes.append((bot_name, proc))
                print(f"[+] {bot_name} started (PID: {proc.pid})")
                time.sleep(1)
            except Exception as e:
                print(f"[-] Failed to start {bot_name}: {e}")
        else:
            print(f"[-] {bot_file} not found!")
    
    print("\n" + "="*50)
    print("[+] System Started with Full Features:")
    print("[+]   - Real SQL Injection Testing")
    print("[+]   - Real XSS Detection")
    print("[+]   - API Exposure Detection")
    print("[+]   - IDOR Testing")
    print("[+]   - Sensitive Data Extraction")
    print("[+]   - HTML Reports (Telegram)")
    print("[+]   - JSON Reports (Downloadable)")
    print("[+]")
    print("[+] Test Targets:")
    print("[+]   - hanshin.com.tw")
    print("[+]   - thisshop.com")
    print("[+]   - netpost.vn")
    print("[+]")
    print("[+] Running Bots:")
    for bot_name, proc in processes:
        print(f"[+]   - {bot_name} (Active)")
    print("="*50)
    
    print("\n[*] System Ready for Investor Demonstration!\n")
    
    # Keep launcher alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        for bot_name, proc in processes:
            print(f"[*] Stopping {bot_name}...")
            proc.terminate()
        print("[+] Done!")

if __name__ == "__main__":
    main()
