import os
import json
import shutil
import subprocess
import hashlib
from huggingface_hub import HfApi

GAMES_FILE = 'games.json'
PROGRESS_FILE = 'progress.json'
OUTPUT_FILE = 'game_links.json'
TEMPLATES_DIR = 'templates'
WORK_DIR = 'work_dir'
EXTRACT_DIR = os.path.join(WORK_DIR, 'extracted')

# ضبط اسم مستودعك الخاص افتراضياً
HF_REPO = os.environ.get('HF_REPO', 'bin-data-node/sys-pkg-store')
HF_TOKEN = os.environ.get('HF_TOKEN')

def get_obfuscated_filename(game_id):
    """توليد اسم مشفر غريب للحزمة لمنع التعرف على اسم اللعبة"""
    hashed = hashlib.md5(f"secure_salt_{game_id}".encode()).hexdigest()[:12]
    return f"pkg_{hashed}_data.7z"

def clean_space():
    """تنظيف القرص ومسح الملفات المؤقتة لتوفير المساحة"""
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
    subprocess.run("rm -f *.7z *.zip raw_archive", shell=True)

def find_largest_exe(base_dir):
    """تحديد ملف التشغيل الرئيسي بحسب الحجم"""
    largest_exe = None
    max_size = -1
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith('.exe'):
                full_path = os.path.join(root, file)
                size = os.path.getsize(full_path)
                if size > max_size:
                    max_size = size
                    largest_exe = full_path
    return largest_exe

def process():
    if not os.path.exists(GAMES_FILE):
        print("ملف games.json غير موجود!")
        return

    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except Exception:
                progress = {}

    with open(GAMES_FILE, 'r', encoding='utf-8') as f:
        games = json.load(f)

    api = HfApi(token=HF_TOKEN)

    for game in games:
        game_id = game['id']
        raw_url = game.get('download_url', '').strip()

        # التخطي إذا كانت الخانة فارغة أو تم إنهاؤها مسبقاً
        if not raw_url or game_id in progress:
            continue

        print(f"\n==========================================")
        print(f"بدء التجهيز التلقائي للعبة: {game_id}")
        print(f"==========================================")

        clean_space()
        os.makedirs(EXTRACT_DIR, exist_ok=True)

        try:
            # 1. تنزيل وفك الضغط
            raw_path = os.path.join(WORK_DIR, "raw_archive")
            subprocess.run(f"curl -A 'Mozilla/5.0' -L '{raw_url}' -o '{raw_path}'", shell=True, check=True)
            subprocess.run(f"7z x '{raw_path}' -o'{EXTRACT_DIR}/' || unrar x '{raw_path}' '{EXTRACT_DIR}/'", shell=True)
            if os.path.exists(raw_path):
                os.remove(raw_path)

            # 2. تحديد موقع أكبر ملف exe ووضع dxvk.conf بجانبه
            container_prof = game.get('container_profile', 'mid_range')
            largest_exe = find_largest_exe(EXTRACT_DIR)
            if largest_exe:
                exe_dir = os.path.dirname(largest_exe)
                dxvk_src = os.path.join(TEMPLATES_DIR, 'containers', container_prof, 'dxvk.conf')
                if os.path.exists(dxvk_src):
                    shutil.copy(dxvk_src, os.path.join(exe_dir, 'dxvk.conf'))

            # 3. إعداد مجلد config وحقن container.ini وملف الأزرار (.ic)
            config_dir = os.path.join(EXTRACT_DIR, 'config')
            os.makedirs(config_dir, exist_ok=True)

            container_src = os.path.join(TEMPLATES_DIR, 'containers', container_prof, 'container.ini')
            if os.path.exists(container_src):
                shutil.copy(container_src, os.path.join(config_dir, 'container.ini'))

            controls_prof = game.get('controls_profile', 'third_person_openworld')
            control_file_src = os.path.join(TEMPLATES_DIR, 'controls', f"{controls_prof}.ic")
            if os.path.exists(control_file_src):
                shutil.copy(control_file_src, os.path.join(config_dir, f"{controls_prof}.ic"))

            # 4. توليد اسم ملف مشفر وإعادة الضغط بـ 7z
            obfuscated_filename = get_obfuscated_filename(game_id)
            subprocess.run(f"cd '{EXTRACT_DIR}' && 7z a -t7z -m0=lzma2 -mx=9 '../../{obfuscated_filename}' ./*", shell=True, check=True)

            # 5. الرفع إلى Hugging Face داخل مجلد مبهم bins/
            api.upload_file(
                path_or_fileobj=obfuscated_filename,
                path_in_repo=f"bins/{obfuscated_filename}",
                repo_id=HF_REPO,
                repo_type="dataset"
            )

            # 6. توليد الرابط المباشر الدائم وتحديث progress.json
            hf_direct_url = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/bins/{obfuscated_filename}"
            progress[game_id] = hf_direct_url

            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

            print(f"تمت العملية بنجاح! الرابط المشفر: {hf_direct_url}")

        except Exception as e:
            print(f"خطأ في معالجة {game_id}: {str(e)}")
        finally:
            clean_space()

    # إنشاء وتحديث game_links.json النهائي
    compiled = []
    for g in games:
        gid = g['id']
        compiled.append({
            "id": gid,
            "name": g['name'],
            "download_url": progress.get(gid, ""),
            "container_profile": g.get("container_profile"),
            "controls_profile": g.get("controls_profile")
        })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(compiled, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    process()

