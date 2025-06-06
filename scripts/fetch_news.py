#!/usr/bin/env python3
"""
Fetch *one* future-oriented English article per run
 ─ 重複(過去 KEEP_HISTORY 件)除外
 ─ stop_words.json で NG ワードフィルタ
 ─ 失敗時でも tmp/news.json を必ず残す
"""

from __future__ import annotations
import json, os, random, re, sys, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
import requests

# ───────── 設定 ─────────
API_KEY      = os.getenv("NEWS_API_KEY")
TOPIC_FILE   = "data/topics_main.json"
STOP_FILE    = "data/stop_words.json"
OUTPUT_FILE  = "tmp/news.json"
USED_FILE    = "tmp/used_titles.json"

PAGE_SIZE     = 20          # NewsAPI 1 クエリ取得件数
KEEP_HISTORY  = 30          # 重複チェック件数
TIME_WINDOW   = 1           # 何日前までの記事を対象にするか (days)

# ───────── 便利関数 ─────────
def load_json(path: str, default):
    p = Path(path)
    return json.loads(p.read_text("utf-8")) if p.exists() else default

def save_json(path: str, obj) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

# ───────── データロード ─────────
topics = load_json(TOPIC_FILE, [])
if not topics:
    sys.exit("❌ topic list empty")

stop_words = load_json(STOP_FILE, [])
stop_re    = re.compile("|".join(map(re.escape, stop_words)), re.I) if stop_words else None
used_set   = set(load_json(USED_FILE, []))

# ───────── NewsAPI 呼び出し ─────────
def query_news(q: str) -> list[dict]:
    since = (datetime.utcnow() - timedelta(days=TIME_WINDOW)).date()
    encoded = urllib.parse.quote_plus(q)
    url = (
        "https://newsapi.org/v2/everything?"
        f"q=\"{encoded}\"&from={since}"
        f"&language=en&sortBy=publishedAt&pageSize={PAGE_SIZE}"
        f"&apiKey={API_KEY}"
    )
    try:
        return requests.get(url, timeout=30).json().get("articles", [])
    except Exception as e:
        print(f"⚠️  NewsAPI error for '{q}': {e}")
        return []

# ───────── メイン処理 ─────────
random.shuffle(topics)                    # 偏りを抑える
picked_article: dict | None = None

for topic in topics:
    for art in query_news(topic):
        title = art.get("title", "")
        snippet = (art.get("description") or "") + (art.get("content") or "")

        if title in used_set:
            continue                      # 重複
        if stop_re and stop_re.search(title + snippet):
            continue                      # NG ワード
        picked_article = art
        break
    if picked_article:
        break

# ───────── 結果保存 ─────────
if picked_article:
    save_json(OUTPUT_FILE, {"articles": [picked_article]})
    used_set.add(picked_article["title"])
    save_json(USED_FILE, list(used_set)[-KEEP_HISTORY:])
    print(f"✅  Saved: {picked_article['title']}")
else:
    # 空 JSON を書き出して後段でスキップ処理を可能に
    save_json(OUTPUT_FILE, {"articles": []})
    print("❌  No suitable article found – wrote empty JSON")
