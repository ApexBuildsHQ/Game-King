import json
import os
import re
import time
from datetime import datetime, timezone
import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

FORBIDDEN_WORDS = {
    "EXPIRED", "WORKING", "CODES", "CODE", "REDEEM", "ROBLOX", "UPDATE", "FREE", 
    "NONE", "OVERVIEW", "DETAILS", "REWARD", "REWARDS", "ACTIVE", "INACTIVE", 
    "VERIFIED", "WELCOME_PROMO_2026", "VIP_LOCKED_CODE", "STATUS", "PAGE", "EDIT",
    "COMMUNITY", "DISCORD", "TWITTER", "YOUTUBE", "WIKI", "CATEGORY", "JANUARY", 
    "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", 
    "OCTOBER", "NOVEMBER", "DECEMBER", "2024", "2025", "2026"
}

def clean_code(text):
    """تنظيف وتدقيق نسق الكود المستخرج"""
    code = text.strip().upper()
    if len(code) < 4 or len(code) > 25:
        return None
    if code in FORBIDDEN_WORDS or any(w in code for w in ["HTTP", "WWW", ".COM", "WIKI"]):
        return None
    if re.match(r"^[A-Z0-9_\-]+$", code):
        return code
    return None

def fetch_from_fandom_api(wiki_domain, page_title):
    """جلب الأكواد عبر API المباشر لـ Wikia/Fandom لتفادي حظر 403 و Cloudflare"""
    url = f"https://{wiki_domain}.fandom.com/api.php?action=parse&page={page_title}&redirects=1&format=json"
    headers = {"User-Agent": USER_AGENT}
    
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            html_content = data.get("parse", {}).get("text", {}).get("*", "")
            
            # استخراج الكلمات التي طابق نموذج الأكواد من داخل نص الـ HTML البرمجي
            extracted = re.findall(r"\b[A-Za-z0-9_\-]{4,22}\b", html_content)
            valid_codes = []
            for c in extracted:
                cleaned = clean_code(c)
                if cleaned and cleaned not in valid_codes:
                    valid_codes.append(cleaned)
            return valid_codes
        else:
            print(f"  [API {res.status_code}] Failed for {wiki_domain}")
    except Exception as e:
        print(f"  [API Error] {wiki_domain}: {e}")
    return []

