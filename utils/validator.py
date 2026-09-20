# utils/validator.py

import re
from config.blacklist import GLOBAL_BLACKLIST


def clean_code_candidate(raw_text):
    """تنظيف النص المبدئي من الأقواس والملاحظات وأزرار النسخ السريع"""
    if not raw_text:
        return ""

    # 1. إزالة أي نص داخل أقواس مثل (NEW) أو [Working] أو {Active}
    cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", "", raw_text)

    # 2. إزالة نصوص أزرار النسخ الملتصقة
    cleaned = re.sub(
        r"(Quick\s*Redeem|Redeem|Copy)", "", cleaned, flags=re.IGNORECASE
    )

    return cleaned.strip()


def validate_game_code(code_candidate, game_rules):
    """فحص الكود بناءً على القواعد العامة وقواعد اللعبة المخصصة"""
    if not code_candidate:
        return False

    clean_code = code_candidate.strip()
    code_upper = clean_code.upper()

    # 1. الاستبعاد بواسطة القائمة السوداء العامة
    if code_upper in GLOBAL_BLACKLIST:
        return False

    # 2. التأكد من الطول القابل للقبول
    if len(clean_code) < 3 or len(clean_code) > 32:
        return False

    # 3. شرط وجود أرقام (إن كانت اللعبة تشترط ذلك)
    if game_rules.get("require_numbers", False):
        if not re.search(r"\d", clean_code):
            return False

    # 4. المطابقة مع التعبير النمطي الخاص باللعبة (Regex Pattern)
    pattern = game_rules.get("regex_pattern", r"^[A-Za-z0-9_\-]+$")
    if not re.match(pattern, clean_code):
        return False

    # 5. استبعاد الكلمات التي تبدأ بروابط أو وسم HTML
    if code_upper.startswith("HTTP") or "<" in clean_code:
        return False

    return True


def extract_code_with_fallback(raw_cell_text, game_rules):
    """الاستخراج الذكي: يحاول استخراج السطر الأول، وإذا فشل يبحث عن نمط الكود داخل الخلية"""
    # المحاولة الأولى: أخذ السطر الأول وتنظيفه
    lines = [
        line.strip() for line in raw_cell_text.split("\n") if line.strip()
    ]
    if lines:
        first_line_cleaned = clean_code_candidate(lines[0])
        if validate_game_code(first_line_cleaned, game_rules):
            return first_line_cleaned

    # المحاولة الثانية (Fallback): البحث بالتعبير النمطي عن الكلمة المطابقة داخل الخلية
    pattern = game_rules.get("regex_pattern", r"[A-Za-z0-9_\-]+")
    matches = re.findall(pattern, raw_cell_text)
    for word in matches:
        word_cleaned = clean_code_candidate(word)
        if validate_game_code(word_cleaned, game_rules):
            return word_cleaned

    return None

