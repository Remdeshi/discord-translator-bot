
import os
import discord
import requests
import asyncio
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot is running!", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)

# 拡張された国旗対応表
flag_map = {
    "🇯🇵": "JA", "🇺🇸": "EN", "🇬🇧": "EN", "🇨🇦": "EN", "🇦🇺": "EN",
    "🇫🇷": "FR", "🇩🇪": "DE", "🇪🇸": "ES", "🇮🇹": "IT", "🇳🇱": "NL",
    "🇵🇹": "PT", "🇷🇺": "RU", "🇰🇷": "KO", "🇨🇳": "ZH", "🇹🇼": "ZH",
    "🇸🇪": "SV", "🇳🇴": "NB", "🇩🇰": "DA", "🇫🇮": "FI", "🇹🇭": "TH",
    "🇮🇩": "ID", "🇵🇱": "PL", "🇨🇿": "CS", "🇷🇴": "RO", "🇹🇷": "TR",
    "🇺🇦": "UK", "🇭🇺": "HU", "🇧🇬": "BG"
}

def translate(text, target_lang):
    response = requests.post(DEEPL_API_URL, data={
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    })
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    return "[翻訳エラー]"

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

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

client.run(DISCORD_TOKEN)
