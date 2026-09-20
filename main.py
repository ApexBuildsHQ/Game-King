# main.py

import json
import re
import urllib.request
from bs4 import BeautifulSoup

from config.games_config import GAMES_CONFIG
from utils.validator import extract_code_with_fallback

# القائمة الشاملة لجميع أنماط تسميات صفحات الأكواد في الفاندوم
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


def fetch_page_html(subdomain, custom_page=None):
    """
    جلب محتوى الصفحة عبر API الفاندوم:
    يجرب الصفحة المخصصة المحددة في إعدادات اللعبة أولاً،
    ثم يجرب القائمة العامة للأنماط المتبقية كبديل (Fallback).
    """
    patterns_to_try = []

    # 1. إذا تم تحديد صفحة مخصصة للعبة في GAMES_CONFIG، نضعها في المقدمة لتسريع السحب
    if custom_page:
        patterns_to_try.append(custom_page)

    # 2. إضافة بقية الأنماط الشائعة لتفادي التكرار وضمان العثور على الصفحة
    for pattern in GLOBAL_PAGE_PATTERNS:
        if pattern not in patterns_to_try:
            patterns_to_try.append(pattern)

    # 3. محاولة السحب عبر API الفاندوم
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


def extract_clean_data(html_content, game_rules):
    """تحليل الجداول واستخراج (الكود، المكافأة، الحالة، وتاريخ الصلاحية)"""
    soup = BeautifulSoup(html_content, "html.parser")
    extracted = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue

            raw_code_cell = cols[0].text.strip()

            # استخراج الكود النقي عبر المحرك المطور
            code = extract_code_with_fallback(raw_code_cell, game_rules)

            if code:
                # 1. استخراج المكافآت (تأخذ الخلية الثالثة أو الثانية إذا لم تتوفر)
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

                # 2. استخراج تاريخ/مدة الصلاحية (الخلية الأخيرة)
                duration_raw = (
                    cols[-1].text.strip() if len(cols) >= 4 else ""
                )
                duration_clean = re.sub(
                    r"\[\d+\]", "", duration_raw
                ).strip()

                # 3. تحديد حالة الكود بناءً على محتوى الخلية
                is_expired = (
                    "Expired" in duration_clean
                    or "Expired" in raw_code_cell
                    or "Inactive" in duration_clean
                )
                status = "منتهي" if is_expired else "شغال"

                # ضبط حالة الأحرف
                final_code = (
                    code
                    if game_rules.get("case_sensitive")
                    else code.upper()
                )

                extracted.append(
                    {
                        "code": final_code,
                        "rewards": rewards_clean,
                        "status": status,
                        "raw_duration": (
                            duration_clean if duration_clean else "غير محدد"
                        ),
                    }
                )

    # إزالة التكرار مع الحفاظ على الأحدث
    unique_list = []
    seen = set()
    for item in extracted:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_list.append(item)

    return unique_list


if __name__ == "__main__":
    final_output = {}

    for game_name, rules in GAMES_CONFIG.items():
        print(f"📡 جاري معالجة لعبة: {game_name}...")

        # تمرير subdomain وصفحة fandom_page المخصصة إن وجدت
        html = fetch_page_html(
            subdomain=rules["subdomain"],
            custom_page=rules.get("fandom_page"),
        )

        if html:
            codes_data = extract_clean_data(html, rules)
            final_output[game_name] = codes_data
            print(
                f"✅ تم سحب {len(codes_data)} كود ببياناتهم الكاملة بنجاح."
            )
        else:
            print(f"⚠️ لم يتم العثور على صفحة الأكواد لـ {game_name}")

    # حفظ البيانات الكاملة في ملف JSON
    with open("clean_codes.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(
        "\n🎉 اكتمل السحب بنجاح وحُفظت كافة البيانات في clean_codes.json"
    )

