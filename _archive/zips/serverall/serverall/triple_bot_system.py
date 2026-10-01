#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triple Bot System - Enterprise Grade
"""

import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_CONFIGS = {
    1: {
        "token": "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
        "name": "三太子 (ntp_nezhabot)"
    },
    2: {
        "token": "7442421291:AAFqqbl86iV15XPtAP0BbxuvRT4JJ-cYS6A",
        "name": "毁灭者 (ddosJyBot)"
    },
    3: {
        "token": "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA",
        "name": "哮天犬 (lstjks_jy_bot)"
    }
}

class SingleBot:
    """单个 Bot 实例"""
    def __init__(self, bot_id: int, config: dict):
        self.bot_id = bot_id
        self.config = config
        self.app = None
    
    async def create_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        print(f"\n[+] Bot #{self.bot_id} - /start from {update.effective_user.username}")
        text = (
            f"<b>Bot #{self.bot_id}</b>\n\n"
            f"Name: {self.config['name']}\n"
            f"Status: Online\n\n"
            f"Commands:\n"
            f"/start - Menu\n"
            f"/help - Help"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        text = update.message.text
        print(f"\n[+] Bot #{self.bot_id} - Message: {text[:50]}")
        await update.message.reply_text(f"Echo: {text}")
    
    async def initialize(self):
        """初始化 Bot"""
        print(f"\n[*] Bot #{self.bot_id}: Initializing...")
        
        self.app = Application.builder().token(self.config['token']).build()
        
        # 添加 handlers
        self.app.add_handler(CommandHandler("start", self.create_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        print(f"[+] Bot #{self.bot_id}: Ready to start polling")
    
    async def start(self):
        """启动 Bot"""
        print(f"[*] Bot #{self.bot_id}: Starting polling...")
        await self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

async def run_bot(bot_id: int, config: dict):
    """在独立的任务中运行单个 Bot"""
    try:
        bot = SingleBot(bot_id, config)
        await bot.initialize()
        await bot.start()
    except Exception as e:
        print(f"[-] Bot #{bot_id} error: {e}")

async def main():
    """主函数 - 运行所有 Bot"""
    print("[*] Dragon-V Enterprise Triple Bot System")
    print("[*] Starting all bots...")
    print()
    
    # 创建所有 Bot 的任务
    tasks = []
    for bot_id, config in BOT_CONFIGS.items():
        task = asyncio.create_task(run_bot(bot_id, config))
        tasks.append(task)
    
    print("="*60)
    print("[+] All 3 bots are now running!")
    print("="*60)
    print()
    
    # 等待所有任务
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Stopped")
        sys.exit(0)
