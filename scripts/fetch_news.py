#!/usr/bin/env python3
"""
topics_main.json のキーワードを 1 つずつ試し、
まだ使っていないタイトルの記事を 1 本取得して tmp/news.json に保存
"""
import json, os, random, requests
from datetime import datetime, timedelta
from pathlib import Path

API_KEY          = os.getenv("NEWS_API_KEY")
TOPIC_FILE       = "data/topics_main.json"
OUTPUT_FILE      = "tmp/news.json"
USED_TITLES_FILE = "tmp/used_titles.json"
MAX_PER_TOPIC    = 25          # NewsAPI pageSize
LANG             = "en"
DAYS_BACK        = 3           # 直近 n 日以内の記事だけ対象

TMP_DIR = Path("tmp"); TMP_DIR.mkdir(exist_ok=True)

# ───────────────────────────
def load_json(path: str, fallback):
    p = Path(path)
    return fallback if not p.exists() else json.loads(p.read_text())

def save_json(path: str, data) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def fetch_news(keyword: str):
    since = (datetime.utcnow() - timedelta(days=DAYS_BACK)).date()
    url   = (
        "https://newsapi.org/v2/everything?"
        f"q={keyword}"
        f"&from={since}"
        f"&sortBy=publishedAt"
        f"&language={LANG}"
        f"&pageSize={MAX_PER_TOPIC}"
        f"&apiKey={API_KEY}"
    )
    return requests.get(url, timeout=20).json()

# ───────────────────────────
def main():
    topics       = load_json(TOPIC_FILE, [])
    used_titles  = load_json(USED_TITLES_FILE, [])

    random.shuffle(topics)          # 偏り防止

    for kw in topics:
        data = fetch_news(kw)
        for art in data.get("articles", []):
            title = art.get("title", "").strip()
            if title and title not in used_titles:
                save_json(OUTPUT_FILE, {"articles": [art]})
                used_titles.append(title)
                used_titles = used_titles[-40:]   # ローテーション 40件保持
                save_json(USED_TITLES_FILE, used_titles)
                print(f"✅ pick: “{title}” ← {kw}")
                return

        print(f"⚠ no fresh article for '{kw}'")

    print("❌ 新規記事を見つけられませんでした")

if __name__ == "__main__":
    main()
