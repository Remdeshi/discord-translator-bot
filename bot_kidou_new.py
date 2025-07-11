# -*- coding: utf-8 -*-
"""
Discrdボット起動ファイル
・翻訳機能：DM、国旗リアクション、複数翻訳リアクション
・イベント通知管理機能：
"""
import asyncio
import os
import json
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from threading import Thread

import discord
from discord import app_commands, TextChannel  # ← ここでTextChannelをimport
from discord.ext import commands

# 関連pythonファイルのロード
import config  # config.py をインポート
import utils.translate_pub as tr
from utils.translate import translate
from utils.lang_settings import load_lang_settings, save_lang_settings
from web.uptime_server import start_flask


TRANSLATE_MESSAGE_DICT = {}


# 関連フォルダ・ファイルの初期化
def ensure_data_files():
    """
    関連フォルダ・ファイルの初期化処理。
    config.py の定数を参照。
    """
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)

    if not os.path.exists(config.TEMP_DIR):
        os.makedirs(config.TEMP_DIR)

    if not os.path.exists(config.EVENTS_FILE):
        with open(config.EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(config.USER_LANG_FILE):
        with open(config.USER_LANG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    return


# 翻訳用インスタンス作成
tran = tr.Translator(api_key=config.DEEPL_API_KEY, char_count_file=config.CHAR_COUNT_FILE)

# Botの権限の設定
intents = discord.Intents.default()
intents.members = True # メンバー管理の権限
intents.message_content = True # メッセージの内容を取得する権限
intents.messages = True
intents.reactions = True

# Botをインスタンス化
bot = commands.Bot(
    command_prefix="!", # $コマンド名　でコマンドを実行できるようになる
    # case_insensitive=True, # コマンドの大文字小文字を区別しない ($hello も $Hello も同じ!)
    intents=intents # 権限を設定
)

# Flaskサーバーを別スレッドで起動
Thread(target=start_flask, daemon=True).start()

def load_events(guild_id=None):
    # DATA_DIR の存在確認と作成は config.py で実行される
    if not os.path.exists(config.EVENTS_FILE):
        with open(config.EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []

    try:
        with open(config.EVENTS_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
            if guild_id is not None:
                events = [data for data in events if data.get("guild_id") == guild_id]
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
        with open(config.EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save events: {e}")


def add_event(month, day, hour, minute, name, content, channel_id, guild_id, reminders=None, timezone="JST"):
    print("🟢 add_event 開始")

    if reminders is None:
        reminders = [30, 20, 10]

    if timezone == "JST":
        tz = pytz.timezone("Asia/Tokyo")
    elif timezone == "UTC":
        tz = pytz.UTC
    else:
        tz = pytz.UTC # デフォルトはUTC

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
        "guild_id": guild_id,
        "announced": False,
        "reminders": reminders,
        "reminded": [False] * len(reminders)
    }

    print("🟡 load_events 呼び出し")
    events = load_events(guild_id=guild_id)
    print("🟢 load_events 完了")

    events.append(event)

    print("🟡 save_events 呼び出し")
    save_events(events, guild_id=guild_id)
    print("🟢 save_events 完了")


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
    ensure_data_files()          # ここで初期化処理を呼ぶ
    try:
        # 特定のギルドIDを指定する場合 (テスト用にコメントアウト)
        # MY_GUILD = discord.Object(id=0)  # ここに実際のギルドIDを入れる
        # await bot.tree.sync(guild=MY_GUILD)
        await bot.tree.sync()
        print("✅ Commands synced successfully.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"✅ Logged in as {bot.user}")


@bot.tree.command(name="setlang", description="あなたの母国語を設定します")
@app_commands.choices(lang=config.LANG_CHOICES) # configから参照
async def setlang(interaction: discord.Interaction, lang: discord.app_commands.Choice[str]):
    user_id = str(interaction.user.id)
    data = load_lang_settings()
    data[user_id] = lang.value
    save_lang_settings(data)
    await interaction.response.send_message(f"✅ あなたの母国語を {lang.name} に設定しました！", ephemeral=True)


@bot.tree.command(name="create_timestamp", description="指定した日付と時刻をタイムゾーン付きで表示します")
@app_commands.choices(timezone=config.TIMEZONE_CHOICES) # configから参照
async def create_timestamp(
    interaction: discord.Interaction,
    month: int,
    day: int,
    hour: int,
    minute: int,
    timezone: discord.app_commands.Choice[str]
):
    tz = pytz.timezone(timezone.value)
    try:
        dt = tz.localize(datetime(datetime.now().year, month, day, hour, minute))
        unix_time = int(dt.timestamp())
        timestamp_str = f"<t:{unix_time}>"
        embed = discord.Embed(title="TimeStamp", description=f"🕒 {timestamp_str}", color=discord.Color.blue())
        embed.add_field(name="TimeZone", value=timezone.name, inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"❌ Error in create_timestamp: {e}")
        if interaction.response.is_done():
            await interaction.followup.send("タイムスタンプの作成中にエラーが発生しました。", ephemeral=True)
        else:
            await interaction.response.send_message("タイムスタンプの作成中にエラーが発生しました。", ephemeral=True)


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
    timezone: str = "JST"
):
    print("🟢 /addevent 実行開始")
    await interaction.response.defer(ephemeral=True)

    try:
        # reminders parse
        reminder_list = []
        if reminders:
            try:
                reminder_list = [int(x.strip()) for x in reminders.split(",")]
            except ValueError:
                await interaction.followup.send(
                    "リマインダーはカンマ区切りの数字で指定してください。",
                    ephemeral=True
                )
                return

        add_event(
            month, day, hour, minute, name, content, channel.id,
            interaction.guild_id, reminder_list,
            timezone=timezone
        )

        # タイムゾーンオブジェクトの取得 (add_event内と重複するが、確認のためここでも定義)
        if timezone.upper() == "UTC":
            tz = pytz.UTC
        else:
            tz = pytz.timezone("Asia/Tokyo") # デフォルトはJST想定

        # now = datetime.now(tz) # add_event内で計算されるため不要
        # year = now.year # add_event内で計算されるため不要
        # event_datetime = tz.localize(datetime(year, month, day, hour, minute)) # add_event内で計算されるため不要

        reminder_text = ""
        if reminder_list:
            reminder_text = "この通知は " + "、".join(f"{m}分前" for m in reminder_list) + " にお知らせします。"

        await interaction.followup.send(
            f"✅ イベント「{name}」を登録しました！\n{reminder_text}\nタイムゾーン: {timezone}",
            ephemeral=True
        )
        print("✅ /addevent 完了")

    except Exception as e:
        print(f"🔴 /addevent 例外: {e}")
        try:
            await interaction.followup.send(
                f"❌ イベント登録に失敗しました: {e}",
                ephemeral=True
            )
        except discord.NotFound: # interactionが既に無効な場合
            print("Interaction not found, cannot send error message.")
        except Exception as e_followup: # フォローアップ送信時の別のエラー
            print(f"Error sending followup message for addevent failure: {e_followup}")


@bot.tree.command(name="deleteevent", description="指定したイベントを削除します")
@app_commands.describe(index="削除するイベントの番号（/listevents で確認）")
async def deleteevent(interaction: discord.Interaction, index: int):
    try:
        events = load_events(guild_id=interaction.guild_id) # guild_idを指定
        if not events:
            await interaction.response.send_message("登録されているイベントはありません。", ephemeral=True)
            return

        if index < 1 or index > len(events):
            await interaction.response.send_message("無効なイベント番号です。", ephemeral=True)
            return

        removed_event = events.pop(index - 1)
        save_events(events, guild_id=interaction.guild_id) # guild_idを指定
        await interaction.response.send_message(
            f"✅ イベント「{removed_event.get('name', '無名イベント')}」を削除しました。", ephemeral=True
        )
    except Exception as e:
        print(f"❌ Error in deleteevent: {e}")
        if interaction.response.is_done():
            await interaction.followup.send("イベントの削除中にエラーが発生しました。", ephemeral=True)
        else:
            try:
                await interaction.response.send_message("イベントの削除中にエラーが発生しました。", ephemeral=True)
            except discord.NotFound:
                 print("Interaction not found, cannot send error message for deleteevent.")
            except Exception as e_response:
                print(f"Error sending response message for deleteevent failure: {e_response}")


@bot.tree.command(name="listevents", description="登録済みイベントの一覧を表示します")
async def listevents(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
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

        for i, event_data in enumerate(events, 1): # event -> event_data に変更（可読性のため）
            # 日時情報が存在しないイベントはスキップ
            datetime_str = event_data.get("datetime")
            if not datetime_str:
                continue

            try:
                dt = datetime.fromisoformat(datetime_str)
            except Exception: # 詳細なエラーは不要なため、Exceptionでキャッチ
                continue  # パースできない日時はスキップ

            event_timezone_str = event_data.get("timezone", "JST") # event -> event_data
            # dtオブジェクトはUTCで保存されている前提
            dt_utc = dt.replace(tzinfo=timezone_utc) # 常にUTCとして扱う

            # 表示用のタイムゾーンに変換
            if event_timezone_str.upper() == "UTC":
                dt_display = dt_utc
            else: # JST or other (デフォルトJST)
                dt_display = dt_utc.astimezone(timezone_jst)


            unix_timestamp = int(dt_utc.timestamp()) # タイムスタンプはUTC基準で
            timestamp_str = f"<t:{unix_timestamp}:F>" # Discordがユーザーのローカルタイムに変換

            name = event_data.get("name", "無名イベント") # event -> event_data
            content = event_data.get("content", "") # event -> event_data
            channel_id = event_data.get("channel_id", 0) # event -> event_data
            channel_obj = interaction.guild.get_channel(channel_id)
            channel_name = channel_obj.name if channel_obj else f"不明なチャンネル（ID: {channel_id}）"

            reminders = event_data.get("reminders", []) # event -> event_data
            if reminders:
                reminder_text = "この通知は " + "、".join(f"{m}分前" for m in reminders) + " にお知らせします。"
            else:
                reminder_text = "リマインダー設定なし"

            embed.add_field(
                name=f"{i}. {name} - {timestamp_str}（表示: {event_timezone_str}）", # タイムゾーン表示を明確化
                value=(
                    f"📢 内容: {content}\n"
                    f"📡 チャンネル: {channel_name}\n"
                    # f"🌍 登録タイムゾーン: {event_timezone_str}\n" # ユーザーが指定したTZ
                    f"⏰ {reminder_text}"
                ),
                inline=False,
            )
        if not embed.fields: # 表示するイベントが一つもなかった場合
            await interaction.followup.send("表示可能なイベントがありません。", ephemeral=True)
            return

        await interaction.followup.send(embed=embed, ephemeral=True)
    except discord.NotFound: # defer 後に interaction が無効になった場合
        print("Interaction not found in listevents after defer.")
        return # ここで処理を終了
    except Exception as e:
        print(f"❌ Error in listevents: {e}")
        try:
            # followup.sendは既にdeferされているので使えるはず
            await interaction.followup.send("イベント一覧の表示中にエラーが発生しました。", ephemeral=True)
        except discord.NotFound:
            print("Interaction not found, cannot send error message for listevents.")
        except Exception as e_followup:
            print(f"Error sending followup message for listevents failure: {e_followup}")


# BotへのDMに返信
@bot.event
async def on_message(message):
    # ボット、チャンネルからのDMは無視
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = str(message.author.id)
    settings = load_lang_settings()
    native_lang = settings.get(user_id, config.DEFAULT_LANG) # config.py から読み込む
    other_lang = "EN" if native_lang != "EN" else config.DEFAULT_LANG # config.py から読み込む
    target_lang = native_lang

    # ユーザーの母国語に翻訳
    translated_text, source_lang = await tran.translate(message.content, target_lang)
    await message.channel.send(translated_text)
    # await bot.process_commands(message)

    return


# リアクション追加に反応
@bot.event
async def on_raw_reaction_add(payload):
    # ボットからのリアクションは無視
    if payload.user_id == bot.user.id:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        print("チャンネルではありません")
        return

    # リアクション元メッセージを取得
    message = await channel.fetch_message(payload.message_id)

    # 翻訳対応の国旗リアクションの場合
    if str(payload.emoji) in config.FLAG_MAP: # config.py から読み込む
        wait_sec_delete = 60
        try:
            # 国旗の言語に翻訳
            target_lang = config.FLAG_MAP[str(payload.emoji)]  # config.py から読み込む
            translated_text, source_lang = await tran.translate(message.content, target_lang)
            # リアクションを削除
            user = await bot.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)

            # 送信メッセージを作成
            send_embed = discord.Embed(
                description=translated_text,
                color=discord.Color.teal()
            )
            send_embed.set_author(
                name=user.display_name,
                icon_url=user.avatar.url if user.avatar else None
            )
            send_message = await channel.send(embed=send_embed)  # 送信メッセージを保存

            await asyncio.sleep(wait_sec_delete)
            await send_message.delete()  # 60秒後に翻訳メッセージ削除

        except Exception as err:
            print(f"リアクション翻訳エラー: {err}")

    # 複数翻訳対応リアクションの場合
    if str(payload.emoji) in config.REACTION_DICT:
        max_select_msg = 100  # 最大選択メッセージ数
        global TRANSLATE_MESSAGE_DICT
        type_reaction = config.REACTION_DICT[str(payload.emoji)]
        user_id = str(payload.user_id) # ユーザーIDを取得
        user = await bot.fetch_user(payload.user_id) # payloadから直接user_idを取得

        # ユーザーごとの辞書が存在しない場合は初期化
        if user_id not in TRANSLATE_MESSAGE_DICT:
            TRANSLATE_MESSAGE_DICT[user_id] = {
                "start": None,
                "start_emoji": "",
                "finish": None,
                "finish_emoji": ""
            }

        user_translate_data = TRANSLATE_MESSAGE_DICT[user_id]

        # 複数翻訳開始リアクションの場合
        if type_reaction.startswith("開始"):
            print(f"リアクション絵文字: {str(payload.emoji)} , {type_reaction}")
            user_translate_data["start"] = message
            user_translate_data["start_emoji"] = str(payload.emoji)
            await user.send(f"複数翻訳リアクションを検知: {str(payload.emoji)} , {type_reaction}")

        # 複数翻訳終了リアクションの場合
        if type_reaction.startswith("終了"):
            print(f"リアクション絵文字: {str(payload.emoji)} , {type_reaction}")
            user_translate_data["finish"] = message
            user_translate_data["finish_emoji"] = str(payload.emoji)
            await user.send(f"複数翻訳リアクションを検知: {str(payload.emoji)} , {type_reaction}")

        # 開始/終了の2つのリアクションが揃ったら翻訳実行
        flg_translate = (user_translate_data["start"] is not None) and \
                        (user_translate_data["finish"] is not None)
        if flg_translate:
            lang_settings = load_lang_settings()
            target_lang = lang_settings.get(user_id, config.DEFAULT_LANG) # user_idを文字列に変換
            msg_target_start = user_translate_data["start"]
            msg_target_finish = user_translate_data["finish"]

            target_msg_list = []
            # 開始リアクションのメッセージを翻訳対象に追加
            target_msg_list.append(msg_target_start)
            counter = 0
            # 開始/終了リアクション内の複数メッセージを翻訳対象に追加
            async for msg_history_item in channel.history(after=msg_target_start, before=msg_target_finish, limit=max_select_msg): # 変数名を変更
                counter += 1
                if counter <= max_select_msg:
                    target_msg_list.append(msg_history_item) # 変数名を変更
                else:
                    print(f"一度に翻訳可能なメッセージ数を超過しました: {counter}")

            # 終了リアクションのメッセージを翻訳対象に追加
            target_msg_list.append(msg_target_finish)

            try:
                # 翻訳対象を順次翻訳してDM送信
                for msg_to_translate in target_msg_list: # 変数名を変更
                    # 送信メッセージのユーザーを取得
                    user_author = await bot.fetch_user(msg_to_translate.author.id) # 変数名を変更
                    origin_text = msg_to_translate.content # 変数名を変更
                    print(f"翻訳実行: {origin_text}")
                    translated_text, source_lang = await tran.translate(origin_text, target_lang)
                    print(f"翻訳後　: {translated_text}")

                    # 送信メッセージを作成
                    send_embed = discord.Embed(
                        description=translated_text,
                        color=discord.Color.teal()
                    )
                    send_embed.set_author(
                        name=user_author.display_name,
                        icon_url=user_author.avatar.url if user_author.avatar else None
                    )
                    await user.send(embed=send_embed)   # ユーザーにDM送信

                # 最大翻訳数超過時は警告をDM
                if counter >= max_select_msg:
                    await user.send(f"翻訳メッセージ数が最大値を超えました: {counter} / {max_select_msg}")

            except Exception as err:
                print(f"エラー発生: {err}")

            finally:
                # リアクション削除:開始
                start_message_to_remove_reaction = user_translate_data["start"] # 変数名を変更
                del_emoji_start = user_translate_data["start_emoji"] # 変数名を変更
                await start_message_to_remove_reaction.remove_reaction(del_emoji_start, user) # 変数名を変更
                print(f"リアクション削除: {str(del_emoji_start)}  \t, ID:{start_message_to_remove_reaction.id}") # 変数名を変更
                user_translate_data["start"] = None
                user_translate_data["start_emoji"] = None

                # リアクション削除:終了
                finish_message_to_remove_reaction = user_translate_data["finish"] # 変数名を変更
                del_emoji_finish = user_translate_data["finish_emoji"] # 変数名を変更
                await finish_message_to_remove_reaction.remove_reaction(del_emoji_finish, user) # 変数名を変更
                print(f"リアクション削除: {str(del_emoji_finish)}  \t, ID:{finish_message_to_remove_reaction.id}") # 変数名を変更
                user_translate_data["finish"] = None
                user_translate_data["finish_emoji"] = None
                # ユーザーのデータを辞書から削除 (もしくは初期化)
                if user_id in TRANSLATE_MESSAGE_DICT:
                    del TRANSLATE_MESSAGE_DICT[user_id]

    return


@bot.event
async def on_connect():
    bot.loop.create_task(event_checker(bot))


if __name__ == "__main__": # 直接実行された場合のみボットを起動
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN) # configから参照
    else:
        print("DISCORD_TOKENが設定されていません。config.pyまたは環境変数を確認してください。")
