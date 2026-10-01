#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Reply Test - Send a message directly to test user
"""

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"
USER_ID = 8093460847  # Your user ID from the logs

async def main():
    """Main"""
    try:
        from telegram import Bot
        
        print("[*] Direct Reply Test")
        print()
        
        bot = Bot(token=TOKEN)
        
        print("[*] Testing direct message send...")
        print(f"    To user: {USER_ID}")
        print()
        
        # Try to send a direct message
        message = await bot.send_message(
            chat_id=USER_ID,
            text="<b>Direct Test Message</b>\n\nIf you see this, the bot can send messages!",
            parse_mode="HTML"
        )
        
        print("[+] SUCCESS! Message sent!")
        print(f"    Message ID: {message.message_id}")
        print()
        print("Check Telegram - you should have received a message from @ntp_nezhabot")
        
    except Exception as e:
        print(f"[-] FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
