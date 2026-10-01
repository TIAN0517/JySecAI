#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Health Check
检查系统是否正常运行
"""

import requests
import json
import time
from datetime import datetime

BOTS = {
    "Bot #1": {
        "token": "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
        "name": "ntp_nezhabot"
    },
    "Bot #3": {
        "token": "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA",
        "name": "lstjks_jy_bot"
    }
}

def check_bot(bot_name, bot_info):
    """检查 Bot 是否在线"""
    print(f"\n[*] Checking {bot_name}...")
    
    try:
        token = bot_info['token']
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_data = data.get('result', {})
                print(f"[+] {bot_name} is ONLINE")
                print(f"    Bot Username: @{bot_data.get('username', 'N/A')}")
                print(f"    Bot ID: {bot_data.get('id', 'N/A')}")
                print(f"    Bot Name: {bot_data.get('first_name', 'N/A')}")
                return True
            else:
                print(f"[-] {bot_name} API Error: {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"[-] {bot_name} HTTP Error: {response.status_code}")
            return False
    
    except requests.exceptions.Timeout:
        print(f"[-] {bot_name} TIMEOUT - Check network connection")
        return False
    except Exception as e:
        print(f"[-] {bot_name} ERROR: {e}")
        return False

def main():
    print("="*60)
    print("Dragon-V Enterprise System Health Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    for bot_name, bot_info in BOTS.items():
        results[bot_name] = check_bot(bot_name, bot_info)
    
    print("\n" + "="*60)
    print("SYSTEM SUMMARY")
    print("="*60)
    
    online_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nBots Online: {online_count}/{total_count}")
    print("\nStatus:")
    for bot_name, status in results.items():
        status_text = "✅ ONLINE" if status else "❌ OFFLINE"
        print(f"  {bot_name}: {status_text}")
    
    if online_count == total_count:
        print("\n[+] System Status: FULLY OPERATIONAL ✅")
        print("[+] Ready for deployment!")
        return 0
    elif online_count > 0:
        print(f"\n[!] System Status: PARTIAL ({online_count}/{total_count}) ⚠️")
        print("[!] Some bots are not responding")
        return 1
    else:
        print("\n[-] System Status: OFFLINE ❌")
        print("[-] No bots responding")
        print("[*] Try: python LAUNCH.py")
        return 2

if __name__ == "__main__":
    exit(main())
