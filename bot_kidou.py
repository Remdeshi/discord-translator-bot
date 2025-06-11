import os
import json
import pytz
from datetime import datetime, timedelta
import discord
from discord import app_commands, TextChannel
from discord.ext import commands, tasks
from deepl import Translator
import random

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
translator = Translator(os.environ["DEEPL_AUTH_KEY"])

DATA_DIR = "data"
EVENTS_DIR = os.path.join(DATA_DIR, "events")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(EVENTS_DIR):
    os.makedirs(EVENTS_DIR)


def ensure_data_files():
    # 特にメインフォルダは上で作ってるが、念のため
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(EVENTS_DIR):
        os.makedirs(EVENTS_DIR)


def get_events_file_path(guild_id: int) -> str:
    return os.path.join(EVENTS_DIR, f"events_{guild_id}.json")


def load_events(guild_id: int):
    filepath = get_events_file_path(guild_id)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events, guild_id: int):
    filepath = get_events_file_path(guild_id)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)


def add_event(guild_id: int, title, datetime_obj, channel_id, timezone, reminders):
    events = load_events(guild_id)
    event = {
        "title": title,
        "datetime": datetime_obj.isoformat(),
        "channel_id": channel_id,
        "reminders": reminders,
        "reminded": [False] * len(reminders),
        "timezone": timezone
    }
    events.append(event)
    save_events(events, guild_id)


@bot.event
async def on_ready():
    ensure_data_files()
    await bot.tree.sync()
    bot.loop.create_task(event_checker(bot))
    print(f"✅ Logged in as {bot.user}")


@bot.tree.command(name="addevent", description="イベントを追加します")
@app_commands.describe(
    title="イベントタイトル",
    date="イベントの日付 (YYYY-MM-DD)",
    time="イベントの時刻 (HH:MM 24時間制)",
    channel="通知するテキストチャンネル",
    timezone="タイムゾーン (例: Asia/Tokyo)",
    reminders="リマインダー時間(分)をカンマ区切りで入力(例: 1440,60,10)"
)
async def addevent(interaction: discord.Interaction, title: str, date: str, time: str, channel: TextChannel, timezone: str, reminders: str):
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        await interaction.response.send_message(f"無効なタイムゾーンです: {timezone}", ephemeral=True)
        return

    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("日付か時刻の形式が間違っています。", ephemeral=True)
        return

    dt = tz.localize(dt)

    try:
        reminders_list = [int(x.strip()) for x in reminders.split(",") if x.strip()]
    except ValueError:
        await interaction.response.send_message("リマインダーは整数の分でカンマ区切りで指定してください。", ephemeral=True)
        return

    add_event(interaction.guild_id, title, dt, channel.id, timezone, reminders_list)

    await interaction.response.send_message(f"イベント「{title}」を追加しました。", ephemeral=True)


@bot.tree.command(name="listevents", description="登録されているイベント一覧を表示します")
async def listevents(interaction: discord.Interaction):
    events = load_events(interaction.guild_id)
    if not events:
        await interaction.response.send_message("イベントは登録されていません。", ephemeral=True)
        return

    # datetime順にソート
    events.sort(key=lambda e: e["datetime"])

    embed = discord.Embed(title="登録イベント一覧")
    for i, event in enumerate(events, start=1):
        dt = datetime.fromisoformat(event["datetime"])
        tz = pytz.timezone(event.get("timezone", "UTC"))
        dt_local = dt.astimezone(tz)
        dt_str = dt_local.strftime("%Y-%m-%d %H:%M %Z")

        reminders_str = ", ".join(str(r) + "分前" for r in event["reminders"])
        embed.add_field(
            name=f"{i}. {event['title']}",
            value=f"日時: {dt_str}\n通知先チャンネルID: {event['channel_id']}\nリマインダー: {reminders_str}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="deleteevent", description="イベントを削除します")
@app_commands.describe(number="削除するイベント番号")
async def deleteevent(interaction: discord.Interaction, number: int):
    events = load_events(interaction.guild_id)
    if number < 1 or number > len(events):
        await interaction.response.send_message("無効な番号です。", ephemeral=True)
        return

    removed_event = events.pop(number - 1)
    save_events(events, interaction.guild_id)
    await interaction.response.send_message(f"イベント「{removed_event['title']}」を削除しました。", ephemeral=True)


async def event_checker(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        for guild in bot.guilds:
            events = load_events(guild.id)
            for event in events:
                event_dt = datetime.fromisoformat(event["datetime"]).replace(tzinfo=pytz.utc)
                reminders = event["reminders"]
                reminded_flags = event["reminded"]
                channel = guild.get_channel(event["channel_id"])
                if channel is None:
                    continue

                for idx, reminder_minutes in enumerate(reminders):
                    if not reminded_flags[idx]:
                        notify_time = event_dt - timedelta(minutes=reminder_minutes)
                        if notify_time <= now_utc <= notify_time + timedelta(seconds=60):
                            try:
                                await channel.send(f"イベント「{event['title']}」のリマインダー: {reminder_minutes}分前です！")
                                reminded_flags[idx] = True
                            except Exception as e:
                                print(f"Error sending reminder: {e}")

            save_events(events, guild.id)
        await discord.utils.sleep_until(datetime.utcnow() + timedelta(seconds=30))  # 30秒間隔でチェック


@bot.tree.command(name="translate", description="指定したテキストを日本語か英語に翻訳します。")
@app_commands.describe(text="翻訳するテキスト")
async def translate(interaction: discord.Interaction, text: str):
    if not text:
        await interaction.response.send_message("翻訳するテキストを入力してください。", ephemeral=True)
        return

    if any('\u3040' <= ch <= '\u309F' or '\u30A0' <= ch <= '\u30FF' for ch in text):
        # 日本語文字が含まれていたら英語へ翻訳
        target_lang = "EN"
    else:
        # それ以外は日本語へ翻訳
        target_lang = "JA"

    try:
        result = translator.translate_text(text, target_lang=target_lang)
        await interaction.response.send_message(f"翻訳結果:\n{result.text}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"翻訳エラー: {e}", ephemeral=True)


bot.run(os.environ["DISCORD_BOT_TOKEN"])
