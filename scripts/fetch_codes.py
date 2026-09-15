import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime, timezone

# قائمة الكلمات المحظورة لمنع التقاط عناوين الجداول
BLACKLIST = {
    "CODE", "CODES", "REDEEM", "REWARD", "REWARDS", "STATUS", "EXPIRED", 
    "NOTES", "DETAILS", "ACTIVE", "LINK", "NONE", "SERVER", "UNKNOWN",
    "DESCRIPTION", "PROMOTIONAL", "OFFICIAL", "INDEFINITE", "ITEM", "ITEMS",
    "VALUE", "DURATION", "AVAILABILITY", "TYPE"
}

def clean_code(text):
    """تنظيف الكود من الحواشي المرجعية والرموز الزائدة"""
    text = re.sub(r'\[\d+\]', '', text) # إزالة المراجع مثل [1]
    parts = text.strip().split()
    return parts[0] if parts else ""

def is_valid_code(code):
    code_clean = code.strip().strip(':-_')
    if not code_clean or len(code_clean) < 4 or len(code_clean) > 30:
        return False
    if code_clean.upper() in BLACKLIST:
        return False
    if code_clean.isdigit(): # استبعاد الأرقام الخالصة
        return False
    if any(x in code_clean.upper() for x in ["HTTP", "WWW", "WIKI", "EDIT"]):
        return False
    return True

def fetch_fandom_codes(domain, page_title):
    """جلب محتوى الصفحة مباشرة عبر MediaWiki API لتجاوز حظر البوتات"""
    api_url = f"https://{domain}.fandom.com/api.php"
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "format": "json"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(api_url, params=params, headers=headers, timeout=12)
        if res.status_code != 200:
            return []
        
        data = res.json()
        if "parse" not in data or "text" not in data["parse"]:
            return []
            
        html_content = data["parse"]["text"]["*"]
    except Exception as e:
        print(f"Error fetching API for {domain}: {e}")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    extracted_codes = set()

    # البحث داخل الجداول التي تحتوي على الأكواد
    for table in soup.find_all('table'):
        table_text = table.get_text().lower()
        # تخطي الجداول المخصصة للأكواد المنتهية الصلاحية
        if "expired" in table_text and "active" not in table_text:
            continue

        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            
            # البحث في أول خليتين لأن الكود يكون عادةً بالخلية الأولى
            for cell in cells[:2]:
                elements = cell.find_all(['code', 'b', 'strong'])
                if elements:
                    for el in elements:
                        candidate = clean_code(el.get_text())
                        if is_valid_code(candidate):
                            extracted_codes.add(candidate)
                else:
                    candidate = clean_code(cell.get_text())
                    if is_valid_code(candidate):
                        extracted_codes.add(candidate)

    return list(extracted_codes)

