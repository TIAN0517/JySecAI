#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRAGON-V One-Click Launcher
Enterprise-Grade Vulnerability Scanning System
"""

import os
import sys
import time
import subprocess
import threading

# ==================== Configuration ====================
BOT_CONFIG = {
    "bot_1": {
        "file": "bot_ultimate_with_waf_bypass.py",
        "name": "Bot #1 (ntp_nezhabot)",
    },
    "bot_3": {
        "file": "bot_3_ultimate_with_waf_bypass.py", 
        "name": "Bot #3 (lstjks_jy_bot)",
    }
}

REQUIRED_MODULES = [
    "telegram",
    "requests"
]

# ==================== Helper Functions ====================

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*80)
    print("DRAGON-V Enterprise Vulnerability Scanning System - One-Click Start")
    print("="*80)
    print()

def check_python_version():
    """Check Python version"""
    print("[*] Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"OK: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"FAILED: Need Python 3.7+, got {version.major}.{version.minor}")
        return False

def check_imports():
    """Check required modules"""
    print("[*] Checking imports...", end=" ")
    
    missing = []
    for module in REQUIRED_MODULES:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"FAILED: Missing {', '.join(missing)}")
        print()
        print("FIX: Run these commands:")
        print(f"  python -m pip install --upgrade python-telegram-bot")
        print(f"  python -m pip install requests")
        return False
    
    print("OK")
    return True

def check_bot_files():
    """Check if Bot files exist"""
    print("[*] Checking Bot files...", end=" ")
    
    for bot_key, config in BOT_CONFIG.items():
        if not os.path.exists(config["file"]):
            print(f"FAILED: {config['file']} not found")
            return False
    
    print("OK")
    return True

def start_bot_thread(bot_key, config):
    """Start a bot in a separate thread and show output"""
    bot_file = config["file"]
    bot_name = config["name"]
    
    print(f"\n[*] Starting {bot_name} in background...", end=" ")
    sys.stdout.flush()
    
    try:
        # Start bot with output visible
        proc = subprocess.Popen(
            [sys.executable, bot_file],
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        print(f"OK (PID: {proc.pid})")
        sys.stdout.flush()
        return proc
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return None

def print_status(processes):
    """Print system status"""
    print()
    print("="*80)
    print("SYSTEM STATUS")
    print("="*80)
    print()
    print("Active Bots:")
    for bot_key, config in BOT_CONFIG.items():
        if bot_key in processes and processes[bot_key].poll() is None:
            print(f"  * {config['name']} - RUNNING")
        else:
            print(f"  * {config['name']} - STOPPED/ERROR")
    
    print()
    print("Features:")
    print("  * SQL Injection (Real Data Extraction)")
    print("  * XSS (Session Hijacking)")
    print("  * API Disclosure (Endpoint Enumeration)")
    print("  * WAF Bypass (10 Advanced Methods)")
    print("  * Enterprise Reports (HTML + JSON)")
    
    print()
    print("Usage in Telegram:")
    print("  1. Search: @ntp_nezhabot or @lstjks_jy_bot")
    print("  2. Command: /start")
    print("  3. Select: Start Scan")
    print("  4. Input: Target URL (e.g., hanshin.com.tw)")
    print("  5. Wait: 5-15 minutes for results")
    
    print()
    print("="*80)
    print("System is READY! Bots are running in background")
    print("="*80)
    print()

def monitor_processes(processes):
    """Monitor running processes"""
    try:
        while True:
            time.sleep(5)
            # Check if any bot crashed
            for bot_key, proc in processes.items():
                if proc.poll() is not None:
                    print(f"\n[WARNING] {BOT_CONFIG[bot_key]['name']} stopped (exit code: {proc.poll()})")
    except KeyboardInterrupt:
        print()
        print()
        print("[*] Received stop signal...")
        print("[*] Shutting down bots...")
        
        for bot_key, proc in processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"    * {BOT_CONFIG[bot_key]['name']} - stopped")
            except:
                try:
                    proc.kill()
                except:
                    pass
                print(f"    * {BOT_CONFIG[bot_key]['name']} - force stopped")
        
        print()
        print("System stopped successfully")
        print()

def main():
    """Main function"""
    print_banner()
    
    # Pre-flight checks
    print("PRE-FLIGHT CHECKS:")
    print("-" * 80)
    
    if not check_python_version():
        return False
    
    if not check_bot_files():
        return False
    
    if not check_imports():
        return False
    
    print()
    print("=" * 80)
    print()
    print("STARTING BOTS:")
    print("-" * 80)
    
    # Start bots
    processes = {}
    for bot_key, config in BOT_CONFIG.items():
        proc = start_bot_thread(bot_key, config)
        if proc:
            processes[bot_key] = proc
        time.sleep(1)
    
    print()
    
    if not processes:
        print("ERROR: No bots started!")
        return False
    
    print_status(processes)
    
    monitor_processes(processes)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
