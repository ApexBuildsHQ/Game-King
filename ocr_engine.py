# ocr_engine.py - تحليل صور البث المباشر والإعلانات

import aiohttp
from cleaner import clean_code
from config import GAMES_CONFIG
from storage import save_code_locally

OCR_API_KEY = "helloworld" 

async def process_image_url(session: aiohttp.ClientSession, image_url: str, game_slug: str) -> str | None:
    if game_slug not in GAMES_CONFIG:
        return None

    payload = {
        "url": image_url,
        "apikey": OCR_API_KEY,
        "isOverlayRequired": False,
        "OCREngine": 2
    }
    
    try:
        async with session.post("https://api.ocr.space/parse/image", data=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                result = await resp.json()
                parsed_results = result.get("ParsedResults", [])
                if parsed_results:
                    text = parsed_results[0].get("ParsedText", "")
                    for word in text.split():
                        cleaned = clean_code(word, GAMES_CONFIG[game_slug]["regex"])
                        if cleaned:
                            await save_code_locally(game_slug, cleaned, source="Livestream OCR")
                            return cleaned
    except Exception as e:
        print(f"[-] خطأ في تحليل صورة OCR للعبة {game_slug}: {e}")
    return None

