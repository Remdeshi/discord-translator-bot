import json
import asyncio
import os
from datetime import datetime

DATA_DIR = "data"
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")

def load_events():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def add_event(month, day, hour, minute, name, content):
    events = load_events()
    event_datetime = datetime(datetime.now().year, month, day, hour, minute)
    event = {
        "datetime": event_datetime.isoformat(),
        "name": name,
        "content": content,
        "announced": False
    }
    events.append(event)
    save_events(events)

async def event_checker(bot, channel_id):
    while True:
        now = datetime.now()
        events = load_events()
        updated = False

        for event in events:
            event_time = datetime.fromisoformat(event["datetime"])
            if not event.get("announced") and now >= event_time:
                channel = bot.get_channel(channel_id)
                if channel:
                    msg = (
                        f"📢 **Event Reminder** 📢\n"
                        f"**{event['name']}**\n"
                        f"{event['content']}\n"
                        f"Scheduled for: {event_time.strftime('%b %d %H:%M')}"
                    )
                    await channel.send(msg)
                    event["announced"] = True
                    updated = True
        
        if updated:
            save_events(events)

        await asyncio.sleep(60)  # Check every minute
