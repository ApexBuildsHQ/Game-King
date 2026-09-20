# main.py

import json
import re
import urllib.request
from bs4 import BeautifulSoup

from config.games_config import GAMES_CONFIG
from utils.validator import extract_code_with_fallback

# جلب أحدث 12 كود شغال فقط لكل لعبة
TOP_CODES_LIMIT = 12

# الأنماط الشاملة لصفحات Fandom
GLOBAL_PAGE_PATTERNS = [
    "Promotional_Code",
    "Promotional_Codes",
    "Codes",
    "Redeem_Codes",
    "Redemption_Code",
    "Redemption_Codes",
    "Gift_Codes",
    "Coupon_Codes",
    "Locker_Codes",
    "Promo_Codes",
]

# قائمة بالكلمات الإنجليزية العامة المحظور استخراجها كأكواد
JUNK_WORDS_BLACKLIST = {
    "INVENTORY",
    "MECHANICS",
    "CURRENCIES",
    "WIKI",
    "RARITIES",
    "OTHER",
    "MISCELLANEOUS",
    "RULES",
    "STAFF",
    "UPDATES",
    "SERVERS",
    "MESSAGES",
    "CODES",
    "GUIDE",
    "DETAILS",
    "ACTIVE",
    "EXPIRED",
    "REWARDS",
    "STATUS",
    "NOTES",
    "ITEM",
}


def fetch_page_html(subdomain, custom_page=None):
    """جلب محتوى الصفحة ذكياً باستخدام الصفحة المخصصة أولاً ثم القائمة العامة"""
    patterns_to_try = []
    if custom_page:
        patterns_to_try.append(custom_page)

    for pattern in GLOBAL_PAGE_PATTERNS:
        if pattern not in patterns_to_try:
            patterns_to_try.append(pattern)

    for pattern in patterns_to_try:
        url = f"https://{subdomain}.fandom.com/api.php?action=parse&page={pattern}&format=json"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                if "parse" in data and "text" in data["parse"]:
                    return data["parse"]["text"]["*"]
        except Exception:
            continue
    return None


def is_expired_section(table_element):
    """التحقق مما إذا كان الجدول يقع تحت قسم الأكواد المنتهية (Expired/Inactive)"""
    prev = table_element.find_previous(["h2", "h3", "h4", "span"])
    while prev:
        prev_text = prev.text.lower()
        if any(
            word in prev_text
            for word in ["expired", "inactive", "old", "past", "history"]
        ):
            return True
        if any(
            word in prev_text
            for word in ["active", "working", "current", "new", "latest"]
        ):
            return False
        prev = prev.find_previous(["h2", "h3", "h4", "span"])
    return False


def extract_clean_data(html_content, game_rules):
    """تحليل الجداول الذكي مع تصفية الكلمات العامة والأكواد المنتهية"""
    soup = BeautifulSoup(html_content, "html.parser")
    extracted = []

    for table in soup.find_all("table"):
        # تجاوز جداول الأكواد المنتهية أو الأرشيفية
        if is_expired_section(table):
            continue

        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue

            # البحث عن الكود في الخلية الأولى أو الثانية لتفادي اختلاف الهيكل
            raw_code_cell = cols[0].text.strip()
            code = extract_code_with_fallback(raw_code_cell, game_rules)

            if not code and len(cols) > 1:
                raw_code_cell = cols[1].text.strip()
                code = extract_code_with_fallback(raw_code_cell, game_rules)

            if code:
                # تصفية الكلمات الإنجليزية القمامة (Blacklist)
                if code.upper() in JUNK_WORDS_BLACKLIST:
                    continue

                # استخراج المكافآت وتنسيق النطاق
                rewards_raw = (
                    cols[2].text.strip()
                    if len(cols) >= 3
                    else (
                        cols[1].text.strip()
                        if len(cols) >= 2
                        else "مكافأة داخل اللعبة"
                    )
                )
                rewards_clean = re.sub(r"\[\d+\]", "", rewards_raw).strip()

                duration_raw = (
                    cols[-1].text.strip() if len(cols) >= 4 else ""
                )
                duration_clean = re.sub(
                    r"\[\d+\]", "", duration_raw
                ).strip()

                # التحقق المباشر من الصلاحية داخل الخلية
                is_expired = any(
                    word in (duration_clean + raw_code_cell).lower()
                    for word in ["expired", "inactive", "منتهي"]
                )

                if is_expired:
                    continue

                final_code = (
                    code
                    if game_rules.get("case_sensitive")
                    else code.upper()
                )

                extracted.append(
                    {
                        "code": final_code,
                        "rewards": rewards_clean,
                        "status": "شغال",
                        "raw_duration": (
                            duration_clean if duration_clean else "غير محدد"
                        ),
                    }
                )

    # إزالة التكرار مع الحفاظ على الترتيب الأصلي (الأحدث أولاً)
    unique_list = []
    seen = set()
    for item in extracted:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_list.append(item)

    # تحديد أحدث 12 كود فقط
    return unique_list[:TOP_CODES_LIMIT]


if __name__ == "__main__":
    final_output = {}

    for game_name, rules in GAMES_CONFIG.items():
        print(f"📡 جاري معالجة لعبة: {game_name}...")
        html = fetch_page_html(
            subdomain=rules["subdomain"],
            custom_page=rules.get("fandom_page"),
        )

        if html:
            codes_data = extract_clean_data(html, rules)
            final_output[game_name] = codes_data
            print(f"✅ تم سحب {len(codes_data)} كود شغال ومفلتر بنجاح.")
        else:
            print(f"⚠️ لم يتم العثور على صفحة الأكواد لـ {game_name}")

    with open("clean_codes.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(
        "\n🎉 اكتمل السحب بنجاح وحُفظت كافة البيانات المفلترة في codes.json"
    )

