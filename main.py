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


def summarize_articles(articles):
    """Claude API で記事を要約"""
    if not articles:
        return "該当する記事は見つかりませんでした。"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += f"\n【{i}】{a['source']} - {a['title']}\n{a['summary']}\nURL: {a['link']}\n"

    prompt = f"""以下のニュース記事を日本語で簡潔に要約してください。
各記事について以下の形式でまとめてください：

・タイトル（英語の場合は日本語訳も）
・要点（2〜3文）
・URL

記事一覧：
{articles_text}
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


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
