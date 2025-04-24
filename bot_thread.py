# bot_thread.py
import discord
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import threading

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

CHAR_COUNT_FILE = "char_count.json"
DEFAULT_LANG = "JA"
user_lang = DEFAULT_LANG

on_bot_ready_callback = None

def set_on_ready_callback(func):
    global on_bot_ready_callback
    on_bot_ready_callback = func

def set_user_language(lang_code):
    global user_lang
    user_lang = lang_code

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_char_count():
    if not os.path.exists(CHAR_COUNT_FILE):
        return {"month": datetime.now().strftime("%Y-%m"), "count": 0}
    with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_char_count(data):
    with open(CHAR_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_char_count(added_chars):
    data = load_char_count()
    current_month = datetime.now().strftime("%Y-%m")
    if data.get("month") != current_month:
        data = {"month": current_month, "count": 0}
    data["count"] += added_chars
    save_char_count(data)

# 🌍 翻訳処理（ユーザー言語に合わせて相互翻訳）
def translate_text(text):
    response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": user_lang
    })

    if response.status_code != 200:
        return "翻訳エラー（言語判定失敗）"

    detected_lang = response.json()["translations"][0]["detected_source_language"]

    # 設定言語だったら別言語へ、そうでなければ設定言語へ
    target_lang = "EN" if detected_lang == user_lang else user_lang

    second_response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    })

    if second_response.status_code != 200:
        return "翻訳エラー（再翻訳失敗）"

    translated_text = second_response.json()["translations"][0]["text"]
    update_char_count(len(text))
    return translated_text

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    if on_bot_ready_callback:
        on_bot_ready_callback()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    translated_text = translate_text(message.content)
    if translated_text:
        await message.reply(f"{translated_text}")

def start_bot():
    def run():
        client.run(DISCORD_TOKEN)
    threading.Thread(target=run, daemon=True).start()
