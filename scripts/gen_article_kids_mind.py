#!/usr/bin/env python3
"""
gen_article_kids_mind.py
────────────────────────────────────────────────────────────
金曜配信用：Kids Mindfulness Article Generator
"""
import json, os, openai, textwrap
from datetime import datetime
from pathlib import Path

NEWS_FILE = Path("tmp/news_kids_mind.json")
POST_DIR  = Path("posts/news/kids"); POST_DIR.mkdir(parents=True, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")

SYS = "You are a kids mindfulness coach writing in easy Japanese for 8-12 year olds."
PROMPT_NEWS = textwrap.dedent("""
### NEWS
Title: {title}
Desc: {desc}

Create an article in Markdown with the following sections:

## タイトル
(10〜16文字でキャッチーに)

### きょうのヒント
(120〜150文字。親しみやすく、ポジティブに)

### やってみよう！
- Step1
- Step2
- Step3
""").strip()

PROMPT_FALLBACK = textwrap.dedent("""
Create a fresh kids mindfulness article using the same Markdown format but without a NEWS section.
""").strip()

def chat(prompt: str) -> str:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYS},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return resp.choices[0].message.content.strip()

def main():
    if NEWS_FILE.exists():
        news = json.loads(NEWS_FILE.read_text())['articles'][0]
        content = chat(PROMPT_NEWS.format(
            title=news['title'],
            desc=news.get('description', '')[:400]
        ))
    else:
        content = chat(PROMPT_FALLBACK)

    path = POST_DIR / f"{datetime.utcnow():%Y-%m-%d}-mind.md"
    path.write_text(content, encoding="utf-8")
    print("✅ generated", path)

if __name__ == "__main__":
    main()
