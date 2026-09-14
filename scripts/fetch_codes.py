import asyncio
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import requests

# فحص توفر مكتبة genshin
try:
    import genshin

    GENSHIN_LIB_AVAILABLE = True
except ImportError:
    GENSHIN_LIB_AVAILABLE = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.62 Mobile/15E148 Safari/604.1",
]

EXPIRED_AND_NOISE_KEYWORDS = {
    "EXPIRED",
    "EXPIREDCODES",
    "CODES",
    "CODE",
    "WIKI",
    "WORKING",
    "REDEEM",
    "ROBLOX",
    "DISCORD",
    "UPDATE",
    "TWITTER",
    "YOUTUBE",
    "SUB",
    "FREE",
    "NONE",
    "HTTP",
    "HTTPS",
}

# قائمة الـ 38 لعبة بالروابط المحدثة المخصصة لمنع مشكلات التوجيه (&redirects=1)
GAMES_CONFIG = {
    # 1. ألعاب Gacha و RPG
    "genshin_impact": {
        "title": "Genshin Impact",
        "category": "Gacha",
        "fandom_url": "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&redirects=1&format=json",
        "use_genshin_lib": True,
    },
    "honkai_star_rail": {
        "title": "Honkai: Star Rail",
        "category": "Gacha",
        "fandom_url": "https://honkai-star-rail.fandom.com/api.php?action=parse&page=Redemption_Code&redirects=1&format=json",
        "use_genshin_lib": True,
    },
    "zenless_zone_zero": {
        "title": "Zenless Zone Zero",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/ZenlessZoneZero/new.json?limit=10",
    },
    "wuthering_waves": {
        "title": "Wuthering Waves",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/WutheringWaves/new.json?limit=10",
    },
    "solo_leveling_arise": {
        "title": "Solo Leveling: Arise",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/SoloLevelingArise/new.json?limit=10",
    },
    "tower_of_fantasy": {
        "title": "Tower of Fantasy",
        "category": "Gacha",
        "fandom_url": "https://toweroffantasy.fandom.com/api.php?action=parse&page=Codes&redirects=1&format=json",
    },
    "dislyte": {
        "title": "Dislyte",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/Dislyte/new.json?limit=10",
    },
    "cookie_run_kingdom": {
        "title": "Cookie Run: Kingdom",
        "category": "Gacha",
        "fandom_url": "https://cookierunkingdom.fandom.com/api.php?action=parse&page=Codes&redirects=1&format=json",
    },
    "afk_arena": {
        "title": "AFK Arena",
        "category": "Gacha",
        "fandom_url": "https://afk-arena.fandom.com/api.php?action=parse&page=Redemption_Codes&redirects=1&format=json",
    },
    "nikke": {
        "title": "Goddess of Victory: Nikke",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/NikkeMobile/new.json?limit=10",
    },
    "arknights": {
        "title": "Arknights",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/arknights/new.json?limit=10",
    },
    "epic_seven": {
        "title": "Epic Seven",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/EpicSeven/new.json?limit=10",
    },
    "fate_grand_order": {
        "title": "Fate/Grand Order",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/grandorder/new.json?limit=10",
    },
    "blue_archive": {
        "title": "Blue Archive",
        "category": "Gacha",
        "reddit_url": "https://www.reddit.com/r/BlueArchive/new.json?limit=10",
    },
    # 2. ألعاب الباتل رويال والشوتر
    "pubg_mobile": {
        "title": "PUBG Mobile",
        "category": "Battle Royale",
        "reddit_url": "https://www.reddit.com/r/PUBGMobile/new.json?limit=10",
    },
    "codm": {
        "title": "Call of Duty: Mobile",
        "category": "Battle Royale",
        "reddit_url": "https://www.reddit.com/r/CallOfDutyMobile/new.json?limit=10",
    },
    "free_fire": {
        "title": "Garena Free Fire",
        "category": "Battle Royale",
        "reddit_url": "https://www.reddit.com/r/freefire/new.json?limit=10",
    },
    "dead_by_daylight": {
        "title": "Dead by Daylight",
        "category": "Battle Royale",
        "fandom_url": "https://deadbydaylight.fandom.com/api.php?action=parse&page=Codes&redirects=1&format=json",
    },
    # 3. المنصات وألعاب Roblox
    "roblox_blox_fruits": {
        "title": "Roblox: Blox Fruits",
        "category": "Roblox",
        "fandom_url": "https://blox-fruits.fandom.com/api.php?action=parse&page=Codes&redirects=1&format=json",
    },
    "roblox_anime_defenders": {
        "title": "Roblox: Anime Defenders",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/AnimeDefenders/new.json?limit=10",
    },
    "roblox_pet_simulator_99": {
        "title": "Roblox: Pet Simulator 99",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/PetSimulator99/new.json?limit=10",
    },
    "roblox_blade_ball": {
        "title": "Roblox: Blade Ball",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/BladeBall/new.json?limit=10",
    },
    "roblox_all_star_tower": {
        "title": "Roblox: All Star Tower Defense",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/allstartowerdefense/new.json?limit=10",
    },
    "roblox_bedwars": {
        "title": "Roblox: BedWars",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/robloxbedwars/new.json?limit=10",
    },
    "roblox_evomon": {
        "title": "Roblox: Evomon",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/roblox/new.json?limit=10",
    },
    "pokemon_go": {
        "title": "Pokémon GO",
        "category": "Roblox",
        "reddit_url": "https://www.reddit.com/r/TheSilphRoad/new.json?limit=10",
    },
    # 4. الألعاب الاستراتيجية والموارد
    "whiteout_survival": {
        "title": "Whiteout Survival",
        "category": "Strategy",
        "reddit_url": "https://www.reddit.com/r/whiteoutsurvival/new.json?limit=10",
    },
    "state_of_survival": {
        "title": "State of Survival",
        "category": "Strategy",
        "reddit_url": "https://www.reddit.com/r/State_of_Survival/new.json?limit=10",
    },
    "rise_of_kingdoms": {
        "title": "Rise of Kingdoms",
        "category": "Strategy",
        "reddit_url": "https://www.reddit.com/r/RiseofKingdoms/new.json?limit=10",
    },
    "raid_shadow_legends": {
        "title": "Raid: Shadow Legends",
        "category": "Strategy",
        "fandom_url": "https://raidshadowlegends.fandom.com/api.php?action=parse&page=Promo_Codes&redirects=1&format=json",
    },
    "lords_mobile": {
        "title": "Lords Mobile",
        "category": "Strategy",
        "reddit_url": "https://www.reddit.com/r/lordsmobile/new.json?limit=10",
    },
    "clash_of_clans": {
        "title": "Clash of Clans",
        "category": "Strategy",
        "reddit_url": "https://www.reddit.com/r/ClashOfClans/new.json?limit=10",
    },
    # 5. ألعاب الرياضة والتنافس السريع
    "ea_sports_fc": {
        "title": "EA Sports FC Mobile",
        "category": "Sports",
        "reddit_url": "https://www.reddit.com/r/FCMobile/new.json?limit=10",
    },
    "nba_2k": {
        "title": "NBA 2K Mobile",
        "category": "Sports",
        "reddit_url": "https://www.reddit.com/r/NBA2KMobile/new.json?limit=10",
    },
    "rocket_league": {
        "title": "Rocket League Sideswipe",
        "category": "Sports",
        "reddit_url": "https://www.reddit.com/r/RLSideswipe/new.json?limit=10",
    },
    "mlbb": {
        "title": "Mobile Legends: Bang Bang",
        "category": "Sports",
        "reddit_url": "https://www.reddit.com/r/MobileLegendsGame/new.json?limit=10",
    },
    "brawl_stars": {
        "title": "Brawl Stars",
        "category": "Sports",
        "fandom_url": "https://brawlstars.fandom.com/api.php?action=parse&page=Vouchers&redirects=1&format=json",
    },
    "clash_royale": {
        "title": "Clash Royale",
        "category": "Sports",
        "reddit_url": "https://www.reddit.com/r/ClashRoyale/new.json?limit=10",
    },
}


