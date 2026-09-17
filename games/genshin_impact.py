import os
import re
import json
import requests
import urllib.parse
from datetime import datetime

GAME_NAME = "Genshin Impact"

# ---------------------------------------------------------
# قائمة الكلمات المستبعدة الضخمة (Blacklist) لـ Genshin Impact
# ---------------------------------------------------------
EXCLUDED_WORDS = {
    # واجهات الفاندوم والموقع
    "FANDOM", "WIKI", "COMMUNITY", "NAVIGATION", "SEARCH", "LOGIN", "REGISTER", 
    "EDIT", "HISTORY", "DISCUSSION", "TALK", "RECENT", "CHANGES", "RANDOM", 
    "PAGE", "HELP", "DONATE", "CONTENT", "CATEGORIES", "MAIN", "ARTICLE", 
    "POLICY", "TERMS", "PRIVACY", "ABOUT", "CONTACT", "COPYRIGHT", "ALL", 
    "RIGHTS", "RESERVED", "HOME", "VIEW", "SOURCE", "UPDATES", "EXPAND", 
    "COLLAPSE", "TEMPLATE", "CATEGORY", "FILE", "IMAGE", "USER", "PROFILE",
    "HEADER", "FOOTER", "SIDEBAR", "MENU", "REDIRECT", "INDEX", "THUMB",

    # حالة الأكواد والعناوين
    "ACTIVE", "EXPIRED", "WORKING", "REDEEM", "CODES", "CODE", "REWARD", 
    "REWARDS", "FREE", "NEW", "LATEST", "OLD", "STATUS", "TYPE", "DURATION", 
    "NOTE", "NOTES", "DESCRIPTION", "METHOD", "HOW", "TO", "USE", "LIST", 
    "VALID", "INVALID", "UNKNOWN", "VERIFIED", "UNVERIFIED", "PROMOTIONAL",

    # مصطلحات ومكافآت وشخصيات Genshin Impact
    "GENSHIN", "IMPACT", "HOYOVERSE", "MIHOYO", "PRIMOGEMS", "PRIMOGEM", 
    "MORA", "HERO", "HEROS", "WIT", "WITS", "ADVENTURER", "EXPERIENCE", 
    "MYSTIC", "ENHANCEMENT", "ORE", "ORES", "ARCANUM", "FRAGILE", "RESIN", 
    "INTERTWINED", "ACQUAINT", "FATE", "FATES", "STARDUST", "STARGLITTER", 
    "LIVESTREAM", "STREAM", "VERSION", "PATCH", "BANNER", "WISH", "WISHES", 
    "CHARACTER", "WEAPON", "ARTIFACT", "DOMAIN", "SPIRAL", "ABYSS", "TEAVAT", 
    "MONDSTADT", "LIYUE", "INAZUMA", "SUMERU", "FONTAINE", "NATLAN", "SCHNEZNAYA",

    # التواصل الاجتماعي والروابط
    "TWITTER", "DISCORD", "YOUTUBE", "TIKTOK", "REDDIT", "HOYOLAB", "SUBSCRIBE", 
    "SUB", "LIKE", "FOLLOW", "JOIN", "GROUP", "CHANNEL", "SERVER", "LINK", 
    "HTTP", "HTTPS", "WWW", "COM", "URL", "WEB", "SPECIAL", "PROGRAM",

    # الزمان والأيام
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", 
    "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "MONDAY", "TUESDAY", 
    "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "TODAY", 
    "YESTERDAY", "MINUTES", "HOURS", "DAYS", "WEEKS", "MONTHS", "YEARS", 
    "AGO", "AM", "PM", "UTC", "EST", "PST", "GMT", "TIME", "DATE",

    # كلمات إنجليزية عامة
    "TABLE", "COLUMN", "ROW", "VALUE", "NONE", "NULL", "TRUE", "FALSE", 
    "YES", "NO", "TOTAL", "CLICK", "HERE", "CHECK", "MORE", "INFO", "GAME", 
    "PLAY", "PLAYER", "PLAYERS", "GAMER", "GAMERS", "RELEASE", "DETAILS"
}

def fetch_raw_data(url):
    """دالة جلب تستخدم الـ Worker أو الطلب المباشر"""
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
    """استخراج أكواد Genshin Impact القياسية (غالباً 10 إلى 15 حرفاً)"""
    if not text:
        return []
    
    # أكواد قينشن تتكون من أحرف وأرقام كبيرة عادة بحجم بين 8 و 16 حرف
    raw_matches = re.findall(r'\b[a-zA-Z0-9]{8,18}\b', text)
    valid_candidates = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for match in raw_matches:
        upper_match = match.upper()
        if upper_match not in EXCLUDED_WORDS and not match.isdigit():
            valid_candidates.append({
                "code": match,
                "date": today_str
            })

    return valid_candidates

def source_fandom_promotional_codes():
    """المصدر 1: موسوعة Genshin Impact Fandom - صفحة Promotional Code الرئيسية"""
    url = "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&prop=wikitext&format=json&redirects=1"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            items = extract_candidate_codes(wikitext)
            for item in items:
                item["source"] = "Genshin Fandom Main"
            return items
        except Exception:
            pass
    return []

def source_fandom_revisions():
    """المصدر 2: سجل تعديلات موسوعة Genshin الفاندوم لجلب تواريخ الأكواد الجديدة"""
    url = "https://genshin-impact.fandom.com/api.php?action=query&prop=revisions&titles=Promotional_Code&rvprop=content|timestamp&format=json&redirects=1"
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
                        item["source"] = "Genshin Fandom Revisions"
                    return items
        except Exception:
            pass
    return []

def source_reddit_genshin_codes():
    """المصدر 3: تغذية Reddit المفتوحة لقسم أكواد Genshin Impact"""
    url = "https://www.reddit.com/r/Genshin_Impact/search.json?q=flair%3ACode+OR+title%3ARedeem&restrict_sr=on&sort=new&limit=10"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            posts = data.get("data", {}).get("children", [])
            items = []
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "")
                created_utc = post_data.get("created_utc", None)
                
                pub_date = datetime.now().strftime("%Y-%m-%d")
                if created_utc:
                    pub_date = datetime.utcfromtimestamp(created_utc).strftime("%Y-%m-%d")

                extracted = extract_candidate_codes(f"{title} {selftext}")
                for ex in extracted:
                    ex["date"] = pub_date
                    ex["source"] = "Reddit Genshin"
                    items.append(ex)
            return items
        except Exception:
            pass
    return []

def get_codes():
    all_items = []
    
    # تجميع من كافة المصادر
    all_items.extend(source_fandom_promotional_codes())
    all_items.extend(source_fandom_revisions())
    all_items.extend(source_reddit_genshin_codes())
    
    seen_codes = set()
    unique_items = []
    
    for item in all_items:
        code_key = item["code"].lower()
        if code_key not in seen_codes:
            seen_codes.add(code_key)
            unique_items.append(item)

    return GAME_NAME, unique_items

