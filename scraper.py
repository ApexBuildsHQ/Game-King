import os
import re
import sys
import json
import time
import random
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional
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

# الامتدادات المقبولة لملفات الأزرار والإعدادات
CONTROL_EXTENSIONS = {'.ic', '.json', '.xml', '.binds'}
CONFIG_EXTENSIONS = {'.ini', '.cfg', '.conf', '.xml', '.json'}

# قنوات وتجمعات تليجرام شهيرة للمحاكيات للكشط منها بدون API
TELEGRAM_CHANNELS = [
    "winlator_official",
    "winlator_community",
    "mobox_channel",
    "android_emulation_hub"
]

def get_stealth_session() -> requests.Session:
    """توليد جلسة مموهة تبدو كـ Chrome 124 حقيقي وموجهة عبر شبكة Tor تغيير الـ IP"""
    session = requests.Session()
    session.proxies = TOR_PROXY
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    })
    return session

def renew_tor_identity():
    """إعادة تشغيل خدمة Tor للحصول على عنوان IP جديد تماماً"""
    print("[*] Rotating Tor IP...")
    os.system("sudo service tor restart")
    time.sleep(4)

def human_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """محاكاة التأخير البشري بين الطلبات"""
    time.sleep(random.uniform(min_sec, max_sec))

# ================================
# فحص وتدقيق محتوى الملفات
# ================================
def validate_control_file(content: str, ext: str) -> bool:
    """التحقق من أن الملف يحتوي على إحداثيات وأزرار تحكم حقيقية"""
    if len(content.strip()) < 20:
        return False
    keywords = ['button', 'binding', 'x', 'y', 'width', 'height', 'orientation', 'controls', 'dpad', 'joystick']
    content_lower = content.lower()
    return any(kw in content_lower for kw in keywords)

def validate_config_file(content: str, ext: str) -> bool:
    """التحقق من أن الملف يحتوي على إعدادات تشغيل حقيقية للمحاكي"""
    if len(content.strip()) < 20:
        return False
    keywords = ['resolution', 'graphics', 'wine', 'dxvk', 'box64', 'cpu', 'env', 'container', 'driver', 'renderer']
    content_lower = content.lower()
    return any(kw in content_lower for kw in keywords)

