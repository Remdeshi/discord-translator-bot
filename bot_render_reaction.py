import os
import json
import discord
import requests
import asyncio
from flask import Flask, request
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv
import pytz

from discord import app_commands  # ← ★ これを追加
from discord.ext import commands

# ==== 環境変数読み込み ====
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

# ==== Flask アプリ設定 ====
app = Flask(__name__)
CHAR_COUNT_FILE = "char_count.json"
LAST_PING_FILE = "/tmp/last_ping.txt"
PING_LOG_FILE = "/tmp/ping_log.txt"

def start_flask():
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
                return json.load(f), 200
        return {"count": 0, "month": "unknown"}, 200

    @app.route("/ping_log", methods=["GET"])
    def get_ping_log():
        if os.path.exists(PING_LOG_FILE):
            with open(PING_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return {"log": "".join(lines[-10:])}, 200
        return {"log": "ログが存在しません"}, 200

    app.run(host="0.0.0.0", port=8080)

Thread(target=start_flask, daemon=True).start()

# ==== 翻訳・文字数管理 ====
def update_char_count(add_count: int):
    current_month = datetime.now().strftime("%Y-%m")
    data = {"count": 0, "month": current_month}

    if os.path.exists(CHAR_COUNT_FILE):
        with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("month") != current_month:
            data = {"count": 0, "month": current_month}

    data["count"] += add_count
    with open(CHAR_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_lang_settings(data):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== Discord Bot設定 ====
flag_map = {
    "🇧🇬": "BG", "🇨🇳": "ZH", "🇨🇿": "CS", "🇩🇰": "DA", "🇳🇱": "NL", "🇺🇸": "EN", "🇬🇧": "EN",
    "🇪🇪": "ET", "🇫🇮": "FI", "🇫🇷": "FR", "🇩🇪": "DE", "🇬🇷": "EL", "🇭🇺": "HU", "🇮🇩": "ID",
    "🇮🇹": "IT", "🇯🇵": "JA", "🇰🇷": "KO", "🇱🇻": "LV", "🇱🇹": "LT", "🇵🇱": "PL", "🇵🇹": "PT",
    "🇧🇷": "PT", "🇷🇴": "RO", "🇷🇺": "RU", "🇸🇰": "SK", "🇸🇮": "SL", "🇪🇸": "ES"
}

from discord.ext import commands  # ← 上の方にない場合は追加

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


# タイムゾーンの簡潔な選択肢
TIMEZONE_CHOICES = [
    discord.app_commands.Choice(name="JST", value="Asia/Tokyo"),
    discord.app_commands.Choice(name="UTC", value="UTC"),
    discord.app_commands.Choice(name="EST", value="America/New_York"),
    discord.app_commands.Choice(name="PST", value="America/Los_Angeles"),
    discord.app_commands.Choice(name="CST", value="America/Chicago"),
    discord.app_commands.Choice(name="MST", value="America/Denver"),
    discord.app_commands.Choice(name="AKST", value="America/Anchorage"),
    discord.app_commands.Choice(name="HST", value="Pacific/Honolulu"),
    discord.app_commands.Choice(name="GMT", value="Europe/London"),
    discord.app_commands.Choice(name="CET", value="Europe/Berlin"),
    discord.app_commands.Choice(name="EET", value="Europe/Helsinki"),
    discord.app_commands.Choice(name="MSK", value="Europe/Moscow"),
    discord.app_commands.Choice(name="IST", value="Asia/Kolkata"),
    discord.app_commands.Choice(name="HKT", value="Asia/Hong_Kong"),
    discord.app_commands.Choice(name="SGT", value="Asia/Singapore"),
    discord.app_commands.Choice(name="KST", value="Asia/Seoul"),
    discord.app_commands.Choice(name="AEST", value="Australia/Sydney"),
    discord.app_commands.Choice(name="NZDT", value="Pacific/Auckland"),
     # ここからUTC-3関連タイムゾーン追加
    discord.app_commands.Choice(name="BRT (Brazil)", value="America/Sao_Paulo"),
    discord.app_commands.Choice(name="ART (Argentina)", value="America/Argentina/Buenos_Aires"),
    discord.app_commands.Choice(name="Uruguay", value="America/Montevideo"),
    discord.app_commands.Choice(name="Suriname", value="America/Paramaribo"),
    discord.app_commands.Choice(name="Falkland Islands", value="Atlantic/Stanley"),
    
]

# 言語選択肢の定義
LANG_CHOICES = [discord.app_commands.Choice(name=name, value=code) for name, code in [
    ("Bulgarian", "BG"), ("Chinese", "ZH"), ("Czech", "CS"), ("Danish", "DA"),
    ("Dutch", "NL"), ("English", "EN"), ("Estonian", "ET"), ("Finnish", "FI"),
    ("French", "FR"), ("German", "DE"), ("Greek", "EL"), ("Hungarian", "HU"),
    ("Indonesian", "ID"), ("Italian", "IT"), ("Japanese", "JA"), ("Korean", "KO"),
    ("Latvian", "LV"), ("Lithuanian", "LT"), ("Polish", "PL"), ("Portuguese", "PT"),
    ("Romanian", "RO"), ("Russian", "RU"), ("Slovak", "SK"), ("Slovenian", "SL"),
    ("Spanish", "ES")
]]

@bot.event
async def on_ready():
    await bot.tree.sync()  # スラッシュコマンドを同期するための行
    print(f"✅ Logged in as {bot.user}")


# 言語設定コマンド
@bot.tree.command(name="setlang", description="あなたの母国語を設定します")
@app_commands.choices(lang=LANG_CHOICES)
async def setlang(interaction: discord.Interaction, lang: discord.app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    data = load_lang_settings()
    data[user_id] = lang.value
    save_lang_settings(data)
    await interaction.response.send_message(f"✅ あなたの母国語を {lang.name} に設定しました！", ephemeral=True)

# タイムスタンプ作成コマンド
@bot.tree.command(name="create_timestamp", description="指定した日付と時刻をタイムゾーン付きで表示します")
@app_commands.choices(timezone=TIMEZONE_CHOICES)  # ← これを追加！
async def create_timestamp(
    interaction: discord.Interaction,
    month: int,
    day: int,
    hour: int,
    minute: int,
    timezone: discord.app_commands.Choice[str]
):
    tz = pytz.timezone(timezone.value)
    dt = tz.localize(datetime(datetime.now().year, month, day, hour, minute))
    unix_time = int(dt.timestamp())
    timestamp_str = f"<t:{unix_time}>"
    embed = discord.Embed(title="TimeStamp", description=f"🕒 {timestamp_str}", color=discord.Color.blue())
    embed.add_field(name="TimeZone", value=timezone.name, inline=False)
    await interaction.response.send_message(embed=embed)


# DM翻訳（通常テキスト）
@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"

    res = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": message.content,
        "target_lang": "EN"
    })
    if res.status_code != 200:
        await message.channel.send("[翻訳エラー]")
        return

    detected = res.json()["translations"][0]["detected_source_language"]
    target = other_lang if detected == native_lang else native_lang
    translated = translate(message.content, target)

    await message.channel.send(translated)

# リアクション翻訳（埋め込みメッセージ）
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) not in flag_map:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
        user = await bot.fetch_user(payload.user_id)
        translated = translate(message.content, flag_map[str(payload.emoji)])

        embed = discord.Embed(description=translated, color=discord.Color.teal())
        embed.set_footer(text=f"{user.display_name}")
        reply = await message.reply(embed=embed)

        await message.remove_reaction(payload.emoji, user)
        await asyncio.sleep(60)
        await reply.delete()
    except Exception as e:
        print(f"リアクション翻訳エラー: {e}")

# Bot起動
bot.run(DISCORD_TOKEN)
