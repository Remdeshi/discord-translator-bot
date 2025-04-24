# ✅ 完成版 bot_render_main.py
# - Flask (Render) + Discord Bot
# - 母国語設定を使って自動で相互翻訳

from flask import Flask, request
from datetime import datetime
import threading
import discord
import os
import json
import requests
from dotenv import load_dotenv

# ==== 初期化 ====
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

LANG_SETTING_FILE = "lang_setting.json"

app = Flask(__name__)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ==== 言語設定の読み書き ====
def get_lang_setting():
    try:
        with open(LANG_SETTING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"native": "JA", "other": "EN"}

def save_lang_setting(data):
    with open(LANG_SETTING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== Flask ルート ====
@app.route("/", methods=["GET", "HEAD"])
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("last_ping.txt", "w") as f:
        f.write(now)
    return "OK", 200

@app.route("/set_lang", methods=["POST"])
def set_lang():
    data = request.get_json()
    save_lang_setting(data)
    return {"status": "ok"}, 200

# ==== DeepL 翻訳 ====
def translate_text(text):
    setting = get_lang_setting()
    native = setting.get("native", "JA")
    other = setting.get("other", "EN")

    # Step 1: 言語判定
    detect_res = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": native
    })
    if detect_res.status_code != 200:
        return "[翻訳エラー]"
    detected = detect_res.json()["translations"][0]["detected_source_language"]

    # Step 2: 翻訳方向を決定
    target = other if detected == native else native

    # Step 3: 翻訳実行
    final_res = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target
    })
    if final_res.status_code != 200:
        return "[翻訳エラー]"
    return final_res.json()["translations"][0]["text"]

# ==== Discord Bot イベント ====
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
    content = message.content.strip()
    translated = translate_text(content)
    await message.channel.send(translated)

# ==== 並列起動 ====
def start_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()
    client.run(DISCORD_TOKEN)
