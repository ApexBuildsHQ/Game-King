import os
import re
import json
import requests
import urllib.parse
from datetime import datetime

GAME_NAME = "Blox Fruits"

# ---------------------------------------------------------
# قائمة الكلمات المستبعدة الضخمة (Blacklist) لـ Blox Fruits
# ---------------------------------------------------------
EXCLUDED_WORDS = {
    # كلمات واجهات الموقع والـ Wiki
    "FANDOM", "WIKI", "COMMUNITY", "NAVIGATION", "SEARCH", "LOGIN", "REGISTER", 
    "EDIT", "HISTORY", "DISCUSSION", "TALK", "RECENT", "CHANGES", "RANDOM", 
    "PAGE", "HELP", "DONATE", "CONTENT", "CATEGORIES", "MAIN", "ARTICLE", 
    "POLICY", "TERMS", "PRIVACY", "ABOUT", "CONTACT", "COPYRIGHT", "ALL", 
    "RIGHTS", "RESERVED", "HOME", "VIEW", "SOURCE", "UPDATES", "EXPAND", 
    "COLLAPSE", "TEMPLATE", "CATEGORY", "FILE", "IMAGE", "USER", "PROFILE",
    "HEADER", "FOOTER", "SIDEBAR", "MENU", "REDIRECT", "INDEX", "THUMB",

    # كلمات حالة الكود والأوصاف
    "ACTIVE", "EXPIRED", "WORKING", "REDEEM", "CODES", "CODE", "REWARD", 
    "REWARDS", "FREE", "NEW", "LATEST", "OLD", "STATUS", "TYPE", "DURATION", 
    "NOTE", "NOTES", "DESCRIPTION", "METHOD", "HOW", "TO", "USE", "LIST", 
    "VALID", "INVALID", "UNKNOWN", "VERIFIED", "UNVERIFIED", "WORKING_CODES",

    # كلمات آليات لعبة Blox Fruits وRoblox
    "ROBLOX", "BLOX", "FRUITS", "FRUIT", "BELI", "STAT", "RESET", "STATS", 
    "STAT_RESET", "EXP", "BOOST", "BOOSTS", "RACE", "REROL", "REROLL", 
    "MASTERY", "FRAGMENTS", "TITLE", "LEVEL", "MAX", "SEA", "FIRST", "SECOND", 
    "THIRD", "WORLD", "DEV", "DEVS", "ADMIN", "ADMINS", "UPDATE", "UPDATES", 
    "PATCH", "SERVER", "SERVERS", "VIP", "GAMEPASS", "ITEM", "ITEMS", "SWORD", 
    "MELEE", "GUN", "ACCESSORY", "BOAT", "CREW", "BOUNTY", "HONOR", "INVENTORY",

    # أسماء منصات التواصل ومحتوى السوشيال ميديا
    "TWITTER", "DISCORD", "YOUTUBE", "TIKTOK", "REDDIT", "SUBSCRIBE", "SUB", 
    "LIKE", "FOLLOW", "JOIN", "GROUP", "CHANNEL", "SERVER", "LINK", "HTTP", 
    "HTTPS", "WWW", "COM", "URL", "TWITTER_CODE", "STARCODE", "MEMBER",

    # الأيام والشهور والزمن
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", 
    "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "MONDAY", "TUESDAY", 
    "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "TODAY", 
    "YESTERDAY", "MINUTES", "HOURS", "DAYS", "WEEKS", "MONTHS", "YEARS", 
    "AGO", "AM", "PM", "UTC", "EST", "PST", "GMT", "TIME", "DATE",

    # كلمات إنجليزية عامة وشائعة تظهر في الجداول
    "TABLE", "COLUMN", "ROW", "VALUE", "NONE", "NULL", "TRUE", "FALSE", 
    "YES", "NO", "TOTAL", "CLICK", "HERE", "CHECK", "MORE", "INFO", "GAME", 
    "PLAY", "PLAYER", "PLAYERS", "GAMER", "GAMERS", "ROBLOXIAN", "VERSION"
}

def fetch_raw_data(url):
    """دالة جلب عامة تستخدم البروكسي عند توفره مع التراجع للطلب المباشر"""
    worker_url = os.getenv("WORKER_URL", "")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    if worker_url:
        try:
            proxy_target = f"{worker_url}?url={urllib.parse.quote(url, safe='')}"
            res = requests.get(proxy_target, timeout=12)
            if res.status_code == 200 and res.text.strip():
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

def extract_candidate_codes(text):
    """استخراج الأكواد مع الحفاظ على حالة الأحرف والرموز مثل _"""
    if not text:
        return []
    
    raw_matches = re.findall(r'\b[a-zA-Z0-9_]{4,25}\b', text)
    valid_candidates = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for match in raw_matches:
        upper_match = match.upper()
        if upper_match not in EXCLUDED_WORDS and not match.isdigit() and len(match) >= 4:
            valid_candidates.append({
                "code": match,
                "date": today_str
            })

    return valid_candidates

def source_fandom_main():
    """المصدر 1: موسوعة Blox Fruits Fandom الرسمية مع إعادة التوجيه التلقائي"""
    url = "https://blox-fruits.fandom.com/api.php?action=parse&page=Codes&prop=wikitext&format=json&redirects=1"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            items = extract_candidate_codes(wikitext)
            for item in items:
                item["source"] = "Blox Fruits Fandom Wiki"
            return items
        except Exception:
            pass
    return []

def source_roblox_fandom():
    """المصدر 2: موسوعة Roblox Fandom العامة مع إعادة التوجيه التلقائي"""
    url = "https://roblox.fandom.com/api.php?action=parse&page=Blox_Fruits_Codes&prop=wikitext&format=json&redirects=1"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            items = extract_candidate_codes(wikitext)
            for item in items:
                item["source"] = "Roblox Wiki"
            return items
        except Exception:
            pass
    return []

def source_fandom_recent_revisions():
    """المصدر 3: سجل التعديلات الحديثة لموسوعة Blox Fruits لاستخراج التواريخ والأكواد الجديدة"""
    url = "https://blox-fruits.fandom.com/api.php?action=query&prop=revisions&titles=Codes&rvprop=content|timestamp&format=json&redirects=1"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                revisions = page_data.get("revisions", [])
                if revisions:
                    content = revisions[0].get("*", "")
                    timestamp = revisions[0].get("timestamp", "")
                    
                    pub_date = datetime.now().strftime("%Y-%m-%d")
                    if timestamp:
                        try:
                            pub_date = timestamp.split("T")[0]
                        except Exception:
                            pass

                    items = extract_candidate_codes(content)
                    for item in items:
                        item["date"] = pub_date
                        item["source"] = "Fandom Recent Revision"
                    return items
        except Exception:
            pass
    return []

def get_codes():
    all_items = []
    
    all_items.extend(source_fandom_main())
    all_items.extend(source_roblox_fandom())
    all_items.extend(source_fandom_recent_revisions())
    
    seen_codes = set()
    unique_items = []
    
    for item in all_items:
        code_key = item["code"].lower()
        if code_key not in seen_codes:
            seen_codes.add(code_key)
            unique_items.append(item)

    return GAME_NAME, unique_items

