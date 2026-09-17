import os
import re
import json
import requests
import urllib.parse
from datetime import datetime

GAME_NAME = "Honkai: Star Rail"

# ---------------------------------------------------------
# قائمة الكلمات المستبعدة الضخمة (Blacklist) لـ Honkai: Star Rail
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
    "VALID", "INVALID", "UNKNOWN", "VERIFIED", "UNVERIFIED", "REDEMPTION",

    # مصطلحات ومكافآت وشخصيات Honkai: Star Rail
    "HONKAI", "STAR", "RAIL", "STARRAIL", "HOYOVERSE", "MIHOYO", "STELLAR", 
    "JADE", "JADES", "CREDIT", "CREDITS", "TRAILBLAZE", "TRAILBLAZER", "EXP", 
    "PASS", "PASSES", "RAIL_PASS", "SPECIAL_PASS", "WARP", "WARPS", "AETHER", 
    "REFINED", "REFINE", "COSMIC", "SIMULATED", "UNIVERSE", "EXPRESS", "ASTRAL", 
    "POMPOM", "MARCH", "DANHENG", "WELT", "HIMEKO", "LIGHT", "CONE", "CONES", 
    "RELIC", "RELICS", "LIVESTREAM", "VERSION", "PATCH", "BANNER", "CHARACTER",

    # التواصل الاجتماعي والروابط
    "TWITTER", "DISCORD", "YOUTUBE", "TIKTOK", "REDDIT", "HOYOLAB", "SUBSCRIBE", 
    "SUB", "LIKE", "FOLLOW", "JOIN", "GROUP", "CHANNEL", "SERVER", "LINK", 
    "HTTP", "HTTPS", "WWW", "COM", "URL", "WEB", "PROGRAM", "SPECIAL",

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

# عناوين الصفحات المحتملة لأكواد اللعبة على Fandom
FANDOM_TARGET_PAGES = ["Redemption_Code", "Promotional_Codes", "Codes"]

def fetch_raw_data(url):
    """دالة جلب عبر البروكسي والطلب المباشر لمنع توقف السكربت"""
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
    """استخراج الأكواد الشائعة لـ Honkai Star Rail (عادة من 8 إلى 16 حرف ورقم)"""
    if not text:
        return []
    
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

def source_fandom_pages():
    """المصدر 1: المرور على كافة عناوين الصفحات المحتملة لموسوعة Honkai: Star Rail Fandom"""
    items = []
    for page_name in FANDOM_TARGET_PAGES:
        url = f"https://honkai-star-rail.fandom.com/api.php?action=parse&page={page_name}&prop=wikitext&format=json&redirects=1"
        raw_json = fetch_raw_data(url)
        if raw_json:
            try:
                data = json.loads(raw_json)
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                extracted = extract_candidate_codes(wikitext)
                if extracted:
                    for item in extracted:
                        item["source"] = f"HSR Fandom ({page_name})"
                    items.extend(extracted)
            except Exception:
                continue
    return items

def source_fandom_revisions():
    """المصدر 2: فحص سجل التعديلات لأحدث تاريخ إضافة كود"""
    items = []
    for page_name in FANDOM_TARGET_PAGES:
        url = f"https://honkai-star-rail.fandom.com/api.php?action=query&prop=revisions&titles={page_name}&rvprop=content|timestamp&format=json&redirects=1"
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

                        extracted = extract_candidate_codes(content)
                        for item in extracted:
                            item["date"] = pub_date
                            item["source"] = "HSR Fandom Revisions"
                        items.extend(extracted)
            except Exception:
                continue
    return items

def source_reddit_hsr():
    """المصدر 3: البحث المباشر في مجتمع Reddit الخاص بـ Honkai Star Rail"""
    url = "https://www.reddit.com/r/HonkaiStarRail/search.json?q=flair%3ACode+OR+title%3ARedeem+OR+title%3ACodes&restrict_sr=on&sort=new&limit=15"
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
                    ex["source"] = "Reddit HSR"
                    items.append(ex)
            return items
        except Exception:
            pass
    return []

def get_codes():
    all_items = []
    
    # تجميع كافي لكافة المصادر
    all_items.extend(source_fandom_pages())
    all_items.extend(source_fandom_revisions())
    all_items.extend(source_reddit_hsr())
    
    seen_codes = set()
    unique_items = []
    
    for item in all_items:
        code_key = item["code"].lower()
        if code_key not in seen_codes:
            seen_codes.add(code_key)
            unique_items.append(item)

    return GAME_NAME, unique_items

