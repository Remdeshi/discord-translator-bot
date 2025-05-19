import os
import discord
import asyncio
from threading import Thread
from datetime import datetime, timedelta
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
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")  # ← ここに書く！

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

def load_events(guild_id=None):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
            if guild_id is not None:
                events = [e for e in events if e.get("guild_id") == guild_id]
            return events
    except Exception as e:
        print(f"Failed to load events: {e}")
        return []


def save_events(events, guild_id=None):
    try:
        if guild_id is not None:
            all_events = load_events()  # 全イベント読み込み
            other_events = [e for e in all_events if e.get("guild_id") != guild_id]
            events = other_events + events
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save events: {e}")

import pytz
from datetime import datetime

def add_event(month, day, hour, minute, name, content, channel_id, guild_id, reminders=None):
    if reminders is None:
        reminders = [30, 20, 10]

    tz = pytz.timezone("Asia/Tokyo")
    now = datetime.now(tz)
    event_datetime = tz.localize(datetime(now.year, month, day, hour, minute))
    if event_datetime < now:
        event_datetime = event_datetime.replace(year=now.year + 1)

    event_datetime_utc = event_datetime.astimezone(pytz.UTC)

    event = {
        "datetime": event_datetime_utc.isoformat(),
        "name": name,
        "content": content,
        "channel_id": channel_id,
        "guild_id": guild_id,  # ここを追加！
        "announced": False,
        "reminders": reminders,
        "reminded": [False] * len(reminders)
    }

    events = load_events(guild_id=guild_id)  # guild_id指定でロード
    events.append(event)
    save_events(events, guild_id=guild_id)  # guild_id指定で保存