def get_human_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def clean_and_filter_codes(codes):
    """تنظيف وتصفية الأكواد لحذف الضوضاء والأكواد المنتهية"""
    cleaned = []
    seen = set()

    for code in codes:
        code_str = str(code).strip().upper()

        if code_str in seen or len(code_str) < 4 or len(code_str) > 25:
            continue

        if any(noise in code_str for noise in EXPIRED_AND_NOISE_KEYWORDS):
            continue

        if re.match(r"^[A-Z0-9_\-]+$", code_str):
            seen.add(code_str)
            cleaned.append(code_str)

    return cleaned


def fetch_from_fandom(url):
    try:
        res = requests.get(url, headers=get_human_headers(), timeout=10)
        if res.status_code == 200:
            data = res.json()
            html_content = data.get("parse", {}).get("text", {}).get("*", "")
            soup = BeautifulSoup(html_content, "html.parser")

            extracted = []
            for tag in soup.find_all(["code", "b", "strong", "td"]):
                text = tag.text.strip()
                if re.match(r"^[A-Za-z0-9_\-]{4,20}$", text):
                    extracted.append(text)
            return extracted
    except Exception as e:
        print(f"Fandom Fetch Error ({url}): {e}")
    return []


def fetch_from_reddit(url):
    try:
        res = requests.get(url, headers=get_human_headers(), timeout=10)
        if res.status_code == 200:
            data = res.json()
            posts = data.get("data", {}).get("children", [])
            extracted = []
            for post in posts:
                title = post.get("data", {}).get("title", "")
                selftext = post.get("data", {}).get("selftext", "")
                full_text = f"{title} {selftext}"

                found = re.findall(r"\b[A-Z0-9]{5,20}\b", full_text)
                extracted.extend(found)
            return extracted
    except Exception as e:
        print(f"Reddit Fetch Error ({url}): {e}")
    return []


