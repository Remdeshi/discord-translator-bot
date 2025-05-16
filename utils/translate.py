import os
import json
import aiohttp
from datetime import datetime

CHAR_COUNT_FILE = "data/char_count.json"
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

def update_char_count(add_count: int):
    current_month = datetime.now().strftime("%Y-%m")
    data = {"count": 0, "month": current_month}

    if os.path.exists(CHAR_COUNT_FILE):
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("month") != current_month:
            data = {"count": 0, "month": current_month}

    data["count"] += add_count
    with open(CHAR_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def translate(text, target_lang):
    async with aiohttp.ClientSession() as session:
        data = {
            "auth_key": DEEPL_API_KEY,
            "text": text,
            "target_lang": target_lang
        }
        async with session.post(DEEPL_API_URL, data=data) as resp:
            if resp.status == 200:
                res_json = await resp.json()
                update_char_count(len(text))
                return res_json["translations"][0]["text"]
            else:
                return "[翻訳エラー]"
