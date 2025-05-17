import requests
import os
import glob
import base64
import markdown
import random

# WP接続情報（GitHub Secrets または .env）
WP_URL = os.getenv("WP_URL_KIDS")  # 例: https://studyriver.jp/kids（末尾にスラッシュなし）
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS_KIDS")

# 投稿対象のMarkdownフォルダ
POST_DIR = "posts/news/kids/"

# カテゴリとタグ（WordPress側で確認してIDを指定）
CATEGORY_ID = 3  # キッズカテゴリ（例）
TAG_IDS = [4]    # 未来教育タグ（例）

# ランダムで使いまわす画像（WPのメディアID）
MEDIA_IDS = [8, 16]  # キッズ向けの画像を追加していく

def get_auth():
    auth_str = f"{WP_USER}:{WP_APP_PASS_KIDS}"
    return base64.b64encode(auth_str.encode()).decode()

def post_article(title, html, media_id):
    headers = {
        "Authorization": f"Basic {get_auth()}",
        "Content-Type": "application/json"
    }

    url = f"{WP_URL_KIDS}/wp-json/wp/v2/posts"
    print("POST URL:", url)

    payload = {
        "title": title,
        "content": html,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS,
        "featured_media": media_id
    }

    res = requests.post(url, headers=headers, json=payload)

    print("DEBUG status:", res.status_code)
    print("DEBUG resp-len:", len(res.text))
    print("DEBUG first 200:", res.text[:200])

    if res.status_code not in (200, 201):
        print("❌ Post failed:", res.status_code, res.text)
        raise Exception("記事の投稿に失敗しました")
    print("✅ Posted:", res.status_code, res.json().get("link"))

def main():
    files = sorted(glob.glob(f"{POST_DIR}/*.md"), reverse=True)
    if not files:
        print("❌ No articles to post.")
        return

    latest = files[0]
    with open(latest, "r", encoding="utf-8") as f:
        md = f.read()
    html = markdown.markdown(md)
    title = md.splitlines()[0].replace("#", "").strip()

    media_id = random.choice(MEDIA_IDS)
    post_article(title, html, media_id)

if __name__ == "__main__":
    main()
