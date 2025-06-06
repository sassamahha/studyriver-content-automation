#!/usr/bin/env python3

from __future__ import annotations
import os, json, random, re, requests
from datetime import datetime, timedelta
from pathlib import Path

# ──────────────────────────
# 可変パラメータ
# ──────────────────────────
API_KEY        = os.getenv("NEWS_API_KEY")              # NewsAPI key
TOPIC_FILE     = os.getenv("TOPIC_FILE", "data/topics_main.json")
STOP_FILE      = "data/stop_words.json"                 # NG ワード集
OUTPUT_FILE    = "tmp/news.json"
USED_TITLES_FILE = "tmp/used_titles.json"

PAGE_SIZE      = int(os.getenv("NEWS_PAGE_SIZE", 20))   # 1 クエリ最大件数
KEEP_HISTORY   = 30                                     # 重複チェック数

# ──────────────────────────
# 共通 I/O ヘルパ
# ──────────────────────────
def _load_json(path: str, default):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default

def _save_json(path: str, obj) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# ──────────────────────────
# データローダ
# ──────────────────────────
def load_topics() -> list[str]:
    return _load_json(TOPIC_FILE, [])

def load_stops() -> list[str]:
    return _load_json(STOP_FILE, [])

def load_used_titles() -> list[str]:
    return _load_json(USED_TITLES_FILE, [])

def save_used_title(title: str) -> None:
    titles           = load_used_titles()
    titles.append(title)
    _save_json(USED_TITLES_FILE, titles[-KEEP_HISTORY:])

# ──────────────────────────
# NewsAPI 呼び出し
# ──────────────────────────
def fetch_news(query: str) -> dict:
    since = (datetime.utcnow() - timedelta(days=1)).date()
    url   = (
        "https://newsapi.org/v2/everything?"
        f"q=\"{query}\" NOT politics NOT religion"
        f"&from={since}&sortBy=publishedAt&language=en"
        f"&pageSize={PAGE_SIZE}&apiKey={API_KEY}"
    )
    return requests.get(url, timeout=30).json()

# ──────────────────────────
# メイン
# ──────────────────────────
def main() -> None:
    Path("tmp").mkdir(exist_ok=True)

    topics   = load_topics()
    if not topics:
        raise SystemExit("❌ Topic list is empty.")

    stop_re  = re.compile("|".join(map(re.escape, load_stops())), re.I) \
               if Path(STOP_FILE).exists() else None
    used_set = set(load_used_titles())

    # その日のトピックをランダムに 1 つ
    query    = random.choice(topics)
    news     = fetch_news(query)

    for art in news.get("articles", []):
        title   = art.get("title", "")
        snippet = (art.get("description") or "") + (art.get("content") or "")

        if title in used_set:
            continue
        if stop_re and stop_re.search(title + snippet):
            continue

        _save_json(OUTPUT_FILE, {"articles": [art]})
        save_used_title(title)
        print(f"✅ Fetched: {title}")
        return

    print("❌ No non-duplicate safe article found.")

if __name__ == "__main__":
    main()
