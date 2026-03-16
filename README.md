# News Digest

RSSフィードからキーワードマッチした記事をClaudeが日本語要約し、メールで自動配信するシステム。

---

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│  (毎日 07:00 JST / 18:00 JST にスケジュール実行)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ トリガー
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      main.py                                │
│                                                             │
│  1. config.yml 読み込み                                      │
│     └─ キーワード・RSSソース・メール設定                       │
│                                                             │
│  2. RSS フェッチ & フィルタリング                             │
│     ├─ SpaceNews  (spacenews.com)                           │
│     ├─ Payload    (payloadspace.com)                        │
│     └─ 日経        (nikkei.com)                             │
│     └─ 直近12時間以内 & キーワード一致の記事のみ抽出           │
│        (VDES / RF / Defense)                                │
│                                                             │
│  3. Claude API で要約                                        │
│     └─ claude-sonnet-4-6 に記事一覧を渡し日本語要約生成       │
│                                                             │
│  4. Gmail SMTP でメール送信                                   │
│     └─ TO_EMAIL 宛に件名・要約本文を送信                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ワークフロー詳細

### 実行スケジュール

| 実行時刻 (JST) | UTC       | 対象記事                  |
|---------------|-----------|--------------------------|
| 07:00         | 前日 22:00 | 夜間〜朝のニュース          |
| 18:00         | 09:00     | 日中のニュース              |

手動実行も可能（GitHub Actions > Run workflow）。

### データフロー

```
[RSSフィード] ──fetch──► [feedparser でパース]
                                  │
                          直近12h & キーワード判定
                                  │ マッチした記事
                                  ▼
                        [Anthropic Claude API]
                         claude-sonnet-4-6 で
                           日本語要約生成
                                  │
                                  ▼
                        [Gmail SMTP (SSL:465)]
                           メール送信完了
```

---

## ファイル構成

```
news-digest/
├── main.py                        # メインスクリプト
├── config.yml                     # キーワード・ソース設定
├── requirements.txt               # Python依存パッケージ
├── README.md                      # このファイル
└── .github/
    └── workflows/
        └── news_digest.yml        # GitHub Actions ワークフロー定義
```

---

## 設定ファイル (config.yml)

```yaml
keywords:        # フィルタリングキーワード（大文字小文字を区別しない）
  - VDES
  - RF
  - Defense

sources:         # RSSフィードソース
  - name: SpaceNews
    rss_url: https://spacenews.com/feed/
  - name: Payload
    rss_url: https://payloadspace.com/feed/
  - name: 日経
    rss_url: https://www.nikkei.com/rss/

email:
  subject_prefix: "[News Digest]"
```

キーワードやソースの追加・変更はこのファイルを編集してプッシュするだけで反映される。

---

## GitHub Secrets（必須）

| Secret名              | 説明                            |
|----------------------|---------------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic APIキー               |
| `GMAIL_ADDRESS`      | 送信元Gmailアドレス              |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード（16桁）    |
| `TO_EMAIL`           | 受信先メールアドレス             |

---

## 使用技術

| 種別         | 技術                                      |
|-------------|------------------------------------------|
| 実行基盤      | GitHub Actions (ubuntu-latest)           |
| 言語         | Python 3.12                              |
| AI要約       | Claude API (claude-sonnet-4-6)           |
| RSSパース    | feedparser                               |
| メール送信    | smtplib (Gmail SMTP SSL)                 |
| 設定管理      | PyYAML                                   |
