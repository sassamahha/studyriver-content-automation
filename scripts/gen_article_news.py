# scripts/gen_article_news.py

from openai import OpenAI
import os
import json
from datetime import datetime
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news.json"
OUTPUT_DIR = "posts/news/main/"

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def build_messages(news):
    title = news["articles"][0]["title"]
    url = news["articles"][0]["url"]
    desc = news["articles"][0]["description"]

    user_prompt = f"""### ニュース要約
{title}
{url}
{desc}

--- 出力フォーマット ---
# {title}

## 1. ニュース要約（150字以内で）

## 2. IF仮説（3つ・各3階層で深掘り）

### ◉ IF1：〜？
- レベル1（直接変化）：〜
- レベル2（副次影響）：〜
- レベル3（価値観変化）：〜

### ◉ IF2：〜？
- レベル1（直接変化）：〜
- レベル2（副次影響）：〜
- レベル3（価値観変化）：〜

### ◉ IF3：〜？
- レベル1（直接変化）：〜
- レベル2（副次影響）：〜
- レベル3（価値観変化）：〜

## 3. ワーク
> **あなたならどうする？**
- A. ◯◯
- B. ◯◯
- C. ◯◯

## 4. まとめ
「あなたなら、どんな未来を選びますか？」  
コメントで教えてください。"""

    return [
        {
            "role": "system",
            "content": "あなたは『StudyRiver（スタリバ）』の未来仮説メディア専門ライターです。最新ニュースの背景にある未来の可能性を、読者が考えたくなる形で構造化してください。"
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

def generate_article(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1200
    )
    return response.choices[0].message.content

def save_markdown(title, content):
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_title(title)[:40]
    filename = f"{OUTPUT_DIR}{date_str}-{slug}.md"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved: {filename}")

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)
    messages = build_messages(news)
    article = generate_article(messages)
    title = news["articles"][0]["title"]
    save_markdown(title, article)

if __name__ == "__main__":
    main()
