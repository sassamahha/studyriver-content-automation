import os
import json
import re
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news_kids.json"
OUTPUT_DIR = "posts/news/kids/"

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def build_messages(news):
    title = news["articles"][0]["title"]
    url = news["articles"][0]["url"]
    desc = news["articles"][0]["description"]

    user_prompt = f"""以下のニュースをもとに、小学生でもわかるような内容に書きかえてください。

【ニュース】
タイトル: {title}
URL: {url}
説明: {desc}

--- 出力フォーマット ---
# タイトル（ひらがなとやさしい漢字で。疑問文やワクワクするタイトル）

## 1. ニュースのようやく
→ 小学生でもわかるように、やさしい言葉でニュースの内容を説明してください。
→ 最後に「このできごとは、みらいにどうつながるのかな？」という問いかけを入れてください。
→ 「きょうのニュース」などのラベルを付けてもOKです。
→ 引用元リンク（{url}）を文末に書いてください。

## 2. みらいのもしも
→ それぞれ「もし〜だったら？」の形で始めて、こどもが考えやすい未来を「3つ」やさしく説明してください。
→ 例：
### もし、みんなが〇〇をつかうようになったら？
→ △△がふえて、□□がへるかもしれないね。そしてこんなみらいになるかもしれない

## 3. きみはどうする？
→ こどもがじぶんごととして考えられるような3つの選択肢を、やさしく問いかけてください。

## 4. おわりに
→「みらいは、きみのえらびでつくられるよ！」のような前向きなメッセージでしめくくってください。"""

    return [
        {
            "role": "system",
            "content": "あなたは、小学生にわかりやすく未来を考えるきっかけを届ける、こども向けライターです。むずかしい言葉は使わず、親しみやすく、たのしく書いてください。"
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
