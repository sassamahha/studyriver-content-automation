#!/usr/bin/env python3
"""
Kids-friendly news fetcher
  - topics_kids.json を使って 1 本だけ取得
  - stop_words.json で NG ワード除外
  - 失敗しても tmp/news_kids.json を空 JSON で残す
"""

from __future__ import annotations
import json, os, random, re, sys, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
import requests

# ───────── 設定 (★子ども用に変更) ─────────
API_KEY       = os.getenv("NEWS_API_KEY")
TOPIC_FILE    = "data/topics_kids.json"      # ← kids トピック
STOP_FILE     = "data/stop_words.json"
OUTPUT_FILE   = "tmp/news_kids.json"         # ← kids 向け出力
USED_FILE     = "tmp/used_titles_kids.json"  # ← kids 向け重複管理

PAGE_SIZE     = 20
KEEP_HISTORY  = 30
TIME_WINDOW   = 1   # day

# ───────── 共有 util ─────────
def load_json(path: str, default):
    p = Path(path)
    return json.loads(p.read_text("utf-8")) if p.exists() else default

def save_json(path: str, obj) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")

topics    = load_json(TOPIC_FILE, [])
stop_list = load_json(STOP_FILE, [])
stop_re   = re.compile("|".join(map(re.escape, stop_list)), re.I) if stop_list else None
used_set  = set(load_json(USED_FILE, []))

if not topics:
    sys.exit("❌ kids topics list empty")

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
random.shuffle(topics)
picked: dict | None = None

for topic in topics:
    for art in query_news(topic):
        title = art.get("title", "")
        snippet = (art.get("description") or "") + (art.get("content") or "")

        if title in used_set:
            continue
        if stop_re and stop_re.search(title + snippet):
            continue
        picked = art
        break
    if picked:
        break

# ───────── 保存 ─────────
if picked:
    save_json(OUTPUT_FILE, {"articles": [picked]})
    used_set.add(picked["title"])
    save_json(USED_FILE, list(used_set)[-KEEP_HISTORY:])
    print(f"✅ kids saved: {picked['title']}")
else:
    save_json(OUTPUT_FILE, {"articles": []})
    print("❌ kids – no suitable article; empty JSON written")

if __name__ == "__main__":
    pass   # 全処理は import でも使えるように上記で完結
