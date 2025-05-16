# scripts/post_to_wp.py

import requests
import os
import glob
import base64
import markdown
import mimetypes

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

POST_DIR = "posts/news/main/"
IMAGE_PATH = "tmp/thumbnail.png"

CATEGORY_ID = 627
TAG_IDS = [586]

def get_auth():
    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(auth_str.encode()).decode()

def upload_media(img_path):
    if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
        raise Exception("❌ 画像ファイルが存在しないか空です")

    mime_type, _ = mimetypes.guess_type(img_path)
    if mime_type is None:
        mime_type = "image/png"  # fallback

    with open(img_path, "rb") as img:
        headers = {
            "Authorization": f"Basic {get_auth()}",
            "Content-Disposition": f"attachment; filename={os.path.basename(img_path)}",
            "Content-Type": mime_type
        }
        res = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers=headers, data=img.read())

        if res.status_code != 201:
            print("❌ Media upload failed")
            print("Status:", res.status_code)
            print("Response:", res.text)
            raise Exception("画像アップロードに失敗しました")

        print("✅ Media uploaded:", res.json().get("source_url"))
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

    if res.status_code != 201:
        print("❌ Article post failed")
        print("Status:", res.status_code)
        print("Response:", res.text)
        raise Exception("記事の投稿に失敗しました")

    print("✅ Article posted:", res.json().get("link"))

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
