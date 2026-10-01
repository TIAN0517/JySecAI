#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Working Bot - Fixed Version
"""

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("[*] Working Bot v1.0")
print()

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"

async def main():
    """Main"""
    try:
        from telegram import Bot, Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from telegram.constants import ParseMode
        
        print("[+] Imports successful")
        print()
        
        # Create and initialize app FIRST
        print("[*] Creating application...")
        app = Application.builder().token(TOKEN).build()
        
        print("[*] Initializing...")
        await app.initialize()
        
        # Define handlers
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print("\n" + "="*60)
            print("[SUCCESS] /START COMMAND RECEIVED!")
            print("="*60 + "\n")
            
            text = (
                "<b>Dragon-V Bot is Working!</b>\n\n"
                "Welcome to the Enterprise Bot System.\n\n"
                "Commands:\n"
                "/start - Show this menu\n"
                "/help - Get help\n\n"
                "Or just send a message!"
            )
            
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            print("[+] Reply sent successfully!")
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            print("\n[DEBUG] /help received\n")
            await update.message.reply_text("This is the help message!")
        
        async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text
            print(f"\n[DEBUG] Message: {text}\n")
            await update.message.reply_text(f"Echo: {text}")
        
        # Add handlers AFTER initialization
        print("[*] Adding handlers...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        print("[+] Handlers added successfully")
        print()
        
        # Start polling
        print("[*] Starting polling...")
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False
        )
        
        print("[+] Bot is now running!")
        print()
        print("=" * 60)
        print("[+] Ready to receive messages from Telegram")
        print("=" * 60)
        print()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except Exception as e:
        print(f"[-] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Stopped")
        sys.exit(0)
