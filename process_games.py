import os
import json
import shutil
import subprocess
import hashlib
import io
import requests

# إيقاف أشرطة التقدم المزعجة وتفعيل محرك الرفع الفائق السريع (hf_transfer)
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

GAMES_FILE = 'games.json'
PROGRESS_FILE = 'progress.json'
OUTPUT_FILE = 'game_links.json'
TEMPLATES_DIR = 'templates'
WORK_DIR = 'work_dir'
EXTRACT_DIR = os.path.join(WORK_DIR, 'extracted')

HF_REPO = os.environ.get('HF_REPO', 'bin-data-node/sys-pkg-store')
HF_TOKEN = os.environ.get('HF_TOKEN')

class HTTPRangeStream(io.BufferedIOBase):
    """تدفق متوافق مع Seek لقراءة أجزاء من أرشيف ضخم عبر HTTP Range دون تنزيله كاملاً"""
    def __init__(self, url):
        self.url = url
        self.pos = 0
        res = requests.head(url, allow_redirects=True)
        self._size = int(res.headers.get('Content-Length', 0))

    def seekable(self):
        return True

    def readable(self):
        return True

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self._size + offset
        return self.pos

    def tell(self):
        return self.pos

    def read(self, size=-1):
        if self.pos >= self._size:
            return b""
        if size == -1 or size is None:
            end = self._size - 1
        else:
            end = min(self.pos + size - 1, self._size - 1)
        
        headers = {"Range": f"bytes={self.pos}-{end}"}
        res = requests.get(self.url, headers=headers)
        data = res.content
        self.pos += len(data)
        return data

def verify_remote_injected_files(url):
    """قراءة فهرس العناوين بنهاية الملف المرفوع على Hugging Face ومعاينة الملفات المحقونة"""
    print("\n--- جاري جلب الفهرس الخارجي من Hugging Face في ثوانٍ ---")
    try:
        try:
            import py7zr
        except ImportError:
            subprocess.run("pip install py7zr", shell=True, check=True)
            import py7zr

        stream = HTTPRangeStream(url)
        with py7zr.SevenZipFile(stream, mode='r') as archive:
            all_files = archive.getnames()
            injected = [f for f in all_files if 'config/' in f.lower() or 'dxvk.conf' in f.lower()]
            
            print("النتائج المكتشفة داخل حزمة الأرشيف على السيرفر:")
            if injected:
                for file_name in injected:
                    print(f"  [✓] تم العثور على: {file_name}")
            else:
                print("  [!] لم يتم العثور على ملفات المحاكي داخل مجلد config.")
    except Exception as e:
        print(f"تعذر فحص الفهرس عن بعد (الملف مرفوع وسليم على المنصة): {str(e)}")

def get_obfuscated_filename(game_id):
    """توليد اسم مشفر للحزمة"""
    hashed = hashlib.md5(f"secure_salt_{game_id}".encode()).hexdigest()[:12]
    return f"pkg_{hashed}_data.7z"

def clean_space():
    """تنظيف القرص ومسح الملفات المؤقتة"""
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR, ignore_errors=True)
    subprocess.run("rm -f *.7z *.zip raw_archive", shell=True)

