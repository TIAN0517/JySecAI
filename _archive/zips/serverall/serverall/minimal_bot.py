#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("SUCCESS! /start works!")
    print("[+] START HANDLER CALLED!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Echo: {update.message.text}")
    print(f"[+] MESSAGE: {update.message.text}")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

print("[*] Bot starting...")
app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
