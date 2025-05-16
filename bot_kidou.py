import os
import discord
import asyncio
from threading import Thread
from datetime import datetime
import pytz
from dotenv import load_dotenv
import aiohttp
from discord import app_commands
from discord.ext import commands

from utils.translate import translate
from utils.lang_settings import load_lang_settings, save_lang_settings
from web.uptime_server import start_flask

import json

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

Thread(target=start_flask, daemon=True).start()

EVENT_FILE = "data/event.json"
EVENT_CHANNEL_FILE = "data/event_channel.json"

def load_events():
    if not os.path.exists(EVENT_FILE):
        return []
    with open(EVENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(events):
    os.makedirs(os.path.dirname(EVENT_FILE), exist_ok=True)
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def load_event_channel():
    if not os.path.exists(EVENT_CHANNEL_FILE):
        return None
    with open(EVENT_CHANNEL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("channel_id")

def save_event_channel(channel_id):
    os.makedirs(os.path.dirname(EVENT_CHANNEL_FILE), exist_ok=True)
    with open(EVENT_CHANNEL_FILE, "w", encoding="utf-8") as f:
        json.dump({"channel_id": channel_id}, f, ensure_ascii=False, indent=2)

def add_event(event):
    events = load_events()
    events.append(event)
    save_events(events)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

    # 予約イベントを監視して通知を送るタスクを起動
    bot.loop.create_task(event_announcer_task())

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
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
            res_json = await res.json()

    detected = res_json["translations"][0]["detected_source_language"]
    target = other_lang if detected == native_lang else native_lang

    translated = await translate(message.content, target)
    await message.channel.send(translated)

@bot.tree.command(name="event", description="Schedule an event announcement")
@app_commands.describe(
    month="Month (1-12)",
    day="Day (1-31)",
    hour="Hour (0-23)",
    minute="Minute (0-59)",
    name="Event name",
    content="Event description"
)
async def event(interaction: discord.Interaction, month: int, day: int, hour: int, minute: int, name: str, content: str):
    if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59):
        await interaction.response.send_message("❌ Invalid date or time values.", ephemeral=True)
        return

    dt = datetime(datetime.now().year, month, day, hour, minute)
    add_event({
        "datetime": dt.isoformat(),
        "name": name,
        "content": content,
        "announced": False
    })
    await interaction.response.send_message(
        f"✅ Event '{name}' scheduled for {month}/{day} {hour:02}:{minute:02}.", ephemeral=True
    )

@bot.tree.command(name="seteventchannel", description="Set the channel for event announcements")
@app_commands.describe(channel="The text channel to send event announcements")
async def seteventchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    save_event_channel(channel.id)
    await interaction.response.send_message(f"✅ Event announcement channel set to {channel.mention}!", ephemeral=True)

async def event_announcer_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        events = load_events()
        channel_id = load_event_channel()
        if channel_id is None:
            await asyncio.sleep(60)
            continue
        channel = bot.get_channel(channel_id)
        if channel is None:
            await asyncio.sleep(60)
            continue

        updated = False
        for event in events:
            if event["announced"]:
                continue
            event_time = datetime.fromisoformat(event["datetime"])
            if now >= event_time:
                msg = f"📢 **Event Reminder:** {event['name']}\n{event['content']}\n🕒 Scheduled for {event_time.strftime('%Y-%m-%d %H:%M')}"
                try:
                    await channel.send(msg)
                    event["announced"] = True
                    updated = True
                except Exception as e:
                    print(f"Failed to send event announcement: {e}")

        if updated:
            save_events(events)

        await asyncio.sleep(60)  # 1分ごとにチェック

bot.run(DISCORD_TOKEN)
