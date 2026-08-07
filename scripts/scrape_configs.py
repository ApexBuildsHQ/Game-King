import os
import json
import time
import requests

GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GH_TOKEN:
    HEADERS["Authorization"] = f"token {GH_TOKEN}"

# الكلمات التي نرفض تنزيل الملف إذا كانت توجد في الرابط لأنها ملفات عشوائية (RSS/Databases)
FORBIDDEN_KEYWORDS = ["rss", "isitcompatible", "database", "seed", "entries", "catalog"]

def search_and_download_json(game_title, search_keyword):
    """
    بحث موجه ومحدد مع آلية Retry تلقائية عند الوصول للـ Rate Limit
    """
    # تنظيف اسم اللعبة من الأرقام والكلمات المزدوجة لتسهيل البحث
    clean_title = game_title.split("/")[0].strip()
    query = f'"{clean_title}" winlator {search_keyword} extension:json'
    url = f"https://api.github.com/search/code?q={query}"
    
    max_retries = 3
    for attempt in range(max_retries):
        time.sleep(4) # فاصل زمني 4 ثوانٍ بين كل طلب
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                    
                    # استبعاد الملفات العشوائية غير المخصصة للأزرار أو المحاكي
                    if any(bad_word in raw_url.lower() for bad_word in FORBIDDEN_KEYWORDS):
                        continue
                        
                    print(f"  [Valid Match] {game_title} ({search_keyword}): {raw_url}")
                    file_res = requests.get(raw_url, timeout=10)
                    if file_res.status_code == 200:
                        return file_res.json()
                        
                # إذا لم يجد ملفاً صالحاً بعد الفلترة
                return None

            elif response.status_code in (403, 429):
                print(f"  [Rate Limit Hit] Waiting 20 seconds before retry ({attempt+1}/{max_retries})...")
                time.sleep(20)
            else:
                break

        except Exception as e:
            print(f"  [Error] {game_title}: {e}")
            break
            
    return None

def main():
    os.makedirs("controls", exist_ok=True)
    os.makedirs("settings", exist_ok=True)

    if not os.path.exists("games.json"):
        print("Error: games.json not found!")
        return

    with open("games.json", "r", encoding="utf-8") as f:
        games = json.load(f)

    for index, game in enumerate(games, 1):
        game_id = game["id"]
        game_title = game["title"]
        print(f"\n[{index}/{len(games)}] Scanning for: '{game_title}'...")

        # 1. بحث الأزرار
        controls_data = search_and_download_json(game_title, "controls profile")
        if controls_data:
            with open(f"controls/{game_id}.json", "w", encoding="utf-8") as f:
                json.dump(controls_data, f, indent=2)
            print(f"  -> Saved valid controls for {game_id}")

        # 2. بحث الإعدادات
        settings_data = search_and_download_json(game_title, "container config")
        if settings_data:
            with open(f"settings/{game_id}.json", "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
            print(f"  -> Saved valid settings for {game_id}")

if __name__ == "__main__":
    main()

