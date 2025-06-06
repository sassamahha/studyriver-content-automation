#!/usr/bin/env python3
"""
Markdown → HTML 変換して WordPress へ投稿
アイキャッチは MEDIA_IDS を 1 周使い切るまで重複させない。
"""

import base64
import glob
import json
import os
import random
import requests
from pathlib import Path

import markdown

# ──────────────────────────
# WP 接続情報（GitHub Secrets / .env）
# ──────────────────────────
WP_URL      = os.getenv("WP_URL")          # 例: https://studyriver.jp（末尾スラッシュなし）
WP_USER     = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")

# ──────────────────────────
# 投稿対象フォルダ & タクソノミ ID
# ──────────────────────────
POST_DIR     = "posts/news/main"
CATEGORY_ID  = 627
TAG_IDS      = [586]

# ──────────────────────────
# 使い回すメディア ID 一覧
# ──────────────────────────
MEDIA_IDS = [
    1079, 1105, 1106, 1107, 1108,
    1112, 1113, 1132, 1133, 1134, 1135, 1136, 1137,
    1138, 1139, 1145, 1146, 1147, 1148, 1149,
    1150, 1151, 1152, 1153, 1154,
]

# ──────────────────────────
# アイキャッチ重複防止用プール
# ──────────────────────────
POOL_FILE = Path("tmp/media_pool.json")


def _load_pool() -> list[int]:
    if POOL_FILE.exists():
        return json.loads(POOL_FILE.read_text())
    return []


def _save_pool(pool: list[int]) -> None:
    POOL_FILE.parent.mkdir(exist_ok=True)
    POOL_FILE.write_text(json.dumps(pool))


def next_media_id() -> int:
    """MEDIA_IDS を 1 周使い切るまで同じ ID を出さない"""
    pool = _load_pool()

    if not pool:  # 使い切ったら新しくシャッフルしてリセット
        pool = MEDIA_IDS[:]
        random.shuffle(pool)

    media_id = pool.pop()  # 末尾から 1 つ取り出す
    _save_pool(pool)
    return media_id


# ──────────────────────────
# WordPress 連携ヘルパ
# ──────────────────────────
def _basic_auth() -> str:
    token = f"{WP_USER}:{WP_APP_PASS}"
    return base64.b64encode(token.encode()).decode()


HEADERS = {
    "Authorization": f"Basic {_basic_auth()}",
    "Content-Type": "application/json",
}


def post_article(title: str, html: str, media_id: int) -> None:
    """記事を公開してアイキャッチを付与"""
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": title,
        "content": html,
        "status": "publish",
        "categories": [CATEGORY_ID],
        "tags": TAG_IDS,
    }

    res = requests.post(url, headers=HEADERS, json=payload)
    print("DEBUG status:", res.status_code)
    print("DEBUG first 200:", res.text[:200])

    if res.status_code not in (200, 201):
        raise RuntimeError(f"❌ Post failed: {res.status_code}: {res.text}")

    post_id = res.json().get("id")
    print("✅ Posted:", res.json().get("link"))
    _update_featured_image(post_id, media_id)


def _update_featured_image(post_id: int, media_id: int) -> None:
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    payload = {"featured_media": media_id}
    res = requests.post(url, headers=HEADERS, json=payload)
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

    latest = max(files, key=os.path.getmtime)          # 最終更新の 1 本だけ
    md_text = Path(latest).read_text(encoding="utf-8")
    title = md_text.splitlines()[0].lstrip("#").strip()
    html = markdown.markdown(md_text)

    media_id = next_media_id()
    print("🎲 Selected featured_media ID:", media_id)
    post_article(title, html, media_id)


if __name__ == "__main__":
    main()
