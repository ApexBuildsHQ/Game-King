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
    print("🤖 [الذكاء الاصطناعي]: جاري تحميل النموذج في الذاكرة مع توسيع نافذة السياق...", flush=True)
    try:
        llm = Llama.from_pretrained(
            repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
            filename="*Q4_K_M.gguf",
            verbose=False,
            n_ctx=8192,  # تم الرفع لـ 8192 توكن لاستيعاب البيانات الضخمة
        )
    except Exception as e:
        print(f"⚠️ [خطأ تحميل النموذج]: {e}", flush=True)


def extract_game_raw_data(config):
    """سحب البيانات الخام بدون أي قيود على الطول أو عدد العناصر مع دعم كافة الهياكل"""
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

            # 1. سحب البيانات المخبأة في وسوم JSON (قبل إزالة وسوم السكريبت)
            for script in soup.find_all("script", type=re.compile(r"json", re.I)):
                if script.string and regex.search(script.string):
                    raw_items.append(f"[JSON Data]: {script.string[:500]}")

            # 2. إزالة وسوم السكريبت والإعلانات والعناصر الجانبية الضارة
            for noise in soup.find_all(["script", "style", "nav", "footer", "aside", "iframe", "form"]):
                noise.decompose()

            # 3. التخلص من أقسام الأكواد المنتهية بدقة
            for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
                if any(exp in heading.text.lower() for exp in EXPIRED_KEYWORDS):
                    next_node = heading.find_next_sibling()
                    if next_node and next_node.name in ["ul", "ol", "table", "div"]:
                        next_node.decompose()
                    heading.decompose()

            # 4. سحب الجداول كاملاً مع الربط بأقرب عنوان (اسم السيرفر/المنطقة)
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

            # 5. سحب القوائم المباشرة
            for elem in soup.find_all(["ul", "ol"]):
                prev_heading = elem.find_previous(["h2", "h3", "h4", "strong", "b"])
                server_context = prev_heading.text.strip() if prev_heading else "Global"

                for li in elem.find_all("li"):
                    text = " ".join(li.text.split())
                    if not text or "expired" in text.lower():
                        continue

                    if regex.search(text):
                        line = f"[Server: {server_context}] | {text}"
                        raw_items.append(line)

            # 6. سحب الكروت والعناصر النصية العامة (Card Layouts)
            targets = soup.find_all(["p", "code", "div", "span", "section"])
            for elem in targets:
                if elem.find_all(["div", "p", "table", "ul", "ol", "section"]):
                    continue

                text = " ".join(elem.text.split())
                if not text or "expired" in text.lower():
                    continue

                if regex.search(text):
                    prev_heading = elem.find_previous(["h2", "h3", "h4", "strong", "b"])
                    server_context = prev_heading.text.strip() if prev_heading else "Global"
                    line = f"[Server: {server_context}] | {text}"
                    raw_items.append(line)

        except Exception as e:
            print(f"  ⚠ [خطأ أثناء قراءة الرابط]: {e}", flush=True)

    return raw_items


def pre_filter_and_clean_data(raw_items, config):
    """فلترة وتصفية البيانات واستخراج كافة الأكواد المتاحة دون التقييد بـ 30 عنصر"""
    regex_str = config.get("regex_pattern", r"\b[A-Za-z0-9_\-]{4,25}\b")
    regex = re.compile(regex_str, re.IGNORECASE)

    custom_junk = set(w.upper() for w in config.get("custom_junk_words", []))

    code_to_best_line = {}

    for line in raw_items:
        matches = regex.findall(line)
        for match in matches:
            code_upper = match.upper().strip()

            # تفكيك الكلمة عند وجود شُرطة (-) وفحص مكوناتها ضد custom_junk_words
            parts = code_upper.split("-")
            if code_upper in custom_junk or any(p in custom_junk for p in parts) or code_upper.isdigit() or len(code_upper) < 3:
                continue

            if code_upper not in code_to_best_line:
                code_to_best_line[code_upper] = line
            else:
                if len(line) > len(code_to_best_line[code_upper]):
                    code_to_best_line[code_upper] = line

    # إرجاع كافة العناصر المتاحة دون قص
    return list(code_to_best_line.values())


