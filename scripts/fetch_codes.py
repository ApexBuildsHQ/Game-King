import json
import os
import random
import re
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# قائمة User-Agents حديثة ومتنوعة لأجهزة مختلفة (Desktop & Mobile)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
]

# قائمة تنقية صارمة للكلمات غير المرغوب فيها ورؤوس الجداول
FORBIDDEN_WORDS = {
    "EXPIRED", "WORKING", "CODES", "CODE", "REDEEM", "ROBLOX", "UPDATE", "FREE", 
    "NONE", "OVERVIEW", "DETAILS", "REWARD", "REWARDS", "CHINA", "ASIA", "GLOBAL", 
    "AMERICA", "EUROPE", "SERVER", "STATUS", "DESCRIPTION", "NOTES", "ACTIVE", 
    "INACTIVE", "VERIFIED", "WELCOME_PROMO_2026", "VIP_LOCKED_CODE", "ITEM", "ITEMS",
    "CLICK", "HERE", "MORE", "DISCORD", "TWITTER", "YOUTUBE", "FACEBOOK", "TOGGLE"
}

def clean_code(text):
    """تنظيف وتدقيق نسق الكود المستخرج"""
    code = text.strip().upper()
    if len(code) < 4 or len(code) > 25:
        return None
    if code in FORBIDDEN_WORDS or any(w in code for w in ["HTTP", "WWW", "WIKI", ".COM"]):
        return None
    if re.match(r"^[A-Z0-9_\-]+$", code):
        return code
    return None

