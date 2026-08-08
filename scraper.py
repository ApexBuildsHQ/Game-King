import os
import re
import sys
import json
import time
import random
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from bs4 import BeautifulSoup
from curl_cffi import requests

# ================================
# إعدادات البيئة والتخفي
# ================================
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

OUTPUT_BASE_DIR = Path("configs")

CONTROL_EXTENSIONS = {'.ic', '.json', '.xml', '.binds'}
CONFIG_EXTENSIONS = {'.ini', '.cfg', '.conf', '.xml', '.json'}

TELEGRAM_CHANNELS = [
    "winlator_official",
    "winlator_community",
    "mobox_channel",
    "android_emulation_hub"
]

def get_stealth_session() -> requests.Session:
    """جلسة مموهة تتجه عبر Tor مع تزييف بصمة Chrome TLS"""
    session = requests.Session()
    session.proxies = TOR_PROXY
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    })
    return session

def renew_tor_identity():
    """تغيير الـ IP عبر إعادة تشغيل Tor"""
    print("[*] Rotating Tor IP...")
    os.system("sudo service tor restart")
    time.sleep(4)

def human_delay(min_sec: float = 1.5, max_sec: float = 3.5):
    time.sleep(random.uniform(min_sec, max_sec))

def clean_url(raw_url: str) -> str:
    """تفكيك الروابط وإصلاح مسارات GitHub وتحويلها إلى RAW"""
    url = urllib.parse.unquote(raw_url)
    
    # استخراج الرابط الحقيقي إذا كان القادم من توجيه Google
    if "/url?q=" in url:
        match = re.search(r'/url\?q=(https?://[^&]+)', url)
        if match:
            url = match.group(1)

    # تحويل رابط صفحة GitHub إلى رابط ملف RAW مباشر
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        
    return url

# ================================
# فحص وتدقيق محتوى الملفات
# ================================
def validate_control_file(content: str) -> bool:
    if len(content.strip()) < 15:
        return False
    keywords = ['button', 'binding', 'x', 'y', 'width', 'height', 'orientation', 'controls', 'dpad', 'joystick', 'key_']
    return any(kw in content.lower() for kw in keywords)

def validate_config_file(content: str) -> bool:
    if len(content.strip()) < 15:
        return False
    keywords = ['resolution', 'graphics', 'wine', 'dxvk', 'box64', 'cpu', 'env', 'container', 'driver', 'renderer', 'setting']
    return any(kw in content.lower() for kw in keywords)

