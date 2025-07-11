import json
import os
import config   # config.py から読み込む：相対パスのためエラーとなる可能性がある

# config.USER_LANG_FILE = "data/user_lang.json"  # ファイルパスはプロジェクトに合わせて調整してね
DEFAULT_LANG_DATA = {}

def load_lang_settings() -> json:
    return_data = {}

    # ファイルがなければ空ファイル生成
    if not os.path.exists(config.USER_LANG_FILE):
        save_lang_settings(return_data)

    # ファイルがあれば読み込み
    else:
        with open(config.USER_LANG_FILE, "r", encoding="utf-8") as f:
            return_data = json.load(f)

    return return_data

def save_lang_settings(data) -> None:
    with open(config.USER_LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return
