import os
import re
import json
import time
import random
import urllib.parse
import requests

WORKER_URL = os.getenv("WORKER_URL", "")

# خريطة دقيقة وموثوقة لجميع الألعاب مع النطاقات والصفحات الصحيحة
GAMES_CONFIG = {
    "Genshin Impact": {"wiki": "genshin-impact", "pages": ["Promotional_Code", "Codes"]},
    "Honkai: Star Rail": {"wiki": "honkai-star-rail", "pages": ["Redemption_Code", "Codes"]},
    "Zenless Zone Zero": {"wiki": "zenless-zone-zero", "pages": ["Redemption_Code", "Codes"]},
    "Wuthering Waves": {"wiki": "wutheringwaves", "pages": ["Redemption_Code", "Codes"]},
    "Solo Leveling: Arise": {"wiki": "sololeveling", "pages": ["Solo_Leveling:_Arise/Codes", "Codes"]},
    "Tower of Fantasy": {"wiki": "toweroffantasy", "pages": ["Redemption_Code", "Codes"]},
    "Cookie Run: Kingdom": {"wiki": "cookierunkingdom", "pages": ["Coupon_Codes", "Codes"]},
    "Epic Seven": {"wiki": "epic7", "pages": ["Coupon_Codes", "Codes"]},
    "Blox Fruits": {"wiki": "blox-fruits", "pages": ["Codes"]},
    "PUBG Mobile": {"wiki": "pubgmobile", "pages": ["Redemption_Center", "Codes"]},
    "Call of Duty: Mobile (CODM)": {"wiki": "callofduty", "pages": ["Call_of_Duty:_Mobile/Redeem_Codes", "Codes"]},
    "Garena Free Fire": {"wiki": "freefire", "pages": ["Redeem_Codes", "Codes"]},
    "Dead by Daylight": {"wiki": "deadbydaylight", "pages": ["Promo_Codes", "Codes"]},
    "AFK Arena": {"wiki": "afk-arena", "pages": ["Redeeming_Codes", "Codes"]},
    "Goddess of Victory: Nikke": {"wiki": "nikke-goddess-of-victory-international", "pages": ["CD_Key_Codes", "Codes"]},
    "Arknights": {"wiki": "arknights", "pages": ["Gift_Codes", "Codes"]},
    "Dislyte": {"wiki": "dislyte", "pages": ["Gift_Codes", "Codes"]},
    "Whiteout Survival": {"wiki": "whiteout-survival", "pages": ["Gift_Codes", "Codes"]},
    "State of Survival": {"wiki": "state-of-survival", "pages": ["Gift_Codes", "Codes"]},
    "Rise of Kingdoms": {"wiki": "riseofkingdoms", "pages": ["Redeem_Codes", "Codes"]},
    "Raid: Shadow Legends": {"wiki": "raid-shadow-legends", "pages": ["Promo_Codes", "Codes"]},
    "Lords Mobile": {"wiki": "lordsmobile", "pages": ["Redemption_Codes", "Codes"]},
    "Clash of Clans": {"wiki": "clashofclans", "pages": ["Voucher_Codes", "Codes"]},
    "Pokémon GO": {"wiki": "pokemongo", "pages": ["Promo_Codes", "Codes"]},
    "EA Sports FC Mobile": {"wiki": "ea-fc-mobile", "pages": ["Redeem_Codes", "Codes"]},
    "NBA 2K": {"wiki": "nba2k", "pages": ["Locker_Codes", "Codes"]},
    "Rocket League": {"wiki": "rocketleague", "pages": ["Redeemable_codes", "Codes"]},
    "Mobile Legends: Bang Bang (MLBB)": {"wiki": "mobile-legends", "pages": ["Redeem_Codes", "Codes"]},
    "Brawl Stars": {"wiki": "brawlstars", "pages": ["Voucher_Codes", "Codes"]},
    "Clash Royale": {"wiki": "clashroyale", "pages": ["Voucher_Codes", "Codes"]},
    "Pet Simulator 99": {"wiki": "pet-simulator", "pages": ["Pet_Simulator_99:Codes", "Codes"]},
    "Blade Ball": {"wiki": "bladeball", "pages": ["Codes"]},
    "All Star Tower Defense": {"wiki": "allstar-tower-defense-roblox", "pages": ["Codes"]},
    "BedWars": {"wiki": "robloxbedwars", "pages": ["Codes"]},
    "Anime Defenders": {"wiki": "anime-defenders", "pages": ["Codes"]},
    "Evomon": {"wiki": "evomon", "pages": ["Codes"]}
}

CODE_REGEX = r'\b[A-Z0-9]{5,18}\b'

EXCLUDED_TERMS = {
    "REDDIT", "DISCORD", "TWITTER", "UPDATE", "ROBLOX", "GENSHIN", 
    "HTTPS", "HTTP", "WIKI", "FANDOM", "CODES", "CODE", "EXPIRED", 
    "PROMO", "FREE", "REDEEM", "REWARDS", "REWARD", "GITHUB", "JANUARY", 
    "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", 
    "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "ONLINE", "MOBILE",
    "JSON", "DATA", "TITLE", "SELFTEXT", "AUTHOR", "PERMALINK", "URL",
    "ACTION", "PARSE", "WIKITEXT", "FORMAT", "PROP", "PAGE"
}

def fetch_url(url):
    """جلب البيانات باستخدام Worker أو مباشرة"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if WORKER_URL:
        try:
            encoded_url = urllib.parse.quote(url, safe='')
            res = requests.get(f"{WORKER_URL}?url={encoded_url}", timeout=15)
            if res.status_code == 200:
                return res.text
        except Exception:
            pass
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.text
    except Exception:
        pass
    return ""

def get_game_wikitext(subdomain, pages):
    """جلب المحتوى والتحقق من أن الصفحة ليست missingtitle"""
    for page in pages:
        url = f"https://{subdomain}.fandom.com/api.php?action=parse&page={page}&prop=wikitext&format=json"
        raw_text = fetch_url(url)
        if raw_text:
            try:
                data = json.loads(raw_text)
                if "error" not in data and "parse" in data:
                    return data["parse"]["wikitext"].get("*", "")
            except Exception:
                continue
    return ""

def parse_codes(wikitext):
    if not wikitext:
        return []
    raw_matches = re.findall(CODE_REGEX, wikitext)
    valid_codes = [c for c in set(raw_matches) if c.upper() not in EXCLUDED_TERMS and not c.isdigit()]
    return valid_codes

def run_scraper():
    final_results = {}
    print(f"بدء عملية الجمع لـ {len(GAMES_CONFIG)} لعبة...")

    for game_name, config in GAMES_CONFIG.items():
        print(f"-> معالجة: {game_name}...")
        wikitext = get_game_wikitext(config["wiki"], config["pages"])
        codes = parse_codes(wikitext)
        final_results[game_name] = codes
        print(f"   [الأكواد المستخرجة: {len(codes)}]")
        time.sleep(random.uniform(0.5, 1.0))

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    print("\nتم التحديث واكتمال الملف بنجاح.")

if __name__ == "__main__":
    run_scraper()

