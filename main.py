# main.py - التشغيل الشامل مع ديسكورد وتليجرام والويب

import asyncio
import aiohttp
from config import GAMES_CONFIG
from fetcher import fetch_fandom_codes, fetch_reddit_codes
from listeners import start_telegram_listener
from discord_listener import start_discord_listener

async def run_web_scraper_loop():
    print("[+] بدء حلقة سحب الويب التلقائية (Fandom & Reddit)...")
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for game_slug, config in GAMES_CONFIG.items():
                tasks.append(fetch_fandom_codes(session, game_slug, config))
                tasks.append(fetch_reddit_codes(session, game_slug, config))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(600)

async def main():
    print("=== تم تشغيل الخادوم الآلي لسحب واقتناص الأكواد ===")
    await asyncio.gather(
        start_telegram_listener(),
        start_discord_listener(),
        run_web_scraper_loop(),
        return_exceptions=True
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[!] تم إيقاف العمليات.")