# ================================
# محركات الكشط المخصصة للمناطق
# ================================
class GameScraperEngine:
    def __init__(self, game_name: str):
        self.game_name = game_name
        self.clean_name = re.sub(r'[\._\-\s]+', '', game_name).lower()
        self.save_dir = OUTPUT_BASE_DIR / game_name.replace(" ", "_")
        self.session = get_stealth_session()
        
        self.found_controls = False
        self.found_configs = False

    def download_and_save_file(self, url: str, file_type: str) -> bool:
        """تحميل الملف الحقيقي واختباره وحفظه فقط إذا كان سليماً"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            ext = Path(parsed_url.path).suffix.lower()
            
            response = self.session.get(url, impersonate="chrome124", timeout=20)
            if response.status_code == 200:
                content = response.text
                
                # التحقق والحفظ بناءً على النوع
                if file_type == "control" and ext in CONTROL_EXTENSIONS:
                    if validate_control_file(content, ext):
                        self.save_dir.mkdir(parents=True, exist_ok=True)
                        file_path = self.save_dir / f"controls_{self.game_name.replace(' ', '_')}{ext}"
                        file_path.write_text(content, encoding='utf-8')
                        print(f"  [✓] Verified & Saved Control File: {file_path}")
                        self.found_controls = True
                        return True

                elif file_type == "config" and ext in CONFIG_EXTENSIONS:
                    if validate_config_file(content, ext):
                        self.save_dir.mkdir(parents=True, exist_ok=True)
                        file_path = self.save_dir / f"config_{self.game_name.replace(' ', '_')}{ext}"
                        file_path.write_text(content, encoding='utf-8')
                        print(f"  [✓] Verified & Saved Config File: {file_path}")
                        self.found_configs = True
                        return True
        except Exception as e:
            print(f"  [!] Failed to download/validate {url}: {e}")
        return False

    def scrape_reddit(self):
        """كشط مجتمعات Reddit المخصصة للمحاكيات بروابط JSON الخفية"""
        print(f"  [->] Searching Reddit for '{self.game_name}'...")
        search_query = urllib.parse.quote(f"{self.game_name} winlator config OR controls")
        url = f"https://www.reddit.com/r/EmulationOnAndroid/search.json?q={search_query}&restrict_sr=1"
        
        try:
            resp = self.session.get(url, impersonate="chrome124", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get('data', {}).get('children', [])
                for post in posts:
                    self_text = post.get('data', {}).get('selftext', '')
                    urls = re.findall(r'https?://[^\s"\'>]+', self_text)
                    for target_url in urls:
                        if any(target_url.endswith(e) for e in CONTROL_EXTENSIONS) and not self.found_controls:
                            self.download_and_save_file(target_url, "control")
                        if any(target_url.endswith(e) for e in CONFIG_EXTENSIONS) and not self.found_configs:
                            self.download_and_save_file(target_url, "config")
        except Exception as e:
            print(f"  [!] Reddit search error: {e}")

    def scrape_telegram(self):
        """كشط المعاينات العامة لقنوات تليجرام بدون API"""
        print(f"  [->] Searching Telegram channels for '{self.game_name}'...")
        for channel in TELEGRAM_CHANNELS:
            if self.found_controls and self.found_configs:
                break
            
            url = f"https://t.me/s/{channel}?q={urllib.parse.quote(self.game_name)}"
            try:
                resp = self.session.get(url, impersonate="chrome124", timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for msg in soup.find_all("div", class_="tgme_widget_message_text"):
                        links = [a['href'] for a in msg.find_all('a', href=True)]
                        for link in links:
                            if any(link.endswith(e) for e in CONTROL_EXTENSIONS) and not self.found_controls:
                                self.download_and_save_file(link, "control")
                            if any(link.endswith(e) for e in CONFIG_EXTENSIONS) and not self.found_configs:
                                self.download_and_save_file(link, "config")
                human_delay(1.5, 3.0)
            except Exception as e:
                print(f"  [!] Telegram channel '{channel}' error: {e}")

    def scrape_fandom_and_wikis(self):
        """كشط موسوعات Fandom ومستودعات البيانات للعبة"""
        print(f"  [->] Searching Wiki/Fandom resources for '{self.game_name}'...")
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(self.game_name + ' winlator .ic file OR config github')}"
        try:
            resp = self.session.get(search_url, impersonate="chrome124", timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # استخراج روابط Github Raw أو روابط الملفات المباشرة
                    if "github.com" in href and ("/raw/" in href or "/blob/" in href):
                        raw_url = href.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                        if any(raw_url.endswith(e) for e in CONTROL_EXTENSIONS) and not self.found_controls:
                            self.download_and_save_file(raw_url, "control")
                        if any(raw_url.endswith(e) for e in CONFIG_EXTENSIONS) and not self.found_configs:
                            self.download_and_save_file(raw_url, "config")
        except Exception as e:
            print(f"  [!] Wiki/Web search error: {e}")

    def run(self):
        print(f"\n==========================================")
        print(f"[*] Processing Game: {self.game_name}")
        print(f"==========================================")
        
        # تنفيذ خطوات البحث عبر المصادر
        self.scrape_reddit()
        human_delay()
        
        if not (self.found_controls and self.found_configs):
            self.scrape_telegram()
            human_delay()

        if not (self.found_controls and self.found_configs):
            self.scrape_fandom_and_wikis()
            human_delay()

        if not self.found_controls and not self.found_configs:
            print(f"[x] No valid original files found for '{self.game_name}'. (No fallback created strictly as requested).")
        
        # تغيير الـ IP بعد نهاية معالجة كل لعبة
        renew_tor_identity()

# ================================
# نقطة التشغيل الرئيسية
# ================================
def main():
    games_file = Path("games.json")
    if not games_file.exists():
        print("[!] Critical Error: 'games.json' file not found!")
        sys.exit(1)

    try:
        games_list = json.loads(games_file.read_text(encoding='utf-8'))
        if isinstance(games_list, dict) and "games" in games_list:
            games_list = games_list["games"]
    except Exception as e:
        print(f"[!] Error reading games.json: {e}")
        sys.exit(1)

    print(f"[*] Loaded {len(games_list)} games from games.json")
    
    for game in games_list:
        engine = GameScraperEngine(game)
        engine.run()

if __name__ == "__main__":
    main()

