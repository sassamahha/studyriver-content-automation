import os
import json
import re
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news.json"
OUTPUT_DIR = "posts/news/main/"

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def build_messages(news):
    title = news["articles"][0]["title"]
    url = news["articles"][0]["url"]
    desc = news["articles"][0]["description"]

    user_prompt = f"""以下のニュースをもとに、未来仮説メディア『StudyRiver（スタリバ）』向けの“雑誌風読み物”記事を構成してください。

【ニュース】
タイトル: {title}
URL: {url}
概要: {desc}

--- 出力フォーマット ---
# （ニュースをもとにした、日本語の仮説的な問いかけタイトルにしてください）

## 1. ニュース要約
→ 読者が状況をイメージできるように、丁寧で語りかけるような雑誌風の文体で要約してください。  
→ 最後に「この出来事が未来にどうつながるか？」という問いかけのコメントを添えてください。  
→ その下に「引用元：{url}」を明記してください。

## 2. IF仮説（3つ）
→ 各仮説は以下の形式で、物語を語るように展開してください。

【形式】
◉ IF1：◯◯だったら？
（1段落で自然につなぐ。）
- 最初に直接的な変化
- 次に波及的な変化
- 最後に価値観の変化
→ これらを自然な文体で1つの段落として語ってください。

## 3. ワーク
> **あなたならどうする？**
→ 読者に3つの選択肢を出して問いかけます。社会・テクノロジー・個人視点など、未来への関わり方の違いが出るように。

## 4. まとめ
→ コメントを促す雑誌風の締めくくり文を書いてください。  
例：「あなたはどんな未来を思い描きましたか？コメント欄でぜひ教えてください。」"""

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
