# discord_listener.py - الاستماع اللحظي لقنوات ديسكورد

import os
import re
import discord
from config import GAMES_CONFIG, TARGET_DISCORD_CHANNELS
from cleaner import clean_code
from storage import save_code_locally

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[+] تم الاتصال بديسكورد بنجاح كـ {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id in TARGET_DISCORD_CHANNELS:
        raw_text = message.content
        if not raw_text:
            return

        words = re.split(r'[\s\n\r\t,;:]+', raw_text)
        for game_slug, config in GAMES_CONFIG.items():
            for word in words:
                cleaned = clean_code(word, config["regex"])
                if cleaned:
                    await save_code_locally(game_slug, cleaned, source="Discord Realtime")

async def start_discord_listener():
    if not DISCORD_BOT_TOKEN:
        print("[-] لم يتم العثور على DISCORD_BOT_TOKEN، سيتم تخطي ديسكورد.")
        return
    try:
        print("[+] بدء الاستماع اللحظي لقنوات ديسكورد...")
        await client.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"[-] خطأ في مستمع ديسكورد: {e}")

