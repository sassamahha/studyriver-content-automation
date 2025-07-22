#!/usr/bin/env python3
"""
--------------------------------
topics_main.json から主題を 1 つ、
future_signals.json から未来シグナルを 1 つ抽選し、

  1. 「タイトルに signal+topic を含むか」でフィルタ
  2. ヒット 0 → 本文検索にフォールバック
  3. さらに 0 → topic 単体で緩め検索

条件を満たす最新記事 1 本を tmp/news.json に保存する。
"""

import json, os, random, requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

# ───────────── settings ──────────────
API_KEY           = os.getenv("WORLDNEWS_API_KEY")
TOPIC_FILE        = "data/topics_main.json"
SIGNAL_FILE       = "data/future_signals.json"
STOP_FILE         = "data/stop_words.json"
OUTPUT_FILE       = "tmp/news.json"
USED_TITLES_FILE  = "tmp/used_titles.json"

MAX_PER_CALL      = 25                       # number=◯
LANG              = "en"
DAYS_BACK         = 3
ROTATE_KEEP       = 40                       # used_titles の保持件数
API_URL           = "https://api.worldnewsapi.com/search-news"

TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)

# ───────────── utils ──────────────────
def load_json(path: str, fallback):
    p = Path(path)
    return fallback if not p.exists() else json.loads(p.read_text(encoding="utf-8"))

def save_json(path: str, data) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def build_query(topic: str, signal: str, stop_words: List[str]) -> str:
    neg = " ".join(f'-"{w}"' for w in stop_words)
    return f'{signal} "{topic}" {neg}'.strip()

def call_worldnews(params: Dict) -> List[Dict]:
    """World News API thin wrapper (api‑key はクエリで渡す)"""
    params = params.copy()         # mutate 回避
    params["api-key"] = API_KEY
    resp = requests.get(API_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("news", [])

def title_contains(art: Dict, *needles: str) -> bool:
    title = art.get("title", "").lower()
    return all(n.lower() in title for n in needles if n)

# ───────────── main ───────────────────
def main():
    if not API_KEY:
        raise SystemExit("❌ WORLDNEWS_API_KEY env var not set")

    topics      = load_json(TOPIC_FILE, [])
    signals     = load_json(SIGNAL_FILE, [])
    stop_words  = load_json(STOP_FILE, [])
    used_titles = load_json(USED_TITLES_FILE, [])

    random.shuffle(topics)
    since = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).date().isoformat()

    for topic in topics:
        signal = random.choice(signals)
        base_q = build_query(topic, signal, stop_words)

        # —— ① タイトル優先検索
        arts = call_worldnews({
            "text": base_q,
            "language": LANG,
            "earliest-publish-date": since,
            "sort": "publish-time",
            "number": MAX_PER_CALL,
        })
        arts = [a for a in arts if title_contains(a, topic, signal)]

        # —— ② 本文検索フォールバック
        if not arts:
            arts = call_worldnews({
                "text": base_q,
                "language": LANG,
                "earliest-publish-date": since,
                "sort": "publish-time",
                "number": MAX_PER_CALL,
            })

        # —— ③ signal を外して緩め検索
        if not arts:
            loose_q = build_query(topic, "", stop_words)
            arts = call_worldnews({
                "text": loose_q,
                "language": LANG,
                "earliest-publish-date": since,
                "sort": "publish-time",
                "number": MAX_PER_CALL,
            })

        for art in arts:
            title = art.get("title", "").strip()
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
