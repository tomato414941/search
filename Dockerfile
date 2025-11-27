FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080 HOST=0.0.0.0 SEARCH_DB=/data/search.db FLASK_DEBUG=0 \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["gunicorn","-b","0.0.0.0:8080","--workers","1","--threads","8","app:app"]
