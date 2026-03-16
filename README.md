# News Digest

RSSフィードからキーワードマッチした記事をClaudeが日本語要約し、メールで自動配信するシステム。

> このプロジェクトは **Claude Code によるバイブコーディング（Vibe Coding）** で構築されました。
> 自然言語での対話のみでコード・インフラ・ドキュメントを生成しています。

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
│  2. RSS フェッチ & フィルタリング（13ソース）                  │
│     └─ 直近12時間以内 & キーワード一致の記事のみ抽出           │
│                                                             │
│  3. Claude API で記事ごとに構造化要約                         │
│     └─ claude-sonnet-4-6                                    │
│        一言要約 / 要約 / 重要ポイント /                       │
│        背景 / 今後の影響 / 英語学習セクション                  │
│                                                             │
│  4. Gmail SMTP でメール送信                                   │
│     └─ TO_EMAIL 宛に件名・要約本文を送信                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ワークフロー詳細

### 実行スケジュール

| 実行時刻 (JST) | UTC       | 対象記事           |
|---------------|-----------|-------------------|
| 07:00         | 前日 22:00 | 夜間〜朝のニュース  |
| 18:00         | 09:00     | 日中のニュース      |

手動実行も可能（GitHub Actions > Run workflow）。

### データフロー

```
[13のRSSフィード] ──fetch──► [feedparser でパース]
                                      │
                              直近12h & キーワード判定
                                      │ マッチした記事
                                      ▼
                            [Anthropic Claude API]
                             記事ごとに構造化要約生成
                             （英語記事は英語学習セクション付き）
                                      │
                                      ▼
                            [Gmail SMTP (SSL:465)]
                               メール送信完了
```

### メール出力フォーマット（記事ごと）

```
============================================================
【記事 N】ソース名 - タイトル
============================================================
一言要約（20文字以内）

要約（3行）

重要ポイント（3つ）
・ポイント1
・ポイント2
・ポイント3

背景

今後の影響
（宇宙産業・科学・国家安全保障・民間宇宙ビジネスなどへの影響）

📚 英語学習ピックアップ  ← 英語記事のみ
  専門用語 / ネイティブフレーズ

関連企業・人物のGoogle検索リンク
```

---

## RSSソース一覧（13媒体）

### 宇宙産業メディア
| メディア | URL | 特徴 |
|---|---|---|
| SpaceNews | spacenews.com | 宇宙ビジネスの中心メディア。商業宇宙・政策・軍事宇宙 |
| Payload Space | payloadspace.com | 宇宙スタートアップ特化 |
| Ars Technica Space | arstechnica.com/space | SpaceX・NASAの技術記事 |

### DeepTech / VC
| メディア | URL | 特徴 |
|---|---|---|
| TechCrunch | techcrunch.com | スタートアップ・VC動向 |
| Not Boring | notboring.co | DeepTechのビジネス解説 |
| No Mercy No Malice | profgalloway.com | テック×経済 |
| Works in Progress | worksinprogress.co | 技術史・産業史 |

### 宇宙政策・安全保障
| メディア | URL | 特徴 |
|---|---|---|
| Defense News | defensenews.com | 防衛・宇宙政策 |
| Breaking Defense | breakingdefense.com | 国家安全保障・宇宙 |

### 技術トレンド
| メディア | URL | 特徴 |
|---|---|---|
| MIT Technology Review | technologyreview.com | 技術トレンド全般 |
| IEEE Spectrum | spectrum.ieee.org | 工学・エレクトロニクス |

### 日本語
| メディア | URL | 特徴 |
|---|---|---|
| 日経クロステック | xtech.nikkei.com | IT・技術ニュース |
| sorae | sorae.info | 日本語宇宙専門メディア |
| JAXA新着情報 | jaxa.jp | 公式プレスリリース |

---

## キーワード一覧

