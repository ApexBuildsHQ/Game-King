# config/games_config.py

GAMES_CONFIG = {
    # 1. Genshin Impact
    "Genshin Impact": {
        "subdomain": "genshin-impact",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{10,15}$",
        "examples": ["GENSHINGIFT", "NS3T9355M523", "WTDA923592"],
    },
    # 2. Honkai Star Rail
    "Honkai Star Rail": {
        "subdomain": "honkai-star-rail",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{8,12}$",
        "examples": ["2T7BP49K1559", "STARRAILGIFT", "MSDA245598"],
    },
    # 3. Blox Fruits
    "Blox Fruits": {
        "subdomain": "blox-fruits",
        "case_sensitive": True,
        "require_numbers": False,
        "regex_pattern": r"^[A-Za-z0-9_]{3,30}$",
        "examples": [
            "BIGNEWS",
            "Sub2OfficialNoobie",
            "KITT_RESET",
            "fudd10_v2",
        ],
    },
    # 4. Zenless Zone Zero
    "Zenless Zone Zero": {
        "subdomain": "zenless-zone-zero",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
        "examples": ["ZENLESSGIFT", "ZZZFREE100", "404NOTFOUND"],
    },
    # 5. Wuthering Waves
    "Wuthering Waves": {
        "subdomain": "wutheringwaves",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
        "examples": ["WUTHERINGGIFT", "BLACKSHORES", "WUTHERING2024"],
    },
    # 6. Whiteout Survival (تم تصحيح subdomain وإضافة توجيه مباشر)
    "Whiteout Survival": {
        "subdomain": "whiteoutsurvival",
        "case_sensitive": False,
        "require_numbers": True,
        "regex_pattern": r"^[A-Za-z0-9]{5,15}$",
        "examples": ["WOS0213", "g4S9d1", "STATE500"],
    },
    # 7. Solo Leveling Arise (إضافة توجيه مباشر للصفحة)
    "Solo Leveling Arise": {
        "subdomain": "solo-leveling-arise",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9_]{5,20}$",
        "examples": ["WORLD1STLEVELUP", "THXSLARISE", "SOLOLEVELING_0508"],
    },
    # 8. Cookie Run: Kingdom
    "Cookie Run Kingdom": {
        "subdomain": "cookierunkingdom",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9\-]{6,20}$",
        "examples": [
            "WELCOMETOKINGDOM",
            "CRK1STBIRTHDAYD1",
            "KINGDOMWITHSONIC",
        ],
    },
    # 9. Tower of Fantasy
    "Tower of Fantasy": {
        "subdomain": "toweroffantasy",
        "case_sensitive": False,
        "require_numbers": False,
        "regex_pattern": r"^[A-Z0-9]{6,15}$",
        "examples": ["TOF2NDANNIVERSARY", "TOF1STANNIVERSARY", "TOF373"],
    },
    # 10. AFK Arena
    "AFK Arena": {
        "subdomain": "afk-arena",
        "case_sensitive": False,
        "require_numbers": True,
        "regex_pattern": r"^[A-Za-z0-9]{6,15}$",
        "examples": ["afk888", "mise2266qa", "uf4shruchf"],
    },
}

