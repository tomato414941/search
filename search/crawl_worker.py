# search/crawl_worker.py

from __future__ import annotations

import os
import time
from typing import List

import requests
from bs4 import BeautifulSoup

from search.db import open_db, upsert_page
from search.frontier_redis import dequeue_top, enqueue_batch, get_redis, normalize_url
from search.ingest import html_to_doc

UA = os.getenv(
    "CRAWL_USER_AGENT", "SearchBot/0.2 (+https://example.local/; minimal crawler)"
)
TIMEOUT = int(os.getenv("CRAWL_TIMEOUT_SEC", "10"))
OUTLINKS_PER_PAGE = int(os.getenv("CRAWL_OUTLINKS_PER_PAGE", "50"))


def extract_links(base_url: str, html: str, limit: int) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: List[str] = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if isinstance(href, list):
            href = href[0] if href else None
        u = normalize_url(base_url, href)
        if u:
            urls.append(u)
        if len(urls) >= limit:
            break
    return urls


def run_worker(db_path: str):
    r = get_redis()
    con = open_db(db_path)
    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    try:
        while True:
            item = dequeue_top(r)
            if not item:
                time.sleep(0.2)
                continue
            url, score = item

            try:
                resp = session.get(url, timeout=TIMEOUT)
            except requests.RequestException:
                # 失敗したURLはとりあえずスコアを下げて再キュー（簡易バックオフ）
                r.zadd("crawl:queue", {url: max(score - 5.0, -100.0)})
                continue

            ct = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and (
                "text/html" in ct or ct.startswith("text/")
            ):
                title, content = html_to_doc(resp.text)
                if content:
                    upsert_page(con, url, title, content)
                    con.commit()

                discovered = extract_links(url, resp.text, OUTLINKS_PER_PAGE)
                if discovered:
                    enqueue_batch(r, discovered, base_score=100.0)
            else:
                # HTML以外・エラー等は軽く減点して再投入（将来は delay へ）
                if resp.status_code in (429,) or resp.status_code >= 500:
                    r.zadd("crawl:queue", {url: max(score - 1.0, -100.0)})
                # 4xxは何もしない（墓にしないが、seenに残るので基本再訪しない）
            # ループ継続
    finally:
        con.close()