### 1. マクロ / 未来予測
`space economy` `commercial space industry` `new space industry` `space infrastructure` `orbital economy`
`space industrial base` `space supply chain` `space logistics` `space manufacturing` `space commercialization`
`future of space industry` `space market forecast` `space industry trends`
`宇宙経済` `宇宙産業` `宇宙インフラ`

### 2. 市場 / ビジネス分析
`satellite market` `satellite constellation` `satellite data market` `launch services market`
`space infrastructure market` `space logistics market` `space startup funding` `space venture capital`
`space industry report` `space market analysis`
`衛星市場` `宇宙スタートアップ`

### 3. 競合 / 技術（RF × maritime × security）
`RF geolocation satellite` `satellite RF sensing` `radio frequency intelligence satellite`
`satellite spectrum monitoring` `RF monitoring satellite` `maritime domain awareness satellite`
`satellite ship detection` `AIS satellite` `VDES satellite` `space-based RF sensing`
`VDES` `IoT` `RF` `spectrum` `maritime`
`電波` `海洋監視`

### 4. 安全保障 / 国家戦略
`space domain awareness` `space situational awareness` `national security space`
`military satellite surveillance` `space defense` `space ISR satellite` `ELINT satellite` `SIGINT satellite`
`space force` `space defense budget` `dual-use technology` `strategic autonomy` `space sovereignty` `industrial policy`
`安全保障` `防衛` `宇宙安全保障` `防衛宇宙`

### 5. DeepTech / 投資
`deeptech startup` `hard tech startup` `frontier tech` `industrial renaissance`
`deeptech venture capital` `space technology investment` `capital intensive startup`
`venture scale` `deep industrials` `DeepTech`
`宇宙投資` `宇宙ベンチャー`

### 6. 企業 / 競合
`ArkEdge Space` `ArkEdge` `HawkEye 360` `HawkEye360` `Unseenlabs`
`RF geolocation satellite company` `satellite RF intelligence company`

### その他技術トレンド
`propulsion` `in-orbit servicing` `autonomy` `AI for space` `launch market` `LEO economy` `launch cadence` `launch economics`

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

## GitHub Secrets（必須）

| Secret名              | 説明                            |
|----------------------|---------------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic APIキー               |
| `GMAIL_ADDRESS`      | 送信元Gmailアドレス              |
| `GMAIL_APP_PASSWORD` | Gmailアプリパスワード（16桁）    |
| `TO_EMAIL`           | 受信先メールアドレス             |

---

## 概算コスト（月額）

| サービス              | 費用                  | 備考                              |
|---------------------|----------------------|----------------------------------|
| GitHub Actions       | **無料**             | パブリックリポジトリは無制限        |
| Gmail SMTP           | **無料**             | Googleアカウントがあれば無償利用可  |
| Anthropic Claude API | **約100〜500円/月**  | 下記試算参照                       |
| **合計**             | **約100〜500円/月**  |                                  |

### Claude API コスト試算

- 実行回数：2回/日 × 30日 = **60回/月**
- 1回あたり平均マッチ記事数：3〜5件（ソース13媒体・キーワード30語超）
- 記事ごとに個別API呼び出し（構造化要約）
  - 入力：約1,500トークン/記事
  - 出力：約1,000トークン/記事
- claude-sonnet-4-6 料金：入力 $3/MTok、出力 $15/MTok
  - 月60回 × 平均4記事 = 240回のAPI呼び出し
  - 入力：240 × 1,500 = 360,000トークン → **$1.08**
  - 出力：240 × 1,000 = 240,000トークン → **$3.60**
  - 月合計：**約$4.68（≒ 700円）**

> マッチ記事数によって変動。記事が少ない日はほぼ無コスト。

---

## 使用技術

| 種別       | 技術                             |
|-----------|----------------------------------|
| 実行基盤   | GitHub Actions (ubuntu-latest)   |
| 言語       | Python 3.12                      |
| AI要約     | Claude API (claude-sonnet-4-6)   |
| RSSパース  | feedparser                       |
| メール送信 | smtplib (Gmail SMTP SSL)         |
| 設定管理   | PyYAML                           |
