#!/usr/bin/env python3
"""
topics_kids.json 用 – 未来科学ネタを子ども向けに 1 本取得
"""
import json, os, random, requests
from datetime import datetime, timedelta
from pathlib import Path

API_KEY          = os.getenv("NEWS_API_KEY")
TOPIC_FILE       = "data/topics_kids.json"
OUTPUT_FILE      = "tmp/news_kids.json"
USED_TITLES_FILE = "tmp/used_titles_kids.json"
MAX_PER_TOPIC    = 25
LANG             = "en"
DAYS_BACK        = 7            # kids は幅広く 1 週間

TMP_DIR = Path("tmp"); TMP_DIR.mkdir(exist_ok=True)

def load_json(p, fb): return fb if not Path(p).exists() else json.loads(Path(p).read_text())
def save_json(p, d): Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2))

def fetch_news(q):
    since = (datetime.utcnow() - timedelta(days=DAYS_BACK)).date()
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={q}&from={since}&sortBy=publishedAt&language={LANG}"
        f"&pageSize={MAX_PER_TOPIC}&apiKey={API_KEY}"
    )
    return requests.get(url, timeout=20).json()

def main():
    topics      = load_json(TOPIC_FILE, [])
    used_titles = load_json(USED_TITLES_FILE, [])
    random.shuffle(topics)

    for kw in topics:
        for art in fetch_news(kw).get("articles", []):
            title = art.get("title", "").strip()
            if title and title not in used_titles:
                save_json(OUTPUT_FILE, {"articles": [art]})
                used_titles.append(title)
                used_titles = used_titles[-40:]
                save_json(USED_TITLES_FILE, used_titles)
                print(f"✅ kids pick: “{title}” ← {kw}")
                return
        print(f"⚠ kids no fresh for '{kw}'")

    print("❌ kids 新規記事なし")

if __name__ == "__main__":
    main()