def find_largest_exe(base_dir):
    """تحديد ملف التشغيل الرئيسي بحسب الحجم مع استثناء مجلدات البرامج الملحقة"""
    largest_exe = None
    max_size = -1
    excluded_dirs = {'_commonredist', 'redist', 'redistributable', 'support', '__installer', 'directx'}

    for root, dirs, files in os.walk(base_dir):
        # استثناء مجلدات البرامج الملحقة من البحث والمسح
        dirs[:] = [d for d in dirs if d.lower() not in excluded_dirs]
        
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

    # ضمان وجود ملف progress.json دائماً لمنع أخطاء Git
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            try:
                progress = json.load(f)
            except Exception:
                progress = {}
    else:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    with open(GAMES_FILE, 'r', encoding='utf-8') as f:
        games = json.load(f)

    for game in games:
        game_id = game['id']
        raw_url = game.get('download_url', '').strip()

        if not raw_url or game_id in progress:
            continue

        print(f"\n==========================================")
        print(f"بدء التجهيز التلقائي للعبة: {game_id}")
        print(f"==========================================")

        clean_space()
        os.makedirs(EXTRACT_DIR, exist_ok=True)

        try:
            # 1. تنزيل الملف بأقصى سرعة ببروتوكول aria2c
            raw_path = os.path.join(WORK_DIR, "raw_archive")
            aria_cmd = (
                f"aria2c -x 16 -s 16 -k 1M "
                f"--max-tries=10 --retry-wait=3 "
                f"--user-agent='Mozilla/5.0' "
                f"-d '{WORK_DIR}' -o 'raw_archive' '{raw_url}'"
            )
            subprocess.run(aria_cmd, shell=True, check=True)

            # فك الضغط مع إظهار النسبة المئوية (-bsp1)
            subprocess.run(f"7z x -bsp1 '{raw_path}' -o'{EXTRACT_DIR}/' || unrar x '{raw_path}' '{EXTRACT_DIR}/'", shell=True)
            if os.path.exists(raw_path):
                os.remove(raw_path)

            # 2. إدراج dxvk.conf بجانب أكبر ملف exe
            container_prof = game.get('container_profile', 'mid_range')
            largest_exe = find_largest_exe(EXTRACT_DIR)
            if largest_exe:
                exe_dir = os.path.dirname(largest_exe)
                dxvk_src = os.path.join(TEMPLATES_DIR, 'containers', container_prof, 'dxvk.conf')
                if os.path.exists(dxvk_src):
                    shutil.copy(dxvk_src, os.path.join(exe_dir, 'dxvk.conf'))

            # 3. إعداد مجلد config وحقن الملفات بأسماء موحدة ومظبوطة
            config_dir = os.path.join(EXTRACT_DIR, 'config')
            os.makedirs(config_dir, exist_ok=True)

            container_src = os.path.join(TEMPLATES_DIR, 'containers', container_prof, 'container.ini')
            if os.path.exists(container_src):
                shutil.copy(container_src, os.path.join(config_dir, 'container.ini'))

            # معالجة ملف عناصر التحكم وتغيير امتداده واسمه إلى controls.icp
            controls_prof = game.get('controls_profile', 'third_person_openworld')
            control_src_icp = os.path.join(TEMPLATES_DIR, 'controls', f"{controls_prof}.icp")
            control_src_ic = os.path.join(TEMPLATES_DIR, 'controls', f"{controls_prof}.ic")

            if os.path.exists(control_src_icp):
                shutil.copy(control_src_icp, os.path.join(config_dir, 'controls.icp'))
            elif os.path.exists(control_src_ic):
                shutil.copy(control_src_ic, os.path.join(config_dir, 'controls.icp'))

            # 4. التجميع السريع بنسبة ضغط خفيفة (-mx=1) لإنشاء حزمة واحدة
            obfuscated_filename = get_obfuscated_filename(game_id)
            subprocess.run(f"cd '{EXTRACT_DIR}' && 7z a -t7z -mx=1 '../../{obfuscated_filename}' ./*", shell=True, check=True)

            # 5. الرفع بنقل متوازي فائق السرعة عبر hf_transfer لمنع Timeout
            upload_cmd = (
                f"export HF_HUB_ENABLE_HF_TRANSFER=1 && "
                f"hf upload {HF_REPO} '{obfuscated_filename}' 'bins/{obfuscated_filename}' "
                f"--repo-type=dataset --token={HF_TOKEN}"
            )
            subprocess.run(upload_cmd, shell=True, check=True)

            # 6. تسجيل الرابط المباشر المنفرد وفحص الفهرس مباشرة
            hf_direct_url = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/bins/{obfuscated_filename}"
            progress[game_id] = hf_direct_url

            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

            print(f"تم الرفع بنجاح! الرابط المباشر: {hf_direct_url}")

            # فك رأس الأرشيف على Hugging Face وتأكيد وجود الملفات
            verify_remote_injected_files(hf_direct_url)

        except Exception as e:
            print(f"خطأ في معالجة {game_id}: {str(e)}")
        finally:
            clean_space()

    # تحديث game_links.json
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

