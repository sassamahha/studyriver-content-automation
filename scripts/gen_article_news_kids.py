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

    user_prompt = f"""きょうのニュースを、子どもにもわかるように、やさしくていねいに説明してください。  
そのうえで、「みらいってどうなるんだろう？」と子どもが考えられるような構成で、下の形式でまとめてください。

【ニュース】
タイトル: {title}
URL: {url}
説明: {desc}

--- 出力フォーマット（この順番で） ---

# （ひらがな＋やさしい日本語のタイトル）

## 1. ニュースのようやく
→ まずは「きょうのニュースだよ！」から始めて、  
　子どもにも伝わるように語りかけるように説明してください。

→ 次に「どうしてそんなことになったの？」という気持ちを大切にして、  
　「なぜ？」を3回くらいくりかえして、ニュースの背景を深ぼってください。  
　（例：「どうして？」→「それはね…」のように）

→ 最後に「このできごとは、みらいにどうつながるのかな？」という一文でしめくくってください。  
→ その下に「引用元：{url}」とリンクを明記してください。

## 2. つまり、こうだね
→ ニュースの内容から子どもがひとことで理解できる「やさしい結論」を書いてください。  
（例：「だから、すぐにやめないで、つづけたほうがいいかもしれないね。」など）

## 3. みらいのもしも
→ 「#### もしも１：～だったら？」という仮説を3つ（もしも１、もしも２、もしも３）書いてください。  
→ それぞれを1つの短い段落で書いて、  
　仮説→変化→気づき、という自然な文章にしてください。  
　※ 箇条書きにはせず、文章で書いてください。

## 4. きみはどうする？（ワーク）
→ 子どもに問いかける形で、「じぶんだったらどうするかな？」と考えさせる文章にしてください。  
→ 複数の視点（やってみる／やらない／ちがうことを考える）なども交えてください。

## 5. おわりに
→ もう一度やさしい結論を想起させて、前向きなメッセージでしめくくってください。  
（例：「みらいは、きみのえらびでつくられるよ！」など）"""

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
