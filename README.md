# 🌍 Discord 翻訳Bot（DeepL使用）

## 機能
- Discord上のメッセージを自動で翻訳（DeepL API）
- 翻訳結果を返信で返します（例：英語→日本語）

---

## 🚀 セットアップ手順

### 1. 必要なもの
- Python 3.8+
- Discord Bot トークン
- DeepL APIキー（[公式サイト](https://www.deepl.com/pro-api)）

---

### 2. ボットの作り方（Discord Bot登録）

1. Discordの [Developer Portal](https://discord.com/developers/applications) へアクセス  
2. 「New Application」で新規作成  
3. 左メニュー「Bot」→「Add Bot」  
4. 「TOKEN」→「コピー」して `.env` に貼り付け  
5. 「OAuth2」→「URL Generator」  
   - Scopes: `bot`  
   - Bot Permissions: `Send Messages`, `Read Message History`, `Message Content`  
6. 生成されたURLでBotをサーバーに招待

---

### 3. このBotの動かし方

```bash
git clone https://github.com/your-repo/discord-translator-bot.git
cd discord-translator-bot
cp .env.example .env
# → .env をエディタで開いてトークンとAPIキー入力

pip install -r requirements.txt
python main.py
```

---

## 🧠 備考
- DeepLは無料枠でも十分使えるけど、1日制限があるので注意
- 複数言語対応やチャンネル限定対応も簡単に拡張可能！