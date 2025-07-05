# 🌐 Discord 翻訳 & イベント通知 Bot

> **DeepL APIで翻訳 + Discordでイベント通知を自動化！**
> DM翻訳 / リアクション翻訳 / イベント登録 & リマインダー機能つき。

---

## 📌 主な機能

### 💬 翻訳機能（DeepL API 使用）

* ユーザーの母国語に応じてDMの翻訳を返信
* メッセージに国旗リアクションをつけると自動翻訳（例：🇯🇵 → 日本語に翻訳）

### 🗓 イベント機能

* `/addevent` で日時・内容・チャンネル・リマインダーを設定
* 指定時刻に通知 + 事前リマインダー
* `/listevents` でイベント一覧表示
* `/deleteevent` で削除可能

---

## ⚙️ セットアップ

### ✅ 必要なもの

* Python 3.8以上
* Discord Bot トークン
* DeepL APIキー（[取得はこちら](https://www.deepl.com/pro-api)）

---

### 🛠 インストール手順

```bash
git clone https://github.com/your-name/discord-translator-eventbot.git
cd discord-translator-eventbot

cp .env.example .env
# → エディタで.envを開き、トークンとAPIキーを設定

pip install -r requirements.txt
python main.py
```

`.env` の例：

```env
DISCORD_TOKEN=xxxxxxxxxxxxxxxxxx
DEEPL_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## ✨ 使い方（コマンド一覧）

| コマンド名               | 説明                  |
| ------------------- | ------------------- |
| `/setlang`          | 自分の母国語を設定（DM翻訳用）    |
| `/addevent`         | イベントを登録（リマインダー付き）   |
| `/listevents`       | 登録済みイベントの一覧表示       |
| `/deleteevent`      | イベントを削除             |
| `/create_timestamp` | タイムゾーン付きのタイムスタンプを生成 |

---

## 🌍 対応タイムゾーン例

* JST（日本）
* UTC（協定世界時）
* EST / PST / CST / MST（アメリカ）
* CET / GMT（ヨーロッパ）
* IST / KST / HKT などアジア圏も対応

---

## 🧠 補註

* **翻訳機能**

  * DeepL無料版でも動作しますが、1日または月の上限に注意してください
  * 国旗リアクションによる翻訳は60秒後に自動削除されます
  * DM翻訳は送信した言語を検出して、相手の設定言語に自動変換します

* **イベント機能**

  * イベントデータは `data/events.json` に保存されます（ギルド別対応）
  * 起動後は自動でイベント監視タスクが動きます

---

## 📂 ディレクトリ構成（一部）

```
project/
├── main.py
├── utils/
│   ├── translate.py
│   └── lang_settings.py
├── web/
│   └── uptime_server.py
├── data/
│   └── events.json
├── .env.example
└── requirements.txt
```

---

## 📄 ライセンス

MIT License（予定）
コントリビューション・Issue 大歓迎！
