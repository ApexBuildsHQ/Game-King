import glob
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)

try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

# الكلمات المفتاحية الأساسية لملاحظة العناوين والأقسام المنتهية
EXPIRED_KEYWORDS = [
    "expired", "outdated", "past codes", "inactive", 
    "old codes", "منتهية", "غير شغالة", "expired codes"
]

llm = None
if HAS_LLAMA:
    print("🤖 [الذكاء الاصطناعي]: جاري تحميل النموذج في الذاكرة...", flush=True)
    llm = Llama.from_pretrained(
        repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
        filename="*Q4_K_M.gguf",
        verbose=False,
        n_ctx=2048,
    )


def extract_game_raw_data(config):
    """سحب البيانات الخام اعتماداً على مصادر اللعبة مع ربط الأكواد بالسيرفرات المكتوبة خارج الجداول والقوائم"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    raw_items = []
    regex_str = config.get("regex_pattern", r"\b[A-Za-z0-9_\-]{4,25}\b")
    regex = re.compile(regex_str, re.IGNORECASE)

    for url in config.get("sources", []):
        try:
            print(f"  🔗 [فحص الرابط]: {url}", flush=True)
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code != 200:
                print(f"  ⚠️ [فشل الاتصال]: كود الاستجابة {res.status_code}", flush=True)
                continue

            soup = BeautifulSoup(res.text, "html.parser")

            # 1. إزالة وسوم السكريبت والإعلانات والعناصر الجانبية الضارة
            for noise in soup.find_all(["script", "style", "nav", "footer", "aside", "iframe", "form"]):
                noise.decompose()

            # 2. التخلص من أقسام الأكواد المنتهية بدقة
            for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
                if any(exp in heading.text.lower() for exp in EXPIRED_KEYWORDS):
                    next_node = heading.find_next_sibling()
                    if next_node and next_node.name in ["ul", "ol", "table", "div"]:
                        next_node.decompose()
                    heading.decompose()

            # 3. سحب الجداول مع الربط بأقرب عنوان يسبق الجدول (اسم السيرفر/المنطقة)
            for table in soup.find_all("table"):
                prev_heading = table.find_previous(["h2", "h3", "h4", "strong", "b"])
                server_context = prev_heading.text.strip() if prev_heading else "Global"

                for row in table.find_all("tr"):
                    row_text = row.text.strip()
                    if "expired" in row_text.lower():
                        continue

                    cols = [c.text.strip() for c in row.find_all(["td", "th"]) if c.text.strip()]
                    if cols:
                        line = f"[Server: {server_context}] | " + " | ".join(cols)
                        if regex.search(line):
                            raw_items.append(line)

            # 4. سحب القوائم والفقرات المباشرة مع ربط السيرفر المسبق
            for elem in soup.find_all(["ul", "ol"]):
                prev_heading = elem.find_previous(["h2", "h3", "h4", "strong", "b"])
                server_context = prev_heading.text.strip() if prev_heading else "Global"

                for li in elem.find_all("li"):
                    text = " ".join(li.text.split())
                    if not text or "expired" in text.lower():
                        continue

                    if regex.search(text):
                        line = f"[Server: {server_context}] | {text[:150]}"
                        raw_items.append(line)

        except Exception as e:
            print(f"  ⚠️ [خطأ أثناء قراءة الرابط]: {e}", flush=True)

    return raw_items


def pre_filter_and_clean_data(raw_items, config):
    """فلترة وتصفية البيانات اعتماداً حصراً على custom_junk_words و regex_pattern الخاص باللعبة"""
    regex_str = config.get("regex_pattern", r"\b[A-Za-z0-9_\-]{4,25}\b")
    regex = re.compile(regex_str, re.IGNORECASE)

    custom_junk = set(w.upper() for w in config.get("custom_junk_words", []))

    code_to_best_line = {}

    for line in raw_items:
        matches = regex.findall(line)
        for match in matches:
            code_upper = match.upper().strip()

            if code_upper in custom_junk or code_upper.isdigit() or len(code_upper) < 3:
                continue

            if code_upper not in code_to_best_line:
                code_to_best_line[code_upper] = line
            else:
                if len(line) > len(code_to_best_line[code_upper]):
                    code_to_best_line[code_upper] = line

    cleaned_candidates = list(code_to_best_line.values())
    return cleaned_candidates[:30]


def sanitize_and_structure_with_ai(game_name, raw_candidates):
    """الفلترة النهائية وتحويل البيانات لمصفوفة JSON منظمّة بالذكاء الاصطناعي"""
    if not raw_candidates:
        return []

    if not llm:
        print("  ⚠️ [تنبيه]: نموذج الذكاء الاصطناعي غير متوفر، سيتم استخدام الفلترة الاحتياطية.", flush=True)
        fallback_codes = []
        seen = set()
        for text in raw_candidates:
            parts = text.split("|")
            code = parts[0].strip()
            if code.upper() not in seen:
                seen.add(code.upper())
                fallback_codes.append({
                    "code": code,
                    "reward": parts[1].strip() if len(parts) > 1 else None,
                    "server": None,
                    "created_at": None,
                    "expiry": None,
                    "status": "شغال",
                })
        return fallback_codes

    prompt = f"""[INST] You are an expert data sanitization engine for gaming platforms.
