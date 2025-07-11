import os
import discord
from dotenv import load_dotenv

# Data files
BASE_DIR = "discord-translator-bot"
DATA_DIR = "data"
TEMP_DIR = "tmp"
EVENTS_FILE = "events.json"
CHAR_COUNT_FILE = "char_count.json"
USER_LANG_FILE = "user_lang.json"

# Key Params
DISCORD_TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DEEPL_API_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Discord Settings
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
    ("Lithuanian", "LT"), ("Polish", "PL"), ("Portuguese", "PT"),
    ("Romanian", "RO"), ("Russian", "RU"), ("Slovak", "SK"), ("Slovenian", "SL"),
    ("Spanish", "ES"), ("Turkish", "TR")
]]

# Intents for Discord bot (used in multiple files)
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.reactions = True

# Bot Reaction Flag settings
FLAG_MAP = {
    "🇧🇬": "BG", "🇨🇳": "ZH", "🇨🇿": "CS", "🇩🇰": "DA", "🇳🇱": "NL", "🇺🇸": "EN", "🇬🇧": "EN",
    "🇪🇪": "ET", "🇫🇮": "FI", "🇫🇷": "FR", "🇩🇪": "DE", "🇬🇷": "EL", "🇭🇺": "HU", "🇮🇩": "ID",
    "🇮🇹": "IT", "🇯🇵": "JA", "🇰🇷": "KO", "🇱🇻": "LV", "🇱🇹": "LT", "🇵🇱": "PL", "🇵🇹": "PT",
    "🇧🇷": "PT", "🇷🇴": "RO", "🇷🇺": "RU", "🇸🇰": "SK", "🇸🇮": "SL", "🇪🇸": "ES", "🇹🇷": "TR"
}

REACTION_DICT = {
    "⬆️": "開始", "⬇️": "終了",
    "▶️": "開始1", "⏸️": "終了2"
}

# DeepL API
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_USAGE_URL = "https://api-free.deepl.com/v2/usage"
CHAR_LIMIT = 500000
DEFAULT_LANG = "JA"

# Kansi specific
RENDER_URL = "https://testdiscord-u1jg.onrender.com"

# Update DISCORD_TOKEN and DEEPL_API_KEY after loading .env
load_dotenv()
if os.getenv("DISCORD_TOKEN"):
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if os.getenv("DEEPL_API_KEY"):
    DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

# global BASE_DIR
path_dir_base = os.path.dirname(__file__)
if str.endswith(path_dir_base, BASE_DIR):
    BASE_DIR = path_dir_base
else:
    BASE_DIR = os.path.join(path_dir_base,BASE_DIR)

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, DATA_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

TEMP_DIR = os.path.join(BASE_DIR, DATA_DIR)
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
CHAR_COUNT_FILE = os.path.join(DATA_DIR, "char_count.json")
USER_LANG_FILE = os.path.join(DATA_DIR, "user_lang.json")
