import os
import re
import json
import requests
import urllib.parse
from datetime import datetime

GAME_NAME = "NBA 2K"

# ---------------------------------------------------------
# قائمة الكلمات المستبعدة الضخمة (Blacklist) لـ NBA 2K Locker Codes
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
    "VALID", "INVALID", "UNKNOWN", "VERIFIED", "UNVERIFIED", "LOCKER", "LOCKERCODES",

    # مصطلحات ومكافآت مودات NBA 2K و MyTEAM
    "NBA2K", "MYTEAM", "MYCAREER", "VC", "MTP", "TOKENS", "TOKEN", "PACK", 
    "PACKS", "CARD", "CARDS", "PLAYER", "PLAYERS", "OPAL", "GALAXY", "DARK", 
    "MATTER", "PINK", "DIAMOND", "AMETHYST", "RUBY", "SAPPHIRE", "GOLD", 
    "SILVER", "BRONZE", "EMERALD", "AGENT", "RATING", "SEASON", "CHALLENGE", 
    "DRAFT", "DOMINATION", "TRIPLE", "THREAT", "AUCTION", "SHOES", "BADGE", 
    "BADGES", "CONSUMABLE", "BALL", "DROP", "SPIN", "WHEEL", "BALL_DROP",

    # التواصل الاجتماعي والروابط
    "TWITTER", "DISCORD", "YOUTUBE", "TIKTOK", "REDDIT", "SUBSCRIBE", 
    "SUB", "LIKE", "FOLLOW", "JOIN", "GROUP", "CHANNEL", "SERVER", "LINK", 
    "HTTP", "HTTPS", "WWW", "COM", "URL", "WEB", "SPOTLIGHT", "PROMO",

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
    """استخراج الأكواد المقبولة لـ NBA 2K (تدعم الأكواد المقسمة بشرطات مثل XXX-XXX-XXX)"""
    if not text:
        return []
    
    # regex يستخرج الأكواد التي تحتوي على شرطات (-) أو نصوص ورموز متصلة بطول 6 إلى 30 حرف
    raw_matches = re.findall(r'\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+\b|\b[a-zA-Z0-9_]{6,25}\b', text)
    valid_candidates = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for match in raw_matches:
        upper_match = match.upper().replace("-", "")
        if upper_match not in EXCLUDED_WORDS and not match.isdigit() and len(match) >= 6:
            valid_candidates.append({
                "code": match,
                "date": today_str
            })

    return valid_candidates

def source_fandom_nba2k():
    """المصدر 1: موسوعة NBA 2K Fandom - صفحة Locker Codes الرسمية"""
    url = "https://nba2k.fandom.com/api.php?action=parse&page=Locker_Codes&prop=wikitext&format=json&redirects=1"
    raw_json = fetch_raw_data(url)
    if raw_json:
        try:
            data = json.loads(raw_json)
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            items = extract_candidate_codes(wikitext)
            for item in items:
                item["source"] = "NBA 2K Fandom Wiki"
            return items
        except Exception:
            pass
    return []

def source_fandom_revisions():
    """المصدر 2: سجل التعديلات الحديثة لموسوعة NBA 2K Fandom لجلب التواريخ الدقيقة"""
    url = "https://nba2k.fandom.com/api.php?action=query&prop=revisions&titles=Locker_Codes&rvprop=content|timestamp&format=json&redirects=1"
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
                        item["source"] = "NBA 2K Fandom Revisions"
                    return items
        except Exception:
            pass
    return []

def source_reddit_myteam():
    """المصدر 3: مجتمع Reddit المخصص لمود MyTEAM وأكواد اللعبة r/MyTeam"""
    url = "https://www.reddit.com/r/MyTeam/search.json?q=flair%3ALocker+Code+OR+title%3ALocker+Code&restrict_sr=on&sort=new&limit=15"
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
                    ex["source"] = "Reddit r/MyTeam"
                    items.append(ex)
            return items
        except Exception:
            pass
    return []

def source_reddit_nba2k():
    """المصدر 4: مجتمع Reddit العام للعبة NBA 2K r/NBA2k"""
    url = "https://www.reddit.com/r/NBA2k/search.json?q=title%3ALocker+Code&restrict_sr=on&sort=new&limit=15"
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
                    ex["source"] = "Reddit r/NBA2k"
                    items.append(ex)
            return items
        except Exception:
            pass
    return []

def get_codes():
    all_items = []
    
    # تجميع كافي من كافة المصادر
    all_items.extend(source_fandom_nba2k())
    all_items.extend(source_fandom_revisions())
    all_items.extend(source_reddit_myteam())
    all_items.extend(source_reddit_nba2k())
    
    seen_codes = set()
    unique_items = []
    
    for item in all_items:
        code_key = item["code"].lower()
        if code_key not in seen_codes:
            seen_codes.add(code_key)
            unique_items.append(item)

    return GAME_NAME, unique_items

