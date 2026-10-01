#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset Bot - Clear all updates and restart
"""

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"

async def main():
    """Main"""
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    
    print("[*] Reset Bot")
    print()
    
    # Create bot
    bot = Bot(token=TOKEN)
    
    # Get all updates first
    print("[*] Getting all pending updates...")
    updates = await bot.get_updates(offset=-1, allowed_updates=Update.ALL_TYPES)
    print(f"[+] Found {len(updates)} pending updates")
    
    if updates:
        # Get the latest update_id and skip past it
        latest_id = updates[-1].update_id
        print(f"[*] Latest update ID: {latest_id}")
        print(f"[*] Fetching with offset {latest_id + 1} to clear queue...")
        
        # Fetch with new offset to mark as read
        await bot.get_updates(offset=latest_id + 1, limit=1)
        print("[+] Queue cleared!")
    
    print()
    print("[*] Creating fresh application...")
    app = Application.builder().token(TOKEN).build()
    
    print("[*] Initializing...")
    await app.initialize()
    
    print("[*] Adding handlers...")
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("\n[!!!] /START RECEIVED !!!\n")
        await update.message.reply_text("Bot is working!")
    
    async def any_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"\n[!!!] MESSAGE: {update.message.text} !!!\n")
        await update.message.reply_text(f"Echo: {update.message.text}")
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_msg))
    
    print("[+] Ready!")
    print()
    print("="*60)
    print("[+] Bot is listening - send a message NOW!")
    print("="*60)
    print()
    
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Stopped")
        sys.exit(0)
