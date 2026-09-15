import json
import os
import random
import re
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
]

# قائمة تنقية صارمة لمنع إدخال الكلمات الإدارية ورؤوس الجداول
FORBIDDEN_WORDS = {
    "EXPIRED", "WORKING", "CODES", "CODE", "REDEEM", "ROBLOX", "UPDATE", "FREE", 
    "NONE", "OVERVIEW", "DETAILS", "REWARD", "REWARDS", "CHINA", "ASIA", "GLOBAL", 
    "AMERICA", "EUROPE", "SERVER", "STATUS", "DESCRIPTION", "NOTES", "ACTIVE", 
    "INACTIVE", "VERIFIED", "WELCOME_PROMO_2026", "VIP_LOCKED_CODE", "ITEM", "ITEMS",
    "CLICK", "HERE", "MORE", "DISCORD", "TWITTER", "YOUTUBE", "FACEBOOK", "TOGGLE"
}

def clean_code(text):
    """تنظيف النص والتأكد من مطابقته للنمط الحقيقي للأكواد"""
    code = text.strip().upper()
    if len(code) < 4 or len(code) > 25:
        return None
    if code in FORBIDDEN_WORDS or any(w in code for w in ["HTTP", "WWW", "WIKI", ".COM"]):
        return None
    if re.match(r"^[A-Z0-9_\-]+$", code):
        return code
    return None

def get_browser_headers():
    """محاكاة هيدرز متصفح بشري حديث لتخطي أنظمة الحظر"""
    agent = random.choice(USER_AGENTS)
    return {
        "User-Agent": agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def fetch_game_codes(url):
    """جلب الأكواد وتصليحها واستخراجها بدون تكرار"""
    try:
        res = requests.get(url, headers=get_browser_headers(), timeout=15)
        if res.status_code == 200:
            codes = []
            # دعم جلب البيانات سواء كانت من Fandom API JSON أو صفحة HTML إخبارية
            if "fandom.com/api.php" in url:
                data = res.json()
                html_text = data.get("parse", {}).get("text", {}).get("*", "")
                soup = BeautifulSoup(html_text, "html.parser")
            else:
                soup = BeautifulSoup(res.text, "html.parser")

            for tag in soup.find_all(["code", "strong", "b", "td"]):
                cleaned = clean_code(tag.text)
                if cleaned and cleaned not in codes:
                    codes.append(cleaned)
            return codes
    except Exception as e:
        print(f"  [Fetch Error] {url}: {e}")
    return []

def main():
    db_path = "data/codes.json"
    
    # 1. قراءة قاعدة البيانات الحالية للحصول على الأكواد المخزنة سابقاً
    existing_db = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                existing_db = json.load(f).get("games", {})
        except Exception as e:
            print(f"Warning: Failed to read existing DB: {e}")

    # 2. القائمة الكاملة لـ 38 لعبة بأدق مصادر الجلب المباشرة
    GAMES_CONFIG = {
        # --- Gacha & RPG (14) ---
        "genshin_impact": {
            "name": "Genshin Impact",
            "category": "Gacha",
            "url": "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&redirects=1&format=json"
        },
        "honkai_star_rail": {
            "name": "Honkai: Star Rail",
            "category": "Gacha",
            "url": "https://honkai-star-rail.fandom.com/api.php?action=parse&page=Redemption_Code&redirects=1&format=json"
        },
        "zenless_zone_zero": {
            "name": "Zenless Zone Zero",
            "category": "Gacha",
            "url": "https://zenless-zone-zero.fandom.com/api.php?action=parse&page=Redemption_Code&redirects=1&format=json"
        },
        "wuthering_waves": {
            "name": "Wuthering Waves",
            "category": "Gacha",
            "url": "https://wutheringwaves.fandom.com/api.php?action=parse&page=Redemption_Codes&redirects=1&format=json"
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

        # --- Battle Royale & Action (4) ---
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

        # --- Roblox & Mobile Games (8) ---
        "roblox_blox_fruits": {
            "name": "Roblox: Blox Fruits",
            "category": "Roblox",
            "url": "https://blox-fruits.fandom.com/api.php?action=parse&page=Codes&redirects=1&format=json"
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

        # --- Strategy Games (6) ---
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

        # --- Sports & Arcade (6) ---
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

    final_output = {}

    for game_id, config in GAMES_CONFIG.items():
        print(f"Checking updates for: {config['name']}...")
        
        # جلب الأكواد الجديدة المسحوبة
        fresh_codes = fetch_game_codes(config["url"])
        
        # استخراج الأكواد القديمة المعتمدة لهذه اللعبة تحديداً
        old_game_data = existing_db.get(game_id, {})
        old_codes = old_game_data.get("free_codes", []) + old_game_data.get("vip_codes", [])
        old_codes = [c for c in old_codes if c not in FORBIDDEN_WORDS]

        # 3. شرط الفحص والمقارنة المستقل لكل لعبة:
        if fresh_codes and set(fresh_codes) != set(old_codes):
            # حالة 1: وُجدت أكواد جديدة ومختلفة -> حذف القديم واستبداله بالجديد كلياً
            print(f"  -> NEW CODES FOUND ({len(fresh_codes)}). Replacing old codes for {config['name']}.")
            selected_codes = fresh_codes
        elif old_codes:
            # حالة 2: لم تُوجد أكواد جديدة أو تعثر الجلب -> الإبقاء على الأكواد القديمة دون أي تغيير
            print(f"  -> NO NEW CODES. Retaining {len(old_codes)} existing codes for {config['name']}.")
            selected_codes = old_codes
        else:
            # حالة 3: لعبة جديدة تماماً وليس لها سجل سابق
            selected_codes = ["WELCOME_PROMO_2026"]

        # توزيع الأكواد كاملة دون تقليص للعدد المجلوب (أول 3 مجانية والباقي VIP)
        free_codes = selected_codes[:3]
        vip_codes = selected_codes[3:] if len(selected_codes) > 3 else []

        final_output[game_id] = {
            "name": config["name"],
            "category": config["category"],
            "codes_count": len(selected_codes),
            "free_codes": free_codes,
            "vip_codes": vip_codes
        }

        # تأخير زمني لتفادي الحظر
        time.sleep(random.uniform(1.5, 3.0))

    # 4. حفظ النتيجة النهائية في data/codes.json
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "games": final_output
    }

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n[SUCCESS] Independent verification completed for all 38 games!")

if __name__ == "__main__":
    main()

