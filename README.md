# 🌍 Discord 翻訳 & イベント通知 Bot（DeepL連携）

> このBotは、**DeepL翻訳API**と**Discordスラッシュコマンド**を活用した、**翻訳＋多言語対応イベント通知Bot**です。翻訳・タイムゾーン・リマインダーまでカバーする、コミュニケーション支援に最適なツールです。

---

## 🧠 主な機能（詳細解説）

### 💬 翻訳機能（DeepL API連携）

#### ✅ DM翻訳

* ユーザーがDMで送ったテキストを、自動的に検出 → 母国語へ翻訳し返信
* 言語設定（`/setlang`）により、ユーザーごとの基準言語（母国語）を保持
* 翻訳の対象言語は自動判別（DeepL APIが検出）

#### ✅ リアクション翻訳

* 国旗リアクション（例：🇯🇵, 🇺🇸, 🇫🇷）を付けると、そのメッセージ本文が翻訳され、Embedで返信
* 翻訳メッセージは60秒後に自動削除 → チャットを汚さず、瞬時に理解
* 対応言語は最大30以上（DeepL対応言語＋国旗絵文字）

#### 🔍 言語の自動判別フロー

```
① ユーザーがDM送信 or リアクション追加
② DeepL APIで元の言語を検出
③ ユーザーの設定言語と異なる場合、翻訳実行
④ 翻訳結果をEmbed形式で返信
```

---

### 🗓 イベント登録・通知機能（スケジューラー内蔵）

#### ✅ イベント登録 `/addevent`

* 月・日・時間・分・イベント名・説明・通知チャンネルを指定
* タイムゾーン（例：JST/UTCなど）を選択可能
* リマインダー（例：30,20,10 分前など）をカンマ区切りで設定
* 各イベントは `.json` ファイルに保存され、Bot再起動でも保持

#### ✅ イベント表示 `/listevents`

* サーバーごとに登録済みのイベントをリスト化（Embed表示）
* 各イベントの：

  * 日時（タイムゾーン付き）
  * 通知予定チャンネル
  * リマインダー設定
  * 内容や投稿者情報 などが表示される

#### ✅ イベント削除 `/deleteevent`

* `/listevents` で表示された番号を使って削除
* 安全な番号チェックあり（範囲外ならエラー表示）

#### ✅ イベント通知フロー

```
① 登録されたイベントを60秒ごとにチェック
② 「あとX分前」（リマインダー）を順番に送信（送信済みは記録）
③ 本番時刻になったら「イベント開始」通知を自動送信
④ 終了済みイベントはJSONから削除 or スキップ
```

---

## ⚙️ セットアップ手順

### ✅ 必要なもの

* Python 3.8以上（推奨：3.10〜）
* Discord Botトークン（[取得リンク](https://discord.com/developers/applications)）
* DeepL APIキー（[登録ページ](https://www.deepl.com/pro-api)）

### 🔧 インストール手順

```bash
git clone https://github.com/your-name/discord-translator-eventbot.git
cd discord-translator-eventbot

cp .env.example .env  # → 設定ファイルを準備
vi .env  # トークンとAPIキーを記入

pip install -r requirements.txt
python main.py
```

### `.env` 設定例

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
DEEPL_API_KEY=YOUR_DEEPL_API_KEY
```

---

## 🔤 スラッシュコマンド一覧（全コマンド）

| コマンド                | 引数               | 説明                           |
| ------------------- | ---------------- | ---------------------------- |
| `/setlang`          | 言語コード（ENなど）      | あなたの母国語を設定                   |
| `/addevent`         | 日付・時刻・内容など       | イベントを登録（タイムゾーン・通知付き）         |
| `/listevents`       | -                | 登録済みイベントの一覧表示                |
| `/deleteevent`      | イベント番号           | イベントを削除（番号は `/listevents` で） |
| `/create_timestamp` | 月, 日, 時間, タイムゾーン | Discordタイムスタンプ生成             |

---

## 🌍 対応タイムゾーン（例）

| 表示名          | TimeZone ID          |
| ------------ | -------------------- |
| JST（日本）      | Asia/Tokyo           |
| UTC（世界標準）    | UTC                  |
| EST（米東）      | America/New\_York    |
| PST（米西）      | America/Los\_Angeles |
| KST（韓国）      | Asia/Seoul           |
| HKT（香港）      | Asia/Hong\_Kong      |
| SGT（シンガポール）  | Asia/Singapore       |
| CET（中央ヨーロッパ） | Europe/Berlin        |
| GMT（英国）      | Europe/London        |
| AEST（豪州）     | Australia/Sydney     |
| NZDT（NZ）     | Pacific/Auckland     |

> 🕒 イベント時刻はすべて内部的に UTC で統一 → 表示時に選択タイムゾーンに変換。

---

## 🧠 技術メモ・内部仕様

### 🔁 翻訳処理

* 使用API：`https://api-free.deepl.com/v2/translate`
* 通信：非同期HTTP（`aiohttp`）でDeepLに接続
* 翻訳対象：メッセージ本文のみ（ファイル・画像は対象外）
* 対応言語（リアクション）：英語 🇺🇸 / 日本語 🇯🇵 / 中国語 🇨🇳 / 韓国語 🇰🇷 / ドイツ語 🇩🇪 / 他多数

### ⏰ イベント通知処理

* 全イベントは `data/events.json` に保存（各イベントに以下を含む）:

  * 開始日時（ISO8601/UTC）
  * 通知チャンネルID
  * ギルドID
  * リマインダー（最大3段階）と通知済みフラグ
* 通知判定は `datetime.now(pytz.UTC)` にて毎分チェック

### 📦 設定ファイル & 保存ファイル

```
.env              # トークン・APIキーを保存
lang_settings.json # 各ユーザーの母国語設定
/data/events.json # サーバーごとのイベント情報
```

### 📁 ディレクトリ構成

```
discord-translator-eventbot/
├── main.py               # 全コマンド・イベント処理の中核
├── utils/
│   ├── translate.py      # DeepL翻訳ロジック
│   └── lang_settings.py  # ユーザー言語設定の読み書き
├── web/
│   └── uptime_server.py  # Render/Uptime対策用のミニWebサーバー
├── data/
│   └── events.json       # イベントデータ保存場所
├── .env.example          # 環境変数のサンプル
└── requirements.txt      # 依存ライブラリ一覧
```

---

## 📜 ライセンス & 利用

* ライセンス：MIT（予定）
* 無料・商用利用OK
* クレジット表示も自由
* 改変・再配布歓迎

---

## 🙋‍♂️ 今後の拡張アイデア（貢献歓迎！）

* Web UIでイベントを登録・削除・管理できるフロントエンド（Flask/Next.js）
* MongoDBやPostgreSQLなどでイベント保存（JSON→DB）
* メッセージ翻訳履歴の記録・検索機能
* Botのマルチインスタンス管理・多言語翻訳の自動連携

