# config.py - إعدادات الألعاب الـ 5 الأكثر بحثاً وقنوات تليجرام وديسكورد

GAMES_CONFIG = {
    "bloxfruits": {
        "name": "Blox Fruits (Roblox)",
        "category": "Roblox",
        "regex": r"^[A-Za-z0-9_]{4,20}$",
        "fandom_wiki": "https://bloxfruits.fandom.com/api.php?action=parse&page=Codes&format=json",
        "reddit_url": "https://www.reddit.com/r/bloxfruits/new.json?limit=10"
    },
    "genshin": {
        "name": "Genshin Impact",
        "category": "Gacha",
        "regex": r"^[A-Z0-9]{10,12}$",
        "fandom_wiki": "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&format=json",
        "reddit_url": "https://www.reddit.com/r/Genshin_Impact/new.json?limit=10"
    },
    "honkaistarrail": {
        "name": "Honkai: Star Rail",
        "category": "Gacha",
        "regex": r"^[A-Z0-9]{10,12}$",
        "fandom_wiki": "https://honkai-star-rail.fandom.com/api.php?action=parse&page=Redemption_Code&format=json",
        "reddit_url": "https://www.reddit.com/r/HonkaiStarRail/new.json?limit=10"
    },
    "nba2k": {
        "name": "NBA 2K (Locker Codes)",
        "category": "Sports",
        "regex": r"^[A-Z0-9]{3,8}(-[A-Z0-9]{3,8}){1,3}$",
        "fandom_wiki": "https://nba2k.fandom.com/api.php?action=parse&page=Locker_Codes&format=json",
        "reddit_url": "https://www.reddit.com/r/NBA2k/new.json?limit=10"
    },
    "pokemongo": {
        "name": "Pokémon GO",
        "category": "Mobile AR",
        "regex": r"^[A-Za-z0-9]{12,16}$",
        "fandom_wiki": "https://pokemongo.fandom.com/api.php?action=parse&page=Promo_Codes&format=json",
        "reddit_url": "https://www.reddit.com/r/TheSilphRoad/new.json?limit=10"
    }
}

# قنوات تليجرام المستهدفة
TARGET_TELEGRAM_CHANNELS = [
    '@GenshinImpactCodes',
    '@BloxFruitsOfficialCodes',
    '@FreeFireCodesGlobal',
    '@pubg_codes_best'
]

# معرفات قنوات ديسكورد المستهدفة (ضع أرقام Channel IDs هنا)
TARGET_DISCORD_CHANNELS = [
    123456789012345678,
    987654321098765432
]

GLOBAL_BLACKLIST = {
    "EXPIRED", "WORKING", "NEW", "CODES", "CODE", "REDEEM", "FREE", "UPDATE",
    "DISCORD", "TWITTER", "YOUTUBE", "TIKTOK", "TELEGRAM", "LINK", "CLICK",
    "HERE", "GIFT", "REWARDS", "GEMS", "COINS", "SUBSCRIBE", "LIKE", "SHARE",
    "HTTP", "HTTPS", "WWW", "COM", "HTML", "SCRIPT", "VAR", "CONST", "LET",
    "FUNCTION", "CLASS", "IMPORT", "SELECT", "DIV", "SPAN", "HREF", "SRC",
    "NULL", "UNDEFINED", "TRUE", "FALSE", "SERVER", "ADMIN", "STATUS", "INFO"
}

NOISE_CHARACTERS = r"[\"'\<\>\{\}\[\]\(\)\*\#\!\@\$\%\^\&\=\+\|\;\:\,\?\`~\\]"

