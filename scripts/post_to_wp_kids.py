#!/usr/bin/env python3
"""
post_to_wp_kids.py
────────────────────────────────────────────────────────────
Kids シリーズの記事（Markdown）を WordPress に投稿するスクリプト
  * アイキャッチは MEDIA_IDS を重複させずローテート
  * カテゴリー / タグは --subtype で切り替え
"""

import argparse, base64, glob, json, os, random
from pathlib import Path

import markdown, requests

# ── WP 接続情報 ───────────────────────────────────────────
WP_URL   = os.getenv("WP_URL")      # 末尾スラッシュなし
WP_USER  = os.getenv("WP_USER")
WP_PASS  = os.getenv("WP_APP_PASS")

# ── Kids ディレクトリ ────────────────────────────────────
POST_DIR = "posts/news/kids"

# サブタイプ別のカテゴリーID & タグID （あとで WP ダッシュボードで確認して更新）
TAXONOMY = {
    "kids_main": {"cat": 633, "tags": [586, 1022]},
    "kids_mind": {"cat": 1185, "tags": [1187, 1191, 1193, 1022]},   
    "kids_jobs": {"cat": 1183, "tags": [1195, 1022]},   
}

# ── アイキャッチ候補 ────────────────────────────────────
MEDIA_IDS = [1643, 1642, 1641, 1640, 1140, 1077, 1078, 1104, 3242]
POOL_FILE = Path("tmp/media_pool_kids.json")

# ── Util：画像プール ────────────────────────────────────
def _load_pool(): return json.loads(POOL_FILE.read_text()) if POOL_FILE.exists() else []
def _save_pool(pool): POOL_FILE.parent.mkdir(exist_ok=True); POOL_FILE.write_text(json.dumps(pool))

def next_media_id():
    pool = _load_pool()
    if not pool:
        pool = MEDIA_IDS[:]; random.shuffle(pool)
    mid = pool.pop(); _save_pool(pool); return mid

# ── HTTP ヘルパ ───────────────────────────────────────────
AUTH_HDR = {
    "Authorization": "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode(),
    "Content-Type": "application/json",
}

def post_article(title, html, cat_id, tag_ids, media_id):
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {"title": title, "content": html, "status": "publish",
               "categories": [cat_id], "tags": tag_ids}
    res = requests.post(url, headers=AUTH_HDR, json=payload)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Post failed: {res.status_code}: {res.text}")
    post_id = res.json()["id"]; print("✅ Posted:", res.json()['link'])
    # アイキャッチ
    r = requests.post(f\"{WP_URL}/wp-json/wp/v2/posts/{post_id}\",
                      headers=AUTH_HDR, json={\"featured_media\": media_id})
    print(\"📷 アイキャッチ\", \"OK\" if r.ok else \"FAIL\", r.status_code)

# ── メイン ──────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(\"--subtype\", choices=TAXONOMY.keys(), default=\"kids_main\")
    args = ap.parse_args()

    md_files = glob.glob(f\"{POST_DIR}/*.md\")
    if not md_files: return print(\"❌ No articles to post\")

    latest = max(md_files, key=os.path.getmtime)
    md = Path(latest).read_text()
    title = md.splitlines()[0].lstrip('# ').strip()
    html  = markdown.markdown(md)

    tax    = TAXONOMY[args.subtype]
    media  = next_media_id()
    print(f\"🎲 subtype={args.subtype}, category={tax['cat']}, media={media}\")
    post_article(title, html, tax['cat'], tax['tags'], media)

if __name__ == \"__main__\": main()
