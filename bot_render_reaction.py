import os
import json
import discord
import requests
import asyncio
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# ==== 環境変数読み込み ====
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

# ==== Flask（Render用） ====
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot is running!", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask, daemon=True).start()

# ==== Discord Bot 初期化 ====
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# ==== 国旗とDeepL対応言語のマッピング ====
flag_map = {
    "🇯🇵": "JA", "🇺🇸": "EN", "🇬🇧": "EN", "🇨🇦": "EN", "🇦🇺": "EN",
    "🇫🇷": "FR", "🇩🇪": "DE", "🇪🇸": "ES", "🇮🇹": "IT", "🇳🇱": "NL",
    "🇵🇹": "PT", "🇷🇺": "RU", "🇰🇷": "KO", "🇨🇳": "ZH", "🇹🇼": "ZH",
    "🇸🇪": "SV", "🇳🇴": "NB", "🇩🇰": "DA", "🇫🇮": "FI", "🇹🇭": "TH",
    "🇮🇩": "ID", "🇵🇱": "PL", "🇨🇿": "CS", "🇷🇴": "RO", "🇹🇷": "TR",
    "🇺🇦": "UK", "🇭🇺": "HU", "🇧🇬": "BG"
}

# ==== 言語設定ファイル ====
LANG_FILE = "user_lang.json"

def load_lang_settings():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_lang_settings(data):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== DeepL 翻訳関数 ====
def translate(text, target_lang):
    response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    })
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    return "[翻訳エラー]"

# ==== Botログイン時 ====
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

# ==== DMで母国語設定＆翻訳 ====
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        content = message.content.strip().lower()
        user_id = str(message.author.id)
        lang_data = load_lang_settings()

        # 母国語設定コマンド
        if content.startswith("/setlang "):
            lang_code = content.replace("/setlang ", "").upper()
            if lang_code in flag_map.values():
                lang_data[user_id] = lang_code
                save_lang_settings(lang_data)
                await message.channel.send(f"✅ 母国語を `{lang_code}` に設定しました！")
            else:
                await message.channel.send("⚠️ 無効な言語コードです。例: `/setlang EN`")
            return

        if content == "/setlang":
            langs = ", ".join(sorted(set(flag_map.values())))
            await message.channel.send(f"🌐 対応言語コード一覧:\n{langs}\n例: `/setlang JA`")
            return

        # 通常メッセージ：翻訳処理
        native_lang = lang_data.get(user_id, "JA")
        target_lang = "EN" if native_lang == "JA" else "JA"
        translated = translate(message.content, target_lang)
        await message.channel.send(f"🗣️ {translated}")

# ==== サーバーでリアクション翻訳 ====
@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    emoji = str(payload.emoji)
    if emoji not in flag_map:
        return

    channel = client.get_channel(payload.channel_id)
    if not channel:
        return

    try:
        message = await channel.fetch_message(payload.message_id)
        user = await client.fetch_user(payload.user_id)
        translated = translate(message.content, flag_map[emoji])
        reply = await channel.send(f"<@{payload.user_id}> {emoji} {translated}")
        await message.remove_reaction(emoji, user)
        await asyncio.sleep(30)
        await reply.delete()
    except Exception as e:
        print(f"エラー: {e}")

# ==== Bot起動 ====
client.run(DISCORD_TOKEN)
