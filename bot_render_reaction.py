import os
import json
import discord
import requests
import asyncio
from flask import Flask, request
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# ==== 環境変数 ====
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

# ==== Flask（Render監視用）====
app = Flask(__name__)
CHAR_COUNT_FILE = "char_count.json"
PING_LOG_FILE = "ping_log.txt"
LAST_PING_FILE = "last_ping.txt"

@app.route("/", methods=["GET", "HEAD"])
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LAST_PING_FILE, "w") as f:
        f.write(now)
    with open(PING_LOG_FILE, "a") as f:
        f.write(now + "\n")
    return "OK", 200

@app.route("/char_count", methods=["GET"])
def get_char_count():
    if os.path.exists(CHAR_COUNT_FILE):
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, 200
    return {"count": 0, "month": "unknown"}, 200

def update_char_count(add_count: int):
    current_month = datetime.now().strftime("%Y-%m")
    if os.path.exists(CHAR_COUNT_FILE):
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"count": 0, "month": current_month}

    if data.get("month") != current_month:
        data = {"count": 0, "month": current_month}

    data["count"] += add_count
    with open(CHAR_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Flaskをバックグラウンドで起動
Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()

# ==== DeepL翻訳 ====
def translate(text, target_lang):
    response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    })
    if response.status_code == 200:
        update_char_count(len(text))  # ★ 翻訳ごとに文字数加算
        return response.json()["translations"][0]["text"]
    return "[翻訳エラー]"

# ==== 言語設定用ファイル ====
LANG_FILE = "user_lang.json"
def load_lang_settings():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_lang_settings(data):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== 言語候補 ====
LANG_CHOICES = [
    app_commands.Choice(name="Japanese", value="JA"),
    app_commands.Choice(name="English", value="EN"),
    app_commands.Choice(name="French", value="FR"),
    app_commands.Choice(name="German", value="DE"),
    app_commands.Choice(name="Korean", value="KO"),
    app_commands.Choice(name="Chinese", value="ZH"),
    app_commands.Choice(name="Spanish", value="ES"),
    app_commands.Choice(name="Russian", value="RU"),
    app_commands.Choice(name="Italian", value="IT")
]

# ==== Botの準備 ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== スラッシュコマンド登録 ====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ==== /setlang コマンド ====
@bot.tree.command(name="setlang", description="あなたの母国語を設定します")
@app_commands.choices(lang=LANG_CHOICES)
async def setlang(interaction: discord.Interaction, lang: app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    data = load_lang_settings()
    data[user_id] = lang.value
    save_lang_settings(data)
    await interaction.response.send_message(f"✅ あなたの母国語を `{lang.name}` に設定しました！", ephemeral=True)

# ==== DMで自動翻訳 ====
@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    lang_data = load_lang_settings()
    native_lang = lang_data.get(user_id, "JA")
    target_lang = "EN" if native_lang == "JA" else "JA"

    translated = translate(message.content, target_lang)
    await message.channel.send(f"{translated}")

# ==== Bot起動 ====
bot.run(DISCORD_TOKEN)
