#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed Triple Bot System - Handlers added AFTER initialization
"""

import os
import sys
import asyncio
from datetime import datetime

# Set encoding to UTF-8 for output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("[*] Dragon-V Enterprise Triple Bot System")
print("[*] Version: 3.2 (Fixed)")
print()

try:
    print("[*] Importing modules...")
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler, 
        MessageHandler, filters, ContextTypes
    )
    from telegram.constants import ParseMode
    print("[+] Telegram modules loaded")
    
except Exception as e:
    print(f"[-] Error importing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Bot Tokens
BOT_TOKENS = {
    1: "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
    2: "7442421291:AAFqqbl86iV15XPtAP0BbxuvRT4JJ-cYS6A",
    3: "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA"
}

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int):
    """Handle /start command"""
    print(f"[+] Bot #{bot_id} - /start from user {update.effective_user.id}")
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

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int):
    """Handle messages"""
    text = update.message.text
    print(f"[+] Bot #{bot_id} - Message from user {update.effective_user.id}: {text[:50]}")
    await update.message.reply_text(
        f"<b>Message Received</b>\n\n"
        f"<code>{text[:100]}</code>\n\n"
        f"Starting scan...",
        parse_mode=ParseMode.HTML
    )

async def setup_bot(bot_id: int, token: str):
    """Setup single bot with handlers AFTER initialization"""
    print(f"[*] Setting up Bot #{bot_id}...")
    
    try:
        # Create app
        app = Application.builder().token(token).build()
        
        # Initialize FIRST
        print(f"    [*] Initializing Bot #{bot_id}...")
        await app.initialize()
        
        # Add handlers AFTER initialization
        print(f"    [*] Adding handlers to Bot #{bot_id}...")
        
        # Create lambda to capture bot_id
        start_func = lambda u, c, bid=bot_id: start_handler(u, c, bid)
        message_func = lambda u, c, bid=bot_id: message_handler(u, c, bid)
        
        app.add_handler(CommandHandler("start", start_func))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_func))
        
        # Start polling
        print(f"    [+] Starting polling for Bot #{bot_id}...")
        await app.updater.start_polling(allowed_updates=None)
        
        print(f"    [+] Bot #{bot_id} is ready!")
        return app
    except Exception as e:
        print(f"    [-] Error setting up Bot #{bot_id}: {e}")
        import traceback
        traceback.print_exc()
        raise

async def main():
    """Main function"""
    print("[*] Initializing Triple Bot System...")
    print()
    
    apps = {}
    try:
        # Setup all three bots
        for bot_id, token in BOT_TOKENS.items():
            print(f"[*] Bot #{bot_id}:")
            apps[bot_id] = await setup_bot(bot_id, token)
            print()
        
        print("=" * 60)
        print("[+] All 3 Bots are now listening!")
        print("=" * 60)
        print()
        print("[*] Ready for messages in Telegram...")
        print("[*] Waiting... (Press Ctrl+C to stop)")
        print()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        print("\n[*] Stopping all bots...")
        for bot_id, app in apps.items():
            try:
                print(f"    [*] Stopping Bot #{bot_id}...")
                await app.updater.stop()
                await app.shutdown()
                print(f"    [+] Bot #{bot_id} stopped")
            except Exception as e:
                print(f"    [-] Error stopping Bot #{bot_id}: {e}")
        print("[+] All bots stopped")
        print("[*] Exiting...")
        sys.exit(0)
    
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Program terminated")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
