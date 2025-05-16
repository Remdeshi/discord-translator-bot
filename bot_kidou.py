import os
import discord
import asyncio
from threading import Thread
from datetime import datetime
import pytz
from dotenv import load_dotenv
import json

from discord import app_commands, TextChannel  # ← ここでTextChannelをimport
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

DATA_DIR = "data"
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")

def load_events():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load events: {e}")
        return []

def save_events(events):
    try:
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save events: {e}")

def add_event(month, day, hour, minute, name, content, channel_id):
    now = datetime.now()
    event_datetime = datetime(now.year, month, day, hour, minute)
    if event_datetime < now:
        event_datetime = event_datetime.replace(year=now.year + 1)

    event = {
        "datetime": event_datetime.isoformat(),
        "name": name,
        "content": content,
        "channel_id": channel_id,
        "announced": False
    }
    events = load_events()
    events.append(event)
    save_events(events)

async def event_checker(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        events = load_events()
        updated = False

        for event in events:
            event_time = datetime.fromisoformat(event["datetime"])
            if not event.get("announced") and now >= event_time:
                channel = bot.get_channel(event["channel_id"])
                if channel:
                    msg = (
                        f"📢 **イベント通知** 📢\n"
                        f"**{event['name']}**\n"
                        f"{event['content']}\n"
                        f"日時: {event_time.strftime('%m/%d %H:%M')}"
                    )
                    try:
                        await channel.send(msg)
                        event["announced"] = True
                        updated = True
                    except Exception as e:
                        print(f"Failed to send event message: {e}")

        if updated:
            save_events(events)

        await asyncio.sleep(60)

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

@bot.tree.command(name="addevent", description="イベントを登録します")
@app_commands.describe(
    month="month（1〜12）",
    day="day（1〜31）",
    hour="hour（0〜23）",
    minute="min（0〜59）",
    name="event_name",
    content="event",
    channel="channel"
)
async def addevent(
    interaction: discord.Interaction,
    month: int,
    day: int,
    hour: int,
    minute: int,
    name: str,
    content: str,
    channel: TextChannel  # ← 修正済み
):
    try:
        add_event(month, day, hour, minute, name, content, channel.id)  # ← channel_idではなくchannel.id
        await interaction.response.send_message(f"✅ イベント「{name}」を登録しました！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ イベント登録に失敗しました: {e}", ephemeral=True)

@bot.tree.command(name="deleteevent", description="登録済みのイベントを削除します")
@app_commands.describe(index="削除したいイベントの番号")
async def deleteevent(interaction: discord.Interaction, index: int):
    events = load_events()
    if not events:
        await interaction.response.send_message("登録されているイベントはありません。", ephemeral=True)
        return

    if index < 1 or index > len(events):
        await interaction.response.send_message("無効なイベント番号です。", ephemeral=True)
        return

    removed_event = events.pop(index - 1)
    save_events(events)
    await interaction.response.send_message(
        f"✅ イベント「{removed_event.get('name', '無名イベント')}」を削除しました。", ephemeral=True
    )


@bot.tree.command(name="listevents", description="登録済みイベントの一覧を表示します")
async def listevents(interaction: discord.Interaction):
    events = load_events()
    if not events:
        await interaction.response.send_message("登録されているイベントはありません。", ephemeral=True)
        return

    embed = discord.Embed(title="登録イベント一覧", color=discord.Color.green())
    for i, event in enumerate(events, 1):
        dt = datetime.fromisoformat(event["datetime"])
        name = event.get("name", "無名イベント")
        content = event.get("content", "")
        channel_id = event.get("channel_id", 0)
        embed.add_field(
            name=f"{i}. {name} - {dt.strftime('%m/%d %H:%M')}",
            value=f"内容: {content}\n送信先チャンネルID: {channel_id}",
            inline=False,
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"

    target = other_lang
    translated = await translate(message.content, target)

    if translated == "[翻訳エラー]":
        await message.channel.send(translated)
    else:
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

@bot.event
async def on_connect():
    bot.loop.create_task(event_checker(bot))

bot.run(DISCORD_TOKEN)
