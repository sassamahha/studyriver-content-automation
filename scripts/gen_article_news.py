#!/usr/bin/env python3
"""
gen_article_news.py  ―  World News API で拾った記事を
未来仮説メディア『StudyRiver（スタリバ）』向けの
“雑誌風読み物” Markdown に仕立てるワンショットスクリプト
"""

import os, json, re
from datetime import datetime
from openai import OpenAI

# ─────────── settings
client      = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INPUT_FILE  = "tmp/news.json"
OUTPUT_DIR  = "posts/news/main/"

# ─────────── helpers
def sanitize_title(title: str) -> str:
    """ファイルスラッグ用に英数とハイフンだけ残す"""
    return re.sub(r"[^a-zA-Z0-9\-]", "-", title.lower()).strip("-")[:40]

def pick_desc(art: dict) -> str:
    return (art.get("description")
            or art.get("summary")
            or art.get("text", "")).strip()

def build_messages(news: dict):
    art   = news["articles"][0]
    title = art["title"]
    url   = art["url"]
    desc  = pick_desc(art)

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

#### 要約：
- {{ポイント1}}
- {{ポイント2}}
- {{ポイント3}}
→　箇条書きは3ポイント程度で、構造的かつわかりやすい表現にする。専門用語は避け、シンプルな文章を心がけてください。

## 2.背景を考える

> 社会制度・法制度・インフラ・業界慣習など、ニュースの根っこにある構造的な問題を簡潔に説明する。  
> 読者の視点と重なるよう、日常生活への影響や接点の例を挙げる。  
> 「この問題は、なぜ今起きたのか？」「どんな仕組みがそうさせたのか？」「この問題は、私たちの◯◯とどう関係している？」

→　多言語に翻訳しているため、宗教や特定の文化的価値観に関連した説明は避け、多様な国・地域で共通して理解される客観的な視点に限定すること。
→　背景は深掘りせず、根っこをシンプルに説明して、次セクションに繋がる文章構成で締めてください。

## 3.未来はどうなる？
→ 記事のメインセクションです。各仮説は以下の形式で、物語を語るように「3つ（IF1,IF2,IF3）」展開してください。
#### 仮説1（中立）：○○が当たり前になる未来  
> {{仮説1の説明}}

#### 仮説2（楽観）：○○が大きく発展する未来  
> {{仮説2の説明}}

#### 仮説3（悲観）：○○が失われていく未来  
> {{仮説3の説明}}

→ ３つの仮説は独立した囲みブロックにしてください。各仮説の説明は下記３構成で、文章は自然につないでください。尚、多言語に翻訳しているため、宗教や特定の文化的価値観に関連した説明は避け、多様な国・地域で共通して理解される客観的な視点に限定すること。
- 最初に直接的な変化
- 次に波及的な変化
- 最後に価値観の変化

## 4. わたしたちにできるヒント

#### 考え方のヒント
- {{読者自身の価値観を問い直す視点}}
- {{日常や選択に活かす視点}}

#### 小さな実践ヒント
- {{個人としてすぐに意識できること}}
- {{社会的に共有できること}}

→ 「大きい行動」ではなく、「思考＋小さな実践」の読者のささいなきっかけ作りとなる要素を意識する。

## 5. あなたならどうする？
- {{問い１}}
- {{問い２}}
- {{問い３}}
- まとめ文章

→ 読者に3つの選択肢を出して問いかけます。社会・テクノロジー・個人視点など、未来への関わり方の違いが出るように。
→ コメントを促すような読者への問いかけで締め、雑誌風に書いてください。  
例：「あなたはどんな未来を思い描きましたか？SNS引用やコメントでぜひ教えてください。」"""

    return [
        {
            "role": "system",
            "content": "あなたは『StudyRiver（スタリバ）』の未来仮説メディアに記事を寄稿する、読者との会話を大切にする雑誌ライターです。専門的すぎず、親しみやすく、想像を引き出す文章を心がけてください。"
        },
        {"role": "user", "content": user_prompt}
    ]

def generate_article(msgs: list[str]) -> str:
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7,
        max_tokens=1500
    )
    return res.choices[0].message.content

def save_markdown(title: str, md: str):
    date = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_title(title)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}{date}-{slug}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ Saved: {path}")

# ─────────── main
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
