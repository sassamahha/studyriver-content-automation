import os
import json
import re
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news_kids_jobs.json"
OUTPUT_DIR = "posts/news/kids_jobs/"

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def build_messages(news):
    title = news["articles"][0]["title"]
    url = news["articles"][0]["url"]
    desc = news["articles"][0]["description"]

    user_prompt = f"""子ども向け雑誌の "未来のしごと図鑑" 用プロフィールを 1 本書いてください。

<comment>
以下のガイドラインは**回答に含めない**こと。
- 出力は Markdown で、`# ` から始める本文のみを返す
- タイトルは 「未来の職業：<一言要約>」 固定
- 指示文・comment タグは消す
</comment>

【ニュース】
タイトル: {title}
URL: {url}
概要: {desc}

<comment>
--- 出力フォーマット ---
# 未来の職業：<一言要約>
## どんな仕事？
> 未来の世界で働く具体例を挙げて、200字程度で書く

## どんな未来に変えてくれる？
> 具体例の先を想像をふくらませ 未来仮説を200字程度で書く

## どんな力がいる？
- スキル1 (スキル名：どんな力か一言要約)
- スキル2
- スキル3

## どうやって学ぶ？
- 方法1（子どもでも試せる）
- 方法2
- 方法3
</comment>
"""

    return [
        {
            "role": "system",
            "content": "あなたは『StudyRiver（スタリバ）』の未来仮説メディアに記事を寄稿する、読者との会話を大切にする雑誌ライターです。専門的すぎず、親しみやすく、想像を引き出す文章を心がけてください。"
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
        max_tokens=1500
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

    if not news.get("articles"):
        print("❌ ニュース記事が見つかりませんでした。")
        return

    messages = build_messages(news)
    article = generate_article(messages)
    title = news["articles"][0]["title"]
    save_markdown(title, article)

if __name__ == "__main__":
    main()
