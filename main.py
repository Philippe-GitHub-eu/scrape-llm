import asyncio, json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from requests_cache import CachedSession

from extractors import readable_text, select_text
from llm import generate_json

load_dotenv()

cache = CachedSession("http_cache", expire_after=3600)

class Article(BaseModel):
    url: str
    title: str | None = None
    author: str | None = None
    summary: str | None = None
    published: str | None = None

SCHEMA_HINT = json.dumps(Article.model_json_schema())
HEADERS = {"User-Agent": "scrape-llm/1.0 (+https://example.local)"}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=8))
async def fetch(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

async def scrape_one(url: str) -> Article:
    async with httpx.AsyncClient(http2=True) as client:
        html = await fetch(client, url)

    title = (select_text(html, "meta[property='og:title']") 
             or select_text(html, "title"))
    main_text = readable_text(html)

    prompt = f"""
Extract this web page into JSON with fields: url, title, author, summary, published.
Prefer concise summary (≤ 3 sentences). Use ISO 8601 for dates if present.
Input:
URL: {url}

TITLE (maybe empty):
{title}

MAIN TEXT:
{main_text[:6000]}
"""
    data = generate_json(prompt, schema_hint=SCHEMA_HINT, max_new_tokens=256, temperature=0.1)
    try:
        return Article(**data)
    except ValidationError:
        return Article(url=url, title=title or None, summary=None, author=None, published=None)

async def main(urls: list[str]) -> list[Article]:
    sem = asyncio.Semaphore(5)
    async def bound(u: str):
        async with sem:
            return await scrape_one(u)
    return await asyncio.gather(*[bound(u) for u in urls])

if __name__ == "__main__":
    import sys
    urls = sys.argv[1:] or ["https://example.com/"]
    results = asyncio.run(main(urls))
    for a in results:
        print(a.model_dump_json())
