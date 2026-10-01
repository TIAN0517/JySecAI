#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRAGON-V Complete System Launcher
Simple Python launcher to start both bots
"""

import subprocess
import time
import os
import sys

print("\n" + "="*70)
print("DRAGON-V Complete System - Enterprise Grade + Exploitation + WAF Bypass")
print("="*70)

print("\n[*] Cleaning old processes...")
os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)
print("[+] Done!\n")

print("[*] Starting Bot 1...")
print("    File: bot_ultimate_with_waf_bypass.py")
try:
    subprocess.Popen("start python bot_ultimate_with_waf_bypass.py", shell=True)
    print("[+] Bot 1 started in new window\n")
except:
    print("[!] Error starting Bot 1\n")

time.sleep(2)

print("[*] Starting Bot 3...")
print("    File: bot_3_ultimate_with_waf_bypass.py")
try:
    subprocess.Popen("start python bot_3_ultimate_with_waf_bypass.py", shell=True)
    print("[+] Bot 3 started in new window\n")
except:
    print("[!] Error starting Bot 3\n")

print("="*70)
print("[+] SUCCESS! Complete System Started!")
print("="*70)

print("\nFeatures:")
print("  ✓ 20+ Real CVE Database")
print("  ✓ Real POC Exploitation")
print("  ✓ Real Data Extraction")
print("  ✓ WAF Detection System")
print("  ✓ 10 Advanced WAF Bypass Techniques")
print("  ✓ AliYunDun Specialized Bypass")
print("  ✓ Support for sqlmap-proof WAF")

print("\nSupported WAF:")
print("  • AliYunDun (Alibaba Cloud Computing)")
print("  • CloudFlare")
print("  • ModSecurity")

print("\nNext steps:")
print("  1. Open Telegram")
print("  2. Add @ntp_nezhabot or @lstjks_jy_bot")
print("  3. Send /start")
print("  4. Click 'Start Ultimate Scan'")
print("  5. Enter target URL")
print("  6. Wait for complete scan + exploitation + WAF bypass\n")

print("="*70)
print("System is ready for use!")
print("="*70 + "\n")

input("Press Enter to exit...")
