# search/ingest.py
import re

from bs4 import BeautifulSoup


def html_to_doc(html: str) -> tuple[str, str]:
    """
    HTMLから (title, text) を抽出。最小実装：script/style等を除去し、テキストを空白で連結。
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # ざっくりノイズ除去を足したい場合は以下を有効化：
    # for tag in soup.select("nav, footer, aside"):
    #     tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return title, text
