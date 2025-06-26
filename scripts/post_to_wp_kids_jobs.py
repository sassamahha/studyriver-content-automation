
#!/usr/bin/env python3
"""
Kids jobs 記事を WordPress へ投稿
- posts/news/kids-jobs/ 直下の最新 Markdown 1 本を投稿
- アイキャッチは MEDIA_IDS をローテーション
"""

import base64
import glob
import json
import os
import random
from pathlib import Path

import markdown
import requests


# ──────────────────────────
# WordPress 接続情報（GitHub Secrets / .env）
# ──────────────────────────
WP_URL      = os.getenv("WP_URL")          # 例: https://studyriver.jp（末尾スラッシュなし）
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# ──────────────────────────
# Kids 用ディレクトリ & タクソノミ
# ──────────────────────────
POST_DIR    = "posts/news/kids_jobs"
CATEGORY_ID = 1183
TAG_IDS     = [1195, 1022]

# ──────────────────────────
# アイキャッチ候補（事前アップしたメディア ID）
# ──────────────────────────
MEDIA_IDS = [
    1643, 1642, 1641, 1640, 1140, 1077, 1078, 1104
]

# Kids 用プールは大人版と分離
POOL_FILE = Path("tmp/media_pool_kids_jobs.json")


# ──────────────────────────
# 画像プールユーティリティ
# ──────────────────────────
def _load_pool() -> list[int]:
    if POOL_FILE.exists():
        return json.loads(POOL_FILE.read_text())
    return []


def _save_pool(pool: list[int]) -> None:
    POOL_FILE.parent.mkdir(exist_ok=True)
    POOL_FILE.write_text(json.dumps(pool))


def next_media_id() -> int:
    """MEDIA_IDS を 1 周使い切るまで同じ ID を選ばない"""
    pool = _load_pool()
    if not pool:                       # 使い切ったらシャッフルして再生成
        pool = MEDIA_IDS[:]
        random.shuffle(pool)

    media_id = pool.pop()
    _save_pool(pool)
    return media_id


# ──────────────────────────
# WordPress ヘルパ
# ──────────────────────────
def _basic_auth() -> str:
    token = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(token.encode()).decode()


HEADERS = {
    "Authorization": f"Basic {_basic_auth()}",
    "Content-Type": "application/json",
}


def post_article(title: str, html: str, media_id: int) -> None:
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": title,
        "content": html,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS,
    }

    res = requests.post(url, headers=HEADERS, json=payload)
    print("DEBUG status:", res.status_code, "len", len(res.text))

    if res.status_code not in (200, 201):
        raise RuntimeError(f"❌ Post failed: {res.status_code}: {res.text}")

    post_id = res.json()["id"]
    print("✅ Posted:", res.json()["link"])
    _update_featured_image(post_id, media_id)


def _update_featured_image(post_id: int, media_id: int) -> None:
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    res = requests.post(
        url,
        headers=HEADERS,
        json={"featured_media": media_id},
    )
    msg = "📷 アイキャッチ追加" if res.ok else "⚠️ アイキャッチ追加失敗"
    print(msg, res.status_code)


# ──────────────────────────
# メイン処理
# ──────────────────────────
def main() -> None:
    files = glob.glob(f"{POST_DIR}/*.md")
    if not files:
        print("❌ No articles to post.")
        return

    latest = max(files, key=os.path.getmtime)          # 最終更新 1 本
    md_text = Path(latest).read_text(encoding="utf-8")

    title = md_text.splitlines()[0].lstrip("#").strip()
    html  = markdown.markdown(md_text)

    media_id = next_media_id()
    print("🎲 Selected featured_media ID:", media_id)
    post_article(title, html, media_id)


if __name__ == "__main__":
    main()
