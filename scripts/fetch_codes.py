import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime, timezone

# قائمة الكلمات الإنجليزية الشائعة وعناصر الهيدر للاستبعاد الصارم
STRICT_BLACKLIST = {
    "AMERICA", "CHINA", "EUROPE", "ASIA", "USED", "EXPIRED", "ACTIVE", 
    "THIS", "PAGE", "LINK", "STUDIO", "SOULSTONE", "CODE", "CODES", 
    "REDEEM", "REWARD", "REWARDS", "DETAILS", "SERVER", "UNKNOWN", 
    "PROMOTIONAL", "OFFICIAL", "ITEM", "ITEMS", "FREE", "WIKI", "HTTP"
}

# نمط كود اللعبة: يجب أن يتكون من حروف وأرقام وشُرط فقط (غالبيتها حروف كبيرة)
CODE_PATTERN = re.compile(r'^[A-Z0-9_\-]{4,30}$')

def clean_and_validate_code(text):
    """تنظيف النص واستخراج الكود الحقيقي فقط"""
    # إزالة المراجع مثل [1] وإزالة علامات الترقيم من الأطراف
    cleaned = re.sub(r'\[\d+\]', '', text).strip()
    cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned)
    
    # تحويل النص إلى حروف كبيرة للتحقق
    upper_val = cleaned.upper()
    
    if not CODE_PATTERN.match(upper_val):
        return None
    if upper_val in STRICT_BLACKLIST:
        return None
    if upper_val.isdigit(): # استبعاد الأرقام الخالصة
        return None
        
    return upper_val

