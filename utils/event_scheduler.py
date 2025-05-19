async def event_checker(bot):
    print("🔁 Event checker started")
    while True:
        now = datetime.now(JST)
        print(f"🕒 Now: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        events = load_events()
        print(f"📋 Events to check: {len(events)}")
        updated = False

        for event in events:
            try:
                event_time = datetime.fromisoformat(event["datetime"])
                if event_time.tzinfo is None:
                    event_time = pytz.UTC.localize(event_time)
                event_time_jst = event_time.astimezone(JST)

                print(f"🕓 Event time: {event_time_jst.strftime('%Y-%m-%d %H:%M:%S')} - Announced: {event.get('announced')}")

                if not event.get("announced") and now >= event_time_jst:
                    channel_id = event.get("channel_id")
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"📢 イベント: **{event['name']}**\n{event['content']}")
                        event["announced"] = True
                        updated = True
                    else:
                        print(f"❌ Channel not found: {channel_id}")
            except Exception as e:
                print(f"Error checking event: {e}")

        if updated:
            save_events(events)

        await asyncio.sleep(60)
