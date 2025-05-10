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

# ==== Flask ====
app = Flask(__name__)
CHAR_COUNT_FILE = "char_count.json"
LAST_PING_FILE = "/tmp/last_ping.txt"
PING_LOG_FILE = "/tmp/ping_log.txt"

@app.route("/", methods=["GET", "HEAD"])
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.method == "HEAD":
        print(f"📡 HEADリクエスト受信（更新スキップ）: {now}")
        return "", 200
    with open(LAST_PING_FILE, "w") as f:
        f.write(now)
    with open(PING_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] UptimeRobot : 正常\n")
    print(f"📡 GETリクエストでPing更新: {now}")
    return "OK", 200

@app.route("/last_ping", methods=["GET"])
def get_last_ping():
    if os.path.exists(LAST_PING_FILE):
        with open(LAST_PING_FILE, "r") as f:
            return {"last_ping": f.read().strip()}, 200
    return {"last_ping": "まだ受信なし"}, 200

@app.route("/char_count", methods=["GET"])
def get_char_count():
    if os.path.exists(CHAR_COUNT_FILE):
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, 200
    return {"count": 0, "month": "unknown"}, 200

@app.route("/ping_log", methods=["GET"])
def get_ping_log():
    if os.path.exists(PING_LOG_FILE):
        with open(PING_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_10 = lines[-10:] if len(lines) >= 10 else lines
        return {"log": "".join(last_10)}, 200
    return {"log": "ログが存在しません"}, 200

Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()

# ==== 翻訳文字数管理 ====
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

# ==== DeepL翻訳 ====
def translate(text, target_lang):
    response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    })
    if response.status_code == 200:
        update_char_count(len(text))
        return response.json()["translations"][0]["text"]
    return "[翻訳エラー]"

# ==== 言語設定 ====
LANG_FILE = "user_lang.json"
def load_lang_settings():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def save_lang_settings(data):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== Discord Bot ====
flag_map = {
    "🇧🇬": "BG", "🇨🇳": "ZH", "🇨🇿": "CS", "🇩🇰": "DA", "🇳🇱": "NL", "🇺🇸": "EN", "🇬🇧": "EN",
    "🇪🇪": "ET", "🇫🇮": "FI", "🇫🇷": "FR", "🇩🇪": "DE", "🇬🇷": "EL", "🇭🇺": "HU", "🇮🇩": "ID",
    "🇮🇹": "IT", "🇯🇵": "JA", "🇰🇷": "KO", "🇱🇻": "LV", "🇱🇹": "LT", "🇵🇱": "PL", "🇵🇹": "PT",
    "🇧🇷": "PT", "🇷🇴": "RO", "🇷🇺": "RU", "🇸🇰": "SK", "🇸🇮": "SL", "🇪🇸": "ES"
}

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

LANG_CHOICES = [app_commands.Choice(name=name, value=code) for name, code in [
    ("Bulgarian", "BG"), ("Chinese", "ZH"), ("Czech", "CS"), ("Danish", "DA"),
    ("Dutch", "NL"), ("English", "EN"), ("Estonian", "ET"), ("Finnish", "FI"),
    ("French", "FR"), ("German", "DE"), ("Greek", "EL"), ("Hungarian", "HU"),
    ("Indonesian", "ID"), ("Italian", "IT"), ("Japanese", "JA"), ("Korean", "KO"),
    ("Latvian", "LV"), ("Lithuanian", "LT"), ("Polish", "PL"), ("Portuguese", "PT"),
    ("Romanian", "RO"), ("Russian", "RU"), ("Slovak", "SK"), ("Slovenian", "SL"),
    ("Spanish", "ES")
]]

@bot.tree.command(name="setlang", description="あなたの母国語を設定します")
@app_commands.choices(lang=LANG_CHOICES)
async def setlang(interaction: discord.Interaction, lang: app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    data = load_lang_settings()
    data[user_id] = lang.value
    save_lang_settings(data)
    await interaction.response.send_message(f"✅ あなたの母国語を `{lang.name}` に設定しました！", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ==== DMで相互翻訳 ====
@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    lang_data = load_lang_settings()
    native_lang = lang_data.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"
    text = message.content

    detect_res = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": "EN"
    })
    if detect_res.status_code != 200:
        await message.channel.send("[翻訳エラー]")
        return

    detected_lang = detect_res.json()["translations"][0]["detected_source_language"]
    target_lang = other_lang if detected_lang == native_lang else native_lang
    translated = translate(text, target_lang)

    embed = discord.Embed(description=translated, color=discord.Color.teal())
    await message.channel.send(embed=embed)

# ==== リアクション翻訳 ====
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    emoji = str(payload.emoji)
    if emoji not in flag_map:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
        user = await bot.fetch_user(payload.user_id)
        translated = translate(message.content, flag_map[emoji])

        embed = discord.Embed(description=translated, color=discord.Color.teal())
        reply = await channel.send(f"<@{payload.user_id}> {emoji}", embed=embed)
        await message.remove_reaction(emoji, user)
        await asyncio.sleep(60)
        await reply.delete()
    except Exception as e:
        print(f"リアクション翻訳エラー: {e}")

# ==== Bot起動 ====
bot.run(DISCORD_TOKEN)
