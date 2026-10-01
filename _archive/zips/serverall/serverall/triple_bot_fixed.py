#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triple Bot System - FIXED
使用 start_polling() 而不是 run_polling()
"""

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_CONFIGS = {
    1: {
        "token": "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
        "name": "三太子"
    },
    2: {
        "token": "7442421291:AAFqqbl86iV15XPtAP0BbxuvRT4JJ-cYS6A",
        "name": "毁灭者"
    },
    3: {
        "token": "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA",
        "name": "哮天犬"
    }
}

class SingleBot:
    """单个 Bot 实例"""
    def __init__(self, bot_id: int, config: dict):
        self.bot_id = bot_id
        self.config = config
        self.app = None
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        print(f"\n[+] Bot #{self.bot_id} - /START from {update.effective_user.username}")
        text = (
            f"<b>Bot #{self.bot_id}</b>\n\n"
            f"Name: {self.config['name']}\n"
            f"Status: Online\n\n"
            f"Send any message to test!"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        print(f"[+] Bot #{self.bot_id} - Reply sent")
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        text = update.message.text
        print(f"\n[+] Bot #{self.bot_id} - Message: {text[:50]}")
        await update.message.reply_text(f"Echo: {text}")
        print(f"[+] Bot #{self.bot_id} - Echo sent")
    
    async def start(self):
        """启动 Bot"""
        try:
            print(f"[*] Bot #{self.bot_id}: Initializing application...")
            self.app = Application.builder().token(self.config['token']).build()
            
            print(f"[*] Bot #{self.bot_id}: Adding handlers...")
            self.app.add_handler(CommandHandler("start", self.start_handler))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            
            print(f"[*] Bot #{self.bot_id}: Initializing app...")
            await self.app.initialize()
            
            print(f"[*] Bot #{self.bot_id}: Starting polling...")
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            print(f"[+] Bot #{self.bot_id}: Polling started successfully!")
            
            # 保持运行
            while True:
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"[-] Bot #{self.bot_id} error: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数 - 运行所有 Bot"""
    print("[*] Dragon-V Enterprise Triple Bot System (FIXED)")
    print("[*] Starting all bots simultaneously...")
    print()
    
    # 创建所有 Bot 的任务
    tasks = []
    for bot_id, config in BOT_CONFIGS.items():
        task = asyncio.create_task(SingleBot(bot_id, config).start())
        tasks.append(task)
    
    print("="*60)
    print("[+] All 3 bots are now initializing and starting...")
    print("="*60)
    print()
    
    # 等待所有任务（实际上会无限等待）
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[*] Stopping all bots...")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] System stopped")
        sys.exit(0)
