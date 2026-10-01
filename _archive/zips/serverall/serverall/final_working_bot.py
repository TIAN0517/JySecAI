#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Working Bot - Complete Fixed Version
"""

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("[*] Final Working Bot")
print()

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"

async def main():
    """Main"""
    try:
        from telegram import Bot, Update
        from telegram.ext import (
            Application, 
            CommandHandler, 
            MessageHandler, 
            filters, 
            ContextTypes,
            BaseHandler
        )
        from telegram.constants import ParseMode
        
        print("[+] Imports successful")
        print()
        
        # Create bot to test connection
        print("[*] Testing bot connection...")
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        print(f"[+] Connected as: @{me.username}")
        print()
        
        # Create application
        print("[*] Creating application...")
        app = Application.builder().token(TOKEN).build()
        
        print("[*] Initializing application...")
        await app.initialize()
        
        # Define handlers
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print("\n" + "="*60)
            print("[SUCCESS] /START command received!")
            print(f"From: {update.effective_user.username}")
            print("="*60 + "\n")
            
            text = (
                "<b>Dragon-V Enterprise Bot</b>\n\n"
                "Welcome! The bot is working.\n\n"
                "Commands:\n"
                "/start - Show this message\n"
                "/help - Get help\n\n"
                "Or send any message!"
            )
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            print("[+] Reply sent to user")
        
        async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print("\n[+] /help received\n")
            await update.message.reply_text("This is help information.")
        
        async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text
            print(f"\n[+] Message received: {text[:50]}\n")
            await update.message.reply_text(f"Echo: {text}")
        
        # Add handlers
        print("[*] Adding handlers...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        print("[+] Handlers added")
        print()
        
        # Start polling with aggressive settings
        print("[*] Starting polling...")
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30
        )
        
        print("[+] Polling started")
        print()
        print("="*60)
        print("[+] BOT IS READY!")
        print("[+] Send messages in Telegram now!")
        print("="*60)
        print()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Stopped by user")
        sys.exit(0)
