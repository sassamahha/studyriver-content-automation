# scripts/fetch_news.py

import requests
import json
from datetime import datetime, timedelta
import os

API_KEY = os.getenv("NEWS_API_KEY")
TOPIC_FILE = "data/topics_main.json"
OUTPUT_FILE = "tmp/news.json"

def load_topics():
    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        topics = json.load(f)
    return topics

def fetch_news(query):
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&from={yesterday}&sortBy=publishedAt&language=en&pageSize=1&apiKey={API_KEY}"
    )
    response = requests.get(url)
    return response.json()

def main():
    topics = load_topics()
    query = " OR ".join(topics)
    news = fetch_news(query)

    os.makedirs("tmp", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

    print("✅ News fetched and saved to", OUTPUT_FILE)

if __name__ == "__main__":
    main()
