import discord
import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

SOURCE_LANG = "JA"
TARGET_LANG = "EN"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CHAR_COUNT_FILE = "char_count.json"

def load_char_count():
    try:
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"count": 0}

def save_char_count(count):
    with open(CHAR_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f)

def translate(text, source_lang, target_lang):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    response = requests.post(url, data=data, headers=headers)
    result = response.json()
    return result["translations"][0]["text"]

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user.name}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    current_lang = None

    # 自動判定：メッセージが日本語なら英語へ、それ以外は日本語へ翻訳
    if any(c in content for c in "ぁあぃいぅうえおかがきぎくぐけげこごさしすせそたちつてとなにぬねのまみむめもやゆよらりるれろわをん漢字"):
        current_lang = SOURCE_LANG
        target_lang = TARGET_LANG
    else:
        current_lang = TARGET_LANG
        target_lang = SOURCE_LANG

    translated = translate(content, current_lang, target_lang)
    await message.channel.send(f" {translated}")

    # 文字数カウント
    count_data = load_char_count()
    count_data["count"] += len(content)
    save_char_count(count_data["count"])

client.run(DISCORD_TOKEN)
