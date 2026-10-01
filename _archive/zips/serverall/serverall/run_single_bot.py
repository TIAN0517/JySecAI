#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Bot Launcher - Run one bot at a time
"""

import os
import sys
import asyncio

# Set encoding to UTF-8 for output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("[*] Dragon-V Single Bot System")
print()

try:
    print("[*] Importing modules...")
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, filters, ContextTypes
    )
    from telegram.constants import ParseMode
    print("[+] Telegram modules loaded")
    
except Exception as e:
    print(f"[-] Error importing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("Which bot do you want to run?")
print("=" * 60)
print("1. Bot #1 (8314772330)")
print("2. Bot #2 (7442421291)")
print("3. Bot #3 (8344575992)")
print()

choice = input("Enter choice (1-3): ").strip()

BOT_TOKENS = {
    "1": ("8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw", 1),
    "2": ("7442421291:AAFqqbl86iV15XPtAP0BbxuvRT4JJ-cYS6A", 2),
    "3": ("8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA", 3),
}

if choice not in BOT_TOKENS:
    print("[-] Invalid choice!")
    sys.exit(1)

token, bot_id = BOT_TOKENS[choice]

print()
print(f"[*] Starting Bot #{bot_id}...")
print()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    print(f"[+] /start from user {update.effective_user.id} in chat {update.effective_chat.id}")
    await update.message.reply_text(
        f"<b>Dragon-V Enterprise Bot #{bot_id}</b>\n\n"
        f"<b>Features</b>\n"
        f"* WAF Detection (95%+)\n"
        f"* False Positive Control (< 1%)\n"
        f"* Enterprise Grade\n"
        f"\n<b>Input URL to scan</b>\n"
        f"Example: https://example.com",
        parse_mode=ParseMode.HTML
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages"""
    text = update.message.text
    print(f"[+] Message from user {update.effective_user.id}: {text[:50]}")
    await update.message.reply_text(
        f"<b>Message Received</b>\n\n"
        f"<code>{text[:100]}</code>\n\n"
        f"Starting scan...",
        parse_mode=ParseMode.HTML
    )

async def main():
    """Main function"""
    try:
        # Create app
        app = Application.builder().token(token).build()
        
        print(f"[*] Initializing Bot #{bot_id}...")
        await app.initialize()
        
        print(f"[*] Adding handlers...")
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        print(f"[*] Starting polling...")
        await app.updater.start_polling(allowed_updates=None)
        
        print(f"[+] Bot #{bot_id} is ready!")
        print()
        print("=" * 60)
        print(f"[+] Bot #{bot_id} is listening!")
        print("=" * 60)
        print()
        print("[*] Waiting for messages... (Press Ctrl+C to stop)")
        print()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        print("\n[*] Stopping bot...")
        try:
            await app.updater.stop()
            await app.shutdown()
            print("[+] Bot stopped")
        except:
            pass
        sys.exit(0)
    
    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Program terminated")
        sys.exit(0)
