import os
import re
import json
import time
import random
import urllib.parse
import requests

# جلب رابط الـ Worker من المتغيرات البيئية
WORKER_URL = os.getenv("WORKER_URL")

if not WORKER_URL:
    print("[ تحذير ]: لم يتم العثور على WORKER_URL في GitHub Secrets. يرجى ضبطه والتأكد منه.")

# مصفوفة الألعاب الـ 38 مع روابط مصححة تماماً
GAMES_DATABASE = {
    # ==================== 1. ألعاب Gacha و RPG (14 لعبة) ====================
    "Genshin Impact": [
        "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/Genshin_Impact/new.json?limit=25"
    ],
    "Honkai: Star Rail": [
        "https://honkai-star-rail.fandom.com/api.php?action=parse&page=Redemption_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/HonkaiStarRail/new.json?limit=25"
    ],
    "Zenless Zone Zero": [
        "https://zenless-zone-zero.fandom.com/api.php?action=parse&page=Redemption_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/ZZZ_Official/new.json?limit=25"
    ],
    "Wuthering Waves": [
        "https://wutheringwaves.fandom.com/api.php?action=parse&page=Redemption_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/WutheringWaves/new.json?limit=25"
    ],
    "Solo Leveling: Arise": [
        "https://sololeveling.fandom.com/api.php?action=parse&page=Solo_Leveling:_Arise/Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/SoloLevelingArise/new.json?limit=25"
    ],
    "Tower of Fantasy": [
        "https://toweroffantasy.fandom.com/api.php?action=parse&page=Redemption_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/TowerofFantasy/new.json?limit=25"
    ],
    "Dislyte": [
        "https://dislyte.fandom.com/api.php?action=parse&page=Gift_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/Dislyte/new.json?limit=25"
    ],
    "Cookie Run: Kingdom": [
        "https://cookierunkingdom.fandom.com/api.php?action=parse&page=Coupon_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/CookieRunKingdoms/new.json?limit=25"
    ],
    "AFK Arena": [
        "https://afk-arena.fandom.com/api.php?action=parse&page=Redeeming_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/afkarena/new.json?limit=25"
    ],
    "Goddess of Victory: Nikke": [
        "https://nikke-goddess-of-victory-international.fandom.com/api.php?action=parse&page=CD_Key_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/NikkeMobile/new.json?limit=25"
    ],
    "Arknights": [
        "https://arknights.fandom.com/api.php?action=parse&page=Gift_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/arknights/new.json?limit=25"
    ],
    "Epic Seven": [
        "https://epic7.fandom.com/api.php?action=parse&page=Coupon_Code&prop=wikitext&format=json",
        "https://www.reddit.com/r/EpicSeven/new.json?limit=25"
    ],
    "Fate/Grand Order (FGO)": [
        "https://fategrandorder.fandom.com/api.php?action=parse&page=Present_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/grandorder/new.json?limit=25"
    ],
    "Blue Archive": [
        "https://bluearchive.fandom.com/api.php?action=parse&page=Coupon_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/BlueArchive/new.json?limit=25"
    ],

    # ==================== 2. ألعاب الباتل رويال والشوتر (4 ألعاب) ====================
    "PUBG Mobile": [
        "https://pubgmobile.fandom.com/api.php?action=parse&page=Redemption_Center&prop=wikitext&format=json",
        "https://www.reddit.com/r/PUBGMobile/new.json?limit=25"
    ],
    "Call of Duty: Mobile (CODM)": [
        "https://callofduty.fandom.com/api.php?action=parse&page=Call_of_Duty:_Mobile/Redeem_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/CallOfDutyMobile/new.json?limit=25"
    ],
    "Garena Free Fire": [
        "https://freefire.fandom.com/api.php?action=parse&page=Redeem_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/freefire/new.json?limit=25"
    ],
    "Dead by Daylight": [
        "https://deadbydaylight.fandom.com/api.php?action=parse&page=Promo_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/deadbydaylight/new.json?limit=25"
    ],

    # ==================== 3. ألعاب أطوار Roblox والمنصات (7 ألعاب) ====================
    "Blox Fruits": [
        "https://blox-fruits.fandom.com/api.php?action=parse&page=Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/BloxFruits/new.json?limit=25"
    ],
    "Anime Defenders": [
        "https://anime-defenders.fandom.com/api.php?action=parse&page=Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/AnimeDefenders/new.json?limit=25"
    ],
    "Evomon": [
        "https://evomon.fandom.com/api.php?action=parse&page=Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/Roblox/new.json?limit=25"
    ],
    "Pet Simulator 99": [
        "https://pet-simulator.fandom.com/api.php?action=parse&page=Pet_Simulator_99:Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/PetSimulator99/new.json?limit=25"
    ],
    "Blade Ball": [
        "https://blade-ball.fandom.com/api.php?action=parse&page=Blade_Ball_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/BladeBall/new.json?limit=25"
    ],
    "All Star Tower Defense": [
        "https://allstartowerdefense.fandom.com/api.php?action=parse&page=ASTD_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/allstartowerdefense/new.json?limit=25"
    ],
    "BedWars": [
        "https://robloxbedwars.fandom.com/api.php?action=parse&page=Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/RobloxBedwars/new.json?limit=25"
    ],

    # ==================== 4. الألعاب الاستراتيجية والموارد (6 ألعاب) ====================
    "Whiteout Survival": [
        "https://whiteout-survival.fandom.com/api.php?action=parse&page=Gift_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/whiteoutsurvival/new.json?limit=25"
    ],
    "State of Survival": [
        "https://state-of-survival.fandom.com/api.php?action=parse&page=Gift_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/stateofsurvival/new.json?limit=25"
    ],
    "Rise of Kingdoms": [
        "https://riseofkingdoms.fandom.com/api.php?action=parse&page=Redeem_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/RiseofKingdoms/new.json?limit=25"
    ],
    "Raid: Shadow Legends": [
        "https://raid-shadow-legends.fandom.com/api.php?action=parse&page=Promo_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/RaidShadowLegends/new.json?limit=25"
    ],
    "Lords Mobile": [
        "https://lordsmobile.fandom.com/api.php?action=parse&page=Redemption_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/lordsmobile/new.json?limit=25"
    ],
    "Clash of Clans": [
        "https://clashofclans.fandom.com/api.php?action=parse&page=Voucher_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/ClashOfClans/new.json?limit=25"
    ],

    # ==================== 5. ألعاب الرياضة والتنافس السريع (7 ألعاب) ====================
    "Pokémon GO": [
        "https://pokemongo.fandom.com/api.php?action=parse&page=Promo_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/TheSilphRoad/new.json?limit=25"
    ],
    "EA Sports FC Mobile": [
        "https://fifa-mobile.fandom.com/api.php?action=parse&page=Redeem_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/FCMobile/new.json?limit=25"
    ],
    "NBA 2K": [
        "https://nba2k.fandom.com/api.php?action=parse&page=Locker_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/NBA2k/new.json?limit=25"
    ],
    "Rocket League": [
        "https://rocketleague.fandom.com/api.php?action=parse&page=Redeemable_codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/RocketLeague/new.json?limit=25"
    ],
    "Mobile Legends: Bang Bang (MLBB)": [
        "https://mobile-legends.fandom.com/api.php?action=parse&page=Redeem_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/MobileLegendsGame/new.json?limit=25"
    ],
    "Brawl Stars": [
        "https://brawlstars.fandom.com/api.php?action=parse&page=Voucher_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/Brawlstars/new.json?limit=25"
    ],
    "Clash Royale": [
        "https://clashroyale.fandom.com/api.php?action=parse&page=Voucher_Codes&prop=wikitext&format=json",
        "https://www.reddit.com/r/ClashRoyale/new.json?limit=25"
    ]
}