def get_human_browser_headers():
    """توليد هيدرز كاملة توهم الموقع بأن الطلب قادم من متصفح بشري حقيقي"""
    agent = random.choice(USER_AGENTS)
    is_mobile = "Mobile" in agent
    
    headers = {
        "User-Agent": agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    if "Chrome" in agent:
        headers["Sec-Ch-Ua"] = '"Not/A)Brand";v="8", "Chromium";v="128", "Google Chrome";v="128"'
        headers["Sec-Ch-Ua-Mobile"] = "?1" if is_mobile else "?0"
        headers["Sec-Ch-Ua-Platform"] = '"Android"' if is_mobile else '"Windows"'
        
    return headers

def fetch_game_codes(url):
    """جلب الأكواد بمحاكاة المتصفح مع معالجة الأخطاء"""
    try:
        headers = get_human_browser_headers()
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            codes = []
            
            # البحث عن الأكواد في العناصر المعتادة داخل المقالات
            for tag in soup.find_all(["code", "strong", "b", "td"]):
                cleaned = clean_code(tag.text)
                if cleaned and cleaned not in codes:
                    codes.append(cleaned)
            return codes
        else:
            print(f"  [HTTP {res.status_code}] Failed to access {url}")
    except Exception as e:
        print(f"  [Error] Could not fetch from {url}: {e}")
    return []

def main():
    db_path = "data/codes.json"
    
    # 1. تحميل قاعدة البيانات السابقة إن وجدت
    existing_games_db = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                existing_games_db = json.load(f).get("games", {})
        except Exception as e:
            print(f"Warning: Failed to load previous DB: {e}")

    # 2. القائمة الكاملة لـ 38 لعبة مع أفضل المصادر المحدثة لكل منها
    GAMES_CONFIG = {
        # --- Gacha & RPG ---
        "genshin_impact": {
            "name": "Genshin Impact",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/genshin-impact/codes/"
        },
        "honkai_star_rail": {
            "name": "Honkai: Star Rail",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/honkai-star-rail/codes/"
        },
        "zenless_zone_zero": {
            "name": "Zenless Zone Zero",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/zenless-zone-zero/codes/"
        },
        "wuthering_waves": {
            "name": "Wuthering Waves",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/wuthering-waves/codes/"
        },
        "solo_leveling_arise": {
            "name": "Solo Leveling: Arise",
            "category": "Gacha",
            "url": "https://progameguides.com/solo-leveling-arise/solo-leveling-arise-codes/"
        },
        "tower_of_fantasy": {
            "name": "Tower of Fantasy",
            "category": "Gacha",
            "url": "https://progameguides.com/tower-of-fantasy/tower-of-fantasy-codes/"
        },
        "dislyte": {
            "name": "Dislyte",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/dislyte/codes/"
        },
        "cookie_run_kingdom": {
            "name": "Cookie Run: Kingdom",
            "category": "Gacha",
            "url": "https://progameguides.com/cookie-run-kingdom/cookie-run-kingdom-codes/"
        },
        "afk_arena": {
            "name": "AFK Arena",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/afk-arena/codes/"
        },
        "nikke": {
            "name": "Goddess of Victory: Nikke",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/goddess-of-victory-nikke/codes/"
        },
        "arknights": {
            "name": "Arknights",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/arknights/codes/"
        },
        "epic_seven": {
            "name": "Epic Seven",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/epic-seven/codes/"
        },
        "fate_grand_order": {
            "name": "Fate/Grand Order",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/fate-grand-order/codes/"
        },
        "blue_archive": {
            "name": "Blue Archive",
            "category": "Gacha",
            "url": "https://www.pocketgamer.com/blue-archive/codes/"
        },

        # --- Battle Royale & Action ---
        "pubg_mobile": {
            "name": "PUBG Mobile",
            "category": "Battle Royale",
            "url": "https://www.pocketgamer.com/pubg-mobile/codes/"
        },
        "codm": {
            "name": "Call of Duty: Mobile",
            "category": "Battle Royale",
            "url": "https://www.pocketgamer.com/call-of-duty-mobile/codes/"
        },
        "free_fire": {
            "name": "Garena Free Fire",
            "category": "Battle Royale",
            "url": "https://www.pocketgamer.com/garena-free-fire/codes/"
        },
        "dead_by_daylight": {
            "name": "Dead by Daylight",
            "category": "Battle Royale",
            "url": "https://progameguides.com/dead-by-daylight/dead-by-daylight-codes/"
        },

        # --- Roblox Games ---
        "roblox_blox_fruits": {
            "name": "Roblox: Blox Fruits",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/roblox-blox-fruits-codes/"
        },
        "roblox_anime_defenders": {
            "name": "Roblox: Anime Defenders",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/anime-defenders-codes/"
        },
        "roblox_pet_simulator_99": {
            "name": "Roblox: Pet Simulator 99",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/pet-simulator-99-codes/"
        },
        "roblox_blade_ball": {
            "name": "Roblox: Blade Ball",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/blade-ball-codes/"
        },
        "roblox_all_star_tower": {
            "name": "Roblox: All Star Tower Defense",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/roblox-all-star-tower-defense-codes/"
        },
        "roblox_bedwars": {
            "name": "Roblox: BedWars",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/roblox-bedwars-codes/"
        },
        "roblox_evomon": {
            "name": "Roblox: Evomon",
            "category": "Roblox",
            "url": "https://progameguides.com/roblox/evomon-codes/"
        },
        "pokemon_go": {
            "name": "Pokémon GO",
            "category": "Mobile",
            "url": "https://www.pocketgamer.com/pokemon-go/promo-codes/"
        },

        # --- Strategy Games ---
        "whiteout_survival": {
            "name": "Whiteout Survival",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/whiteout-survival/codes/"
        },
        "state_of_survival": {
            "name": "State of Survival",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/state-of-survival/codes/"
        },
        "rise_of_kingdoms": {
            "name": "Rise of Kingdoms",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/rise-of-kingdoms/codes/"
        },
        "raid_shadow_legends": {
            "name": "Raid: Shadow Legends",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/raid-shadow-legends/promo-codes/"
        },
        "lords_mobile": {
            "name": "Lords Mobile",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/lords-mobile/codes/"
        },
        "clash_of_clans": {
            "name": "Clash of Clans",
            "category": "Strategy",
            "url": "https://www.pocketgamer.com/clash-of-clans/codes/"
        },

        # --- Sports & Arcade ---
        "ea_sports_fc": {
            "name": "EA Sports FC Mobile",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/ea-sports-fc-mobile/redeem-codes/"
        },
        "nba_2k": {
            "name": "NBA 2K Mobile",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/nba-2k-mobile/locker-codes/"
        },
        "rocket_league": {
            "name": "Rocket League Sideswipe",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/rocket-league-sideswipe/codes/"
        },
        "mlbb": {
            "name": "Mobile Legends: Bang Bang",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/mobile-legends-bang-bang/codes/"
        },
        "brawl_stars": {
            "name": "Brawl Stars",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/brawl-stars/voucher-codes/"
        },
        "clash_royale": {
            "name": "Clash Royale",
            "category": "Sports",
            "url": "https://www.pocketgamer.com/clash-royale/codes/"
        }
    }

    final_games_output = {}

    for game_id, config in GAMES_CONFIG.items():
        print(f"Processing ({config['name']})...")
        
        # جلب الأكواد الجديدة
        fresh_codes = fetch_game_codes(config["url"])
        
        # استخراج الأكواد القديمة
        old_game_data = existing_games_db.get(game_id, {})
        old_codes = old_game_data.get("free_codes", []) + old_game_data.get("vip_codes", [])
        old_codes = [c for c in old_codes if c not in FORBIDDEN_WORDS]

        # شرط المقارنة والاستبدال المستقل لكل لعبة
        if fresh_codes and set(fresh_codes) != set(old_codes):
            print(f"  -> SUCCESS: Found {len(fresh_codes)} NEW codes. Updating {config['name']}.")
            selected_codes = fresh_codes
        elif old_codes:
            print(f"  -> NO CHANGE: Retaining {len(old_codes)} existing codes for {config['name']}.")
            selected_codes = old_codes
        else:
            print(f"  -> FALLBACK: Assigning default promo code for {config['name']}.")
            selected_codes = ["WELCOME_PROMO_2026"]

        # توزيع الأكواد مجاني / VIP
        free_codes = selected_codes[:3]
        vip_codes = selected_codes[3:] if len(selected_codes) > 3 else ["VIP_LOCKED_CODE"]

        final_games_output[game_id] = {
            "name": config["name"],
            "category": config["category"],
            "codes_count": len(selected_codes),
            "free_codes": free_codes,
            "vip_codes": vip_codes
        }

        # تأخير زمني عشوائي (2 إلى 4 ثوانٍ) لمنع حظر البوتات
        time.sleep(random.uniform(2.0, 4.0))

    # 3. حفظ البيانات المحدثة
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "games": final_games_output
    }

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n[COMPLETE] All 38 games processed independently and file saved successfully!")

if __name__ == "__main__":
    main()

