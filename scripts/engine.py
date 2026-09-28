import glob
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

# تفعيل الطباعة اللحظية الفورية على السيرفر (GitHub Actions)
sys.stdout.reconfigure(line_buffering=True)

# استيراد مكتبة الذكاء الاصطناعي
try:
    from llama_cpp import Llama

    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

# الكلمات المفتاحية لملاحظة الأقسام المنتهية (مقارنة حساسة للكلمة وتعمل مع الحروف الصغيرة دائماً)
EXPIRED_KEYWORDS = [
    "expired",
    "outdated",
    "past codes",
    "inactive",
    "old codes",
    "منتهية",
    "غير شغالة",
]

# تحميل نموذج الذكاء الاصطناعي محلياً
llm = None
if HAS_LLAMA:
    print(
        "🤖 [الذكاء الاصطناعي]: جاري تحميل النموذج في الذاكرة...", flush=True
    )
    llm = Llama.from_pretrained(
        repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
        filename="*Q4_K_M.gguf",
        verbose=False,
        n_ctx=2048,
    )


def extract_game_raw_data(config):
    """سحب النصوص والجداول اعتماداً حصرياً على الـ Regex والكلمات المستبعدة المحددة في ملف اللعبة"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    raw_items = []

    # 1. جلب الـ Regex المحدد داخل ملف اللعبة (مع إجبار عدم التأثر بالحروف الكبيرة/الصغيرة)
    regex_str = config.get("regex_pattern", r"\b[A-Za-z0-9_\-]{4,25}\b")
    regex = re.compile(regex_str, re.IGNORECASE)

    # 2. جلب قائمة الكلمات المستبعدة المحددة في ملف اللعبة فقط (تحويلها للحروف الكبيرة لتوحيد المقارنة)
    custom_junk_words = config.get("custom_junk_words", [])
    junk_words = set(w.upper() for w in custom_junk_words)

    for url in config.get("sources", []):
        try:
            print(f"  🔗 [فحص الرابط]: {url}", flush=True)
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code != 200:
                print(
                    f"  ⚠️ [فشل الاتصال]: كود الاستجابة {res.status_code}",
                    flush=True,
                )
                continue

            soup = BeautifulSoup(res.text, "html.parser")

            # أ. سحب الجداول مع تجارب تجاهل الأقسام المنتهية (Case-Insensitive)
            tables = soup.find_all("table")
            for table in tables:
                parent_text = (
                    table.parent.text.lower() if table.parent else ""
                )
                if any(exp in parent_text for exp in EXPIRED_KEYWORDS):
                    continue

                for row in table.find_all("tr"):
                    cols = [
                        c.text.strip()
                        for c in row.find_all(["td", "th"])
                        if c.text.strip()
                    ]
                    if cols:
                        row_str = " | ".join(cols)
                        if regex.search(row_str):
                            raw_items.append(row_str)

            # ب. استبعاد عناوين الأقسام المنتهية
            for expired_elem in soup.find_all(
                ["h1", "h2", "h3", "h4", "div", "p"]
            ):
                if any(
                    exp in expired_elem.text.lower() for exp in EXPIRED_KEYWORDS
                ):
                    expired_elem.decompose()

            # ج. سحب القوائم والفقرات النصية
            blocks = soup.find_all(["li", "p", "div", "code", "span", "strong"])
            for block in blocks:
                text = block.text.strip()
                matches = regex.findall(text)
                for match in matches:
                    # فحص الكلمة مقابل قائمة الكلمات المستبعدة الخاصة باللعبة بالحروف الكبيرة
                    if match.upper() not in junk_words and not match.isdigit():
                        raw_items.append(text)
                        break

        except Exception as e:
            print(f"  ⚠️ [خطأ أثناء قراءة الرابط]: {e}", flush=True)

    unique_raw = list(set(raw_items))[:35]
    return unique_raw


def sanitize_and_structure_with_ai(game_name, raw_candidates):
    """فلترة وتنقِية البيانات بواسطة الذكاء الاصطناعي"""
    if not raw_candidates:
        return []

    if not llm:
        print(
            "  ⚠️ [تنبيه]: نموذج الذكاء الاصطناعي غير متوفر، سيتم اعتماد الفلترة الأساسية.",
            flush=True,
        )
        fallback_codes = []
        for text in raw_candidates:
            words = text.split("|")
            code = words[0].strip()
            fallback_codes.append(
                {
                    "code": code,
                    "reward": words[1].strip() if len(words) > 1 else None,
                    "server": None,
                    "expiry": None,
                    "status": "شغال",
                }
            )
        return fallback_codes

    prompt = f"""[INST] You are an expert data sanitization engine for gaming platforms.
Analyze the following raw scraped data lines for the game "{game_name}":
{json.dumps(raw_candidates, ensure_ascii=False)}

Your Task:
1. Identify and extract ONLY valid, active promo/redeem codes for "{game_name}".
2. Filter out false positive English words, website titles, code labels, and broken strings.
3. Extract rewards, server restriction, and expiration dates if present in the line.
4. Output STRICTLY a valid JSON array of objects with keys: "code", "reward", "server", "expiry", "status".
5. Set "status" to "شغال" for all valid codes. If reward/server/expiry is missing, set its value to null.

