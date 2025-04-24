from flask import Flask
from datetime import datetime
import threading
import discord
import os
import requests
from dotenv import load_dotenv

# ==== 初期化 ====
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
SOURCE_LANG = "JA"
TARGET_LANG = "EN"

app = Flask(__name__)
client = discord.Client(intents=discord.Intents.default())

# ==== Flaskルート（UptimeRobotの監視） ====
@app.route("/", methods=["HEAD", "GET"])
def home():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("last_ping.txt", "w") as f:
        f.write(now)
    return "OK", 200

# ==== 翻訳関数 ====
def translate(text, source_lang, target_lang):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        return result["translations"][0]["text"]
    except:
        return "[翻訳エラー]"

# ==== Discord Botイベント ====
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()

    # 自動判定：日本語→英語、他→日本語
    if any(c in content for c in "ぁあぃいぅうえおかがきぎくぐけげこごさしすせそたちつてとまみむめもやゆよらりるれろわをん漢字"):
        current_lang = SOURCE_LANG
        target_lang = TARGET_LANG
    else:
        current_lang = TARGET_LANG
        target_lang = SOURCE_LANG

    translated = translate(content, current_lang, target_lang)
    await message.channel.send(translated)

# ==== 並列起動 ====
def start_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()
    client.run(DISCORD_TOKEN)
