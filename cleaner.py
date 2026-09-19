# cleaner.py - محرك تنظيف النصوص وإزالة الرموز والكلمات العشوائية

import re
from config import GLOBAL_BLACKLIST, NOISE_CHARACTERS

def clean_code(raw_text: str, regex_pattern: str) -> str | None:
    if not raw_text or not isinstance(raw_text, str):
        return None

    text = re.sub(r'<[^>]+>', '', raw_text)
    text = re.sub(NOISE_CHARACTERS, '', text).strip()

    if any(c in text for c in [' ', '\t', '\n', '\r']):
        return None

    upper_check = text.upper()
    if upper_check in GLOBAL_BLACKLIST or upper_check.startswith(("HTTP", "HTTPS", "WWW", "JSON", "API", "SRC")):
        return None

    match = re.fullmatch(regex_pattern, text)
    if match:
        final_code = match.group(0)
        if final_code.upper() not in GLOBAL_BLACKLIST:
            return final_code

    return None

