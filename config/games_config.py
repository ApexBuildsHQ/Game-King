# config/games_config.py

GAMES_CONFIG = {
    # 1. Genshin Impact: حروف كبيرة وأرقام فقط (10 إلى 15 خانة)
    "Genshin Impact": {
        "subdomain": "genshin-impact",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{10,15}$",
    },
    # 2. Honkai Star Rail: حروف كبيرة وأرقام فقط (8 إلى 12 خانة)
    "Honkai Star Rail": {
        "subdomain": "honkai-star-rail",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{8,12}$",
    },
    # 3. Blox Fruits: تقبل حروف كبيرة وصغيرة وشرطة سفلية (3 إلى 25 خانة)
    "Blox Fruits": {
        "subdomain": "blox-fruits",
        "case_sensitive": True,
        "require_numbers": False,
        "regex_pattern": r"^[A-Za-z0-9_]{3,25}$",
    },
    # 4. Zenless Zone Zero: حروف كبيرة وأرقام فقط (6 إلى 15 خانة)
    "Zenless Zone Zero": {
        "subdomain": "zenless-zone-zero",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
    },
    # 5. Wuthering Waves: حروف كبيرة وأرقام فقط (6 إلى 15 خانة)
    "Wuthering Waves": {
        "subdomain": "wutheringwaves",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
    },
    # 6. Whiteout Survival: تشترط وجود أرقام داخل الكود (5 إلى 15 خانة)
    "Whiteout Survival": {
        "subdomain": "whiteoutsurvival",
        "case_sensitive": False,
        "require_numbers": True,  # يرفض أي كلمة بدون أرقام
        "regex_pattern": r"^[A-Za-z0-9]{5,15}$",
    },
    # 7. Solo Leveling Arise: حروف كبيرة وأرقام وشرطة سفلية فقط (5 إلى 20 خانة)
    "Solo Leveling Arise": {
        "subdomain": "solo-leveling-arise",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9_]{5,20}$",
    },
    # 8. Cookie Run Kingdom: حروف كبيرة وأرقام وشرطة - فقط (6 إلى 20 خانة)
    "Cookie Run Kingdom": {
        "subdomain": "cookierunkingdom",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9\-]{6,20}$",
    },
    # 9. Tower of Fantasy: حروف كبيرة وأرقام فقط (6 إلى 15 خانة)
    "Tower of Fantasy": {
        "subdomain": "toweroffantasy",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
    },
    # 10. AFK Arena: تشترط وجود أرقام وتقبل حروف صغيرة/كبيرة (6 إلى 15 خانة)
    "AFK Arena": {
        "subdomain": "afk-arena",
        "case_sensitive": False,
        "require_numbers": True,  # يرفض أي كلمة بدون أرقام
        "regex_pattern": r"^[A-Za-z0-9]{6,15}$",
    },
}

