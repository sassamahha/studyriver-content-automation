import requests
import os
import glob
import base64
import markdown
import random

# WP接続情報（GitHub Secrets または .env）
WP_URL = os.getenv("WP_URL")  # 例: https://studyriver.jp（末尾スラッシュなし）
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# 投稿対象のMarkdownフォルダ
POST_DIR = "posts/news/main/"

# カテゴリとタグ（WordPress側で確認してIDを指定）
CATEGORY_ID = 627
TAG_IDS = [586]

# ランダムで使いまわす画像（WPのメディアID）
MEDIA_IDS = [
    1079, 1078, 1077
]

def get_auth():
    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(auth_str.encode()).decode()

def post_article(title, html, media_id):
    headers = {
        "Authorization": f"Basic {get_auth()}",
        "Content-Type": "application/json"
    }

    url = f"{WP_URL}/wp-json/wp/v2/posts"
    print("POST URL:", url)

    payload = {
        "title": title,
        "content": html,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS
    }

    res = requests.post(url, headers=headers, json=payload)

    print("DEBUG status:", res.status_code)
    print("DEBUG resp-len:", len(res.text))
    print("DEBUG first 200:", res.text[:200])

    if res.status_code not in (200, 201):
        print("❌ Post failed:", res.status_code, res.text)
        raise Exception("記事の投稿に失敗しました")

    post_id = res.json().get("id")
    print("✅ Posted:", res.status_code, res.json().get("link"))

    # --- 投稿成功後にアイキャッチ画像を付与 ---
    update_featured_image(post_id, media_id)

def update_featured_image(post_id, media_id):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    headers = {
        "Authorization": f"Basic {get_auth()}",
        "Content-Type": "application/json"
    }

    payload = {"featured_media": media_id}
    res = requests.post(url, headers=headers, json=payload)

    print("📷 アイキャッチ画像追加:", res.status_code)
    if res.status_code not in (200, 201):
        print("⚠️ アイキャッチ追加失敗:", res.text)

def main():
    files = glob.glob(f"{POST_DIR}/*.md")
    if not files:
        print("❌ No articles to post.")
        return

    # 最新の更新日時のファイルを取得
    latest = max(files, key=os.path.getmtime)
    
    with open(latest, "r", encoding="utf-8") as f:
        md = f.read()
    html = markdown.markdown(md)
    title = md.splitlines()[0].replace("#", "").strip()

    media_id = random.choice(MEDIA_IDS)
    post_article(title, html, media_id)

if __name__ == "__main__":
    main()
