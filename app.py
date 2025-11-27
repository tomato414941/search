# app.py
import os

from flask import Flask, jsonify, render_template, request

from search.search_service import search as run_search

# ==============================================================
# 設定
# ==============================================================

DB_PATH = os.getenv(
    "SEARCH_DB", os.path.join(os.path.dirname(__file__), "data", "search.db")
)
RESULTS_LIMIT = int(os.getenv("RESULTS_LIMIT", "10"))

# 上限値（環境変数で上書き可）
MAX_QUERY_LEN = int(os.getenv("MAX_QUERY_LEN", "512"))
MAX_PER_PAGE = int(os.getenv("MAX_PER_PAGE", "50"))
MAX_PAGE = int(os.getenv("MAX_PAGE", "1000"))

# ==============================================================
# Flaskアプリケーション
# ==============================================================

app = Flask(__name__, template_folder="templates")
app.config["JSON_AS_ASCII"] = False

# --- DB 初期化（Gunicornでも必ず実行される位置） ---
from search.db import ensure_db  # noqa: E402

DB_DIR = os.path.dirname(DB_PATH)
os.makedirs(DB_DIR, exist_ok=True)
ensure_db(DB_PATH)

# ==============================================================
# ヘルパー
# ==============================================================


def _parse_pos_int(value: str | None, default: int, *, min_v: int = 1) -> int:
    """正の整数を安全にパースする"""
    try:
        x = int(value) if value is not None else default
    except ValueError:
        x = default
    return max(x, min_v)


# ==============================================================
# ルーティング
# ==============================================================


@app.get("/")
def search_page():
    """検索ページ"""

    query = (request.args.get("q") or "").strip() or None
    if query is not None and len(query) > MAX_QUERY_LEN:
        query = query[:MAX_QUERY_LEN]

    page_number = min(_parse_pos_int(request.args.get("page"), 1), MAX_PAGE)
    per_page = min(RESULTS_LIMIT, MAX_PER_PAGE)

    result = run_search(DB_PATH, query, per_page, page_number) if query else None
    return render_template(
        "search.html",
        q=query,
        result=result,
    )


@app.get("/api/search")
def api_search():
    """検索API（JSON）"""

    query = (request.args.get("q") or "").strip()
    if len(query) > MAX_QUERY_LEN:
        query = query[:MAX_QUERY_LEN]

    per_page = min(
        _parse_pos_int(request.args.get("limit"), RESULTS_LIMIT), MAX_PER_PAGE
    )
    page_number = min(_parse_pos_int(request.args.get("page"), 1), MAX_PAGE)

    data = (
        run_search(DB_PATH, query, per_page, page_number)
        if query
        else {
            "query": "",
            "total": 0,
            "page": 1,
            "per_page": per_page,
            "last_page": 1,
            "hits": [],
        }
    )
    return jsonify(data)


@app.get("/health")
def health():
    """ヘルスチェック用"""
    return jsonify({"ok": True})


# ==============================================================
# エントリーポイント（ローカル起動用）
# ==============================================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
