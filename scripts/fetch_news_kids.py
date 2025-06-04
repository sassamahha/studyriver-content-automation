import requests
import json
from datetime import datetime, timedelta
import os

API_KEY = os.getenv("NEWS_API_KEY")
TOPIC_FILE = "data/topics_main.json"
OUTPUT_FILE = "tmp/news.json"
USED_TITLES_FILE = "tmp/used_titles.json"

def load_topics():
    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_used_titles():
    if os.path.exists(USED_TITLES_FILE):
        with open(USED_TITLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used_title(title):
    titles = load_used_titles()
    titles.append(title)
    titles = titles[-30:]  # 過去30件だけ記録
    with open(USED_TITLES_FILE, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False)

def fetch_news(query):
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&from={yesterday}&sortBy=publishedAt&language=en&pageSize=10&apiKey={API_KEY}"
    )
    response = requests.get(url)
    return response.json()

def main():
    os.makedirs("tmp", exist_ok=True)
    topics = load_topics()
    query = " OR ".join(topics)
    news_data = fetch_news(query)
    used_titles = load_used_titles()

    for article in news_data.get("articles", []):
        title = article.get("title", "")
        if title not in used_titles:
            # 保存対象が決定したら書き出し
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump({"articles": [article]}, f, ensure_ascii=False, indent=2)
            save_used_title(title)
            print(f"✅ Fetched: {title}")
            return

    print("❌ 重複しないニュースが見つかりませんでした")

if __name__ == "__main__":
    main()
