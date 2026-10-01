#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import time
import os

os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)

print("[*] Starting Bot #1...")
subprocess.Popen("python bot_1_group_support.py")
time.sleep(1)

print("[*] Starting Bot #3...")
subprocess.Popen("python bot_3_group_support.py")
time.sleep(1)

print("\n[+] SUCCESS! Both bots are running!\n")
print("[+] Next steps:")
print("    1. Open Telegram")
print("    2. Add @ntp_nezhabot to your group")
print("    3. Add @lstjks_jy_bot to your group")
print("    4. Send /start in the group")
print("    5. Click 'Complete Scan'")
print("    6. Enter target URL")
print("\n[+] Done!")
