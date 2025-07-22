#!/usr/bin/env python3
"""gen_article_news.py — News → 雑誌風記事生成"""

import os, json, re
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news.json"
OUTPUT_DIR = "posts/news/main/"

# ───────────────── utils
def sanitize_title(title: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")[:40]

def get_desc(article: dict) -> str:              
    """WorldNewsAPI → summary / text を説明文として使う"""
    desc = article.get("description")            
    if not desc:
        desc = article.get("summary") or article.get("text", "")
    return desc.strip()

# ───────────── prompt builder
def build_messages(news):
    art  = news["articles"][0]
    title = art["title"]
    url   = art["url"]
    desc  = get_desc(art)                       

    print("🟡 DEBUG: Promptビルド中 (タイトル):", title)

    user_prompt = f"""以下のニュースをもとに、未来仮説メディア『StudyRiver（スタリバ）』向けの“雑誌風読み物”記事を構成してください。

【ニュース】
タイトル: {title}
URL: {url}
概要: {desc}

--- 出力フォーマット ---
# （ニュースをもとにした、日本語の仮説的な問いかけタイトルにしてください）

{{リード文として、今起きている出来事やニュースに触れたあと、「この流れが続いたら？」という問いを提示し、読者にIFを投げかけてください。尚、多言語に翻訳しているため、宗教や特定の文化的価値観に関連した説明は避け、多様な国・地域で共通して理解される客観的な視点に限定すること。}}

## 1. 今日のニュース
引用元:  
{{URL}}
...
（以下フォーマットはそのまま）
"""
    return [
        {
            "role": "system",
            "content": "あなたは『StudyRiver（スタリバ）』の未来仮説メディアに記事を寄稿する、読者との会話を大切にする雑誌ライターです。専門的すぎず、親しみやすく、想像を引き出す文章を心がけてください。"
        },
        {"role": "user", "content": user_prompt}
    ]

# ───────────── OpenAI
def generate_article(msgs):
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7,
        max_tokens=1500,
    )
    return res.choices[0].message.content

# ───────────── IO
def save_markdown(title, content):
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_title(title)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}{date_str}-{slug}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved: {path}")

# ───────────── main
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)

    if not news.get("articles"):
        print("❌ ニュース記事が見つかりませんでした。")
        return

    msgs = build_messages(news)
    article_md = generate_article(msgs)
    save_markdown(news["articles"][0]["title"], article_md)

if __name__ == "__main__":
    main()