async def event_checker(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now(tz=pytz.UTC)  # UTC
        events = load_events()
        remaining_events = []

        for event in events:
            event_time = datetime.fromisoformat(event["datetime"])
            channel = bot.get_channel(event["channel_id"])
            if not channel:
                print(f"Channel with ID {event['channel_id']} not found.")
                remaining_events.append(event)
                continue

            # リマインダー通知処理
            for i, minutes_before in enumerate(event.get("reminders", [])):
                reminder_time = event_time - timedelta(minutes=minutes_before)
                # 通知対象時間の1分間の猶予でチェック
                if reminder_time <= now < reminder_time + timedelta(seconds=60):
                    if not event["reminded"][i]:
                        unix_timestamp = int(event_time.timestamp())
                        msg = (
                            f"⏰ イベント『{event['name']}』まであと{minutes_before}分です！\n"
                            f"{event['content']}\n"
                            f"日時: <t:{unix_timestamp}:F>"
                        )
                        try:
                            await channel.send(msg)
                            event["reminded"][i] = True  # 通知済みフラグON
                        except Exception as e:
                            print(f"Failed to send reminder: {e}")

            # イベント本番通知
            if now >= event_time:
                if not event["announced"]:
                    unix_timestamp = int(event_time.timestamp())
                    msg = (
                        f"📢 **イベント開始！** 📢\n"
                        f"**{event['name']}**\n"
                        f"{event['content']}\n"
                        f"日時: <t:{unix_timestamp}:F>"
                    )
                    try:
                        await channel.send(msg)
                        event["announced"] = True
                    except Exception as e:
                        print(f"Failed to send event message: {e}")
                # イベント完了なのでリストから除外
                continue
            else:
                remaining_events.append(event)

        save_events(remaining_events)
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

from discord import app_commands, TextChannel
from discord.ext import commands

from discord import app_commands, TextChannel
import discord

@bot.tree.command(name="addevent", description="イベントを登録します")
@app_commands.describe(
    month="month（1〜12）",
    day="day（1〜31）",
    hour="hour（0〜23）",
    minute="min（0〜59）",
    name="event_name",
    content="event",
    channel="channel",
    reminders="通知する分前（カンマ区切り、例: 30,20,10）",
    timezone="タイムゾーンを選択してください"
)
@app_commands.choices(
    timezone=[
        app_commands.Choice(name="日本時間 (JST)", value="JST"),
        app_commands.Choice(name="協定世界時 (UTC)", value="UTC"),
    ]
)
async def addevent(
    interaction: discord.Interaction,
    month: int,
    day: int,
    hour: int,
    minute: int,
    name: str,
    content: str,
    channel: TextChannel,
    reminders: str = None,
    timezone: str = "JST"  # ← ここだけ変更！
):
    reminder_list = []
    if reminders:
        try:
            reminder_list = [int(x.strip()) for x in reminders.split(",")]
        except ValueError:
            await interaction.response.send_message("リマインダーはカンマ区切りの数字で指定してください。", ephemeral=True)
            return

    await interaction.response.defer(ephemeral=True)

    try:
        add_event(
            month, day, hour, minute, name, content, channel.id,
            interaction.guild_id, reminder_list,
            timezone=timezone.value
        )
    except Exception as e:
        await interaction.followup.send(f"❌ イベント登録に失敗しました: {e}", ephemeral=True)
        return

    reminder_text = ""
    if reminder_list:
        reminder_text = "この通知は " + "、".join(f"{m}分前" for m in reminder_list) + " にお知らせします。"

    await interaction.followup.send(
        f"✅ イベント「{name}」を登録しました！\n{reminder_text}\nタイムゾーン: {timezone.value}",
        ephemeral=True
    )

@bot.tree.command(name="deleteevent", description="指定したイベントを削除します")
@app_commands.describe(index="削除するイベントの番号（/listevents で確認）")
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
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    guild_id = guild.id
    events = load_events(guild_id=guild_id)

    if not events:
        await interaction.followup.send("登録されているイベントはありません。", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"登録イベント一覧 - サーバー: {guild.name}",
        color=discord.Color.green()
    )

    timezone_jst = pytz.timezone("Asia/Tokyo")
    timezone_utc = pytz.UTC

    for i, event in enumerate(events, 1):
        timezone = event.get("timezone", "JST")
        dt = datetime.fromisoformat(event["datetime"])

        if timezone == "UTC":
            dt = dt.replace(tzinfo=timezone_utc)
        else:
            dt = dt.replace(tzinfo=timezone_utc).astimezone(timezone_jst)

        unix_timestamp = int(dt.timestamp())
        timestamp_str = f"<t:{unix_timestamp}:F>"

        name = event.get("name", "無名イベント")
        content = event.get("content", "")
        channel_id = event.get("channel_id", 0)
        channel = interaction.guild.get_channel(channel_id)
        channel_name = channel.name if channel else f"不明なチャンネル（ID: {channel_id}）"

        reminders = event.get("reminders", [])
        if reminders:
            reminder_text = "この通知は " + "、".join(f"{m}分前" for m in reminders) + " にお知らせします。"
        else:
            reminder_text = "リマインダー設定なし"

        embed.add_field(
            name=f"{i}. {name} - {timestamp_str}（{timezone}）",
            value=(
                f"📢 内容: {content}\n"
                f"📡 チャンネル: {channel_name}\n"
                f"🌍 タイムゾーン: {timezone}\n"
                f"⏰ {reminder_text}"
            ),
            inline=False,
        )

    await interaction.followup.send(embed=embed, ephemeral=True)



# DM翻訳（通常テキスト）
import aiohttp

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, "JA")
    other_lang = "EN" if native_lang != "EN" else "JA"

    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": message.content,
        "target_lang": "EN",  # とりあえずEN固定（あとで言語検出から切り替えも可）
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params) as resp:
            if resp.status != 200:
                await message.channel.send("[翻訳エラー]")
                return
            data = await resp.json()

    detected = data["translations"][0]["detected_source_language"]
    target = other_lang if detected == native_lang else native_lang

    # 再度翻訳（目的の言語に）
    if target != detected:
        params["target_lang"] = target
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as resp:
                if resp.status != 200:
                    await message.channel.send("[翻訳エラー]")
                    return
                data = await resp.json()
        translated = data["translations"][0]["text"]
    else:
        translated = message.content  # もし検出言語＝ターゲットなら翻訳不要

    await message.channel.send(translated)

    await bot.process_commands(message)  # 忘れずに





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

        embed = discord.Embed(
            description=translated,
            color=discord.Color.teal()
        )
        embed.set_author(
            name=user.display_name,
            icon_url=user.avatar.url if user.avatar else None
        )

        msg = await channel.send(embed=embed)  # 送信メッセージを保存

        await message.remove_reaction(payload.emoji, user)
        await asyncio.sleep(60)

        await msg.delete()  # 60秒後に翻訳メッセージ削除

    except Exception as e:
        print(f"リアクション翻訳エラー: {e}")


@bot.event
async def on_connect():
    bot.loop.create_task(event_checker(bot))

bot.run(DISCORD_TOKEN)