# Regex لاقتناص الأكواد (حروف كبيرة وأرقام بطول من 5 إلى 18)
CODE_REGEX = r'\b[A-Z0-9]{5,18}\b'

# قائمة موسعة لاستبعاد الجمل والكلمات العامة التي يقتنصها الـ Regex
EXCLUDED_TERMS = {
    # كلمات برمجية ونصوص هيدر
    "REDDIT", "DISCORD", "TWITTER", "UPDATE", "ROBLOX", "GENSHIN", 
    "HTTPS", "HTTP", "WIKI", "FANDOM", "CODES", "CODE", "EXPIRED", 
    "PROMO", "FREE", "REDEEM", "REWARDS", "REWARD", "GITHUB", "JANUARY", 
    "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", 
    "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "ONLINE", "MOBILE",
    "JSON", "DATA", "TITLE", "SELFTEXT", "AUTHOR", "PERMALINK", "URL",
    
    # كلمات عامة تم العثور عليها بالخطأ في الفحص السابق
    "PERFECT", "TERRIBLE", "DRAWING", "FAREWELL", "EVERY", "OMEGA",
    "ROASTING", "HAPPYSUNDAY", "GOODFORTUNE", "SWEETDREAMS", "LIGHTTHEWAY",
    "CHARMEDONE", "DREAMTOGETHER", "SHAREANDSAVEIT", "REMEMBRANCE",
    "HAPPYSPRINGFES", "THEETERNALLAND", "HAOCHIXIANZHOU", "HERESTHECODE",
    "ALLORNOTHING", "RAPPAISHERE", "LOVEFROMROBIN", "DIVEINTODREAMS",
    "ROBININSIDE", "THISISTHEHERTA", "THEHERTAGIFT", "STARRAILKARAOKE",
    "FIREFLYSGIFT", "LUCKYGAME", "AWAITSYOURLIGHT", "THEDAHLIA",
    "TINGYUNISBACK", "SUNDAYCALENDAR", "MOREPEACH", "HERTAGIFT",
    "FLAMESOFHEART", "WARMSUNLIGHT", "JOURNEYWELL", "NOMATTERTHECOST",
    "BLACKSHORES", "ETERNALFLAME", "FACEALEPH1", "TREASUREHUNT",
    "BACKTOSCHOOL", "STARCHASER", "RISKEVERYTHING", "MECHANISMCITY",
    "ILLUSIONHAUNTS", "WUTHERINGGIFT", "ALLEYESONUS", "THISISFINALE",
    "STRANGEVISITORS", "JOINCARNEVALE", "BEYONDTHEDOOR", "HEARTOFSWORD",
    "STARRYSTAGE", "SLICEDSPACE", "CRUMBLEDCITY", "DREAMSPERSIST",
    "RUNEREADER", "INTOTHEFOG", "SHADOWOFGLORY", "EVERFLOWING",
    "SPECIALONAIR", "COOKIERUNXIDUS", "XMASINKINGDOM", "TRENDYCOOKIESYT",
    "THANX300MPLAYERS", "TODEARESTFROMIHWAN", "STAFFBATTLE", "REWARDFUN",
    "BIGNEWS", "ADMINDARES", "ADMINFIGHT", "EASTEREXP", "ADMINHACKED",
    "TRIPLEABUSE", "DRAGONABUSE", "CODESLIDE", "NOMOREHACK", "BANEXPLOIT",
    "NOEXPLOITER", "DEVSCOOKING", "SEATROLLING"
}

