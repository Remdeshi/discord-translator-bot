import os
import discord
import asyncio
from threading import Thread
from datetime import datetime
import pytz
from dotenv import load_dotenv
import aiohttp  # 追加
from discord import app_commands
from discord.ext import commands

from utils.translate import translate  # これをasync対応にするのが理想です
from utils.lang_settings import load_lang_settings, save_lang_settings
from web.uptime_server import start_flask

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# ... flag_map や選択肢リストは省略 ...

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

Thread(target=start_flask, daemon=True).start()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)  # 他のコマンドも動かすため
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"

    # 非同期でDeepLの言語検出を行う
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": os.getenv("DEEPL_API_KEY"),
                "text": message.content,
                "target_lang": "EN"
            }
        ) as res:
            if res.status != 200:
                await message.channel.send("[翻訳エラー]")
                return
            res_json = await res.json()

    detected = res_json["translations"][0]["detected_source_language"]
    target = other_lang if detected == native_lang else native_lang

    # translate() が非同期なら await つける形に修正してください
    translated = await translate(message.content, target)

    await message.channel.send(translated)

# それ以外のコマンドやリアクション翻訳はそのままでOKです

bot.run(DISCORD_TOKEN)
