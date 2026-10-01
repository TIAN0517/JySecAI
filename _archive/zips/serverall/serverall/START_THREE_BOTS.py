#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start all three bots in separate processes - FIXED
"""

import subprocess
import sys
import time
import os

print("[*] Starting Triple Bot System in Separate Processes")
print()

# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"[*] Working directory: {current_dir}")
print()

# Kill any existing Python processes
print("[*] Cleaning up old processes...")
subprocess.run("taskkill /IM python.exe /F 2>nul", shell=True, stderr=subprocess.DEVNULL)
time.sleep(2)
print("[+] Old processes cleaned")
print()

# Start bots with absolute paths
bot_files = [
    os.path.join(current_dir, "bot_1_instance.py"),
    os.path.join(current_dir, "bot_2_instance.py"),
    os.path.join(current_dir, "bot_3_instance.py")
]

processes = []

for i, bot_file in enumerate(bot_files, 1):
    if os.path.exists(bot_file):
        print(f"[*] Starting Bot #{i}...")
        try:
            p = subprocess.Popen([sys.executable, bot_file], cwd=current_dir)
            processes.append(p)
            time.sleep(1)  # Slight delay between starts
        except Exception as e:
            print(f"[-] Failed to start Bot #{i}: {e}")
    else:
        print(f"[-] Bot #{i} file not found: {bot_file}")

print()
print("="*60)
print("[+] All bots should be running now!")
print("="*60)
print()
print("[*] Go to Telegram and test all 3 bots")
print("[*] Press Ctrl+C to stop all bots")
print()

try:
    # Wait for all processes
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\n[*] Stopping all bots...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    
    for p in processes:
        try:
            p.wait(timeout=2)
        except:
            p.kill()
    
    print("[+] All bots stopped")
    sys.exit(0)