def fetch_via_worker(target_url, retries=2):
    """إرسال الطلب عبر Cloudflare Worker مع ميزة إعادة المحاولة للتغلب على خطأ 429"""
    if not WORKER_URL:
        return ""

    encoded_url = urllib.parse.quote(target_url, safe='')
    proxy_url = f"{WORKER_URL}?url={encoded_url}"

    for attempt in range(retries + 1):
        try:
            response = requests.get(proxy_url, timeout=20)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                # إذا حدث ضغط طلبات، انتظر 4 ثوانٍ وأعد المحاولة
                time.sleep(4)
            else:
                print(f"[حالة الاستجابة {response.status_code}]: {target_url}")
        except Exception as e:
            if attempt == retries:
                print(f"[خطأ اتصالات]: {target_url} -> {e}")
            time.sleep(2)
    return ""

def extract_text_from_response(raw_content, url):
    """استخراج النصوص بحسب نوع المصدر"""
    if not raw_content:
        return ""

    # 1. إذا كان المصدر Reddit JSON
    if ".json" in url:
        try:
            data = json.loads(raw_content)
            posts = data.get('data', {}).get('children', [])
            extracted_text = []
            for post in posts:
                pdata = post.get('data', {})
                extracted_text.append(pdata.get('title', ''))
                extracted_text.append(pdata.get('selftext', ''))
            return " ".join(extracted_text)
        except Exception:
            pass

    # 2. إذا كان المصدر Fandom MediaWiki API
    if "api.php" in url and "format=json" in url:
        try:
            data = json.loads(raw_content)
            wikitext = data.get('parse', {}).get('wikitext', {}).get('*', '')
            if wikitext:
                return wikitext
        except Exception:
            pass

    # 3. تنظيف وسوم HTML كبديل افتراضي
    clean_text = re.sub(r'<[^>]+>', ' ', raw_content)
    return clean_text

def parse_codes(text_content):
    """تصفية واستخراج الأكواد النظيفة فقط"""
    raw_matches = re.findall(CODE_REGEX, text_content)
    
    valid_codes = []
    for code in raw_matches:
        code_upper = code.upper()
        # استبعاد الكلمات المستبعدة والأرقام المحضة
        if code_upper not in EXCLUDED_TERMS and not code.isdigit():
            valid_codes.append(code)

    return list(set(valid_codes))

def run_scraper():
    final_results = {}
    print(f"بدء عملية الجمع المزدوجة لـ {len(GAMES_DATABASE)} لعبة...")

    for game_name, sources in GAMES_DATABASE.items():
        print(f"-> جاري معالجة: {game_name} عبر {len(sources)} مصادر...")
        game_codes = []

        for url in sources:
            raw_content = fetch_via_worker(url)
            text_content = extract_text_from_response(raw_content, url)
            
            extracted = parse_codes(text_content)
            game_codes.extend(extracted)
            
            # فاصل زمني آمن لتفادي حظر الطلبات السريعة (429)
            time.sleep(random.uniform(2.0, 3.2))

        # دمج الأكواد وتصفية المكرر منها
        unique_codes = list(set(game_codes))
        final_results[game_name] = unique_codes
        print(f"   [إجمالي الأكواد الفريدة لـ {game_name}: {len(unique_codes)}]")

    # حفظ المخرجات في ملف codes.json
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    print("\nاكتملت عملية الفحص بنجاح وتم تحديث ملف codes.json.")

if __name__ == "__main__":
    run_scraper()

