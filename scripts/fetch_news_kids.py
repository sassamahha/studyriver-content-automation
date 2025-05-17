import requests
import json
import os
from datetime import datetime, timedelta
import random
import re

API_KEY = os.getenv("NEWS_API_KEY")
TOPIC_FILE = "data/topics_kids.json"
OUTPUT_FILE = "tmp/news_kids.json"
POST_DIR = "posts/news/kids/"

def load_topics():
    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def is_already_posted(title):
    slug = sanitize_title(title)[:40]
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{POST_DIR}{date_prefix}-{slug}.md"
    return os.path.exists(filename)

def fetch_news(query):
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&from={yesterday}&sortBy=publishedAt&language=en&pageSize=5&apiKey={API_KEY}"
    )
    response = requests.get(url)
    return response.json()

def main():
    topics = load_topics()
    query = " OR ".join(topics)
    response = fetch_news(query)
    articles = response.get("articles", [])

    if not articles:
        print("❌ No news articles found.")
        return

    # フィルタ：未投稿の記事だけに絞る
    new_articles = [a for a in articles if not is_already_posted(a["title"])]

    if not new_articles:
        print("⚠️ All fetched articles already posted. Skipping.")
        return

    # ランダムで1件選択
    chosen = random.choice(new_articles)

    # 保存
    os.makedirs("tmp", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"articles": [chosen]}, f, indent=2, ensure_ascii=False)

    print("✅ New article (kids) selected and saved:", chosen["title"])

if __name__ == "__main__":
    main()
