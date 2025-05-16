import requests
import os
import glob
import base64
import markdown

# 環境変数から取得
WP_URL = os.getenv("WP_URL")  # 例: https://studyriver.jp
WP_USER = os.getenv("WP_USER")  # 例: sasasasasasaki
WP_APP_PASS = os.getenv("WP_APP_PASS")  # アプリケーションパスワード

# 設定パス
POST_DIR = "posts/news/main/"
IMAGE_PATH = "tmp/thumbnail.webp"

# カテゴリ・タグ
CATEGORY_ID = 627
TAG_IDS = [586]

def get_auth():
    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(auth_str.encode()).decode()

def upload_media(img_path):
    with open(img_path, "rb") as img:
        headers = {
            "Authorization": f"Basic {get_auth()}",
            "Content-Disposition": "attachment; filename=thumbnail.webp",
            "Content-Type": "image/webp"
        }
        res = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers=headers, data=img.read())
        if res.status_code != 201:
            print("❌ Upload failed:", res.status_code, res.text)
            raise Exception("画像アップロードに失敗しました")
        return res.json()["id"]

def post_article(title, html, media_id):
    headers = {
        "Authorization": f"Basic {get_auth()}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": html,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS,
        "featured_media": media_id
    }
    res = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", headers=headers, json=payload)
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
    media_id = upload_media(IMAGE_PATH)
    post_article(title, html, media_id)

if __name__ == "__main__":
    main()
