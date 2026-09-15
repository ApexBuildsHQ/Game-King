import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime, timezone

# قائمة الكلمات المحظورة لاستبعاد أي عناصر HTML أو وسم ويكي قد يشبه الكود
BLACKLIST = {
    "CLASS", "LANG", "SPAN", "HREF", "TITLE", "REDIRECT", "DESCRIPTION", 
    "PROMOTIONAL", "OFFICIAL", "EXPIRED", "ACTIVE", "UNKNOWN", "SERVER",
    "GLOBAL", "INDEFINITE", "REDEEMED", "SETTINGS", "DISCOVERED", "ITEM",
    "HTTP", "HTTPS", "WIKI", "FANDOM", "SRC", "ALT", "STYLE", "WIDTH", "HEIGHT"
}

# نمط التحقق: أكواد تتكون من حروف وأرقام (ومشرطة اختياريًا) بطول بين 5 و 25
CODE_REGEX = re.compile(r'^[A-Za-z0-9\-]{5,25}$')

def is_valid_code(code_str):
    code = code_str.strip().strip(':-_')
    if not CODE_REGEX.match(code):
        return False
    if code.upper() in BLACKLIST:
        return False
    if code.isdigit(): # استبعاد الأرقام الخالصة
        return False
    return True

def scrape_fandom_codes(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    valid_codes = set()

    # 1. جلب النصوص داخل وسوم <code> و <pre>
    for code_elem in soup.find_all(['code', 'pre']):
        text = code_elem.get_text().strip()
        if is_valid_code(text):
            valid_codes.add(text)

    # 2. جلب النصوص من الخلية الأولى في جداول الأكواد النشطة
    tables = soup.find_all('table', class_=['sortable', 'article-table', 'wikitable'])
    for table in tables:
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells:
                raw_cell = cells[0].get_text().strip()
                # اقتطاع أول كلمة في حال وجود ملاحظات داخل نفس الخلية
                clean_word = raw_cell.split()[0] if raw_cell.split() else ""
                if is_valid_code(clean_word):
                    valid_codes.add(clean_word)

    return list(valid_codes)

# قاعدة بيانات الـ 38 لعبة مع المصادر الموثوقة
SOURCES = {
    # --- Gacha & Anime RPGs ---
    "genshin_impact": {"name": "Genshin Impact", "category": "Gacha", "url": "https://genshin-impact.fandom.com/wiki/Promotional_Code"},
    "honkai_star_rail": {"name": "Honkai: Star Rail", "category": "Gacha", "url": "https://honkai-star-rail.fandom.com/wiki/Redemption_Code"},
    "zenless_zone_zero": {"name": "Zenless Zone Zero", "category": "Gacha", "url": "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"},
    "wuthering_waves": {"name": "Wuthering Waves", "category": "Gacha", "url": "https://wutheringwaves.fandom.com/wiki/Redemption_Code"},
    "solo_leveling_arise": {"name": "Solo Leveling: Arise", "category": "Action RPG", "url": "https://sololeveling.fandom.com/wiki/Redemption_Codes"},
    "honkai_impact_3rd": {"name": "Honkai Impact 3rd", "category": "Gacha", "url": "https://honkaiimpact3.fandom.com/wiki/Exchange_Codes"},
    "blue_archive": {"name": "Blue Archive", "category": "Gacha", "url": "https://bluearchive.fandom.com/wiki/Coupon_Codes"},
    "nikke": {"name": "Goddess of Victory: Nikke", "category": "Gacha", "url": "https://nikke-goddess-of-victory-nikke.fandom.com/wiki/Redemption_Codes"},
    "reverse_1999": {"name": "Reverse: 1999", "category": "Gacha", "url": "https://reverse1999.fandom.com/wiki/Redemption_Codes"},
    "outerplane": {"name": "Outerplane", "category": "Gacha", "url": "https://outerplane.fandom.com/wiki/Coupon_Codes"},
    "black_clover_m": {"name": "Black Clover M", "category": "Gacha", "url": "https://blackcloverm.fandom.com/wiki/Redemption_Codes"},
    "arknights": {"name": "Arknights", "category": "Strategy/Gacha", "url": "https://arknights.fandom.com/wiki/Gift_Codes"},
    "epic_seven": {"name": "Epic Seven", "category": "Turn-based RPG", "url": "https://epic7.fandom.com/wiki/Coupon_Codes"},
    "dislyte": {"name": "Dislyte", "category": "Turn-based RPG", "url": "https://dislyte.fandom.com/wiki/Gift_Codes"},

    # --- Strategy & Idle Games ---
    "afk_arena": {"name": "AFK Arena", "category": "Idle RPG", "url": "https://afk-arena.fandom.com/wiki/Redemption_Codes"},
    "afk_journey": {"name": "AFK Journey", "category": "Idle RPG", "url": "https://afkjourney.fandom.com/wiki/Redemption_Codes"},
    "raid_shadow_legends": {"name": "RAID: Shadow Legends", "category": "RPG", "url": "https://raidshadowlegends.fandom.com/wiki/Promo_Codes"},
    "whiteout_survival": {"name": "Whiteout Survival", "category": "Strategy", "url": "https://whiteoutsurvival.fandom.com/wiki/Gift_Codes"},
    "last_war_survival": {"name": "Last War: Survival", "category": "Strategy", "url": "https://lastwar.fandom.com/wiki/Gift_Codes"},
    "legend_of_mushroom": {"name": "Legend of Mushroom", "category": "Idle", "url": "https://legendofmushroom.fandom.com/wiki/Redemption_Codes"},
    "summoners_war": {"name": "Summoners War", "category": "Turn-based RPG", "url": "https://summonerswar.fandom.com/wiki/Coupon_Codes"},
    "tower_of_fantasy": {"name": "Tower of Fantasy", "category": "MMORPG", "url": "https://toweroffantasy.fandom.com/wiki/Redemption_Codes"},
    "cookie_run_kingdom": {"name": "Cookie Run: Kingdom", "category": "RPG/Base Building", "url": "https://cookierunkingdom.fandom.com/wiki/Coupon_Codes"},

    # --- Battle Royale & Multiplayer MOBAs ---
    "free_fire": {"name": "Garena Free Fire", "category": "Battle Royale", "url": "https://garena.fandom.com/wiki/Free_Fire_Redeem_Codes"},
    "pubg_mobile": {"name": "PUBG Mobile", "category": "Battle Royale", "url": "https://pubg.fandom.com/wiki/PUBG_Mobile_Redeem_Codes"},
    "mobile_legends": {"name": "Mobile Legends: Bang Bang", "category": "MOBA", "url": "https://mobile-legends.fandom.com/wiki/Redeem_Code"},
    "brawl_stars": {"name": "Brawl Stars", "category": "Action/MOBA", "url": "https://brawlstars.fandom.com/wiki/Voucher_Codes"},
    "clash_royale": {"name": "Clash Royale", "category": "Strategy", "url": "https://clashroyale.fandom.com/wiki/Voucher_Codes"},
    "pokemon_go": {"name": "Pokémon GO", "category": "AR / Mobile", "url": "https://pokemongo.fandom.com/wiki/Promo_Codes"},
    "monster_hunter_now": {"name": "Monster Hunter Now", "category": "AR / Action", "url": "https://monsterhunter.fandom.com/wiki/MHN_Promo_Codes"},
    "dead_by_daylight": {"name": "Dead by Daylight", "category": "Asymmetrical Horror", "url": "https://deadbydaylight.fandom.com/wiki/Promo_Codes"},
    "coin_master": {"name": "Coin Master", "category": "Casual", "url": "https://coin-master.fandom.com/wiki/Free_Spins"},

    # --- Roblox Popular Experiences ---
    "roblox_blox_fruits": {"name": "Roblox: Blox Fruits", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/Blox_Fruits_Codes"},
    "roblox_astd": {"name": "Roblox: All Star Tower Defense", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/ASTD_Codes"},
    "roblox_pet_sim_99": {"name": "Roblox: Pet Simulator 99", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/Pet_Simulator_99_Codes"},
    "roblox_blade_ball": {"name": "Roblox: Blade Ball", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/Blade_Ball_Codes"},
    "roblox_king_legacy": {"name": "Roblox: King Legacy", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/King_Legacy_Codes"},
    "roblox_anime_adventures": {"name": "Roblox: Anime Adventures", "category": "Roblox", "url": "https://roblox.fandom.com/wiki/Anime_Adventures_Codes"}
}

def main():
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(SOURCES),
        "games": {}
    }

    print(f"Starting extraction for {len(SOURCES)} games...\n")

    for game_id, info in SOURCES.items():
        print(f"Scraping [{info['name']}]...")
        codes = scrape_fandom_codes(info["url"])
        
        output_data["games"][game_id] = {
            "name": info["name"],
            "category": info["category"],
            "source_url": info["url"],
            "codes_count": len(codes),
            "free_codes": codes
        }
        
        # التأخير لمدة ثانية واحدة لمنع السيرفر من حجب الطلبات أثناء التجميع
        time.sleep(1)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\nExtraction completed successfully! Check codes.json")

if __name__ == "__main__":
    main()