async def fetch_hoyoverse_official():
    codes = []
    if GENSHIN_LIB_AVAILABLE:
        try:
            client = genshin.Client()
            fetched_codes = await client.get_genshin_codes()
            codes = [c.code for c in fetched_codes]
        except Exception as e:
            print(f"genshin.py error: {e}")
    return codes


def load_existing_db(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"games": {}}


def main():
    db_path = "data/codes.json"
    existing_db = load_existing_db(db_path)

    new_database = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "games": {},
    }

    for game_id, config in GAMES_CONFIG.items():
        print(f"Processing: {config['title']}...")
        fetched_codes = []

        # 1. الاستعانة بـ genshin.py للألعاب المدعومة
        if config.get("use_genshin_lib") and GENSHIN_LIB_AVAILABLE:
            fetched_codes = asyncio.run(fetch_hoyoverse_official())

        # 2. Fandom API
        if not fetched_codes and "fandom_url" in config:
            fetched_codes = fetch_from_fandom(config["fandom_url"])

        # 3. Reddit JSON
        if not fetched_codes and "reddit_url" in config:
            fetched_codes = fetch_from_reddit(config["reddit_url"])

        cleaned_codes = clean_and_filter_codes(fetched_codes)

        # استرجاع الأكواد القديمة للحفاظ عليها في حال عدم التحديث
        old_game_data = existing_db.get("games", {}).get(game_id, {})
        old_codes = old_game_data.get("free_codes", []) + old_game_data.get(
            "vip_codes", []
        )
        old_codes = [c for c in old_codes if c != "VIP_LOCKED_CODE"]

        if cleaned_codes:
            final_codes = cleaned_codes
            print(f"  -> Found {len(final_codes)} fresh codes.")
        elif old_codes:
            final_codes = old_codes
            print(f"  -> Retained {len(final_codes)} existing codes.")
        else:
            final_codes = ["WELCOME_PROMO_2026"]
            print("  -> Assigned default promo code.")

        free_codes = final_codes[:3]
        vip_codes = final_codes[3:] if len(final_codes) > 3 else ["VIP_LOCKED_CODE"]

        new_database["games"][game_id] = {
            "name": config["title"],
            "category": config["category"],
            "codes_count": len(final_codes),
            "free_codes": free_codes,
            "vip_codes": vip_codes,
        }

        # تأخير زمني لتفادي الحظر
        time.sleep(random.uniform(1.5, 3.0))

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(new_database, f, ensure_ascii=False, indent=2)

    print("\n[SUCCESS] data/codes.json has been updated smoothly!")


if __name__ == "__main__":
    main()