# قاعدة بيانات الـ 38 لعبة مع تقسيم الـ Domain والـ Page لتتوافق مع API
SOURCES = {
    "genshin_impact": {"name": "Genshin Impact", "category": "Gacha", "domain": "genshin-impact", "page": "Promotional_Code"},
    "honkai_star_rail": {"name": "Honkai: Star Rail", "category": "Gacha", "domain": "honkai-star-rail", "page": "Redemption_Code"},
    "zenless_zone_zero": {"name": "Zenless Zone Zero", "category": "Gacha", "domain": "zenless-zone-zero", "page": "Redemption_Code"},
    "wuthering_waves": {"name": "Wuthering Waves", "category": "Gacha", "domain": "wutheringwaves", "page": "Redemption_Code"},
    "solo_leveling_arise": {"name": "Solo Leveling: Arise", "category": "Action RPG", "domain": "sololeveling", "page": "Redemption_Codes"},
    "honkai_impact_3rd": {"name": "Honkai Impact 3rd", "category": "Gacha", "domain": "honkaiimpact3", "page": "Exchange_Codes"},
    "blue_archive": {"name": "Blue Archive", "category": "Gacha", "domain": "bluearchive", "page": "Coupon_Codes"},
    "nikke": {"name": "Goddess of Victory: Nikke", "category": "Gacha", "domain": "nikke-goddess-of-victory-nikke", "page": "Redemption_Codes"},
    "reverse_1999": {"name": "Reverse: 1999", "category": "Gacha", "domain": "reverse1999", "page": "Redemption_Codes"},
    "outerplane": {"name": "Outerplane", "category": "Gacha", "domain": "outerplane", "page": "Coupon_Codes"},
    "black_clover_m": {"name": "Black Clover M", "category": "Gacha", "domain": "blackcloverm", "page": "Redemption_Codes"},
    "arknights": {"name": "Arknights", "category": "Strategy/Gacha", "domain": "arknights", "page": "Gift_Codes"},
    "epic_seven": {"name": "Epic Seven", "category": "Turn-based RPG", "domain": "epic7", "page": "Coupon_Codes"},
    "dislyte": {"name": "Dislyte", "category": "Turn-based RPG", "domain": "dislyte", "page": "Gift_Codes"},
    "afk_arena": {"name": "AFK Arena", "category": "Idle RPG", "domain": "afk-arena", "page": "Redemption_Codes"},
    "afk_journey": {"name": "AFK Journey", "category": "Idle RPG", "domain": "afkjourney", "page": "Redemption_Codes"},
    "raid_shadow_legends": {"name": "RAID: Shadow Legends", "category": "RPG", "domain": "raidshadowlegends", "page": "Promo_Codes"},
    "whiteout_survival": {"name": "Whiteout Survival", "category": "Strategy", "domain": "whiteoutsurvival", "page": "Gift_Codes"},
    "last_war_survival": {"name": "Last War: Survival", "category": "Strategy", "domain": "lastwar", "page": "Gift_Codes"},
    "legend_of_mushroom": {"name": "Legend of Mushroom", "category": "Idle", "domain": "legendofmushroom", "page": "Redemption_Codes"},
    "summoners_war": {"name": "Summoners War", "category": "Turn-based RPG", "domain": "summonerswar", "page": "Coupon_Codes"},
    "tower_of_fantasy": {"name": "Tower of Fantasy", "category": "MMORPG", "domain": "toweroffantasy", "page": "Redemption_Codes"},
    "cookie_run_kingdom": {"name": "Cookie Run: Kingdom", "category": "RPG/Base Building", "domain": "cookierunkingdom", "page": "Coupon_Codes"},
    "free_fire": {"name": "Garena Free Fire", "category": "Battle Royale", "domain": "garena", "page": "Free_Fire_Redeem_Codes"},
    "pubg_mobile": {"name": "PUBG Mobile", "category": "Battle Royale", "domain": "pubg", "page": "PUBG_Mobile_Redeem_Codes"},
    "mobile_legends": {"name": "Mobile Legends: Bang Bang", "category": "MOBA", "domain": "mobile-legends", "page": "Redeem_Code"},
    "brawl_stars": {"name": "Brawl Stars", "category": "Action/MOBA", "domain": "brawlstars", "page": "Voucher_Codes"},
    "clash_royale": {"name": "Clash Royale", "category": "Strategy", "domain": "clashroyale", "page": "Voucher_Codes"},
    "pokemon_go": {"name": "Pokémon GO", "category": "AR / Mobile", "domain": "pokemongo", "page": "Promo_Codes"},
    "monster_hunter_now": {"name": "Monster Hunter Now", "category": "AR / Action", "domain": "monsterhunter", "page": "MHN_Promo_Codes"},
    "dead_by_daylight": {"name": "Dead by Daylight", "category": "Asymmetrical Horror", "domain": "deadbydaylight", "page": "Promo_Codes"},
    "coin_master": {"name": "Coin Master", "category": "Casual", "domain": "coin-master", "page": "Free_Spins"},
    "roblox_blox_fruits": {"name": "Roblox: Blox Fruits", "category": "Roblox", "domain": "roblox", "page": "Blox_Fruits_Codes"},
    "roblox_astd": {"name": "Roblox: All Star Tower Defense", "category": "Roblox", "domain": "roblox", "page": "ASTD_Codes"},
    "roblox_pet_sim_99": {"name": "Roblox: Pet Simulator 99", "category": "Roblox", "domain": "roblox", "page": "Pet_Simulator_99_Codes"},
    "roblox_blade_ball": {"name": "Roblox: Blade Ball", "category": "Roblox", "domain": "roblox", "page": "Blade_Ball_Codes"},
    "roblox_king_legacy": {"name": "Roblox: King Legacy", "category": "Roblox", "domain": "roblox", "page": "King_Legacy_Codes"},
    "roblox_anime_adventures": {"name": "Roblox: Anime Adventures", "category": "Roblox", "domain": "roblox", "page": "Anime_Adventures_Codes"}
}

def main():
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(SOURCES),
        "games": {}
    }

    print(f"Fetching codes via Fandom API for {len(SOURCES)} games...\n")

    for game_id, info in SOURCES.items():
        print(f"Scraping [{info['name']}]...")
        codes = fetch_fandom_codes(info["domain"], info["page"])
        
        output_data["games"][game_id] = {
            "name": info["name"],
            "category": info["category"],
            "source_url": f"https://{info['domain']}.fandom.com/wiki/{info['page']}",
            "codes_count": len(codes),
            "free_codes": codes
        }
        time.sleep(0.5)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\nExtraction finished successfully! Update your repository script.")

if __name__ == "__main__":
    main()

