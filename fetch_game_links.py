import json
import requests
import time
import sys

# قائمة الكلمات الاستبعادية لمنع جلب ملفات التحديثات، الأغلفة، أو نسخ الكونسول
EXCLUDE_KEYWORDS = [
    "x360", "ps3", "wii", "cover", "patch", "update", "mugen", 
    "alpha", "demo", "lockdown", "dic-files", "torrent", "manual",
    "addon", "dlc", "soundtrack", "mod", "trainer"
]

def verify_link_exists(url):
    """التحقق المباشر من أن الرابط يعطي 200 OK وقابل للتحميل فعلياً"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def get_verified_download_link(game_title):
    search_url = "https://archive.org/advancedsearch.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }

    # المحاولة بأكثر من صيغة بحث لضمان العثور على النسخة المحمولة (PC Portable / GOG / Rip)
    search_queries = [
        f'title:("{game_title}") AND mediatype:(software) AND (format:"7Z" OR format:"ZIP")',
        f'title:("{game_title} PC") AND mediatype:(software)',
        f'title:("{game_title} Portable") AND mediatype:(software)'
    ]

    for query in search_queries:
        params = {
            'q': query,
            'fl[]': 'identifier,title,downloads',
            'sort[]': 'downloads desc', # الترتيب حسب الأكثر تحميلاً
            'rows': '10',
            'output': 'json'
        }

        try:
            res = requests.get(search_url, params=params, headers=headers, timeout=15)
            docs = res.json().get('response', {}).get('docs', [])

            for item in docs:
                item_id = item['identifier']
                metadata_url = f"https://archive.org/metadata/{item_id}/files"
                
                files_res = requests.get(metadata_url, headers=headers, timeout=15).json()
                files = files_res.get('result', [])

                valid_candidates = []
                for f in files:
                    file_name = f.get('name', '')
                    file_name_lower = file_name.lower()
                    file_size = int(f.get('size', 0))

                    # 1. التاكد من الامتداد
                    if not (file_name_lower.endswith('.7z') or file_name_lower.endswith('.zip')):
                        continue

                    # 2. استبعاد الملفات المخفية والملفات التي تحتوي على كلمات استبعادية
                    if file_name.startswith('.') or any(bad_word in file_name_lower for bad_word in EXCLUDE_KEYWORDS):
                        continue

                    # 3. شرط الحجم: استبعاد الملفات الصغار جداً (أقل من 200 ميجابايت غالباً ليست لعبة كاملة)
                    if file_size < 200 * 1024 * 1024:
                        continue

                    valid_candidates.append((file_name, file_size, item_id))

                if valid_candidates:
                    # فرز المرشحات وتفضيل الملف الأكبر حجماً (الحزمة الكاملة)
                    valid_candidates.sort(key=lambda x: x[1], reverse=True)
                    
                    for candidate_file, _, candidate_id in valid_candidates:
                        direct_url = f"https://archive.org/download/{candidate_id}/{candidate_file}"
                        
                        # 4. الفحص الميداني: التأكد من أن سيرفر Archive يُرجع استجابة 200 فعالة
                        if verify_link_exists(direct_url):
                            return direct_url

            time.sleep(1)

        except Exception as e:
            continue

    return ""

def main():
    try:
        with open("game_2.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("❌ خطأ: ملف game_2.json غير موجود!")
        sys.exit(1)

    result_links = []
    print(f"🔍 بدء الفحص والتحقق الآلي لـ {len(games_data)} لعبة...\n")

    for game in games_data:
        game_id = game.get("id")
        game_title = game.get("title")
        container_profile = game.get("container_profile", "mid_range")
        controls_profile = game.get("controls_profile", "third_person_openworld")

        print(f"⏳ جاري فحص والتمحيص عن: {game_title}...")
        verified_link = get_verified_download_link(game_title)

        if verified_link:
            print(f"✅ تم التأكد والاعتماد (200 OK): {verified_link}\n")
        else:
            print(f"⚠️ لم يتم العثور على حزمة سليمة ومفحوصة لـ {game_title}\n")

        result_links.append({
            "id": game_id,
            "name": game_title,
            "download_url": verified_link,
            "container_profile": container_profile,
            "controls_profile": controls_profile
        })

    with open("game_links.json", "w", encoding="utf-8") as f:
        json.dump(result_links, f, ensure_ascii=False, indent=2)

    print("🎉 اكتمل الفحص وتوليد game_links.json بروابط مؤكدة 100%!")

if __name__ == "__main__":
    main()

