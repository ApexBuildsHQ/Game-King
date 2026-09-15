import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime, timezone

# قائمة الكلمات المحظورة لمنع تسرب النصوص العامة والمصطلحات الشائعة
STRICT_BLACKLIST = {
    "AMERICA", "CHINA", "EUROPE", "ASIA", "USED", "EXPIRED", "ACTIVE", 
    "THIS", "PAGE", "LINK", "STUDIO", "SOULSTONE", "CODE", "CODES", 
    "REDEEM", "REWARD", "REWARDS", "DETAILS", "SERVER", "UNKNOWN", 
    "PROMOTIONAL", "OFFICIAL", "ITEM", "ITEMS", "FREE", "WIKI", "HTTP",
    "HTTPS", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
    "DISCORD", "TWITTER", "YOUTUBE", "UPDATE", "WORKING", "EXPIRE"
}

def clean_and_validate_code(text, game_type="general"):
    """تنظيف وتصفية النص لاستخراج الكود الحقيقي فقط"""
    if not text:
        return None
        
    # إزالة المراجع الويكية والمؤشرات المزدوجة
    cleaned = re.sub(r'\[\d+\]', '', text).strip()
    
    # حذف جميع علامات الترقيم الغريبة (مثل ?, =, :, ", ', ,)
    cleaned = re.sub(r'[^\w\-_]', '', cleaned)
    
    if len(cleaned) < 4 or len(cleaned) > 32:
        return None
        
    upper_val = cleaned.upper()
    
    # استبعاد الكلمات المحظورة والأرقام الخالصة
    if upper_val in STRICT_BLACKLIST or upper_val.isdigit():
        return None
        
    # قواعد مطابقة الأكواد حسب نوع اللعبة
    if game_type == "roblox":
        # ألعاب روبلوكس قد تحتوي على حروف كبيرة وصغيرة
        if re.match(r'^[A-Za-z0-9_\-]{3,30}$', cleaned):
            return cleaned
    else:
        # باقي الألعاب تتطلب حروفاً كبيرة وأرقاماً وشُرط فقط
        if re.match(r'^[A-Z0-9_\-]{4,32}$', upper_val):
            return upper_val
            
    return None

def fetch_game_codes(domain, pages, game_type):
    """جلب الأكواد عبر MediaWiki API مع دعم التنقل بين عدة صفحات بديلة"""
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
            
            # 1. استخراج الأكواد من الوسوم المباشرة (code, kbd, b, strong)
            for elem in soup.find_all(['code', 'kbd', 'strong', 'b']):
                code = clean_and_validate_code(elem.get_text(), game_type)
                if code:
                    valid_codes.add(code)

            # 2. استخراج الأكواد من خلايا الجداول
            for table in soup.find_all('table'):
                table_text = table.get_text().lower()
                # تجنب جداول الأكواد المنتهية الصلاحية
                if "expired" in table_text and "active" not in table_text and "working" not in table_text:
                    continue
                    
                for row in table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        # أخذ الكلمة الأولى من أول خليتين داخل الصف
                        for cell in cells[:2]:
                            raw_cell = cell.get_text().strip()
                            first_word = raw_cell.split()[0] if raw_cell.split() else ""
                            code = clean_and_validate_code(first_word, game_type)
                            if code:
                                valid_codes.add(code)
                                
            # إذا تم العثور على أكواد في هذه الصفحة، يتم الاكتفاء بها وعدم الانتقال للصفحة البديلة
            if len(valid_codes) > 0:
                break

        except Exception:
            continue

    return list(valid_codes)

