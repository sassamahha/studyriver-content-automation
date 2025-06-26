#!/usr/bin/env python3

import json, os, random, requests
from datetime import datetime, timedelta
from pathlib import Path

# ─────────── settings
API_KEY           = os.getenv("NEWS_API_KEY")
TOPIC_FILE        = "data/topics_kids_jobs.json"
SIGNAL_FILE       = "data/future_signals_kids_jobs.json"
STOP_FILE         = "data/stop_words.json"
OUTPUT_FILE       = "tmp/news_kids_jobs.json"
USED_TITLES_FILE  = "tmp/used_titles.json"

MAX_PER_CALL      = 25
LANG              = "en"
DAYS_BACK         = 7
ROTATE_KEEP       = 40    # used_titles の保持件数

TMP_DIR = Path("tmp"); TMP_DIR.mkdir(exist_ok=True)

# ─────────── utils
def load_json(path: str, fallback):
    p = Path(path);  return fallback if not p.exists() else json.loads(p.read_text())

def save_json(path: str, data) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def build_query(topic: str, signal: str, stop_words: list[str]) -> str:
    neg = " ".join(f'-"{w}"' for w in stop_words)
    return f'{signal} AND "{topic}" {neg}'.strip()

def call_newsapi(params: dict) -> list[dict]:
    url = "https://newsapi.org/v2/everything"
    resp = requests.get(url, params|{"apiKey": API_KEY}, timeout=20).json()
    return resp.get("articles", [])

# ─────────── main
def main():
    topics      = load_json(TOPIC_FILE, [])
    signals     = load_json(SIGNAL_FILE, [])
    stop_words  = load_json(STOP_FILE, [])
    used_titles = load_json(USED_TITLES_FILE, [])

    random.shuffle(topics)
    since = (datetime.utcnow() - timedelta(days=DAYS_BACK)).date().isoformat()

    for topic in topics:
        signal = random.choice(signals)
        base_q = build_query(topic, signal, stop_words)

        # --- ①タイトル検索
        articles = call_newsapi({
            "qInTitle": base_q,
            "language": LANG,
            "from": since,
            "sortBy": "publishedAt",
            "pageSize": MAX_PER_CALL,
        }) or call_newsapi({
            # --- ②本文検索フォールバック
            "q": base_q,
            "language": LANG,
            "from": since,
            "sortBy": "publishedAt",
            "pageSize": MAX_PER_CALL,
        })

        # --- ③さらにゼロなら signal を外して topic 単体検索
        if not articles:
            loose_q = build_query(topic, "", stop_words)
            articles = call_newsapi({
                "qInTitle": loose_q,
                "language": LANG,
                "from": since,
                "sortBy": "publishedAt",
                "pageSize": MAX_PER_CALL,
            })

        for art in articles:
            title = (art.get("title") or "").strip()
            if title and title not in used_titles:
                save_json(OUTPUT_FILE, {"articles": [art]})
                used_titles.append(title)
                used_titles[:] = used_titles[-ROTATE_KEEP:]
                save_json(USED_TITLES_FILE, used_titles)
                print(f"✅ pick: “{title}” ← {signal} + {topic}")
                return

        print(f"⚠ no fresh article for '{topic}' (signal='{signal}')")

    print("❌ 新規記事を見つけられませんでした")

if __name__ == "__main__":
    main()
