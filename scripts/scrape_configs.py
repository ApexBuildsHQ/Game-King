import os
import json
import time
import requests

# استدعاء التوكن التلقائي من بيئة GitHub Actions
GH_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GH_TOKEN:
    HEADERS["Authorization"] = f"token {GH_TOKEN}"

def search_and_download_json(game_title, search_keyword):
    """
    يبحث بداخل مستودعات GitHub المفتوحة عن ملفات .json المخصصة للعبة
    مع فرض تأخير زمني قدره 3 ثوانٍ بين كل طلب والآخر لحماية السكريبت من الحظر
    """
    # -------------------------------------------------------------
    # فرض تأخير زمني 3 ثوانٍ قبل كل طلب بحث للامتثال لقيود API
    # -------------------------------------------------------------
    time.sleep(3)
    
    query = f"{game_title} winlator {search_keyword} extension:json"
    url = f"https://api.github.com/search/code?q={query}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                # تحويل رابط المعاينة إلى رابط تنزيل مباشر (Raw URL)
                raw_url = items[0]["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                print(f"  [Found] Download URL for {game_title} ({search_keyword}): {raw_url}")
                
                # تنزيل محتوى الملف مباشرة
                file_res = requests.get(raw_url, timeout=10)
                if file_res.status_code == 200:
                    return file_res.json()
        elif response.status_code in (403, 429):
            print("  [Warning] API rate limit hit. Waiting an extra 15 seconds...")
            time.sleep(15)
        else:
            print(f"  [Status {response.status_code}] No matching file for {game_title} ({search_keyword})")

    except Exception as e:
        print(f"  [Error] Failed searching for {game_title} ({search_keyword}): {e}")
        
    return None

def main():
    # إنشاء مجلدات حفظ الأزرار والإعدادات داخل مستودعك
    os.makedirs("controls", exist_ok=True)
    os.makedirs("settings", exist_ok=True)

    if not os.path.exists("games.json"):
        print("Error: games.json not found in root directory!")
        return

    with open("games.json", "r", encoding="utf-8") as f:
        games = json.load(f)

    total_games = len(games)
    print(f"Starting GitHub search pipeline for {total_games} games...")

    for index, game in enumerate(games, 1):
        game_id = game["id"]
        game_title = game["title"]
        print(f"\n[{index}/{total_games}] Scanning GitHub for: '{game_title}'...")

        # 1. البحث وجلب ملف الأزرار المخصص (Controls)
        controls_data = search_and_download_json(game_title, "controls")
        if controls_data:
            controls_file_path = f"controls/{game_id}.json"
            with open(controls_file_path, "w", encoding="utf-8") as f:
                json.dump(controls_data, f, indent=2)
            print(f"  -> Saved controls to: {controls_file_path}")
        else:
            print(f"  -> No custom controls found for {game_title}")

        # 2. البحث وجلب ملف إعدادات المحاكي المخصص (Settings/Container)
        settings_data = search_and_download_json(game_title, "settings") or search_and_download_json(game_title, "container")
        if settings_data:
            settings_file_path = f"settings/{game_id}.json"
            with open(settings_file_path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2)
            print(f"  -> Saved settings to: {settings_file_path}")
        else:
            print(f"  -> No custom settings found for {game_title}")

    print("\nScraping workflow completed successfully!")

if __name__ == "__main__":
    main()

