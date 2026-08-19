import json
import requests
import time
import sys

def get_best_download_link(game_title):
    search_url = "https://archive.org/advancedsearch.php"
    
    # البحث عن اللعبة داخل برمجيات Archive.org والترتيب بالأعلى تحميلاً
    query = f'title:("{game_title}") AND mediatype:(software) AND (format:"7Z" OR format:"ZIP")'
    params = {
        'q': query,
        'fl[]': 'identifier,title,downloads',
        'sort[]': 'downloads desc',  # اختيار الأكثر تحميلاً لضمان الجودة
        'rows': '5',
        'output': 'json'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = response.json()
        docs = data.get('response', {}).get('docs', [])
        
        for item in docs:
            item_id = item['identifier']
            metadata_url = f"https://archive.org/metadata/{item_id}/files"
            
            res_files = requests.get(metadata_url, headers=headers, timeout=15).json()
            files = res_files.get('result', [])
            
            # تصفية الملفات للحصول على أكبر ملف 7z أو zip (الحزمة الكاملة)
            valid_files = []
            for f in files:
                name = f.get('name', '')
                if (name.endswith('.7z') or name.endswith('.zip')) and not name.startswith('.'):
                    size = int(f.get('size', 0))
                    valid_files.append((name, size))
            
            if valid_files:
                # اختيار الملف الأكبر حجماً داخل الحزمة الضخمة
                valid_files.sort(key=lambda x: x[1], reverse=True)
                best_file = valid_files[0][0]
                direct_url = f"https://archive.org/download/{item_id}/{best_file}"
                return direct_url
                
            time.sleep(1) # تريث بسيط لمنع إجهاد API
            
    except Exception as e:
        print(f"⚠️ خطأ أثناء البحث عن {game_title}: {e}")
        
    return None

def main():
    # 1. قراءة قائمة الألعاب من ملف game_2.json
    try:
        with open("game_2.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("❌ خطأ: لم يتم العثور على ملف game_2.json!")
        sys.exit(1)

    result_links = []

    print(f"🔍 بدء معالجة {len(games_data)} لعبة من ملف game_2.json...\n")

    # 2. فحص كل لعبة وجلب الرابط المباشر
    for game in games_data:
        game_id = game.get("id")
        game_title = game.get("title") or game.get("name")
        container_profile = game.get("container_profile", "mid_range")
        controls_profile = game.get("controls_profile", "third_person_openworld")

        print(f"⏳ جاري البحث عن: {game_title}...")
        link = get_best_download_link(game_title)

        if link:
            print(f"✅ تم العثور على الرابط: {link}\n")
        else:
            print(f"❌ لم يتم العثور على رابط مضغوط مباشر لـ {game_title}\n")
            link = ""

        # حفظ البيانات في الهيكل المطلوب
        result_links.append({
            "id": game_id,
            "name": game_title,
            "download_url": link,
            "container_profile": container_profile,
            "controls_profile": controls_profile
        })

    # 3. حفظ النتائج في ملف game_links.json
    with open("game_links.json", "w", encoding="utf-8") as f:
        json.dump(result_links, f, ensure_ascii=False, indent=2)

    print("🎉 تم إنشاء وحفظ ملف game_links.json بنجاح!")

if __name__ == "__main__":
    main()

