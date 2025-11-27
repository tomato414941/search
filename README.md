# search

Redis + SQLite FTS5 で動く、シンプルな自作検索エンジンです。
クローラでページを集めて、Web UI から全文検索できます。

## 必要なもの

- Docker
- Docker Compose

## セットアップ

プロジェクトルートに `.env` を作ります（例）:

```env
HOST=0.0.0.0
PORT=8080
SEARCH_DB=/data/search.db
FLASK_DEBUG=0

REDIS_URL=redis://redis:6379/0
CRAWL_WORKERS=3
CRAWL_OUTLINKS_PER_PAGE=50

CRAWL_SEEDS="https://ja.wikipedia.org/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8"
```

## 起動

```bash
docker compose up --build
```

ブラウザで `http://localhost/` を開くと検索画面が表示されます。
クローラと Redis も同時に起動し、指定したシード URL から自動でクロールが始まります。
