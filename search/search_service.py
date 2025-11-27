# search/search_service.py
import sqlite3
from typing import Any

SEARCH_SQL = """
SELECT
  url,
  title,
  snippet(pages, 2, '<mark>', '</mark>', ' … ', 12) AS snip,
  bm25(pages) AS rank
FROM pages
WHERE pages MATCH ?
ORDER BY rank
LIMIT ? OFFSET ?;
"""

COUNT_SQL = "SELECT count(*) FROM pages WHERE pages MATCH ?;"


def search(db_path: str, q: str | None, k: int = 10, page: int = 1) -> dict[str, Any]:
    """
    SQLite FTS5 検索 + ページネーション（総件数付き）
    return 例:
    {
      "query": "...",
      "total": 101,
      "page": 2,
      "per_page": 10,
      "last_page": 11,
      "hits": [{url,title,snip,rank}, ...]
    }
    """
    if not q:
        return {
            "query": "",
            "total": 0,
            "page": 1,
            "per_page": k,
            "last_page": 1,
            "hits": [],
        }

    page = max(int(page), 1)
    offset = (page - 1) * k

    con = sqlite3.connect(db_path)
    try:
        try:
            total = con.execute(COUNT_SQL, (q,)).fetchone()[0]
            rows = con.execute(SEARCH_SQL, (q, k, offset)).fetchall()
        except sqlite3.OperationalError:
            return {
                "query": q,
                "total": 0,
                "page": 1,
                "per_page": k,
                "last_page": 1,
                "hits": [],
            }

        hits = [{"url": u, "title": t, "snip": s, "rank": r} for (u, t, s, r) in rows]
        last_page = max((total + k - 1) // k, 1)
        return {
            "query": q,
            "total": total,
            "page": page,
            "per_page": k,
            "last_page": last_page,
            "hits": hits,
        }
    finally:
        con.close()
