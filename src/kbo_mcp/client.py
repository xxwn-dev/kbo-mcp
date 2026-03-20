import httpx
from contextlib import asynccontextmanager

BASE_URL = "https://www.koreabaseball.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.koreabaseball.com/",
}


@asynccontextmanager
async def get_http_client():
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers=HEADERS,
        timeout=15.0,
        follow_redirects=True,
    ) as client:
        yield client
