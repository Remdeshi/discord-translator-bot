import os
import discord
import asyncio
from threading import Thread
from datetime import datetime
import pytz
from dotenv import load_dotenv

from discord import app_commands
from discord.ext import commands

from utils.translate import translate
from utils.lang_settings import load_lang_settings, save_lang_settings
from web.uptime_server import start_flask

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

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
    discord.app_commands.Choice(name="BRT (Brazil)", value="America/Sao_Paulo"),
    discord.app_commands.Choice(name="ART (Argentina)", value="America/Argentina/Buenos_Aires"),
    discord.app_commands.Choice(name="Uruguay", value="America/Montevideo"),
    discord.app_commands.Choice(name="Suriname", value="America/Paramaribo"),
    discord.app_commands.Choice(name="Falkland Islands", value="Atlantic/Stanley"),
]

LANG_CHOICES = [discord.app_commands.Choice(name=name, value=code) for name, code in [
    ("Bulgarian", "BG"), ("Chinese", "ZH"), ("Czech", "CS"), ("Danish", "DA"),
    ("Dutch", "NL"), ("English", "EN"), ("Estonian", "ET"), ("Finnish", "FI"),
    ("French", "FR"), ("German", "DE"), ("Greek", "EL"), ("Hungarian", "HU"),
    ("Indonesian", "ID"), ("Italian", "IT"), ("Japanese", "JA"), ("Korean", "KO"),
    ("Latvian", "LV"), ("Lithuanian", "LT"), ("Polish", "PL"), ("Portuguese", "PT"),
    ("Romanian", "RO"), ("Russian", "RU"), ("Slovak", "SK"), ("Slovenian", "SL"),
    ("Spanish", "ES")
]]

Thread(target=start_flask, daemon=True).start()

import aiohttp

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="setlang", description="あなたの母国語を設定します")
@app_commands.choices(lang=LANG_CHOICES)
async def setlang(interaction: discord.Interaction, lang: discord.app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    data = load_lang_settings()
    data[user_id] = lang.value
    save_lang_settings(data)
    await interaction.response.send_message(f"✅ あなたの母国語を {lang.name} に設定しました！", ephemeral=True)

@bot.tree.command(name="create_timestamp", description="指定した日付と時刻をタイムゾーン付きで表示します")
@app_commands.choices(timezone=TIMEZONE_CHOICES)
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

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"

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

            data = await res.json()
            detected = data["translations"][0]["detected_source_language"]
            target = other_lang if detected == native_lang else native_lang
            translated = await translate(message.content, target)

            await message.channel.send(translated)

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
        translated = await translate(message.content, flag_map[str(payload.emoji)])

        embed = discord.Embed(description=translated, color=discord.Color.teal())
        embed.set_footer(text=f"{user.display_name}")
        reply = await message.reply(embed=embed)

        await message.remove_reaction(payload.emoji, user)
        await asyncio.sleep(60)
        await reply.delete()
    except Exception as e:
        print(f"リアクション翻訳エラー: {e}")

bot.run(DISCORD_TOKEN)
