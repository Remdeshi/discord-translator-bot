import json
import asyncio
import os
from datetime import datetime
import pytz  # タイムゾーン用

DATA_DIR = "data"
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
JST = pytz.timezone("Asia/Tokyo")

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
    now = datetime.now(JST)
    event_datetime = JST.localize(datetime(now.year, month, day, hour, minute))
    if event_datetime < now:
        # 過去なら翌年にずらす
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
    while True:
        now = datetime.now(JST)
        events = load_events()
        updated = False

        for event in events:
            event_time = datetime.fromisoformat(event["datetime"])
            # tzinfoがなければJSTをつける（念のため）
            if event_time.tzinfo is None:
                event_time = JST.localize(event_time)
            
            if not event.get("announced") and now >= event_time:
                channel_id = event.get("channel_id")
                channel = bot.get_channel(channel_id) if channel_id else None
                if channel:
                    msg = (
                        f"📢 **イベント通知** 📢\n"
                        f"**{event['name']}**\n"
                        f"{event['content']}\n"
                        f"Scheduled for: {event_time.strftime('%b %d %H:%M')}"
                    )
                    await channel.send(msg)
                    event["announced"] = True
                    updated = True
                else:
                    print(f"Channel with ID {channel_id} not found.")

        if updated:
            save_events(events)

        await asyncio.sleep(60)
