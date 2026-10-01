#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRAGON-V Complete Launcher
Complete Enterprise System Startup
"""

import os
import sys
import time
import subprocess
import threading

BOT_CONFIG = {
    "bot_1": {
        "file": "bot_ultimate_with_waf_bypass.py",
        "name": "Bot #1 (ntp_nezhabot)",
        "id": "8314772330"
    },
    "bot_3": {
        "file": "bot_3_ultimate_with_waf_bypass.py",
        "name": "Bot #3 (lstjks_jy_bot)",
        "id": "8344575992"
    }
}

def print_title(text):
    """Print formatted title"""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80 + "\n")

def print_section(text):
    """Print section header"""
    print("\n" + "-"*80)
    print(text)
    print("-"*80 + "\n")

def check_system():
    """Check system requirements"""
    print_section("SYSTEM CHECK")
    
    # Python version
    version = sys.version_info
    print(f"[*] Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("[+] Python version OK\n")
    else:
        print("[!] Python 3.7+ required\n")
        return False
    
    # Check modules
    print("[*] Checking required modules...")
    modules = {
        "telegram": "Telegram API",
        "requests": "HTTP Requests"
    }
    
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"    [+] {desc} ({module}) - OK")
        except ImportError:
            print(f"    [-] {desc} ({module}) - MISSING")
            return False
    
    print()
    
    # Check bot files
    print("[*] Checking Bot files...")
    for bot_key, config in BOT_CONFIG.items():
        if os.path.exists(config["file"]):
            size = os.path.getsize(config["file"])
            print(f"    [+] {config['name']} - {size} bytes - OK")
        else:
            print(f"    [-] {config['name']} - NOT FOUND")
            return False
    
    print()
    return True

def start_bot(bot_key, config):
    """Start a bot process"""
    bot_file = config["file"]
    bot_name = config["name"]
    
    print(f"[*] Starting {bot_name}...")
    print(f"    File: {bot_file}")
    print(f"    ID: {config['id']}")
    
    try:
        if sys.platform == "win32":
            # Windows - start in same console (inherit stdout/stderr)
            proc = subprocess.Popen(
                [sys.executable, bot_file],
                stdout=None,
                stderr=None
            )
        else:
            # Linux/Mac
            proc = subprocess.Popen(
                [sys.executable, bot_file]
            )
        
        print(f"    PID: {proc.pid}")
        print(f"    [+] {bot_name} started successfully\n")
        return proc
        
    except Exception as e:
        print(f"    [-] Failed to start: {str(e)}\n")
        return None

def main():
    """Main launcher"""
    print_title("DRAGON-V ENTERPRISE SYSTEM")
    
    print("Starting comprehensive system initialization...\n")
    
    # System check
    if not check_system():
        print("[!] System check failed!")
        print("[*] Please fix the issues above and try again")
        input("Press Enter to exit...")
        return False
    
    # Start bots
    print_section("STARTING BOTS")
    
    processes = {}
    for bot_key, config in BOT_CONFIG.items():
        proc = start_bot(bot_key, config)
        if proc:
            processes[bot_key] = proc
        time.sleep(2)
    
    if not processes:
        print("[!] No bots started!")
        input("Press Enter to exit...")
        return False
    
    # System status
    print_section("SYSTEM STATUS")
    
    print("[+] ONLINE BOTS:\n")
    for bot_key, config in BOT_CONFIG.items():
        if bot_key in processes:
            proc = processes[bot_key]
            status = "RUNNING" if proc.poll() is None else "STOPPED"
            print(f"    [+] {config['name']}")
            print(f"        Status: {status}")
            print(f"        PID: {proc.pid}\n")
    
    print("[+] FEATURES:\n")
    features = [
        "SQL Injection - Real Data Extraction",
        "XSS - Session Hijacking",
        "API Disclosure - Endpoint Enumeration",
        "WAF Bypass - 10 Advanced Methods",
        "Enterprise Reports - HTML + JSON"
    ]
    for feature in features:
        print(f"    ✓ {feature}")
    
    print()
    print_section("TELEGRAM USAGE")
    
    print("Follow these steps to use the system:\n")
    print("1. OPEN TELEGRAM\n")
    print("2. SEARCH FOR BOT:\n")
    print("   - @ntp_nezhabot (Bot #1)\n")
    print("   - @lstjks_jy_bot (Bot #3)\n")
    print("3. SEND COMMAND:\n")
    print("   /start\n")
    print("4. CLICK MENU:\n")
    print("   🔥 Start Scan\n")
    print("5. INPUT TARGET:\n")
    print("   hanshin.com.tw")
    print("   thisshop.com")
    print("   netpost.vn\n")
    print("6. WAIT FOR RESULTS:\n")
    print("   5-15 minutes for complete report\n")
    
    print_section("SYSTEM RUNNING")
    
    print("Both bots are now running in the background.\n")
    print("The system is FULLY OPERATIONAL and ready to scan targets.\n")
    
    print("="*80)
    print("Press Ctrl+C to stop all bots and exit".center(80))
    print("="*80 + "\n")
    
    # Monitor processes
    try:
        while True:
            all_alive = True
            for bot_key, proc in processes.items():
                if proc.poll() is not None:
                    print(f"[!] {BOT_CONFIG[bot_key]['name']} stopped unexpectedly")
                    all_alive = False
            
            if not all_alive:
                print("[!] One or more bots crashed")
                break
            
            time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n\n" + "-"*80)
        print("Shutting down system...".center(80))
        print("-"*80 + "\n")
        
        for bot_key, proc in processes.items():
            print(f"[*] Stopping {BOT_CONFIG[bot_key]['name']}...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"    [+] Stopped")
            except:
                try:
                    proc.kill()
                    print(f"    [+] Force stopped")
                except:
                    pass
        
        print("\n" + "="*80)
        print("System shutdown complete".center(80))
        print("="*80 + "\n")
        
        return True
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