def fetch_fandom_codes(domain, pages):
    """جلب المحتوى عبر MediaWiki API مع دعم مسارات متعددة للصفحات"""
    api_url = f"https://{domain}.fandom.com/api.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    valid_codes = set()
    
    for page in pages:
        params = {
            "action": "parse",
            "page": page,
            "prop": "text",
            "format": "json"
        }
        try:
            res = requests.get(api_url, params=params, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            
            data = res.json()
            if "parse" not in data or "text" not in data["parse"]:
                continue
                
            soup = BeautifulSoup(data["parse"]["text"]["*"], 'html.parser')
            
            # 1. البحث عن الوسوم المباشرة للكود
            for elem in soup.find_all(['code', 'kbd', 'strong', 'b']):
                code = clean_and_validate_code(elem.get_text())
                if code:
                    valid_codes.add(code)

            # 2. البحث داخل خلايا الجداول
            for table in soup.find_all('table'):
                table_text = table.get_text().lower()
                if "expired" in table_text and "active" not in table_text:
                    continue
                    
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        for cell in cells[:2]: # الفحص في أول خليتين
                            first_word = cell.get_text().strip().split()[0] if cell.get_text().strip().split() else ""
                            code = clean_and_validate_code(first_word)
                            if code:
                                valid_codes.add(code)
                                
        except Exception:
            continue

    return list(valid_codes)

# قاعدة بيانات الـ 38 لعبة بعد تصحيح النطاقات وأسماء الصفحات الدقيقة
SOURCES = {
    # --- Gacha & RPGs ---
    "genshin_impact": {"name": "Genshin Impact", "category": "Gacha", "domain": "genshin-impact", "pages": ["Promotional_Code"]},
    "honkai_star_rail": {"name": "Honkai: Star Rail", "category": "Gacha", "domain": "honkai-star-rail", "pages": ["Redemption_Code"]},
    "zenless_zone_zero": {"name": "Zenless Zone Zero", "category": "Gacha", "domain": "zenless-zone-zero", "pages": ["Redemption_Code"]},
    "wuthering_waves": {"name": "Wuthering Waves", "category": "Gacha", "domain": "wutheringwaves", "pages": ["Redemption_Code"]},
    "solo_leveling_arise": {"name": "Solo Leveling: Arise", "category": "Action RPG", "domain": "sololeveling", "pages": ["Redemption_Codes", "Codes"]},
    "honkai_impact_3rd": {"name": "Honkai Impact 3rd", "category": "Gacha", "domain": "honkaiimpact3", "pages": ["Exchange_Codes"]},
    "blue_archive": {"name": "Blue Archive", "category": "Gacha", "domain": "bluearchive", "pages": ["Coupon_Codes", "Redemption_Codes"]},
    "nikke": {"name": "Goddess of Victory: Nikke", "category": "Gacha", "domain": "nikke-goddess-of-victory-nikke", "pages": ["Redemption_Codes", "CD_Keys"]},
    "reverse_1999": {"name": "Reverse: 1999", "category": "Gacha", "domain": "reverse1999", "pages": ["Redemption_Codes", "Codes"]},
    "outerplane": {"name": "Outerplane", "category": "Gacha", "domain": "outerplane", "pages": ["Coupon_Codes"]},
    "black_clover_m": {"name": "Black Clover M", "category": "Gacha", "domain": "blackcloverm", "pages": ["Redemption_Codes", "Codes"]},
    "arknights": {"name": "Arknights", "category": "Strategy/Gacha", "domain": "arknights", "pages": ["Gift_Codes"]},
    "epic_seven": {"name": "Epic Seven", "category": "Turn-based RPG", "domain": "epic7", "pages": ["Coupon_Codes"]},
    "dislyte": {"name": "Dislyte", "category": "Turn-based RPG", "domain": "dislyte", "pages": ["Gift_Codes"]},

    # --- Strategy & Idle ---
    "afk_arena": {"name": "AFK Arena", "category": "Idle RPG", "domain": "afk-arena", "pages": ["Redemption_Codes"]},
    "afk_journey": {"name": "AFK Journey", "category": "Idle RPG", "domain": "afkjourney", "pages": ["Redemption_Codes", "Codes"]},
    "raid_shadow_legends": {"name": "RAID: Shadow Legends", "category": "RPG", "domain": "raidshadowlegends", "pages": ["Promo_Codes"]},
    "whiteout_survival": {"name": "Whiteout Survival", "category": "Strategy", "domain": "whiteoutsurvival", "pages": ["Gift_Codes", "Codes"]},
    "last_war_survival": {"name": "Last War: Survival", "category": "Strategy", "domain": "lastwar", "pages": ["Gift_Codes", "Codes"]},
    "legend_of_mushroom": {"name": "Legend of Mushroom", "category": "Idle", "domain": "legendofmushroom", "pages": ["Redemption_Codes", "Codes"]},
    "summoners_war": {"name": "Summoners War", "category": "Turn-based RPG", "domain": "summonerswar", "pages": ["Coupon_Codes"]},
    "tower_of_fantasy": {"name": "Tower of Fantasy", "category": "MMORPG", "domain": "toweroffantasy", "pages": ["Redemption_Codes"]},
    "cookie_run_kingdom": {"name": "Cookie Run: Kingdom", "category": "RPG/Base Building", "domain": "cookierunkingdom", "pages": ["Coupon_Codes"]},

    # --- Battle Royale & Multiplayer ---
    "free_fire": {"name": "Garena Free Fire", "category": "Battle Royale", "domain": "garena", "pages": ["Free_Fire_Redeem_Codes", "Codes"]},
    "pubg_mobile": {"name": "PUBG Mobile", "category": "Battle Royale", "domain": "pubgmobile", "pages": ["Redemption_Codes", "Codes"]},
    "mobile_legends": {"name": "Mobile Legends: Bang Bang", "category": "MOBA", "domain": "mobile-legends", "pages": ["Redeem_Code"]},
    "brawl_stars": {"name": "Brawl Stars", "category": "Action/MOBA", "domain": "brawlstars", "pages": ["Voucher_Codes"]},
    "clash_royale": {"name": "Clash Royale", "category": "Strategy", "domain": "clashroyale", "pages": ["Voucher_Codes"]},
    "pokemon_go": {"name": "Pokémon GO", "category": "AR / Mobile", "domain": "pokemongo", "pages": ["Promo_Codes"]},
    "monster_hunter_now": {"name": "Monster Hunter Now", "category": "AR / Action", "domain": "monsterhunter", "pages": ["MHN_Promo_Codes", "Codes"]},
    "dead_by_daylight": {"name": "Dead by Daylight", "category": "Asymmetrical Horror", "domain": "deadbydaylight", "pages": ["Promo_Codes"]},
    "coin_master": {"name": "Coin Master", "category": "Casual", "domain": "coin-master", "pages": ["Free_Spins", "Links"]},

    # --- Roblox Games (المستقلة بنطاقاتها الخاصة) ---
    "roblox_blox_fruits": {"name": "Roblox: Blox Fruits", "category": "Roblox", "domain": "blox-fruits", "pages": ["Codes"]},
    "roblox_astd": {"name": "Roblox: All Star Tower Defense", "category": "Roblox", "domain": "allstar-tower-defense", "pages": ["Codes"]},
    "roblox_pet_sim_99": {"name": "Roblox: Pet Simulator 99", "category": "Roblox", "domain": "pet-simulator", "pages": ["Pet_Simulator_99_Codes", "Codes"]},
    "roblox_blade_ball": {"name": "Roblox: Blade Ball", "category": "Roblox", "domain": "blade-ball", "pages": ["Codes"]},
    "roblox_king_legacy": {"name": "Roblox: King Legacy", "category": "Roblox", "domain": "king-legacy", "pages": ["Codes"]},
    "roblox_anime_adventures": {"name": "Roblox: Anime Adventures", "category": "Roblox", "domain": "anime-adventures", "pages": ["Codes"]}
}

def main():
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(SOURCES),
        "games": {}
    }

    print(f"Starting clean code extraction for {len(SOURCES)} games...\n")

    for game_id, info in SOURCES.items():
        print(f"Scraping [{info['name']}]...")
        codes = fetch_fandom_codes(info["domain"], info["pages"])
        
        output_data["games"][game_id] = {
            "name": info["name"],
            "category": info["category"],
            "source_url": f"https://{info['domain']}.fandom.com/wiki/{info['pages'][0]}",
            "codes_count": len(codes),
            "free_codes": codes
        }
        time.sleep(0.3)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\nClean extraction complete! Re-run your GitHub Action.")

if __name__ == "__main__":
    main()

