#!/usr/bin/env python3
"""
fetch_news_kids_generic.py
───────────────────────────────────────────────────────────────────────────────
共通ニュースフェッチャー（NewsAPI） for Kids シリーズ

Modes:
  --mode kids_main   Tue / Thu / Sat : 通常 Kids IF
  --mode kids_mind   Fri            : マインドフルネス
  --mode kids_jobs   Sun            : 未来職業図鑑
"""
import json, os, random, requests, argparse
from datetime import datetime, timedelta
from pathlib import Path

API_KEY  = os.getenv("NEWS_API_KEY")
LANG     = "en"
MAX_SIZE = 25
# 直近 n 日で検索（kids_main は 2 週間とやや広め）
DAYS = {"kids_main": 14, "kids_mind": 5, "kids_jobs": 3}

BASE = Path("data")
TMP  = Path("tmp"); TMP.mkdir(exist_ok=True)

# ───────────────────────────── helpers

def load(path: Path, default):
    return default if not path.exists() else json.loads(path.read_text())

def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def build_query(topic: str, signal: str, stops: list[str]) -> str:
    neg = " ".join(f'-"{w}"' for w in stops)
    return f'{signal} AND "{topic}" {neg}'.strip()

def fetch_news(url: str):
    try:
        return requests.get(url, timeout=20).json().get("articles", [])
    except requests.RequestException:
        return []

# ───────────────────────────── main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["kids_main", "kids_mind", "kids_jobs"], default="kids_main")
    args = ap.parse_args()
    mode = args.mode

    topics  = load(BASE / f"topics_{mode}.json", [])
    signals = load(BASE / f"future_signals_{mode}.json", [])
    if "" not in signals:  # 空信号も入れてシグナルなし検索を許容
        signals.append("")
    stops   = load(BASE / "stop_words.json", [])

    used_file = TMP / f"used_titles_{mode}.json"
    used      = load(used_file, [])

    random.shuffle(topics)
    since = (datetime.utcnow() - timedelta(days=DAYS[mode])).date().isoformat()

    for topic in topics:
        signal = random.choice(signals)
        query  = build_query(topic, signal, stops)

        url_title = (
            "https://newsapi.org/v2/everything?qInTitle=" + query +
            f"&from={since}&sortBy=publishedAt&language={LANG}" +
            f"&pageSize={MAX_SIZE}&apiKey={API_KEY}"
        )
        arts = fetch_news(url_title)

        # フォールバック：本文検索（タイトルヒット 0 件のとき）
        if not arts:
            url_body = (
                "https://newsapi.org/v2/everything?q=" + query +
                f"&from={since}&sortBy=publishedAt&language={LANG}" +
                f"&pageSize={MAX_SIZE}&apiKey={API_KEY}"
            )
            arts = fetch_news(url_body)

        for art in arts:
            title = (art.get("title") or "").strip()
            if title and title not in used:
                output_path = TMP / f"news_{mode}.json"
                save(output_path, {"articles": [art]})
                used.append(title)
                used[:] = used[-40:]  # keep last 40
                save(used_file, used)
                print(f"✅ {mode}: \"{title}\" ← {signal or 'NO-SIGNAL'} + {topic}")
                return
        print(f"⚠ {mode}: no fresh news for '{topic}' (signal='{signal}')")

    print(f"❌ {mode}: 新規記事を見つけられませんでした")

if __name__ == "__main__":
    main()
