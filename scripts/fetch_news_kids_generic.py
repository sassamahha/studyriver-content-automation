#!/usr/bin/env python3
"""
fetch_news_kids_generic.py
────────────────────────────────────────────────────────────
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
DAYS     = {"kids_main": 14, "kids_mind": 5, "kids_jobs": 3}   # 検索期間

BASE = Path("data")
TMP  = Path("tmp"); TMP.mkdir(exist_ok=True)

# ───────────────────────── helpers
def load(path: Path, default):
    return default if not path.exists() else json.loads(path.read_text())

def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def build_query(topic: str, signal: str, stops: list[str]) -> str:
    """空 signal のときは AND を付けない"""
    neg = " ".join(f'-"{w}"' for w in stops)
    if signal:
        return f'{signal} AND "{topic}" {neg}'.strip()
    return f'"{topic}" {neg}'.strip()

def fetch_news(url: str):
    try:
        return requests.get(url, timeout=20).json().get("articles", [])
    except requests.RequestException:
        return []

# ───────────────────────── main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["kids_main", "kids_mind", "kids_jobs"],
                    default="kids_main")
    mode = ap.parse_args().mode

    topics  = load(BASE / f"topics_{mode}.json", [])
    signals = load(BASE / f"future_signals_{mode}.json", [])
    if "" not in signals:
        signals.append("")                   # signal 無し検索も許容
    stops   = load(BASE / "stop_words.json", [])

    used_file = TMP / f"used_titles_{mode}.json"
    used      = load(used_file, [])

    random.shuffle(topics)
    since = (datetime.utcnow() - timedelta(days=DAYS[mode])).date().isoformat()

    for topic in topics:
        signal = random.choice(signals)
        query  = build_query(topic, signal, stops)

        url_title = ( "https://newsapi.org/v2/everything?"
                      f"qInTitle={query}&from={since}&sortBy=publishedAt"
                      f"&language={LANG}&pageSize={MAX_SIZE}&apiKey={API_KEY}" )
        arts = fetch_news(url_title)

        # フォールバック：本文検索
        if not arts:
            url_body = ( "https://newsapi.org/v2/everything?"
                         f"q={query}&from={since}&sortBy=publishedAt"
                         f"&language={LANG}&pageSize={MAX_SIZE}&apiKey={API_KEY}" )
            arts = fetch_news(url_body)

        for art in arts:
            title = (art.get("title") or "").strip()
            if title and title not in used:
                out = TMP / f"news_{mode}.json"
                save(out, {"articles": [art]})
                used.append(title); used[:] = used[-40:]
                save(used_file, used)
                print(f"✅ {mode}: \"{title}\" ← {signal or 'NO-SIGNAL'} + {topic}")
                return
        print(f"⚠ {mode}: no fresh news for '{topic}' (signal='{signal}')")

    print(f"❌ {mode}: 新規記事を見つけられませんでした")

if __name__ == "__main__":
    main()
