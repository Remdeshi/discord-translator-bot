import os
import json

LANG_FILE = "data/user_lang.json"  # ファイルパスはプロジェクトに合わせて調整してね

def load_lang_settings():
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_lang_settings(data):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

