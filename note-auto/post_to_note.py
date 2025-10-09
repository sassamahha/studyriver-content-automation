import os, json, time, tempfile, re, hashlib, glob, subprocess, random
from pathlib import Path
from html import unescape

import yaml, requests
from bs4 import BeautifulSoup
from markdownify import markdownify as html2md
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ====== 基本設定（CWD非依存）======
BASE = Path(__file__).parent.resolve()
POSTED = BASE / "posted.json"

def load_cfg():
    with open(BASE / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_posted_map():
    if POSTED.exists():
        return json.loads(POSTED.read_text(encoding="utf-8"))
    return {}  # { "absolute/or/resolved/path/to/post.md": "sha1" }

def save_posted_map(d):
    POSTED.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# ====== MDユーティリティ ======
def split_frontmatter(md_text: str):
    """先頭の --- ... --- を frontmatter と本文に分離"""
    if md_text.startswith('---'):
        parts = md_text.split('\n', 1)[1].split('\n---', 1)
        if len(parts) == 2:
            fm = yaml.safe_load(parts[0]) or {}
            body = parts[1]
            if body.startswith('\n'):
                body = body[1:]
            return fm, body
    return {}, md_text

def md_body_from_file(path: Path):
    raw = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(raw)
    title = fm.get("title") or path.stem
    # frontmatter に "slug","tags","lang","date","canonical" 等があれば後で利用
    return title, body, fm

def sha1_of_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

# ====== note ログイン/投稿 ======
def login(page, email, password):
    """
    /login に行ってメール/パスを入れてログイン完了まで。
    placeholder 固定に依存しない“頑丈版”。
    """
    page.goto("https://note.com/login", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_load_state("domcontentloaded")

    # Cookie 同意など出ていれば潰す
    for label in ["同意", "同意する", "OK", "Accept", "許可", "わかった"]:
        try:
            page.get_by_role("button", name=re.compile(label)).click(timeout=800)
        except Exception:
            pass

    # 中継ボタンがあるパターンにも対応
    for label in ["メールアドレスでログイン", "メールでログイン"]:
        try:
            page.get_by_role("button", name=re.compile(label)).click(timeout=1000)
            break
        except Exception:
            pass

    # フォーム入力欄を“柔らかい”セレクタで拾う
    email_sel = "input[type='email'], input[name='email'], input[autocomplete='username'], input[placeholder*='メール'], input[placeholder*='note ID']"
    pass_sel  = "input[type='password'], input[name='password'], input[autocomplete='current-password'], input[placeholder*='パスワード']"

    try:
        page.wait_for_selector(email_sel, timeout=12000)
        page.locator(email_sel).first.fill(email)
        page.locator(pass_sel).first.fill(password)
    except Exception:
        # 最悪 form から強引に
        form = page.locator("form").first
        form.locator("input").nth(0).fill(email)
        form.locator("input[type='password']").first.fill(password)

    # 送信（ナビが起きるなら待つ。起きなくても続行）
    navigated = False
    try:
        with page.expect_navigation(wait_until="load", timeout=8000):
            page.get_by_role("button", name=re.compile("ログイン|Sign in")).click(timeout=1500)
        navigated = True
    except Exception:
        try:
            with page.expect_navigation(wait_until="load", timeout=8000):
                page.keyboard.press("Enter")
            navigated = True
        except Exception:
            pass

    # ネットワーク静止まで待機してから成功判定
    page.wait_for_load_state("networkidle")

    success_selectors = [
        "a[href*='/home']",
        "a[href*='/notifications']",
        "a[href^='/me']",
        "a[href*='/new']",
        "img[alt*='アイコン'], img[alt*='プロフィール']",
    ]
    ok = False
    for _ in range(24):  # 最大 ~12秒
        try:
            if "/home" in page.url or page.url.rstrip("/") == "https://note.com":
                ok = True
                break
            if any(page.locator(sel).count() > 0 for sel in success_selectors):
                ok = True
                break
        except Exception:
            pass
        page.wait_for_timeout(500)

    if not ok:
        raise RuntimeError(f"Login might have failed. current url={page.url}, navigated={navigated}")

def open_new_editor(page):
    """
    プロフ→投稿と同等。/new を経由して /notes/<id>/edit へ。
    """
    page.goto("https://editor.note.com/new/", timeout=60000)
    page.wait_for_url("**/edit/**", timeout=60000)
    # エディタ準備（タイトル/本文エリアのどちらかを待つ）
    ok = False
    for _ in range(20):
        if page.locator("textarea[placeholder='記事タイトル'], [placeholder='記事タイトル']").count() > 0:
            ok = True; break
        if page.locator('[contenteditable="true"]').count() > 0:
            ok = True; break
        page.wait_for_timeout(300)
    if not ok:
        raise RuntimeError("エディタが開けませんでした（タイトル/本文エリア検出失敗）")

# ====== クリップボード貼り付け ======
def paste_markdown(page, text: str):
    """
    クリップボードに text を入れて Ctrl+V で貼り付け。
    note 側が Markdown を解釈して見出し/リスト等を整形してくれる。
    """
    page.evaluate("async (t) => await navigator.clipboard.writeText(t)", text)
    page.keyboard.press("Control+V")

# ====== Git の最終コミット時間（Last commit date） ======
def git_last_commit_ts(repo_root: Path, file_path: Path) -> int:
    """
    file_path を最後に更新した Git コミットの UNIX 時刻(%ct) を取得。
    失敗したらファイルの mtime にフォールバック。
    """
    try:
        rel = str(file_path.relative_to(repo_root))
    except ValueError:
        rel = str(file_path)

    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", rel],
            cwd=str(repo_root),
        ).decode("utf-8").strip()
        return int(out)
    except Exception:
        return int(file_path.stat().st_mtime)

# ====== カバー画像（サムネイル）任意アップロード ======
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

def _resolve_repo_path(path_like: str) -> Path:
    """
    config の相対パスを リポジトリルート基準に解決。
    note-auto/ から見て1つ上がリポジトリルートという前提。
    """
    p = Path(path_like)
    if p.is_absolute():
        return p
    repo_root = (BASE / "..").resolve()
    return (repo_root / p).resolve()

def _pick_random_image(images_dir: Path) -> Path | None:
    if not images_dir.exists():
        return None
    files = [p for p in images_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXTS]
    if not files:
        return None
    return random.choice(files)

def _set_cover_image_any(page, img_path: Path) -> bool:
    """
    現在のページ（公開画面 or エディタのバナー）でカバー画像のアップロードポイントを探し、
    file chooser で img_path をセット。成功したら True。
    """
    button_patterns = [
        r"見出し画像", r"カバー画像", r"サムネイル", r"画像を選択", r"アップロード", r"ファイルを選択",
    ]
    for pat in button_patterns:
        try:
            with page.expect_event("filechooser", timeout=1200) as fc:
                page.get_by_role("button", name=re.compile(pat)).first.click()
            chooser = fc.value
            chooser.set_files(str(img_path))
            page.wait_for_timeout(800)
            return True
        except Exception:
            pass

    banner_patterns = [
        r"見出し画像を設定してみませんか", r"見出し画像", r"カバー画像", r"サムネイル",
    ]
    for pat in banner_patterns:
        try:
            with page.expect_event("filechooser", timeout=1000) as fc:
                page.get_by_text(re.compile(pat)).first.click()
            chooser = fc.value
            chooser.set_files(str(img_path))
            page.wait_for_timeout(800)
            return True
        except Exception:
            pass

    return False

# ==== 差し替え：publish_flow（後方互換：cover_pathは任意・未使用でもOK） ====
def publish_flow(page, cover_path=None, *args, **kwargs):
    """
    右上の『公開に進む』→ publish 画面 → 『投稿する』まで。
    cover_path は与えられても与えられなくても動作する（後方互換）。
    """
    # 1) 公開に進む
    page.get_by_role("button", name=re.compile("公開に進む|公開へ進む")).click(timeout=12000)
    page.wait_for_url("**/publish/**", timeout=90000)
    page.wait_for_load_state("domcontentloaded")

    # 2) （任意）カバー画像アップロード
    if cover_path:
        try:
            _set_cover_image_any(page, Path(cover_path))
        except Exception:
            pass  # オプションなので握りつぶす

    # 3) 『投稿する』が有効化されるまで待つ
    post_btn = page.get_by_role("button", name=re.compile("^投稿する$"))
    for _ in range(90):
        try:
            if post_btn.is_enabled():
                break
        except Exception:
            pass
        page.wait_for_timeout(1000)

    # 4) 投稿実行
    try:
        with page.expect_navigation(wait_until="load", timeout=120000):
            post_btn.click(timeout=5000)
    except Exception:
        post_btn.click()
        page.wait_for_load_state("networkidle")

    # 5) 下書きだったらワンリトライ
    try:
        is_draft = page.locator("text=これは公開前の下書きです").count() > 0
    except Exception:
        is_draft = False
    if is_draft:
        page.get_by_role("button", name=re.compile("公開に進む|公開へ進む")).click(timeout=12000)
        page.wait_for_url("**/publish/**", timeout=90000)
        page.wait_for_load_state("domcontentloaded")
        post_btn = page.get_by_role("button", name=re.compile("^投稿する$"))
        for _ in range(60):
            try:
                if post_btn.is_enabled():
                    break
            except Exception:
                pass
            page.wait_for_timeout(1000)
        try:
            with page.expect_navigation(wait_until="load", timeout=120000):
                post_btn.click(timeout=5000)
        except Exception:
            post_btn.click()
            page.wait_for_load_state("networkidle")

    page.wait_for_load_state("networkidle")



# --- 投稿 -----------------
def create_post(page, author_id, title, body_md, footer_md=None, canonical_link=None, tags=None):
    open_new_editor(page)

    # タイトルはタイプ
    try:
        title_box = page.locator("textarea[placeholder='記事タイトル'], [placeholder='記事タイトル']").first
        title_box.click()
    except Exception:
        pass
    page.keyboard.type(title)

    # 本文は“貼り付け”で一括投入（Markdown解釈をnoteに任せる）
    editor = page.locator('[contenteditable="true"]').first
    editor.click()
    paste_markdown(page, (body_md or "").strip())

    # カバー画像の選択（config に upload_cover/cover_images_dir がある場合のみ）
    cover_path = None
    try:
        cfg = load_cfg()
        want_cover = cfg.get("note", {}).get("upload_cover")
        cover_dir = cfg.get("note", {}).get("cover_images_dir")
        if want_cover and cover_dir:
            resolved = _resolve_repo_path(cover_dir)
            img = _pick_random_image(resolved)
            if img:
                cover_path = img
    except Exception:
        pass  # 任意機能なので握りつぶす

    # 公開（カバー画像パスを渡す）
    publish_flow(page, cover_path=cover_path)

# ====== メイン ======
def run_once():
    cfg = load_cfg()
    posted_map = load_posted_map()
    email = os.environ["NOTE_EMAIL"]
    password = os.environ["NOTE_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # クリップボード権限を付与
        ctx = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()
        login(page, email, password)

        changed = False

        for src in cfg.get("sources", []):
            repo_dir = Path(src["repo_dir"]).resolve()
            pattern = src.get("glob", "**/*.md")
            max_per_run = int(src.get("max_per_run", 1))

            # ▼ Git の「Last commit date」降順で並べ替える（最新優先）
            candidates = list(repo_dir.glob(pattern))
            files = sorted(
                candidates,
                key=lambda f: git_last_commit_ts(repo_dir, f),
                reverse=True,
            )

            pushed = 0
            for f in files:
                rel = str(f.resolve())
                md_title, md_body, fm = md_body_from_file(f)
                link = fm.get("canonical") or fm.get("link") or fm.get("url") or ""
                curr_sha = sha1_of_text(md_body)

                prev_sha = posted_map.get(rel)
                if prev_sha == curr_sha:
                    continue  # 変更なしはスキップ

                create_post(
                    page=page,
                    author_id=cfg["note"]["author_id"],
                    title=md_title,
                    body_md=md_body,
                    footer_md=None,
                    canonical_link=link,
                    tags=fm.get("tags", []),
                )

                posted_map[rel] = curr_sha
                changed = True
                pushed += 1
                if pushed >= max_per_run:
                    break

        if changed:
            save_posted_map(posted_map)

        ctx.close(); browser.close()

if __name__ == "__main__":
    run_once()
