import os
import re
import json
import time
import hashlib
import requests

# ==========================================
# 🔑 إعدادات المفاتيح والروابط
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CF_WORKER_URL = os.getenv("CF_WORKER_URL", "").rstrip("/")
CF_WORKER_SECRET = os.getenv("CF_WORKER_SECRET", "")

MAX_CODES_PER_GAME = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# قائمة الـ 38 لعبة بالكامل
GAMES_CONFIG = [
    # Gacha & RPG (14 لعبة)
    {"id": "genshin-impact", "name": "Genshin Impact", "url": "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&format=json"},
    {"id": "honkai-star-rail", "name": "Honkai: Star Rail", "url": "https://honkai-star-rail.fandom.com/api.php?action=parse&page=Redemption_Code&format=json"},
    {"id": "zenless-zone-zero", "name": "Zenless Zone Zero", "url": "https://zenless-zone-zero.fandom.com/api.php?action=parse&page=Redemption_Code&format=json"},
    {"id": "wuthering-waves", "name": "Wuthering Waves", "url": "https://wutheringwaves.fandom.com/api.php?action=parse&page=Redemption_Code&format=json"},
    {"id": "solo-leveling-arise", "name": "Solo Leveling: Arise", "url": "https://sololeveling.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "tower-of-fantasy", "name": "Tower of Fantasy", "url": "https://toweroffantasy.fandom.com/api.php?action=parse&page=Redemption_Codes&format=json"},
    {"id": "dislyte", "name": "Dislyte", "url": "https://dislyte.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "cookie-run-kingdom", "name": "Cookie Run: Kingdom", "url": "https://cookierunkingdom.fandom.com/api.php?action=parse&page=Coupon_Codes&format=json"},
    {"id": "afk-arena", "name": "AFK Arena", "url": "https://afk-arena.fandom.com/api.php?action=parse&page=Redemption_Codes&format=json"},
    {"id": "nikke", "name": "Goddess of Victory: Nikke", "url": "https://nikke-goddess-of-victory-international.fandom.com/api.php?action=parse&page=CD_Keys&format=json"},
    {"id": "arknights", "name": "Arknights", "url": "https://arknights.fandom.com/api.php?action=parse&page=Gift_Codes&format=json"},
    {"id": "epic-seven", "name": "Epic Seven", "url": "https://epic7.fandom.com/api.php?action=parse&page=Livestream_Coupon_Codes&format=json"},
    {"id": "fgo", "name": "Fate/Grand Order", "url": "https://fategrandorder.fandom.com/api.php?action=parse&page=Campaign_Codes&format=json"},
    {"id": "blue-archive", "name": "Blue Archive", "url": "https://bluearchive.fandom.com/api.php?action=parse&page=Coupon_Codes&format=json"},

    # Battle Royale & Shooters (4 ألعاب)
    {"id": "pubg-mobile", "name": "PUBG Mobile", "url": "https://www.reddit.com/r/PUBGMobile/new.json?limit=10"},
    {"id": "codm", "name": "Call of Duty: Mobile", "url": "https://callofduty.fandom.com/api.php?action=parse&page=Redeem_Codes&format=json"},
    {"id": "free-fire", "name": "Garena Free Fire", "url": "https://www.reddit.com/r/freefire/new.json?limit=10"},
    {"id": "dead-by-daylight", "name": "Dead by Daylight", "url": "https://deadbydaylight.fandom.com/api.php?action=parse&page=Codes&format=json"},

    # Roblox & Interactive Platforms (8 ألعاب)
    {"id": "blox-fruits", "name": "Blox Fruits", "url": "https://blox-fruits.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "anime-defenders", "name": "Anime Defenders", "url": "https://anime-defenders.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "evomon", "name": "Evomon", "url": "https://www.reddit.com/r/Roblox/new.json?limit=15"},
    {"id": "pokemon-go", "name": "Pokémon GO", "url": "https://pokemongo.fandom.com/api.php?action=parse&page=Promo_Codes&format=json"},
    {"id": "pet-simulator-99", "name": "Pet Simulator 99", "url": "https://pet-simulator-99.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "blade-ball", "name": "Blade Ball", "url": "https://blade-ball.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "all-star-tower-defense", "name": "All Star Tower Defense", "url": "https://allstartowerdefense.fandom.com/api.php?action=parse&page=Codes&format=json"},
    {"id": "bedwars", "name": "BedWars", "url": "https://robloxbedwars.fandom.com/api.php?action=parse&page=Codes&format=json"},

    # Strategy & Resources (6 ألعاب)
    {"id": "whiteout-survival", "name": "Whiteout Survival", "url": "https://whiteout-survival.fandom.com/api.php?action=parse&page=Gift_Codes&format=json"},
    {"id": "state-of-survival", "name": "State of Survival", "url": "https://state-of-survival.fandom.com/api.php?action=parse&page=Gift_Codes&format=json"},
    {"id": "rise-of-kingdoms", "name": "Rise of Kingdoms", "url": "https://riseofkingdoms.fandom.com/api.php?action=parse&page=Redeem_Codes&format=json"},
    {"id": "raid-shadow-legends", "name": "Raid: Shadow Legends", "url": "https://raid-shadow-legends.fandom.com/api.php?action=parse&page=Promo_Codes&format=json"},
    {"id": "lords-mobile", "name": "Lords Mobile", "url": "https://lordsmobile.fandom.com/api.php?action=parse&page=Redeem_Codes&format=json"},
    {"id": "clash-of-clans", "name": "Clash of Clans", "url": "https://clashofclans.fandom.com/api.php?action=parse&page=Voucher_Codes&format=json"},

    # Sports & Fast Pace (6 ألعاب)
    {"id": "ea-sports-fc-mobile", "name": "EA Sports FC Mobile", "url": "https://www.reddit.com/r/FCMobile/new.json?limit=10"},
    {"id": "nba-2k", "name": "NBA 2K", "url": "https://nba2k.fandom.com/api.php?action=parse&page=Locker_Codes&format=json"},
    {"id": "rocket-league", "name": "Rocket League", "url": "https://rocketleague.fandom.com/api.php?action=parse&page=Promo_Codes&format=json"},
    {"id": "mlbb", "name": "Mobile Legends: Bang Bang", "url": "https://mobile-legends.fandom.com/api.php?action=parse&page=Redeem_Codes&format=json"},
    {"id": "brawl-stars", "name": "Brawl Stars", "url": "https://brawlstars.fandom.com/api.php?action=parse&page=Voucher_Codes&format=json"},
    {"id": "clash-royale", "name": "Clash Royale", "url": "https://clashroyale.fandom.com/api.php?action=parse&page=Voucher_Codes&format=json"}
]

def fetch_raw_data(game_url):
    raw_content = ""
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(game_url, headers=headers, timeout=10)
        if res.status_code == 200:
            raw_content = res.text
    except Exception:
        pass

    if not raw_content and CF_WORKER_URL and CF_WORKER_SECRET:
        try:
            proxy_url = f"{CF_WORKER_URL}/proxy?url={requests.utils.quote(game_url)}"
            proxy_headers = {"X-Worker-Auth": CF_WORKER_SECRET, "User-Agent": USER_AGENT}
            res = requests.get(proxy_url, headers=proxy_headers, timeout=12)
            if res.status_code == 200:
                raw_content = res.text
        except Exception:
            pass

    if not raw_content:
        return ""

    if "fandom.com/api.php" in game_url:
        try:
            data = json.loads(raw_content)
            if "parse" in data and "text" in data["parse"]:
                html_text = data["parse"]["text"]["*"]
                clean_text = re.sub(r'<[^>]+>', ' ', html_text)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                return clean_text
        except Exception:
            pass

    return raw_content

def extract_relevant_sections(text):
    """استخراج الأسطر المحتوية على أكواد وجوائز وتقليل الحشو"""
    lines = text.split('.')
    relevant = [line for line in lines if any(k in line.lower() for k in ['code', 'redeem', 'gift', 'reward', 'active', 'free', 'key'])]
    extracted = ". ".join(relevant)
    return extracted[:4000] if extracted else text[:4000]

def parse_json_from_text(text):
    if not text:
        return {}
    cleaned_text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r'```\s*', '', cleaned_text)
    try:
        match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"⚠️ JSON Parse Error: {e}")
    return {}

def extract_codes_with_ai(prompt):
    # 1. Cloudflare Worker AI (المحاولة الأولى)
    if CF_WORKER_URL and CF_WORKER_SECRET:
        try:
            url = f"{CF_WORKER_URL}/ai-extract"
            headers = {"X-Worker-Auth": CF_WORKER_SECRET, "Content-Type": "application/json"}
            payload = {"prompt": prompt}
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                content = res.json().get('response', '')
                result = parse_json_from_text(str(content))
                if result: return result
            else:
                print(f"❌ Worker Status {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"❌ Worker AI Exception: {e}")

    # 2. Groq AI (المحاولة الثانية الاحتياطية)
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                content = res.json()['choices'][0]['message']['content']
                result = parse_json_from_text(content)
                if result: return result
        except Exception as e:
            print(f"⚠️ Groq failed: {e}")

    # 3. Gemini AI (المحاولة الثالثة الاحتياطية)
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                content = res.json()['candidates'][0]['content']['parts'][0]['text']
                result = parse_json_from_text(content)
                if result: return result
        except Exception as e:
            print(f"⚠️ Gemini failed: {e}")

    return {}

def merge_and_save_codes(existing_db, new_data):
    for game_id, codes in new_data.items():
        if not isinstance(codes, list):
            continue
        
        current_codes = existing_db.get(game_id, [])
        existing_strings = {c['code'] for c in current_codes if isinstance(c, dict) and 'code' in c}
        
        updated_list = list(current_codes)
        for item in codes:
            code_str, reward_str = "", "Free Reward"

            if isinstance(item, str):
                code_str = item.strip().upper()
            elif isinstance(item, dict):
                code_str = str(item.get('code', '')).strip().upper()
                reward_str = item.get('reward', 'Free Reward')

            if code_str and code_str not in existing_strings:
                updated_list.insert(0, {
                    "code": code_str,
                    "reward": reward_str,
                    "added_at": time.strftime("%Y-%m-%d")
                })
                existing_strings.add(code_str)

        existing_db[game_id] = updated_list[:MAX_CODES_PER_GAME]
        
    return existing_db

def main():
    codes_db = {}
    hashes_db = {}
    
    if os.path.exists("codes.json"):
        with open("codes.json", "r", encoding="utf-8") as f:
            try: codes_db = json.load(f)
            except: codes_db = {}

    if os.path.exists("cache_hashes.json"):
        with open("cache_hashes.json", "r", encoding="utf-8") as f:
            try: hashes_db = json.load(f)
            except: hashes_db = {}

    print(f"🚀 Processing {len(GAMES_CONFIG)} games individually...")

    for index, game in enumerate(GAMES_CONFIG, start=1):
        raw_text = fetch_raw_data(game['url'])
        if not raw_text:
            print(f"[{index}/{len(GAMES_CONFIG)}] ⚠️ Could not fetch data for {game['name']}")
            continue
        
        current_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
        if hashes_db.get(game['id']) == current_hash:
            print(f"[{index}/{len(GAMES_CONFIG)}] ⚡ Skipping {game['name']} (No changes)")
            continue

        relevant_text = extract_relevant_sections(raw_text)
        
        prompt = (
            f"Extract active promo/gift codes for the game '{game['id']}' from this text.\n"
            'Return ONLY JSON format: {"' + game['id'] + '": [{"code": "CODEHERE", "reward": "REWARDHERE"}]}\n'
            f"Text:\n{relevant_text}"
        )
        
        print(f"[{index}/{len(GAMES_CONFIG)}] 🤖 Processing {game['name']} via AI...")
        extracted_json = extract_codes_with_ai(prompt)
        
        if extracted_json:
            codes_db = merge_and_save_codes(codes_db, extracted_json)
            hashes_db[game['id']] = current_hash
            print(f"[{index}/{len(GAMES_CONFIG)}] ✅ Successfully extracted codes for {game['name']}")
        else:
            print(f"[{index}/{len(GAMES_CONFIG)}] ⚠️ No codes extracted for {game['name']}")

        time.sleep(1)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(codes_db, f, ensure_ascii=False, indent=2)

    with open("cache_hashes.json", "w", encoding="utf-8") as f:
        json.dump(hashes_db, f, ensure_ascii=False, indent=2)

    print("✅ All Games Processed Successfully!")

if __name__ == "__main__":
    main()

