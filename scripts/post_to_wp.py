# scripts/post_to_wp.py

import requests
import os
import glob
import base64
import markdown

WP_URL = os.getenv("WP_URL")  # https://studyriver.jp
WP_USER = os.getenv("WP_USER")  # 管理者ユーザー名
WP_APP_PASS = os.getenv("WP_APP_PASS")  # Application Password

POST_DIR = "posts/news/main/"
IMAGE_PATH = "tmp/thumbnail.png"

CATEGORY_ID = 627 
TAG_IDS = [586]  
def get_auth():
    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(auth_str.encode()).decode()

def upload_media(img_path):
    with open(img_path, "rb") as img:
        headers = {
            "Authorization": f"Basic {get_auth()}",
            "Content-Disposition": f"attachment; filename=thumbnail.png",
            "Content-Type": "image/png"
        }
        res = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers=headers, data=img.read())
        return res.json()["id"]

def post_article(title, html, media_id):
    headers = {
        "Authorization": f"Basic {get_auth()}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "content": html,
        "status": "publish",  # "draft" にすると下書き
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS,
        "featured_media": media_id
    }
    res = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", headers=headers, json=payload)
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
