# main.py

import json
import re
import urllib.request
from bs4 import BeautifulSoup

from config.games_config import GAMES_CONFIG
from utils.validator import extract_code_with_fallback

TOP_CODES_LIMIT = 12

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
    "TYPE",
    "DESCRIPTION",
    "NAVIGATION",
    "CATEGORY",
}


def fetch_page_html(subdomain, custom_page=None):
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


def is_valid_strict_code(candidate, rules):
    """تحقق صارم إضافي للتأكد من أن الكود ليس كلمة إنجليزية عامة"""
    if not candidate:
        return False

    # 1. التصفية عبر القائمة السوداء
    if candidate.upper() in JUNK_WORDS_BLACKLIST:
        return False

    # 2. إذا كانت اللعبة تشترط وجود أرقام، نتحقق من وجود رقم واحد على الأقل
    if rules.get("require_numbers") and not re.search(r"\d", candidate):
        return False

    # 3. التأكد من انطباق الـ Regex المحدد للعبة
    pattern = rules.get("regex_pattern")
    if pattern and not re.match(pattern, candidate):
        return False

    return True


def extract_clean_data(html_content, game_rules):
    soup = BeautifulSoup(html_content, "html.parser")
    extracted = []

    for table in soup.find_all("table"):
        if is_expired_section(table):
            continue

        # استبعاد رأس الجدول (thead) بالكامل لتجنب قراءة عناوين الأعمدة كأكواد
        rows = table.find_all("tr")
        for row in rows:
            if row.find_parent("thead"):
                continue

            cols = row.find_all(["td", "th"])
            if not cols:
                continue

            code = None
            raw_code_cell = ""
            code_col_index = -1

            for idx, col in enumerate(cols):
                # تجاهل الخلايا التي تعمل كعناوين رئيسية للأنواع داخل الجدول
                if col.name == "th" and len(cols) == 1:
                    continue

                cell_text = col.text.strip()
                potential_code = extract_code_with_fallback(
                    cell_text, game_rules
                )

                if is_valid_strict_code(potential_code, game_rules):
                    code = potential_code
                    raw_code_cell = cell_text
                    code_col_index = idx
                    break

            if code:
                rewards_raw = "مكافأة داخل اللعبة"
                if code_col_index + 1 < len(cols):
                    rewards_raw = cols[code_col_index + 1].text.strip()

                rewards_clean = re.sub(r"\[\d+\]", "", rewards_raw).strip()

                duration_raw = (
                    cols[-1].text.strip() if len(cols) >= 3 else ""
                )
                duration_clean = re.sub(
                    r"\[\d+\]", "", duration_raw
                ).strip()

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
                        "rewards": (
                            rewards_clean
                            if rewards_clean
                            else "مكافأة داخل اللعبة"
                        ),
                        "status": "شغال",
                        "raw_duration": (
                            duration_clean if duration_clean else "غير محدد"
                        ),
                    }
                )

    unique_list = []
    seen = set()
    for item in extracted:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_list.append(item)

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
        "\n🎉 اكتمل السحب بنجاح وحُفظت كافة البيانات المفلترة في clean_codes.json"
    )

