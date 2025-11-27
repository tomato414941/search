# search/db.py
import sqlite3

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(
  url UNINDEXED,
  title,
  content,
  tokenize='porter'
);
"""


def open_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA_SQL)
    return con


def ensure_db(path: str) -> None:
    con = open_db(path)
    con.close()


def upsert_page(con: sqlite3.Connection, url: str, title: str, content: str) -> None:
    # 単純化のため、同一URLを削除→挿入
    con.execute("DELETE FROM pages WHERE url = ?", (url,))
    con.execute(
        "INSERT INTO pages(url,title,content) VALUES(?,?,?)", (url, title, content)
    )