Analyze the following raw scraped data lines for the game "{game_name}":
{json.dumps(raw_candidates, ensure_ascii=False)}

Your Task:
1. Extract ONLY valid, active promo/redeem codes for "{game_name}".
2. Filter out false positive words, website elements, and expired entries.
3. Map descriptions or bonuses into "reward".
4. Extract creation/discovered date into "created_at" and expiration date into "expiry" if available.
5. Parse the [Server: ...] context if present and place the server name in the "server" field (e.g. "India", "Europe", "Global").
6. Output STRICTLY a valid JSON array of objects with keys: "code", "reward", "server", "created_at", "expiry", "status".
7. Set "status" to "شغال" for all active codes. Set missing properties to null.

JSON Output Example:
[
  {{"code": "OPERACOLLAB", "reward": "Primogem x30, Mora x20000", "server": "All", "created_at": "2026-09-28", "expiry": null, "status": "شغال"}},
  {{"code": "WOS0812", "reward": "100 Gems", "server": "Europe", "created_at": null, "expiry": "2026-12-31", "status": "شغال"}}
]
[/INST]"""

    try:
        response = llm(prompt, max_tokens=1000, temperature=0.1)
        output_text = response["choices"][0]["text"].strip()

        json_match = re.search(r"\[.*\]", output_text, re.DOTALL)
        if json_match:
            cleaned_data = json.loads(json_match.group(0))
            
            unique_codes = []
            seen_codes = set()
            for item in cleaned_data:
                code_key = item.get("code", "").strip().upper()
                if code_key and code_key not in seen_codes:
                    seen_codes.add(code_key)
                    unique_codes.append(item)
                    
            return unique_codes
        return []
    except Exception as e:
        print(f"  ❌ [خطأ معالجة الذكاء الاصطناعي]: {e}", flush=True)
        return []


def is_game_data_changed(game_id, new_codes, output_dir="public/data/games"):
    """مقارنة البيانات الجديدة بالملف القديم المرفوع لمنع عمليات الـ Commit والتحديث غير الضرورية"""
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


def generate_global_games_index(output_dir="public/data/games", index_path="public/data/games_index.json"):
    """تحديث ملف الفهرس العام لأزرار الألعاب المتاحة"""
    index_list = []

    if os.path.exists(output_dir):
        for file_name in sorted(os.listdir(output_dir)):
            if file_name.endswith(".json") and file_name != "games_index.json":
                file_path = os.path.join(output_dir, file_name)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        index_list.append({
                            "game_id": data.get("game_id"),
                            "game_name": data.get("game_name"),
                            "total_codes": data.get("total_codes", 0),
                        })
                except Exception:
                    continue

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_list, f, ensure_ascii=False, indent=4)

    print(f"\n✨ [تم الفهرسة]: تم تحديث ملف الفهرس الرئيسي ({index_path}) وإضافة {len(index_list)} لعبة.", flush=True)


def run_master_engine():
    """تشغيل المحرك وقراءة كل ملفات إعدادات الألعاب بشكل مستقل"""
    config_files = glob.glob("config/games/*.json")
    output_dir = "public/data/games"
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================", flush=True)
    print(f"🚀 [بدء المنظومة]: معالجة {len(config_files)} ملف لعبة...", flush=True)
    print("==================================================\n", flush=True)

    for config_file in config_files:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                game_config = json.load(f)

            game_id = game_config.get("game_id")
            game_name = game_config.get("game_name")

            print(f"🎮 [بدء معالجة اللعبة]: {game_name} ({game_id})", flush=True)

            # 1. سحب البيانات الخام من روابط اللعبة
            raw_data = extract_game_raw_data(game_config)
            
            # 2. الفلترة المسبقة المعتمدة على custom_junk_words المرفقة بملف اللعبة
            clean_candidates = pre_filter_and_clean_data(raw_data, game_config)
            print(f"  🔍 [تنقية مسبقة]: إعداد {len(clean_candidates)} عنصر مرشح بنجاح.", flush=True)

            # 3. الهيكلة والتنقية بالذكاء الاصطناعي
            clean_codes = sanitize_and_structure_with_ai(game_name, clean_candidates)
            print(f"  🤖 [تنقية الذكاء الاصطناعي]: تم تأكيد {len(clean_codes)} كود فعال.", flush=True)

            # 4. المقارنة مع الملف القديم المرفوع والحذف/الإضافة عند وجود اختلاف
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

                print(f"  ✅ [تحديث واستبدال]: تم حذف الملف القديم ورفع التحديث الجديد: {file_path}\n", flush=True)
            else:
                print("  ⏸️ [بدون تغيير]: الأكواد تطابق الملف القديم بالضبط. لن يتم تعديل الملف.\n", flush=True)

        except Exception as e:
            print(f"  ❌ [خطأ في ملف {config_file}]: {e}\n", flush=True)

    # 5. تحديث فهرس الألعاب العام
    generate_global_games_index(output_dir)


if __name__ == "__main__":
    run_master_engine()