# قاعدة بيانات الـ 38 لعبة كاملاً مع المسارات الرئيسية والبديلة
GAMES_DATABASE = {
    "genshin_impact": {"name": "Genshin Impact", "category": "Gacha", "type": "general", "domain": "genshin-impact", "pages": ["Promotional_Code", "Codes"]},
    "honkai_star_rail": {"name": "Honkai: Star Rail", "category": "Gacha", "type": "general", "domain": "honkai-star-rail", "pages": ["Redemption_Code", "Codes"]},
    "zenless_zone_zero": {"name": "Zenless Zone Zero", "category": "Gacha", "type": "general", "domain": "zenless-zone-zero", "pages": ["Redemption_Code", "Codes"]},
    "wuthering_waves": {"name": "Wuthering Waves", "category": "Gacha", "type": "general", "domain": "wutheringwaves", "pages": ["Redemption_Code", "Codes"]},
    "solo_leveling_arise": {"name": "Solo Leveling: Arise", "category": "Action RPG", "type": "general", "domain": "sololeveling", "pages": ["Redemption_Codes", "Codes"]},
    "honkai_impact_3rd": {"name": "Honkai Impact 3rd", "category": "Gacha", "type": "general", "domain": "honkaiimpact3", "pages": ["Exchange_Codes", "Codes"]},
    "blue_archive": {"name": "Blue Archive", "category": "Gacha", "type": "general", "domain": "bluearchive", "pages": ["Coupon_Codes", "Redemption_Codes", "Codes"]},
    "nikke": {"name": "Goddess of Victory: Nikke", "category": "Gacha", "type": "general", "domain": "nikke-goddess-of-victory-nikke", "pages": ["Redemption_Codes", "CD_Keys", "Codes"]},
    "reverse_1999": {"name": "Reverse: 1999", "category": "Gacha", "type": "general", "domain": "reverse1999", "pages": ["Redemption_Codes", "Codes"]},
    "outerplane": {"name": "Outerplane", "category": "Gacha", "type": "general", "domain": "outerplane", "pages": ["Coupon_Codes", "Codes"]},
    "black_clover_m": {"name": "Black Clover M", "category": "Gacha", "type": "general", "domain": "blackcloverm", "pages": ["Redemption_Codes", "Codes"]},
    "arknights": {"name": "Arknights", "category": "Strategy/Gacha", "type": "general", "domain": "arknights", "pages": ["Gift_Codes", "Codes"]},
    "epic_seven": {"name": "Epic Seven", "category": "Turn-based RPG", "type": "general", "domain": "epic7", "pages": ["Coupon_Codes", "Codes"]},
    "dislyte": {"name": "Dislyte", "category": "Turn-based RPG", "type": "general", "domain": "dislyte", "pages": ["Gift_Codes", "Codes"]},
    "afk_arena": {"name": "AFK Arena", "category": "Idle RPG", "type": "general", "domain": "afk-arena", "pages": ["Redemption_Codes", "Codes"]},
    "afk_journey": {"name": "AFK Journey", "category": "Idle RPG", "type": "general", "domain": "afkjourney", "pages": ["Redemption_Codes", "Codes"]},
    "raid_shadow_legends": {"name": "RAID: Shadow Legends", "category": "RPG", "type": "general", "domain": "raidshadowlegends", "pages": ["Promo_Codes", "Codes"]},
    "whiteout_survival": {"name": "Whiteout Survival", "category": "Strategy", "type": "general", "domain": "whiteoutsurvival", "pages": ["Gift_Codes", "Codes"]},
    "last_war_survival": {"name": "Last War: Survival", "category": "Strategy", "type": "general", "domain": "lastwar", "pages": ["Gift_Codes", "Codes"]},
    "legend_of_mushroom": {"name": "Legend of Mushroom", "category": "Idle", "type": "general", "domain": "legendofmushroom", "pages": ["Redemption_Codes", "Codes"]},
    "summoners_war": {"name": "Summoners War", "category": "Turn-based RPG", "type": "general", "domain": "summonerswar", "pages": ["Coupon_Codes", "Codes"]},
    "tower_of_fantasy": {"name": "Tower of Fantasy", "category": "MMORPG", "type": "general", "domain": "toweroffantasy", "pages": ["Redemption_Codes", "Codes"]},
    "cookie_run_kingdom": {"name": "Cookie Run: Kingdom", "category": "RPG/Base Building", "type": "general", "domain": "cookierunkingdom", "pages": ["Coupon_Codes", "Codes"]},
    "free_fire": {"name": "Garena Free Fire", "category": "Battle Royale", "type": "general", "domain": "garena", "pages": ["Free_Fire_Redeem_Codes", "Codes"]},
    "pubg_mobile": {"name": "PUBG Mobile", "category": "Battle Royale", "type": "general", "domain": "pubgmobile", "pages": ["Redemption_Codes", "Codes"]},
    "mobile_legends": {"name": "Mobile Legends: Bang Bang", "category": "MOBA", "type": "general", "domain": "mobile-legends", "pages": ["Redeem_Code", "Codes"]},
    "brawl_stars": {"name": "Brawl Stars", "category": "Action/MOBA", "type": "general", "domain": "brawlstars", "pages": ["Voucher_Codes", "Codes"]},
    "clash_royale": {"name": "Clash Royale", "category": "Strategy", "type": "general", "domain": "clashroyale", "pages": ["Voucher_Codes", "Codes"]},
    "pokemon_go": {"name": "Pokémon GO", "category": "AR / Mobile", "type": "general", "domain": "pokemongo", "pages": ["Promo_Codes", "Codes"]},
    "monster_hunter_now": {"name": "Monster Hunter Now", "category": "AR / Action", "type": "general", "domain": "monsterhunter", "pages": ["MHN_Promo_Codes", "Codes"]},
    "dead_by_daylight": {"name": "Dead by Daylight", "category": "Asymmetrical Horror", "type": "general", "domain": "deadbydaylight", "pages": ["Promo_Codes", "Codes"]},
    "coin_master": {"name": "Coin Master", "category": "Casual", "type": "general", "domain": "coin-master", "pages": ["Free_Spins", "Codes"]},
    "roblox_blox_fruits": {"name": "Roblox: Blox Fruits", "category": "Roblox", "type": "roblox", "domain": "blox-fruits", "pages": ["Codes", "Blox_Fruits_Codes"]},
    "roblox_astd": {"name": "Roblox: All Star Tower Defense", "category": "Roblox", "type": "roblox", "domain": "allstar-tower-defense", "pages": ["Codes", "ASTD_Codes"]},
    "roblox_pet_sim_99": {"name": "Roblox: Pet Simulator 99", "category": "Roblox", "type": "roblox", "domain": "pet-simulator", "pages": ["Pet_Simulator_99_Codes", "Codes"]},
    "roblox_blade_ball": {"name": "Roblox: Blade Ball", "category": "Roblox", "type": "roblox", "domain": "blade-ball", "pages": ["Codes"]},
    "roblox_king_legacy": {"name": "Roblox: King Legacy", "category": "Roblox", "type": "roblox", "domain": "king-legacy", "pages": ["Codes"]},
    "roblox_anime_adventures": {"name": "Roblox: Anime Adventures", "category": "Roblox", "type": "roblox", "domain": "anime-adventures", "pages": ["Codes"]}
}

def main():
    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_games": len(GAMES_DATABASE),
        "games": {}
    }

    print(f"Starting code synchronization for {len(GAMES_DATABASE)} games...")

    for game_id, info in GAMES_DATABASE.items():
        print(f"Processing: {info['name']}...")
        codes = fetch_game_codes(info["domain"], info["pages"], info["type"])
        
        output_data["games"][game_id] = {
            "name": info["name"],
            "category": info["category"],
            "source_url": f"https://{info['domain']}.fandom.com/wiki/{info['pages'][0]}",
            "codes_count": len(codes),
            "free_codes": codes
        }
        time.sleep(0.2)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Sync complete. Generated clean codes.json successfully.")

if __name__ == "__main__":
    main()

