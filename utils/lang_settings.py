import os
import json

LANG_FILE = "data/user_lang.json"  # ファイルパスはプロジェクトに合わせて調整してね

def load_lang_settings():
    # ファイルがなければディレクトリ作成＆空ファイル生成
    if not os.path.exists(LANG_FILE):
        os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            f.write("{}")  # 空のJSONを書き込む
        return {}
    # ファイルがあれば読み込み
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_lang_settings(data):
    os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)  # 念のためディレクトリ作成
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