# ================================
# محرك الكشط والتفتيش المحدث
# ================================
class GameScraperEngine:
    def __init__(self, game_input: Union[str, Dict[str, Any]]):
        if isinstance(game_input, dict):
            self.game_name = (
                game_input.get("name") 
                or game_input.get("title") 
                or game_input.get("game") 
                or str(next(iter(game_input.values()), "Unknown_Game"))
            )
        else:
            self.game_name = str(game_input)

        # تجهيز أسماء للبحث بدون مسافات أو رموز
        self.clean_name = re.sub(r'[\._\-\s]+', '', self.game_name).lower()
        self.save_dir = OUTPUT_BASE_DIR / self.game_name.replace(" ", "_")
        self.session = get_stealth_session()
        
        self.found_controls = False
        self.found_configs = False

    def download_and_save_file(self, url: str, file_type: str) -> bool:
        """تحميل الملف واختباره وحفظه"""
        try:
            target_url = clean_url(url)
            parsed_path = Path(urllib.parse.urlparse(target_url).path)
            ext = parsed_path.suffix.lower()

            # تجنب روابط المواقع العامة
            if not ext or ext in ['.html', '.php', '.htm', '.org']:
                return False

            response = self.session.get(target_url, impersonate="chrome124", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                if file_type == "control" and validate_control_file(content):
                    self.save_dir.mkdir(parents=True, exist_ok=True)
                    file_path = self.save_dir / f"controls_{self.game_name.replace(' ', '_')}{ext}"
                    file_path.write_text(content, encoding='utf-8')
                    print(f"  [✓] Verified & Saved Control File: {file_path}")
                    self.found_controls = True
                    return True

                elif file_type == "config" and validate_config_file(content):
                    self.save_dir.mkdir(parents=True, exist_ok=True)
                    file_path = self.save_dir / f"config_{self.game_name.replace(' ', '_')}{ext}"
                    file_path.write_text(content, encoding='utf-8')
                    print(f"  [✓] Verified & Saved Config File: {file_path}")
                    self.found_configs = True
                    return True
        except Exception as e:
            pass
        return False

    def scrape_github_code_api(self):
        """البحث المباشر في GitHub API عن ملفات الأزرار والإعدادات المرفوعة من المطورين"""
        print(f"  [->] Searching GitHub Repositories for '{self.game_name}'...")
        
        queries = [
            f'"{self.game_name}" extension:ic',
            f'"{self.game_name}" winlator controls',
            f'"{self.game_name}" winlator config'
        ]

        for q in queries:
            if self.found_controls and self.found_configs:
                break
            try:
                api_url = f"https://api.github.com/search/code?q={urllib.parse.quote(q)}"
                resp = self.session.get(api_url, impersonate="chrome124", timeout=15)
                if resp.status_code == 200:
                    items = resp.json().get('items', [])
                    for item in items:
                        html_url = item.get('html_url', '')
                        raw_url = clean_url(html_url)
                        
                        ext = Path(urllib.parse.urlparse(raw_url).path).suffix.lower()
                        if ext in CONTROL_EXTENSIONS and not self.found_controls:
                            self.download_and_save_file(raw_url, "control")
                        elif ext in CONFIG_EXTENSIONS and not self.found_configs:
                            self.download_and_save_file(raw_url, "config")
                human_delay(1.0, 2.0)
            except Exception as e:
                print(f"  [!] GitHub API Search error: {e}")

    def scrape_reddit(self):
        """كشط مجتمعات Reddit وتحليل كل الروابط الخارجية المدرجة"""
        print(f"  [->] Searching Reddit for '{self.game_name}'...")
        search_query = urllib.parse.quote(f"{self.game_name} winlator")
        url = f"https://www.reddit.com/r/EmulationOnAndroid/search.json?q={search_query}&restrict_sr=1"
        
        try:
            resp = self.session.get(url, impersonate="chrome124", timeout=15)
            if resp.status_code == 200:
                posts = resp.json().get('data', {}).get('children', [])
                for post in posts:
                    self_text = post.get('data', {}).get('selftext', '')
                    urls = re.findall(r'https?://[^\s"\'>]+', self_text)
                    for target_url in urls:
                        cleaned = clean_url(target_url)
                        ext = Path(urllib.parse.urlparse(cleaned).path).suffix.lower()
                        
                        if ext in CONTROL_EXTENSIONS and not self.found_controls:
                            self.download_and_save_file(cleaned, "control")
                        if ext in CONFIG_EXTENSIONS and not self.found_configs:
                            self.download_and_save_file(cleaned, "config")
        except Exception as e:
            print(f"  [!] Reddit search error: {e}")

    def scrape_telegram(self):
        """كشط المعاينات العامة لقنوات تليجرام"""
        print(f"  [->] Searching Telegram channels for '{self.game_name}'...")
        for channel in TELEGRAM_CHANNELS:
            if self.found_controls and self.found_configs:
                break
            
            url = f"https://t.me/s/{channel}?q={urllib.parse.quote(self.game_name)}"
            try:
                resp = self.session.get(url, impersonate="chrome124", timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = clean_url(a['href'])
                        ext = Path(urllib.parse.urlparse(href).path).suffix.lower()
                        
                        if ext in CONTROL_EXTENSIONS and not self.found_controls:
                            self.download_and_save_file(href, "control")
                        if ext in CONFIG_EXTENSIONS and not self.found_configs:
                            self.download_and_save_file(href, "config")
                human_delay(1.0, 2.0)
            except Exception as e:
                print(f"  [!] Telegram error: {e}")

    def run(self):
        print(f"\n==========================================")
        print(f"[*] Processing Game: {self.game_name}")
        print(f"==========================================")
        
        self.scrape_github_code_api()
        
        if not (self.found_controls and self.found_configs):
            self.scrape_reddit()
            human_delay()

        if not (self.found_controls and self.found_configs):
            self.scrape_telegram()
            human_delay()

        if not self.found_controls and not self.found_configs:
            print(f"[x] No valid original files found for '{self.game_name}'.")
        
        renew_tor_identity()

# ================================
# نقطة التشغيل الرئيسية
# ================================
def main():
    # إنشاء مجلد configs فورياً لمنع أخطاء Git في حال عدم العثور على أي ملفات جديدة
    OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

    games_file = Path("games.json")
    if not games_file.exists():
        print("[!] Critical Error: 'games.json' file not found!")
        sys.exit(1)

    try:
        games_data = json.loads(games_file.read_text(encoding='utf-8'))
        if isinstance(games_data, dict) and "games" in games_data:
            games_list = games_data["games"]
        elif isinstance(games_data, list):
            games_list = games_data
        else:
            games_list = [games_data]

    except Exception as e:
        print(f"[!] Error reading games.json: {e}")
        sys.exit(1)

    print(f"[*] Loaded {len(games_list)} items from games.json")
    
    for game_item in games_list:
        engine = GameScraperEngine(game_item)
        engine.run()

if __name__ == "__main__":
    main()

