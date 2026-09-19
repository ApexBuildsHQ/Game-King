# listeners.py - الاستماع الفوري لقنوات تليجرام عبر Telethon

import re
import os
from telethon import TelegramClient, events
from config import GAMES_CONFIG, TARGET_TELEGRAM_CHANNELS
from cleaner import clean_code
from storage import save_code_locally

TELEGRAM_API_ID = int(os.getenv("TG_API_ID", "12345678"))
TELEGRAM_API_HASH = os.getenv("TG_API_HASH", "YOUR_API_HASH")

client = TelegramClient('realtime_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@client.on(events.NewMessage(chats=TARGET_TELEGRAM_CHANNELS))
async def telegram_message_handler(event):
    raw_text = event.raw_text
    if not raw_text:
        return

    words = re.split(r'[\s\n\r\t,;:]+', raw_text)
    for game_slug, config in GAMES_CONFIG.items():
        for word in words:
            cleaned = clean_code(word, config["regex"])
            if cleaned:
                await save_code_locally(game_slug, cleaned, source="Telegram Realtime")

async def start_telegram_listener():
    try:
        print("[+] بدء الاستماع اللحظي لقنوات تليجرام...")
        await client.start()
        await client.run_until_disconnected()
    except Exception as e:
        print(f"[-] خطأ في مستمع تليجرام: {e}")

