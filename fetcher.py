# fetcher.py - السحب الدوري غير المتزامن من Fandom و Reddit

import re
import aiohttp
from selectolax.parser import HTMLParser
from config import GAMES_CONFIG
from cleaner import clean_code
from storage import save_code_locally

async def fetch_fandom_codes(session: aiohttp.ClientSession, game_slug: str, config: dict):
    url = config.get("fandom_wiki")
    if not url:
        return

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                data = await resp.json()
                html_content = data.get("parse", {}).get("text", {}).get("*", "")
                if html_content:
                    tree = HTMLParser(html_content)
                    elements = tree.css("code, td b, tr td:first-child, span.code")
                    for el in elements:
                        cleaned = clean_code(el.text(), config["regex"])
                        if cleaned:
                            await save_code_locally(game_slug, cleaned, source="Fandom Wiki")
    except Exception as e:
        print(f"[-] خطأ في سحب Fandom للعبة {game_slug}: {e}")

async def fetch_reddit_codes(session: aiohttp.ClientSession, game_slug: str, config: dict):
    url = config.get("reddit_url")
    if not url:
        return

    headers = {"User-Agent": "Mozilla/5.0 (AutomatedCodeFetcher/2.0)"}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                data = await resp.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    title = post.get("data", {}).get("title", "")
                    selftext = post.get("data", {}).get("selftext", "")
                    combined_text = f"{title} {selftext}"
                    
                    words = re.split(r'[\s\n\r\t,;:]+', combined_text)
                    for word in words:
                        cleaned = clean_code(word, config["regex"])
                        if cleaned:
                            await save_code_locally(game_slug, cleaned, source="Reddit JSON")
    except Exception as e:
        print(f"[-] خطأ في سحب Reddit للعبة {game_slug}: {e}")

