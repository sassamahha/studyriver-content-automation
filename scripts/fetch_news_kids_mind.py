#!/usr/bin/env python3
import json, os, random, requests
from datetime import datetime, timedelta
from pathlib import Path

API_KEY = os.getenv("NEWS_API_KEY")
TOPICS  = json.loads(Path("data/topics_kids_mind.json").read_text())
SIGNALS = json.loads(Path("data/future_signals_kids_mind.json").read_text()) + [""]
STOPS   = json.loads(Path("data/stop_words.json").read_text())
TMP     = Path("tmp"); TMP.mkdir(exist_ok=True)
USED_F  = TMP/"used_titles_kids_mind.json"
OUT_F   = TMP/"news_kids_mind.json"

used = json.loads(USED_F.read_text()) if USED_F.exists() else []
since= (datetime.utcnow()-timedelta(days=5)).date()

def q(topic,sig):
    neg=" ".join(f'-\"{w}\"' for w in STOPS)
    return f'{sig} AND \"{topic}\" {neg}'.strip()

def search(url): return requests.get(url,timeout=20).json().get("articles",[])

random.shuffle(TOPICS)
for tp in TOPICS:
    sig=random.choice(SIGNALS)
    base=f"https://newsapi.org/v2/everything?language=en&from={since}&sortBy=publishedAt&pageSize=25&apiKey={API_KEY}"
    arts=search(base+f"&qInTitle={q(tp,sig)}") or search(base+f"&q={q(tp,sig)}")
    for art in arts:
        ttl=(art.get('title') or'').strip()
        if ttl and ttl not in used:
            OUT_F.write_text(json.dumps({'articles':[art]},ensure_ascii=False,indent=2))
            used.append(ttl); used=used[-40:]; USED_F.write_text(json.dumps(used))
            print(f\"✅ mind: {ttl}\"); exit()
print(\"❌ mind: 新規記事なし\")
