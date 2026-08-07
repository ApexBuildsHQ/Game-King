import os
import json
import time
import requests

GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GH_TOKEN:
    HEADERS["Authorization"] = f"token {GH_TOKEN}"

def search_github(query, max_retries=3):
    """استعلام محرك بحث كود GitHub مع دعم إعادة المحاولة عند الـ Rate Limit"""
    url = f"https://api.github.com/search/code?q={query}"
    for attempt in range(max_retries):
        time.sleep(3) # فاصل زمني آمن
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                return res.json().get("items", [])
            elif res.status_code in (403, 429):
                print(f"  [Rate Limit] الانتظار 20 ثانية قبل المحاولة ({attempt+1}/{max_retries})...")
                time.sleep(20)
            else:
                break
        except Exception as e:
            print(f"  [Error] خطأ في الاتصال: {e}")
            break
    return []

def is_valid_control_json(data):
    """التحقق التلقائي من أن ملف JSON هو ملف أزرار وليس حاوية إعدادات"""
    if isinstance(data, dict):
        content_str = json.dumps(data).lower()
        # يجب أن يحتوي على كلمات مفتاحية للأزرار
        has_control_keys = any(k in content_str for k in ["controls", "elements", "binding", "button", "cursor", "dpad"])
        # يجب ألا يكون ملف حاوية إعدادات
        is_not_container = "wineversion" not in content_str and "dxwrapper" not in content_str
        return has_control_keys and is_not_container
    return False

def fetch_control_file(game_title):
    clean_title = game_title.split("/")[0].split("(")[0].strip()
    
    # 1. البحث عن صيغة .ic الرسمية للأزرار
    print(f"  -> جاري البحث عن ملف أزرار صيغة (.ic)...")
    ic_items = search_github(f'"{clean_title}" extension:ic')
    for item in ic_items:
        raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        res = requests.get(raw_url, timeout=10)
        if res.status_code == 200:
            print(f"  [تم العثور على ملف .ic]: {raw_url}")
            return res.content, "ic"

    # 2. البحث عن صيغة .json المخصصة للأزرار مع فحص المحتوى
    print(f"  -> جاري البحث عن ملف أزرار صيغة (.json)...")
    json_items = search_github(f'"{clean_title}" controls extension:json')
    for item in json_items:
        raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        res = requests.get(raw_url, timeout=10)
        if res.status_code == 200:
            try:
                data = res.json()
                if is_valid_control_json(data):
                    print(f"  [تم العثور على أزرار valid JSON]: {raw_url}")
                    return json.dumps(data, indent=2).encode('utf-8'), "json"
            except Exception:
                continue

    return None, None

def fetch_settings_file(game_title):
    clean_title = game_title.split("/")[0].split("(")[0].strip()
    items = search_github(f'"{clean_title}" winlator container extension:json')
    for item in items:
        raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        res = requests.get(raw_url, timeout=10)
        if res.status_code == 200:
            try:
                data = res.json()
                # التأكد من أنه ملف إعدادات حاوية حقيقي
                if "container" in data or "wineVersion" in str(data) or "dxwrapper" in str(data):
                    print(f"  [تم العثور على إعدادات حاوية]: {raw_url}")
                    return data
            except Exception:
                continue
    return None

def main():
    os.makedirs("controls", exist_ok=True)
    os.makedirs("settings", exist_ok=True)

    if not os.path.exists("games.json"):
        print("خطأ: ملف games.json غير موجود!")
        return

    with open("games.json", "r", encoding="utf-8") as f:
        games = json.load(f)

    for index, game in enumerate(games, 1):
        game_id = game["id"]
        game_title = game["title"]
        print(f"\n[{index}/{len(games)}] جاري فحص اللعبة: '{game_title}'...")

        # كشط الأزرار (.ic أو .json)
        ctrl_content, ext = fetch_control_file(game_title)
        if ctrl_content:
            file_path = f"controls/{game_id}.{ext}"
            with open(file_path, "wb") as f:
                f.write(ctrl_content)
            print(f"  -> تم حفظ الأزرار في {file_path}")

        # كشط إعدادات الحاوية (.json)
        settings_data = fetch_settings_file(game_title)
        if settings_data:
            file_path = f"settings/{game_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
            print(f"  -> تم حفظ الإعدادات في {file_path}")

if __name__ == "__main__":
    main()

