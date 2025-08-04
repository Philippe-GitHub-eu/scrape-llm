# main.py

import asyncio
import json
import os
import pathlib
from io import BytesIO
from typing import Iterator, Optional, Tuple, List
from urllib.parse import urljoin

import httpx
from PIL import Image
from pydantic import BaseModel, ValidationError
from selectolax.parser import HTMLParser
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from extractors import readable_text, select_text
from llm import generate_json
from llm_vision import describe_images  # uses env LLM_VISION_MODEL; returns [None]*N if unset

load_dotenv()

"""
import random
UAS = [
    "scrape-llm/1.0 (+https://example.local)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
]
HEADERS = {"User-Agent": random.choice(UAS)}
"""

# Config

HEADERS = {"User-Agent": "scrape-llm/1.1 (+https://example.local)"}

DATA_DIR = pathlib.Path("data/images")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# Models

class ImageInfo(BaseModel):
    url: str
    alt: Optional[str] = None
    caption: Optional[str] = None
    local_path: Optional[str] = None  # for UI display

class Article(BaseModel):
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[str] = None
    images: List[ImageInfo] = []

SCHEMA_HINT = json.dumps(Article.model_json_schema())


# Networking helpers

@retry(stop=stop_after_attempt(3), wait=wait_exponential(0.5, 8))
async def fetch(client: httpx.AsyncClient, url: str) -> str:
    try:
        r = await client.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except httpx.RequestError as e:
        raise RuntimeError(f"connect_error: {e}") from e     # keeps error readable



def pick_candidate_images(html: str, base_url: str, limit: int = 3) -> Iterator[Tuple[str, Optional[str]]]:
    """
    Personal choice to preserve ressources:
    Yield a small set of candidate images (absolute URLs + optional alt),
    preferring og:image / twitter:image, then <img> tags.
    Hard-cap the number of candidates to keep resource use low.
    """
    tree = HTMLParser(html)
    seen: set[str] = set()
    yielded = 0

    # Prefer og/twitter image first
    for sel in ("meta[property='og:image']", "meta[name='twitter:image']"):
        n = tree.css_first(sel)
        if n:
            u = n.attributes.get("content")
            if u:
                u = urljoin(base_url, u)
                if u not in seen and not u.startswith("data:"):
                    seen.add(u)
                    yield (u, None)
                    yielded += 1
                    if yielded >= limit:
                        return

    # Then <img> tags (light sampling)
    for n in tree.css("img"):
        src = n.attributes.get("src") or n.attributes.get("data-src")
        if not src or src.startswith("data:"):
            continue
        u = urljoin(base_url, src)
        if u in seen:
            continue
        seen.add(u)
        alt = n.attributes.get("alt") or None
        yield (u, alt)
        yielded += 1
        if yielded >= limit:
            return

async def try_download_image(client: httpx.AsyncClient, url: str, max_bytes: int = 2_000_000) -> Tuple[Optional[str], int, int]:
    """
    Download a single image with byte cap. Convert to JPEG for predictable size.
    Returns (local_path, width, height) or (None, 0, 0) on failure/small images.
    """
    try:
        r = await client.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        content = r.content[:max_bytes]

        img = Image.open(BytesIO(content))
        if img.width < 256 or img.height < 256:
            return (None, 0, 0)

        fname = f"{abs(hash(url))}.jpg"
        local_path = str(DATA_DIR / fname)
        img.convert("RGB").save(local_path, format="JPEG", quality=80, optimize=True)
        return (local_path, img.width, img.height)
    except Exception:
        return (None, 0, 0)


# Core scraping per URL

async def scrape_one(url: str) -> Article:
    # Fetch HTML
    async with httpx.AsyncClient(http2=True) as client:
        html = await fetch(client, url)

    # Cheap rule-based extraction first
    title = (select_text(html, "meta[property='og:title']") or
             select_text(html, "title"))
    main_text = readable_text(html)

    # --- Images: pick a few and download (hard cap)
    candidates = list(pick_candidate_images(html, url, limit=3))
    picked: List[ImageInfo] = []
    if candidates:
        async with httpx.AsyncClient(http2=True) as img_client:
            for img_url, alt in candidates:
                local_path, w, h = await try_download_image(img_client, img_url)
                if local_path:
                    picked.append(ImageInfo(url=img_url, alt=alt, local_path=local_path))
                if len(picked) >= 3:  # absolute cap
                    break

    # Optional captions via local vision model (if LLM_VISION_MODEL env is set)
    if picked:
        hints = (title or "")[:80]
        caps = describe_images([im.local_path for im in picked if im.local_path], hint=hints)
        for im, cap in zip(picked, caps):
            im.caption = cap

    # Summarize images (tiny blurb for the text LLM)
    img_notes = []
    for im in picked:
        tag = im.caption or (im.alt or "")
        if tag:
            img_notes.append(f"- {tag}")
    img_blurb = "\n".join(img_notes[:3])

    # LLM prompt (strict, short)
    prompt = f"""
Extract this web page into JSON with fields: url, title, author, summary, published.
Prefer concise summary (≤ 3 sentences). Use ISO 8601 for dates if present.
If images info is provided, reflect any key facts briefly in the summary.

Input:
URL: {url}

TITLE (maybe empty):
{title}

IMAGE CAPTIONS (optional, up to 3):
{img_blurb}

MAIN TEXT:
{(main_text or '')[:6000]}
"""

    data = generate_json(
        prompt,
        schema_hint=SCHEMA_HINT,
        max_new_tokens=256,
        temperature=0.1,
    )

    # Attach images before validation
    data["images"] = [im.model_dump() for im in picked]

    try:
        return Article(**data)
    except ValidationError:
        # Safety net: return at least a minimal, valid object
        return Article(
            url=url,
            title=title or None,
            summary=None,
            author=None,
            published=None,
            images=picked,
        )


# Batch runner with controlled concurrency

async def main(urls: List[str]) -> List[Article]:
    sem = asyncio.Semaphore(5)  # keep concurrency sensible

    async def bound(u: str):
        async with sem:
            return await scrape_one(u)

    return await asyncio.gather(*[bound(u) for u in urls])


# CLI entry

if __name__ == "__main__":
    import sys
    urls = sys.argv[1:] or ["https://example.com/"]
    results = asyncio.run(main(urls))
    for a in results:
        print(a.model_dump_json())