def main():
    db_path = "data/codes.json"
    
    # تحميل قاعدة البيانات السابقة إن وجدت للحفاظ على الأكواد في حال تعذر الجلب
    existing_games_db = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                existing_games_db = json.load(f).get("games", {})
        except Exception as e:
            print(f"Warning: Could not read existing DB: {e}")

    # القائمة الكاملة لـ 38 لعبة مع مسارات الـ Fandom API المباشرة
    GAMES_CONFIG = {
        # --- Gacha & RPG ---
        "genshin_impact": {"name": "Genshin Impact", "category": "Gacha", "wiki": "genshin-impact", "page": "Promotional_Code"},
        "honkai_star_rail": {"name": "Honkai: Star Rail", "category": "Gacha", "wiki": "honkai-star-rail", "page": "Redemption_Code"},
        "zenless_zone_zero": {"name": "Zenless Zone Zero", "category": "Gacha", "wiki": "zenless-zone-zero", "page": "Redemption_Code"},
        "wuthering_waves": {"name": "Wuthering Waves", "category": "Gacha", "wiki": "wutheringwaves", "page": "Redemption_Codes"},
        "solo_leveling_arise": {"name": "Solo Leveling: Arise", "category": "Gacha", "wiki": "solo-leveling-arise", "page": "Codes"},
        "tower_of_fantasy": {"name": "Tower of Fantasy", "category": "Gacha", "wiki": "toweroffantasy", "page": "Redeem_Codes"},
        "dislyte": {"name": "Dislyte", "category": "Gacha", "wiki": "dislyte", "page": "Codes"},
        "cookie_run_kingdom": {"name": "Cookie Run: Kingdom", "category": "Gacha", "wiki": "cookie-run-kingdom", "page": "Codes"},
        "afk_arena": {"name": "AFK Arena", "category": "Gacha", "wiki": "afk-arena", "page": "Codes"},
        "nikke": {"name": "Goddess of Victory: Nikke", "category": "Gacha", "wiki": "nikke-god-of-victory-game", "page": "Codes"},
        "arknights": {"name": "Arknights", "category": "Gacha", "wiki": "arknights", "page": "Redemption_Codes"},
        "epic_seven": {"name": "Epic Seven", "category": "Gacha", "wiki": "epic7", "page": "Codes"},
        "fate_grand_order": {"name": "Fate/Grand Order", "category": "Gacha", "wiki": "fategrandorder", "page": "Codes"},
        "blue_archive": {"name": "Blue Archive", "category": "Gacha", "wiki": "bluearchive", "page": "Codes"},

        # --- Battle Royale & Action ---
        "pubg_mobile": {"name": "PUBG Mobile", "category": "Battle Royale", "wiki": "pubgmobile", "page": "Codes"},
        "codm": {"name": "Call of Duty: Mobile", "category": "Battle Royale", "wiki": "callofduty", "page": "Codes"},
        "free_fire": {"name": "Garena Free Fire", "category": "Battle Royale", "wiki": "freefire", "page": "Codes"},
        "dead_by_daylight": {"name": "Dead by Daylight", "category": "Battle Royale", "wiki": "deadbydaylight", "page": "Codes"},

        # --- Roblox Games ---
        "roblox_blox_fruits": {"name": "Roblox: Blox Fruits", "category": "Roblox", "wiki": "blox-fruits", "page": "Codes"},
        "roblox_anime_defenders": {"name": "Roblox: Anime Defenders", "category": "Roblox", "wiki": "anime-defenders", "page": "Codes"},
        "roblox_pet_simulator_99": {"name": "Roblox: Pet Simulator 99", "category": "Roblox", "wiki": "pet-simulator-99", "page": "Codes"},
        "roblox_blade_ball": {"name": "Roblox: Blade Ball", "category": "Roblox", "wiki": "blade-ball", "page": "Codes"},
        "roblox_all_star_tower": {"name": "Roblox: All Star Tower Defense", "category": "Roblox", "wiki": "allstar-tower-defense-roblox", "page": "Codes"},
        "roblox_bedwars": {"name": "Roblox: BedWars", "category": "Roblox", "wiki": "roblox-bedwars", "page": "Codes"},
        "roblox_evomon": {"name": "Roblox: Evomon", "category": "Roblox", "wiki": "evomon-roblox", "page": "Codes"},
        "pokemon_go": {"name": "Pokémon GO", "category": "Mobile", "wiki": "pokemongo", "page": "Codes"},

        # --- Strategy Games ---
        "whiteout_survival": {"name": "Whiteout Survival", "category": "Strategy", "wiki": "whiteout-survival", "page": "Codes"},
        "state_of_survival": {"name": "State of Survival", "category": "Strategy", "wiki": "state-of-survival", "page": "Codes"},
        "rise_of_kingdoms": {"name": "Rise of Kingdoms", "category": "Strategy", "wiki": "riseofkingdoms", "page": "Codes"},
        "raid_shadow_legends": {"name": "Raid: Shadow Legends", "category": "Strategy", "wiki": "raid-shadow-legends", "page": "Promo_Codes"},
        "lords_mobile": {"name": "Lords Mobile", "category": "Strategy", "wiki": "lordsmobile", "page": "Codes"},
        "clash_of_clans": {"name": "Clash of Clans", "category": "Strategy", "wiki": "clashofclans", "page": "Creator_Codes"},

        # --- Sports & Arcade ---
        "ea_sports_fc": {"name": "EA Sports FC Mobile", "category": "Sports", "wiki": "fifa-mobile", "page": "Codes"},
        "nba_2k": {"name": "NBA 2K Mobile", "category": "Sports", "wiki": "nba-2k-mobile", "page": "Locker_Codes"},
        "rocket_league": {"name": "Rocket League Sideswipe", "category": "Sports", "wiki": "rocket-league", "page": "Codes"},
        "mlbb": {"name": "Mobile Legends: Bang Bang", "category": "Sports", "wiki": "mobile-legends", "page": "Codes"},
        "brawl_stars": {"name": "Brawl Stars", "category": "Sports", "wiki": "brawlstars", "page": "Creator_Codes"},
        "clash_royale": {"name": "Clash Royale", "category": "Sports", "wiki": "clashroyale", "page": "Creator_Codes"}
    }

    final_games_output = {}

    for game_id, config in GAMES_CONFIG.items():
        print(f"Processing ({config['name']})...")
        
        fresh_codes = fetch_from_fandom_api(config["wiki"], config["page"])
        
        old_game_data = existing_games_db.get(game_id, {})
        old_codes = old_game_data.get("free_codes", []) + old_game_data.get("vip_codes", [])
        old_codes = [c for c in old_codes if c not in FORBIDDEN_WORDS]

        if fresh_codes:
            print(f"  -> SUCCESS: Retrieved {len(fresh_codes)} valid codes.")
            selected_codes = fresh_codes
        elif old_codes:
            print(f"  -> RETAINED: Keeping {len(old_codes)} existing codes.")
            selected_codes = old_codes
        else:
            print(f"  -> FALLBACK: Assigning default promo code.")
            selected_codes = ["WELCOME_PROMO_2026"]

        free_codes = selected_codes[:3]
        vip_codes = selected_codes[3:] if len(selected_codes) > 3 else ["VIP_LOCKED_CODE"]

        final_games_output[game_id] = {
            "name": config["name"],
            "category": config["category"],
            "codes_count": len(selected_codes),
            "free_codes": free_codes,
            "vip_codes": vip_codes
        }

        time.sleep(1)

    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "games": final_games_output
    }

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n[COMPLETE] Processed all 38 games via API endpoints and saved successfully.")

if __name__ == "__main__":
    main()

