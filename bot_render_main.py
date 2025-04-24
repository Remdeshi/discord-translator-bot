import os
import json
import discord
from discord.ext import commands
import requests
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

SOURCE_LANG = "JA"
TARGET_LANG = "EN"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Flask サーバー（UptimeRobot/Render対策用）
app = Flask("")

@app.route("/")
def home():
    return "I'm alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 文字数管理
def load_char_count():
    try:
        with open("char_count.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"count": 0}

def save_char_count(count):
    with open("char_count.json", "w", encoding="utf-8") as f:
        json.dump({"count": count}, f)

# 翻訳
def translate(text, source_lang, target_lang):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    response = requests.post(url, headers=headers, data=data)
    result = response.json()
    return result["translations"][0]["text"]

# Discord メッセージ受信時
@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    current_lang = None

    # 日本語っぽい文字が含まれていたら英語へ、それ以外は日本語へ
    if any(c in content for c in "ぁあぃいぅうえおかがきぎくぐけげこごさしすせそたちつてとなにぬねのまみむめもやゆよらりるれろわをん漢字"):
        current_lang = SOURCE_LANG
        target_lang = TARGET_LANG
    else:
        current_lang = TARGET_LANG
        target_lang = SOURCE_LANG

    translated = translate(content, current_lang, target_lang)
    await message.channel.send(translated)

    count_data = load_char_count()
    count_data["count"] += len(content)
    save_char_count(count_data["count"])

# 🔥 Flaskサーバーを起動してBotも起動！
keep_alive()
client.run(DISCORD_TOKEN)
