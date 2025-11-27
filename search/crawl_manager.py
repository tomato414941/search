# search/crawl_manager.py

import os
import threading
import time

from search.crawl_worker import run_worker
from search.db import ensure_db
from search.frontier_redis import enqueue_if_new, get_redis

# ==============================================================
# 設定
# ==============================================================

DB_PATH = os.getenv("SEARCH_DB", "/data/search.db")
WORKERS = int(os.getenv("CRAWL_WORKERS", "3"))


# ==============================================================
# シード読み込み（.env）
# ==============================================================


def load_seeds_from_env() -> list[str]:
    """環境変数 CRAWL_SEEDS を空白区切りで読み込み"""
    return [s.strip() for s in os.getenv("CRAWL_SEEDS", "").split() if s.strip()]


# ==============================================================
# フロンティア初期化（シード投入）
# ==============================================================


def init_frontier(seeds: list[str], *, score: float = 100.0) -> int:
    """シードURLをRedisフロンティアに初期投入（既知はスキップ）"""
    r = get_redis()
    added = 0
    for url in seeds:
        if enqueue_if_new(r, url, score=score):
            added += 1
    return added


# ==============================================================
# メイン処理
# ==============================================================


def main():
    """Redisフロンティア + ワーカー起動マネージャ"""

    ensure_db(DB_PATH)

    # 初期シード投入
    seeds = load_seeds_from_env()
    seeded = init_frontier(seeds)
    print(f"[frontier] initialized: {seeded} url(s)")

    # ワーカー起動
    for i in range(WORKERS):
        t = threading.Thread(
            target=run_worker, args=(DB_PATH,), daemon=True, name=f"worker-{i + 1}"
        )
        t.start()
        print(f"[frontier] worker-{i + 1} started")

    # 簡易キープアライブ
    while True:
        time.sleep(60)


# ==============================================================
# エントリーポイント
# ==============================================================

if __name__ == "__main__":
    main()