JSON Output Example:
[
  {{"code": "WOS0812", "reward": "100 Gems", "server": null, "expiry": "2026-12-31", "status": "شغال"}},
  {{"code": "JULHD2026JP", "reward": null, "server": "Japan", "expiry": null, "status": "شغال"}}
]

Do not include any intro, markdown tags (like ```json), or explanatory text. Strictly output JSON array.
[/INST]"""

    try:
        response = llm(prompt, max_tokens=1200, temperature=0.1)
        output_text = response["choices"][0]["text"].strip()

        # إزالة وسوم الكود
        output_text = re.sub(r"^```json\s*", "", output_text, flags=re.IGNORECASE)
        output_text = re.sub(r"\s*```$", "", output_text)

        cleaned_data = json.loads(output_text)
        return cleaned_data if isinstance(cleaned_data, list) else []
    except Exception as e:
        print(
            f"  ❌ [خطأ معالجة الذكاء الاصطناعي]: {e}", flush=True
        )
        return []


def is_game_data_changed(game_id, new_codes, output_dir="public/data/games"):
    """مقارنة بيانات اللعبة الجديدة بالبيانات القديمة المرفوعة"""
    file_path = os.path.join(output_dir, f"{game_id}.json")

    if not os.path.exists(file_path):
        return True

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)

        old_codes = old_data.get("codes", [])

        if len(old_codes) != len(new_codes):
            return True

        old_str = json.dumps(old_codes, sort_keys=True, ensure_ascii=False)
        new_str = json.dumps(new_codes, sort_keys=True, ensure_ascii=False)

        return old_str != new_str

    except Exception:
        return True


def generate_global_games_index(
    output_dir="public/data/games", index_path="public/data/games_index.json"
):
    """تحديث ملف الفهرس المستقل الخاص بالأزرار"""
    index_list = []

    if os.path.exists(output_dir):
        for file_name in sorted(os.listdir(output_dir)):
            if file_name.endswith(".json") and file_name != "games_index.json":
                file_path = os.path.join(output_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        index_list.append(
                            {
                                "game_id": data.get("game_id"),
                                "game_name": data.get("game_name"),
                                "total_codes": data.get("total_codes", 0),
                            }
                        )
                except Exception:
                    continue

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_list, f, ensure_ascii=False, indent=4)

    print(
        f"\n✨ [تم الفهرسة]: تم تحديث ملف الأزرار الرئيسي ({index_path}) وإضافة {len(index_list)} لعبة.",
        flush=True,
    )


def run_master_engine():
    """تشغيل المحرك التنفيذي للعمل على كافة ملفات الإعدادات بالتوالي"""
    config_files = glob.glob("config/games/*.json")
    output_dir = "public/data/games"
    os.makedirs(output_dir, exist_ok=True)

    print(
        f"==================================================", flush=True
    )
    print(
        f"🚀 [بدء المنظومة]: معالجة {len(config_files)} لعبة بالتوالي...",
        flush=True,
    )
    print(
        f"==================================================\n", flush=True
    )

    for config_file in config_files:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                game_config = json.load(f)

            game_id = game_config.get("game_id")
            game_name = game_config.get("game_name")

            print(
                f"🎮 [بدء معالجة اللعبة]: {game_name} ({game_id})", flush=True
            )

            # 1. سحب البيانات الخام
            raw_data = extract_game_raw_data(game_config)
            print(
                f"  🔍 [استخراج خام]: تم العثور على {len(raw_data)} عنصر مرشح.",
                flush=True,
            )

            # 2. التنقية بالذكاء الاصطناعي
            clean_codes = sanitize_and_structure_with_ai(game_name, raw_data)
            print(
                f"  🤖 [تنقية الذكاء الاصطناعي]: أقرّ {len(clean_codes)} كود صالح.",
                flush=True,
            )

            # 3. فحص التغييرات وحذف القديم/رفع الجديد عند الاختلاف فقط
            if is_game_data_changed(game_id, clean_codes, output_dir):
                file_path = os.path.join(output_dir, f"{game_id}.json")

                if os.path.exists(file_path):
                    os.remove(file_path)

                payload = {
                    "game_id": game_id,
                    "game_name": game_name,
                    "total_codes": len(clean_codes),
                    "codes": clean_codes,
                }

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=4)

                print(
                    f"  ✅ [تحديث الملف]: تم حذف القديم ورفع الملف الجديد: {file_path}\n",
                    flush=True,
                )
            else:
                print(
                    f"  ⏸️ [تطابق تام]: البيانات مطابقة للملف المرفوع سابقاً. تم التجاوز بدون تغيير.\n",
                    flush=True,
                )

        except Exception as e:
            print(
                f"  ❌ [خطأ في اللعبة {config_file}]: {e}\n", flush=True
            )

    # 4. بناء وتحديث ملف فهرس الأزرار النهائي
    generate_global_games_index(output_dir)


if __name__ == "__main__":
    run_master_engine()
