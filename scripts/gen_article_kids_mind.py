import os
import json
import re
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news_kids_mind.json"
OUTPUT_DIR = "posts/news/kids_mind/"

def sanitize_title(title):
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")

def build_messages(news):
    title = news["articles"][0]["title"]
    url = news["articles"][0]["url"]
    desc = news["articles"][0]["description"]

    user_prompt = f"""小学校低〜中学年のこどもと保護者を対象に「こころの扱い方」をテーマとした読み物記事を作成してください。

【ニュース】
{title}
URL: {url}
概要: {desc}

--- 出力フォーマット ---
> タイトルは感情をやさしく言語化した問いかけにしてください(例：「“なんでかわからないけど、もやもやする日にあなたはどうする？”」)

> リード文として、課題と解決策を提示します。よくある“こころのもやもや”を取り上げて、  
> その気持ちがどこから来るのか、どう向き合うとよいかという**考え方のヒント**をやさしく提示してください。


## 実際に起きることを想像してみよう

> 以下のような具体的なシーンのタイトルをつけます。
> 各ケース内容は、「事実→その時どう思ったか？→どうやって向き合ったか？」の順番で200文字程度のストーリ仕立てにしてください（目安：3つ）：

### ケースA：友達とのすれ違い
### ケースB：家庭での小さなケンカ  
### ケースC：ひとりのときに感じたさみしさ


## 💬 親子で考える：対話のヒント

> 以下のルールを徹底して、リスト形式で出力してください（テーブルNG）
> Yes/Noではなく、自由に考えたくなるオープンな問い  
> 小学生でも理解しやすい言葉で  
> 各問いに「ねらい（教育的意図）」を記載すること


- **質問例：** もし、気持ちを「色」で表すとしたら、今日は何色？  
  **ねらい：** 想像力・感情の言語化

- **質問例：** いやなことがあったとき、家族でどんな約束をしたら安心できそう？  
  **ねらい：** 行動の選択・家庭内のルールづくり

- **質問例：** 友だちが困っていたら、どんな声をかけたい？  
  **ねらい：** 共感力・社会性


## きみならどうする？
> 読後に**自分を見つめたくなるような余韻**を残してください  
> コメントや感想を促す文（例：「あなたはどう思った？SNSで教えてね」）を加えてもOK
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
