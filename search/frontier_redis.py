# search/frontier_redis.py

import os
from typing import Iterable, Optional, cast
from urllib.parse import parse_qsl, urldefrag, urlencode, urljoin, urlsplit, urlunsplit

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QKEY = os.getenv("CRAWL_QUEUE_KEY", "crawl:queue")  # ZSET
SKEY = os.getenv("CRAWL_SEEN_KEY", "crawl:seen")  # SET

TRACKING_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
}


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def normalize_url(base: str, link: str | None) -> Optional[str]:
    if not link:
        return None
    href = urljoin(base, link)
    href, _ = urldefrag(href)
    if not href.startswith(("http://", "https://")):
        return None
    # lower scheme/host & strip common tracking params
    parts = urlsplit(href)
    host = (parts.hostname or "").lower()
    port = f":{parts.port}" if parts.port else ""
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k not in TRACKING_KEYS
        ]
    )
    return urlunsplit((parts.scheme.lower(), host + port, parts.path, query, ""))


def enqueue_if_new(r: redis.Redis, url: str, score: float) -> bool:
    # 新規URLなら queue に追加（優先度付き）
    added = r.sadd(SKEY, url)
    if added == 1:
        r.zadd(QKEY, {url: float(score)})
        return True
    return False


def enqueue_batch(
    r: redis.Redis, urls: Iterable[str], base_score: float = 100.0
) -> int:
    n = 0
    pipe = r.pipeline()
    for u in urls:
        pipe.sadd(SKEY, u)
    results = pipe.execute()
    # 追加された分だけ zadd（二段に分けてRTT削減）
    to_add = [u for u, added in zip(urls, results) if added == 1]
    if to_add:
        pipe = r.pipeline()
        for u in to_add:
            pipe.zadd(QKEY, {u: base_score})
        pipe.execute()
        n = len(to_add)
    return n


def dequeue_top(r: redis.Redis) -> Optional[tuple[str, float]]:
    res = cast(list[tuple[str, float]], r.zpopmax(QKEY, 1))
    if not res:
        return None
    url, score = res[0]
    return url, float(score)
