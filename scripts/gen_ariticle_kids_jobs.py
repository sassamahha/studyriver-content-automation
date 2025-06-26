#!/usr/bin/env python3
"""
 gen_article_kids_jobs.py
 ───────────────────────────────────────────────────────────
 日曜配信用：Kids Future Jobs Article Generator

 - 入力  : tmp/news_kids_jobs.json （fetch_news_kids_generic.py が生成）
 - 出力先: posts/news/kids/YYYY-MM-DD-job-<hash>.md
 - 目的  : ニュースをヒントに未来の仕事プロフィールを 1 本生成
   （子ども向け、読みやすい日本語 350〜500 文字）
"""
import json, os, openai, textwrap, hashlib
from datetime import datetime
from pathlib import Path

# ───────── Settings ───────────────────────────────────
NEWS_FILE = Path("tmp/news_kids_jobs.json")
POST_DIR  = Path("posts/news/kids")
POST_DIR.mkdir(parents=True, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

# ───────── Prompt Templates ──────────────────────────
SYS_PROMPT = (
    "You are a kid-friendly career futurist. "
    "Target age 8-12. Write concise, engaging Japanese."
)

USER_TEMPLATE = textwrap.dedent(
    """
    ### NEWS
    Title: {title}
    Desc : {desc}

    上記ニュースをヒントに、子ども向け雑誌の "未来のしごと図鑑" 用プロフィールを 1 本書いてください。
    出力は下記 Markdown フォーマットを厳守。

    ## 未来の仕事：<Job Name>（8〜12文字）
    ### なにをする？
    120〜150文字。想像をふくらませる表現で。
    ### どんな力がいる？
    - スキル1（6〜10文字）
    - スキル2（6〜10文字）
    - スキル3（6〜10文字）
    ### どうやって学ぶ？
    - 方法1（子どもでも試せる）
    - 方法2
    - 方法3
    """
).strip()

FALLBACK_PROMPT = textwrap.dedent(
    """
    子ども向け未来職業プロフィールを 1 本、新規に考案してください。フォーマットは同じ。
    """
).strip()

# ───────── Helper Functions ───────────────────────

def load_news() -> dict | None:
    if not NEWS_FILE.exists():
        return None
    data = json.loads(NEWS_FILE.read_text())
    return data.get("articles", [None])[0]


def call_gpt(prompt: str) -> str:
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    return resp.choices[0].message.content.strip()


def save_markdown(md: str) -> None:
    date = datetime.utcnow().strftime("%Y-%m-%d")
    slug = hashlib.md5(md.encode()).hexdigest()[:8]
    path = POST_DIR / f"{date}-job-{slug}.md"
    path.write_text(md, encoding="utf-8")
    print("✅ Saved", path)

# ───────── Main ────────────────────────────────────

def main():
    news = load_news()
    if news:
        prompt = USER_TEMPLATE.format(
            title=news.get("title", ""),
            desc=news.get("description", "")[:400]
        )
        md = call_gpt(prompt)
        if not md.strip():
            print("⚠ GPT returned empty. Using fallback.")
            md = call_gpt(FALLBACK_PROMPT)
    else:
        print("⚠ NEWS file missing or empty. Using fallback.")
        md = call_gpt(FALLBACK_PROMPT)

    save_markdown(md)

if __name__ == "__main__":
    main()
