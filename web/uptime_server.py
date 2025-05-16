import os
import json
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

CHAR_COUNT_FILE = "data/char_count.json"
LAST_PING_FILE = "/tmp/last_ping.txt"
PING_LOG_FILE = "/tmp/ping_log.txt"

def start_flask():
    @app.route("/", methods=["GET", "HEAD"])
    def ping():
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if request.method == "HEAD":
            print(f"📡 HEADリクエスト受信（更新スキップ）: {now}")
            return "", 200
        with open(LAST_PING_FILE, "w") as f:
            f.write(now)
        with open(PING_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{now}] UptimeRobot : 正常\n")
        print(f"📡 GETリクエストでPing更新: {now}")
        return "OK", 200

    @app.route("/last_ping", methods=["GET"])
    def get_last_ping():
        if os.path.exists(LAST_PING_FILE):
            with open(LAST_PING_FILE, "r") as f:
                return {"last_ping": f.read().strip()}, 200
        return {"last_ping": "まだ受信なし"}, 200

    @app.route("/char_count", methods=["GET"])
    def get_char_count():
        if os.path.exists(CHAR_COUNT_FILE):
            with open(CHAR_COUNT_FILE, "r", encoding="utf-8") as f:
                return json.load(f), 200
        return {"count": 0, "month": "unknown"}, 200

    @app.route("/ping_log", methods=["GET"])
    def get_ping_log():
        if os.path.exists(PING_LOG_FILE):
            with open(PING_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return {"log": "".join(lines[-10:])}, 200
        return {"log": "ログが存在しません"}, 200

    app.run(host="0.0.0.0", port=8080)
