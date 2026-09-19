# storage.py - التخزين المحلي، تقليص الأكواد لـ 12 كود، والمزامنة مع مستودع الواجهة

import json
import os
import base64
import aiohttp
from datetime import datetime, timezone
from validator import validate_code

LOCAL_FILE = "codes.json"
GITHUB_TOKEN = os.getenv("GH_TOKEN", "")
FRONTEND_REPO = os.getenv("FRONTEND_REPO", "")

def load_codes_locally() -> dict:
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_codes_to_file(data: dict):
    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def sync_to_github_repo(data: dict):
    if not GITHUB_TOKEN or not FRONTEND_REPO:
        return

    url = f"https://api.github.com/repos/{FRONTEND_REPO}/contents/codes.json"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            sha = ""
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    sha = res_json.get("sha", "")

            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

            payload = {
                "message": "Auto-update codes.json [skip ci]",
                "content": content_b64
            }
            if sha:
                payload["sha"] = sha

            async with session.put(url, headers=headers, json=payload) as resp:
                if resp.status in [200, 201]:
                    print("[+] تم تحديث codes.json بنجاح داخل مستودع الواجهة الرئيسية.")
    except Exception as e:
        print(f"[-] خطأ في تحديث مستودع الواجهة: {e}")

async def save_code_locally(game_slug: str, code: str, source: str = "Unknown"):
    all_data = load_codes_locally()
    
    if game_slug not in all_data:
        all_data[game_slug] = []

    existing_codes = [item["code"] for item in all_data[game_slug]]
    if code in existing_codes:
        return

    status = await validate_code(game_slug, code)
    if status == "expired":
        return

    new_entry = {
        "game_slug": game_slug,
        "code": code,
        "status": status,
        "source": source,
        "detected_at": datetime.now(timezone.utc).isoformat()
    }

    all_data[game_slug].insert(0, new_entry)
    all_data[game_slug] = all_data[game_slug][:12]

    save_codes_to_file(all_data)
    print(f"[+] [كود جديد] {game_slug}: {code} | المصدر: {source}")

    await sync_to_github_repo(all_data)

