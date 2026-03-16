import os
import smtplib
import feedparser
import yaml
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import anthropic

# --- 設定読み込み ---
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

KEYWORDS = [kw.lower() for kw in config["keywords"]]
SOURCES = config["sources"]
SUBJECT_PREFIX = config["email"].get("subject_prefix", "[News Digest]")

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TO_EMAIL = os.environ["TO_EMAIL"]

JST = timezone(timedelta(hours=9))


def is_recent(entry, hours=12):
    """直近 hours 時間以内の記事かどうか判定"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - published < timedelta(hours=hours)
    return True  # 日時不明の場合は含める


def fetch_articles():
    """RSSから記事を取得し、キーワードでフィルタリング"""
    matched = []
    for source in SOURCES:
        feed = feedparser.parse(source["rss_url"])
        for entry in feed.entries:
            if not is_recent(entry):
                continue
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = (title + " " + summary).lower()
            if any(kw in text for kw in KEYWORDS):
                matched.append({
                    "source": source["name"],
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": summary,
                })
    return matched


PROMPT_TEMPLATE = """次のニュースを要約してください。

【出力形式】

一言要約（20文字以内）

要約（3行）

重要ポイント（3つ）
・ポイント1
・ポイント2
・ポイント3

背景
（このニュースの背景や文脈を簡潔に説明）

今後の影響
（社会・経済・企業などへの影響）

{english_section}

【追加ルール】
- 事実ベースのみで回答する
- 推測や意見は書かない
- 不明な情報は「不明」と明記する
- ハルシネーション（存在しない事実・人物・企業）を生成しない
- 記事内に登場する人物・企業・組織名があればGoogle検索リンクを以下形式で付ける
  例：
  OpenAI
  https://www.google.com/search?q=OpenAI

  Sam Altman
  https://www.google.com/search?q=Sam+Altman

【記事】

<<<
{article_text}
>>>
"""

ENGLISH_SECTION = """📚 英語学習ピックアップ
（この記事が英語の場合のみ出力。日本語記事はこのセクションを省略）

専門用語（この記事に登場する業界・技術用語）
例：
  - spectrum allocation（スペクトラム割り当て）：電波の周波数帯を各用途に割り振ること
  - maritime domain awareness（海洋領域認識）：海上の状況を包括的に把握する能力

ネイティブがよく使うフレーズ（記事中の自然な英語表現）
例：
  - "ramp up"（急拡大する）：We expect demand to ramp up significantly.
  - "in the pipeline"（準備中・計画中）：Several new satellites are in the pipeline.
"""


def summarize_articles(articles):
    """Claude API で記事を要約"""
    if not articles:
        return "該当する記事は見つかりませんでした。"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    results = []

    for i, a in enumerate(articles, 1):
        article_text = f"ソース: {a['source']}\nタイトル: {a['title']}\n本文: {a['summary']}\nURL: {a['link']}"
        is_english = not any("\u3000" <= c <= "\u9fff" for c in a["title"] + a["summary"])
        english_section = ENGLISH_SECTION if is_english else ""
        prompt = PROMPT_TEMPLATE.format(article_text=article_text, english_section=english_section)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        results.append(f"{'='*60}\n【記事 {i}】{a['source']} - {a['title']}\n{'='*60}\n{message.content[0].text}")

    return "\n\n".join(results)


def send_email(subject, body):
    """Gmail で送信"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())


def main():
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    print(f"[{now_jst} JST] ニュース取得開始")

    articles = fetch_articles()
    print(f"  マッチした記事数: {len(articles)}")

    summary = summarize_articles(articles)

    subject = f"{SUBJECT_PREFIX} {now_jst} JST"
    send_email(subject, summary)
    print("  メール送信完了")


if __name__ == "__main__":
    main()