def process_chunk_with_ai(game_name, chunk_candidates):
    """معالجة دفعة مصغرة باستخدام الذكاء الاصطناعي مع إصلاح تلقائي لأخطاء الفواصل في JSON"""
    prompt = f"""<|start_header_id|>system<|end_header_id|>
You are an expert data extraction engine.
Extract ONLY valid, active promo/redeem codes for "{game_name}" from the provided lines.
Output MUST strictly be a valid JSON array of objects with keys: "code", "reward", "server", "created_at", "expiry", "status".
Set "status" to "شغال". If reward or server is missing, set to null.
Do NOT write markdown, explanations, or commentary outside the JSON array.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Data lines:
{json.dumps(chunk_candidates, ensure_ascii=False)}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    try:
        response = llm(prompt, max_tokens=1500, temperature=0.1, stop=["<|eot_id|>"])
        output_text = response["choices"][0]["text"].strip()

        # استخراج مصفوفة JSON بمرونة
        json_match = re.search(r"\[\s*\{.*\}\s*\]", output_text, re.DOTALL) or re.search(r"\[.*\]", output_text, re.DOTALL)
        if json_match:
            raw_json_str = json_match.group(0)
            
            # إصلاح تلقائي للفاصلة المفقودة بين الأقواس النسق: } { -> }, {
            fixed_json_str = re.sub(r'\}\s*\{', '},{', raw_json_str)
            # إصلاح الفواصل المفقودة بين العناصر النصية المزدوجة
            fixed_json_str = re.sub(r'"\s*\n\s*"', '", "', fixed_json_str)

            try:
                return json.loads(fixed_json_str)
            except Exception:
                # محاولة قراءة النص الأصلي في حال عدم استلزام التعديل
                return json.loads(raw_json_str)

    except Exception as e:
        print(f"    ⚠️ [خطأ في معالجة الدفعة بالذكاء الاصطناعي]: {e}", flush=True)

    return []


def sanitize_and_structure_with_ai(game_name, raw_candidates, config):
    """تقسيم المرشحات لدفعات صغيرة لمنع تجاوز الـ Token Window مع نظام فلترة احتياطي دقيق"""
    if not raw_candidates:
        return []

    regex_str = config.get("regex_pattern", r"\b[A-Za-z0-9_\-]{4,25}\b")
    regex = re.compile(regex_str, re.IGNORECASE)

    # 1. إذا كان النموذج غير متوفر، تفعيل الاستخراج البرمجي الاحتياطي
    if not llm:
        print("  ⚠️ [تنبيه]: النموذج غير متوفر، استخدام الفلترة الاحتياطية المباشرة.", flush=True)
        fallback_codes = []
        seen = set()
        for line in raw_candidates:
            matches = regex.findall(line)
            for m in matches:
                code_key = m.strip().upper()
                if code_key not in seen:
                    seen.add(code_key)
                    parts = line.split("|")
                    fallback_codes.append({
                        "code": m.strip(),
                        "reward": parts[-1].strip() if len(parts) > 1 else None,
                        "server": parts[0].replace("[Server:", "").replace("]", "").strip() if "[Server:" in parts[0] else None,
                        "created_at": None,
                        "expiry": None,
                        "status": "شغال",
                    })
        return fallback_codes

    # 2. تقسيم كافة المرشحات إلى دفعات صغيرة (12 عنصر في الدفعة) لحماية الذاكرة
    chunk_size = 12
    all_extracted_codes = []
    seen_codes = set()

    for i in range(0, len(raw_candidates), chunk_size):
        chunk = raw_candidates[i:i + chunk_size]
        extracted_chunk = process_chunk_with_ai(game_name, chunk)

        if isinstance(extracted_chunk, list):
            for item in extracted_chunk:
                if isinstance(item, dict) and item.get("code"):
                    code_key = str(item.get("code")).strip().upper()
                    if code_key and code_key not in seen_codes:
                        seen_codes.add(code_key)
                        all_extracted_codes.append(item)

    # 3. خط حماية إضافي: إذا فشل الذكاء الاصطناعي في جلب الأكواد من الدفعات لأي سبب، يتم السحب الاحتياطي
    if not all_extracted_codes and raw_candidates:
        print("  ⚠️ [استجابة احتياطية]: الذكاء الاصطناعي لم ينشئ مصفوفة، استخراج الأكواد برمجياً...", flush=True)
        for line in raw_candidates:
            matches = regex.findall(line)
            for m in matches:
                code_key = m.strip().upper()
                if code_key not in seen_codes:
                    seen_codes.add(code_key)
                    parts = line.split("|")
                    all_extracted_codes.append({
                        "code": m.strip(),
                        "reward": parts[-1].strip() if len(parts) > 1 else None,
                        "server": parts[0].replace("[Server:", "").replace("]", "").strip() if "[Server:" in parts[0] else None,
                        "created_at": None,
                        "expiry": None,
                        "status": "شغال",
                    })

    return all_extracted_codes


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
            
            # 2. الفلترة المسبقة واستخراج كافة العناصر الشغالة دون تحديد القيمة بـ 30
            clean_candidates = pre_filter_and_clean_data(raw_data, game_config)
            print(f"  🔍 [تنقية مسبقة]: إعداد {len(clean_candidates)} عنصر مرشح بنجاح.", flush=True)

            # 3. الهيكلة والتنقية بنظام الدفعات لمنع تجاوز التوكنز
            clean_codes = sanitize_and_structure_with_ai(game_name, clean_candidates, game_config)
            print(f"  🤖 [تنقية الذكاء الاصطناعي]: تم تأكيد {len(clean_codes)} كود فعال.", flush=True)

            # 4. المقارنة مع الملف القديم المرفوع والتحديث عند وجود أجهزة جديدة
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
