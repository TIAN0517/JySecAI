#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import time
import os

print("\n" + "="*60)
print("Dragon-V 完整企业级扫描系统")
print("="*60)
print("\n[*] 清理旧进程...")
os.system("taskkill /IM python.exe /F 2>nul")
time.sleep(2)

print("[+] 完成!")
print("\n[*] 启动 Bot #1 (完整真实版)...")
subprocess.Popen("python bot_1_final.py")
time.sleep(1)

print("[*] 启动 Bot #3 (完整真实版)...")
subprocess.Popen("python bot_3_final.py")
time.sleep(1)

print("\n" + "="*60)
print("[+] SUCCESS! 两个完整版 Bot 已启动!")
print("="*60)
print("\n[功能说明]")
print("✅ 4 阶段完整扫描")
print("✅ 真实的扫描延迟 (能看到每个阶段)")
print("✅ SQL 注入 + XSS + API + IDOR")
print("✅ 群组 + 私聊支持")
print("✅ 完整 HTML + JSON 报告")
print("\n[使用方法]")
print("1. 打开 Telegram")
print("2. 添加 @ntp_nezhabot 到群组")
print("3. 添加 @lstjks_jy_bot 到群组")
print("4. 在群组中发送 /start")
print("5. 点击'完整扫描'")
print("6. 输入网址 (例: hanshin.com.tw)")
print("7. 等待 5-10 分钟观看完整扫描过程")
print("\n[所有扫描都有真实延迟]")
print("- 每个测试都需要真实时间")
print("- 你能看到每个阶段的进度")
print("- 完整的漏洞详情\n")
