import customtkinter as ctk
import tkinter as tk
import threading
import time
import json
import os
import requests
from dotenv import load_dotenv
import tkinter.messagebox as msgbox
from bot_thread import start_bot, set_on_ready_callback, load_char_count, set_user_language

load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

LANG_CODES = {
    "日本語 (JA)": "JA",
    "English (EN)": "EN",
    "Deutsch (DE)": "DE",
    "Français (FR)": "FR",
    "Español (ES)": "ES",
    "Português (PT)": "PT",
    "Italiano (IT)": "IT",
    "Nederlands (NL)": "NL",
    "Polski (PL)": "PL",
    "Русский (RU)": "RU",
    "中文 (ZH)": "ZH",
    "한국어 (KO)": "KO",
    "Türkçe (TR)": "TR",
    "Українська (UK)": "UK"
}

UI_LANGUAGES = {
    "日本語": "ja",
    "English": "en"
}

CONFIG_FILE = "config.json"

class TranslatorUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Language Translator")
        self.geometry("580x600")
        self.font_style = ("Meiryo UI", 12)
        self.ui_language = "ja"

        self.translations = {
            "ja": {
                "start_bot": "🚀 Bot 起動",
                "stop_bot": "🛑 Bot 停止",
                "status_stopped": "ステータス: 停止中",
                "status_running": "ステータス: 実行中",
                "status_starting": "ステータス: 起動中...",
                "status_confirm": "Bot を停止してアプリを終了しますか？",
                "status_canceled": "❎ 操作がキャンセルされました（Bot は継続中）",
                "language_setting": "現在の設定言語",
                "monthly_count": "月間文字数",
                "deepl_usage": "DeepL使用量"
            },
            "en": {
                "start_bot": "🚀 Start Bot",
                "stop_bot": "🛑 Stop Bot",
                "status_stopped": "Status: Stopped",
                "status_running": "Status: Running",
                "status_starting": "Status: Starting...",
                "status_confirm": "Stop the Bot and exit the app?",
                "status_canceled": "❎ Action canceled (Bot is still running)",
                "language_setting": "Selected Language",
                "monthly_count": "Monthly Characters",
                "deepl_usage": "DeepL Usage"
            }
        }

        self.tk_menu = tk.Menu(self)
        lang_menu = tk.Menu(self.tk_menu, tearoff=0)
        for lang in UI_LANGUAGES:
            lang_menu.add_command(label=lang, command=lambda l=lang: self.set_ui_language(l))
        self.tk_menu.add_cascade(label="🌐 UI設定言語", menu=lang_menu)
        self.configure(menu=self.tk_menu)

        self.language_dropdown = ctk.CTkComboBox(
            self, values=list(LANG_CODES.keys()),
            command=self.on_language_select, font=self.font_style, state="readonly")
        self.language_dropdown.pack(pady=(10, 0))

        self.selected_lang_label = ctk.CTkLabel(self, text="", font=self.font_style)
        self.selected_lang_label.pack(pady=(0, 10))

        self.start_button = ctk.CTkButton(self, text="", command=self.start_bot, font=self.font_style)
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(self, text="", command=self.stop_bot,
                                         fg_color="#ff5c5c", text_color="black", hover_color="#ff9999",
                                         font=self.font_style)
        self.stop_button.pack(pady=10)
        self.stop_button.pack_forget()

        self.status_label = ctk.CTkLabel(self, text="", text_color="red", font=self.font_style)
        self.status_label.pack(pady=5)

        self.char_count_label = ctk.CTkLabel(self, text="", font=self.font_style)
        self.char_count_label.pack(pady=5)

        self.deepl_usage_label = ctk.CTkLabel(self, text="", font=self.font_style)
        self.deepl_usage_label.pack(pady=(5, 5))

        self.log_box = ctk.CTkTextbox(self, height=200, wrap="word", font=self.font_style)
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.configure(state="disabled")

        set_on_ready_callback(self.on_bot_ready)
        self.update_char_count_loop()
        self.load_config()
        self.update_ui_texts()

    def get_text(self, key):
        return self.translations[self.ui_language].get(key, f"[{key}]")

    def set_ui_language(self, lang_display):
        self.ui_language = UI_LANGUAGES.get(lang_display, "ja")
        self.update_ui_texts()
        self.save_config()

    def update_ui_texts(self):
        self.start_button.configure(text=self.get_text("start_bot"))
        self.stop_button.configure(text=self.get_text("stop_bot"))
        self.status_label.configure(text=self.get_text("status_stopped"))
        self.selected_lang_label.configure(text=f"{self.get_text('language_setting')}: {self.language_dropdown.get()}")
        self.update_char_count_loop()

    def on_language_select(self, selected_lang):
        lang_code = LANG_CODES.get(selected_lang, "JA")
        set_user_language(lang_code)
        self.selected_lang_label.configure(text=f"{self.get_text('language_setting')}: {selected_lang}")
        self.save_config()

    def save_config(self):
        config = {
            "language": LANG_CODES.get(self.language_dropdown.get(), "JA"),
            "ui_language": self.ui_language
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                lang_code = config.get("language", "JA")
                ui_lang = config.get("ui_language", "ja")
                for name, code in LANG_CODES.items():
                    if code == lang_code:
                        self.language_dropdown.set(name)
                        set_user_language(code)
                        break
                self.ui_language = ui_lang

    def start_bot(self):
        self.status_label.configure(text=self.get_text("status_starting"), text_color="orange")
        self.log("⚙ " + self.get_text("start_bot"))
        self.start_button.configure(state="disabled")
        self.stop_button.pack(pady=10)
        start_bot()

    def stop_bot(self):
        result = msgbox.askyesno("確認 / Confirm", self.get_text("status_confirm"))
        if result:
            self.log("🛑 " + self.get_text("stop_bot"))
            self.after(1000, self.destroy)
        else:
            self.log(self.get_text("status_canceled"))

    def on_bot_ready(self):
        self.status_label.configure(text=self.get_text("status_running"), text_color="green")
        self.log("✅ " + self.get_text("status_running"))

    def update_char_count_loop(self):
        def loop():
            while True:
                count = load_char_count().get("count", 0)
                self.char_count_label.configure(text=f"{self.get_text('monthly_count')}: {count:,}")
                self.update_deepl_usage_label()
                time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()

    def update_deepl_usage_label(self):
        usage = self.get_deepl_usage()
        percent = usage["percent"]
        color = "green" if percent <= 50 else "orange" if percent <= 80 else "red"
        self.deepl_usage_label.configure(
            text=f"{self.get_text('deepl_usage')}: {usage['used']:,} / {usage['limit']:,}（{percent}%）",
            text_color=color
        )

    def get_deepl_usage(self):
        try:
            headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
            response = requests.get("https://api-free.deepl.com/v2/usage", headers=headers)
            data = response.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 1)
            percent = round((used / limit) * 100, 1)
            return {"used": used, "limit": limit, "percent": percent}
        except:
            return {"used": 0, "limit": 0, "percent": 0}

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

if __name__ == "__main__":
    print("✅ UI 起動チェック通過")
    app = TranslatorUI()
    app.mainloop()