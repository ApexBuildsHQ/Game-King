import json
import re
import requests
import time
import sys

# 1. قائمة الكلمات والمصطلحات الاستبعادية لضمان تجنب الملفات الناقصة، التحديثات، والمنصات الأخرى
EXCLUDE_KEYWORDS = [
    "part", "pt1", "pt2", "pt0", "disc1", "disc2", "cd1", "cd2", "dvd1", "dvd2",
    "x360", "ps3", "ps4", "wii", "switch", "psp", "android", "ios",
    "cover", "patch", "update", "mugen", "alpha", "demo", "lockdown", "editor",
    "addon", "dlc", "soundtrack", "mod", "trainer", "manual", "torrent"
]

# أنماط ريجكس (Regex) لكشف الأرشيفات المقسمة مثل .part01.rar أو .7z.001
SPLIT_PATTERNS = [
    r'\.part[0-9]+', 
    r'\.7z\.[0-9]+', 
    r'\.z[0-9]+', 
    r'\.r[0-9]+',
    r'part[0-9]+',
    r'disc[0-9]+',
    r'cd[0-9]+'
]

def is_split_or_invalid_file(filename):
    """التحقق مما إذا كان الملف جزءاً من لعبة مقسمة أو يحوي كلمات حظر"""
    fn_lower = filename.lower()
    
    # فحص الكلمات الاستبعادية
    if any(bad_word in fn_lower for bad_word in EXCLUDE_KEYWORDS):
        return True
        
    # فحص الأنماط البرمجية للأجزاء المقسمة
    for pattern in SPLIT_PATTERNS:
        if re.search(pattern, fn_lower):
            return True
            
    return False

def verify_download_link(url, min_size_mb=300):
    """فحص حي للرابط عبر الطلب المباشر لضمان وجوده (200 OK) وحجمه الكامل"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # إرسال طلب HEAD خفيف دون تحميل الملف بالكامل
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=12)
        
        if response.status_code == 200:
            content_length = int(response.headers.get('content-length', 0))
            # التأكد من أن الملف موجود بحجم حقيقي لا يقل عن الحد الأدنى (مثلاً 300 ميجابايت)
            if content_length >= (min_size_mb * 1024 * 1024):
                return True, content_length
    except Exception:
        pass
        
    return False, 0

def fetch_full_game_package(game_title):
    """البحث المتقدم واختيار حزمة اللعبة المكتملة في ملف واحد فقط"""
    search_url = "https://archive.org/advancedsearch.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    }

    # استعلامات بحث متدرجة للوصول إلى أفضل نسخة PC مكتملة (GOG / Portable / Rip)
    queries = [
        f'title:("{game_title}") AND mediatype:(software) AND (format:"7Z" OR format:"ZIP")',
        f'title:("{game_title} PC") AND mediatype:(software)',
        f'title:("{game_title} GOG") AND mediatype:(software)',
        f'title:("{game_title} Portable") AND mediatype:(software)'
    ]

    for query in queries:
        params = {
            'q': query,
            'fl[]': 'identifier,title,downloads',
            'sort[]': 'downloads desc',  # الأولوية للملفات الأكثر تحميلاً لأنها غالباً السليمة
            'rows': '10',
            'output': 'json'
        }

        try:
            res = requests.get(search_url, params=params, headers=headers, timeout=15)
            docs = res.json().get('response', {}).get('docs', [])

            for item in docs:
                item_id = item['identifier']
                metadata_url = f"https://archive.org/metadata/{item_id}/files"
                
                meta_res = requests.get(metadata_url, headers=headers, timeout=15).json()
                files = meta_res.get('result', [])

                valid_candidates = []
                for f in files:
                    file_name = f.get('name', '')
                    file_name_lower = file_name.lower()
                    file_size = int(f.get('size', 0))

                    # 1. القبول فقط لامتدادات الضغط المعتمدة
                    if not (file_name_lower.endswith('.7z') or file_name_lower.endswith('.zip') or file_name_lower.endswith('.iso')):
                        continue

                    # 2. استبعاد الملفات المقسمة أو التي تحتوي على كلمات حظر
                    if is_split_or_invalid_file(file_name):
                        continue

                    # 3. التأكد من الحجم الأدنى من بيانات Archive المباشرة (أكبر من 300 ميجابايت)
                    if file_size < (300 * 1024 * 1024):
                        continue

                    valid_candidates.append((file_name, file_size, item_id))

                if valid_candidates:
                    # فرز المرشحات واختيار الملف الأكبر حجماً (لضمان الحزمة الكاملة الشاملة للبيانات)
                    valid_candidates.sort(key=lambda x: x[1], reverse=True)

                    for candidate_file, candidate_size, candidate_id in valid_candidates:
                        direct_url = f"https://archive.org/download/{candidate_id}/{candidate_file}"
                        
                        # 4. التحقق الفعلي عبر السيرفر من سلامة رابط التحميل المباشر
                        is_valid, live_size = verify_download_link(direct_url)
                        if is_valid:
                            return direct_url

            time.sleep(0.5) # تجنب إغلاق الاتصال من خوادم Archive

        except Exception:
            continue

    return ""

def main():
    try:
        with open("game_2.json", "r", encoding="utf-8") as f:
            games_data = json.load(f)
    except FileNotFoundError:
        print("❌ خطأ: لم يتم العثور على ملف game_2.json!")
        sys.exit(1)

    output_results = []
    print(f"🚀 بدء الفحص واستخراج الروابط المكتملة لـ {len(games_data)} لعبة...\n")

    for game in games_data:
        game_id = game.get("id")
        game_title = game.get("title")
        container_profile = game.get("container_profile", "mid_range")
        controls_profile = game.get("controls_profile", "third_person_openworld")

        print(f"🔎 جاري البحث عن حزمة سليمـة ومكتمـلـة لـ: [{game_title}]...")
        verified_url = fetch_full_game_package(game_title)

        if verified_url:
            print(f"✅ تم اعتماد رابط الحزمة الكاملة (200 OK):")
            print(f"🔗 {verified_url}\n")
        else:
            print(f"⚠️ لم يتم العثور على حزمة مكتملة برابط مباشر شغّال لـ [{game_title}]\n")

        output_results.append({
            "id": game_id,
            "name": game_title,
            "download_url": verified_url,
            "container_profile": container_profile,
            "controls_profile": controls_profile
        })

    # حفظ النتائج في game_links.json
    with open("game_links.json", "w", encoding="utf-8") as f:
        json.dump(output_results, f, ensure_ascii=False, indent=2)

    print("🎉 اكتملت العملية بنجاح! تم إنشاء game_links.json بروابط حزم كاملة ومجربة.")

if __name__ == "__main__":
    main()

