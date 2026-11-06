import asyncio
import httpx
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.cache import cache_get, cache_set
from app.utils.logger import logger

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None


class ContentFetcher:
    """
    Fetches and extracts readable text from URLs using trafilatura,
    with a BeautifulSoup fallback. Results are cached in Redis.
    """

    def __init__(self, timeout: float = 20.0, max_chars: int = 20000):
        self.timeout = timeout
        self.max_chars = max_chars
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def fetch_url(self, url: str, max_chars: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a URL and extract its main text content.
        Returns {"url", "title", "text"} or None on failure.
        """
        if not url:
            return None

        limit = max_chars or self.max_chars
        cache_key = f"fetch:{url}:{limit}"
        cached = await cache_get(cache_key)
        if cached:
            logger.info(f"Cache hit for URL fetch: {url}")
            return cached

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self.headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
        except Exception as e:
            logger.warning(f"Failed to fetch URL {url}: {e}")
            return None

        title = ""
        text = ""

        if trafilatura is not None:
            try:
                text = trafilatura.extract(
                    html,
                    favor_recall=True,
                    include_comments=False,
                    include_tables=True,
                ) or ""
                metadata = trafilatura.extract_metadata(html)
                if metadata is not None:
                    title = getattr(metadata, "title", "") or ""
            except Exception as e:
                logger.warning(f"trafilatura extraction failed for {url}: {e}")

        if not text:
            try:
                soup = BeautifulSoup(html, "html.parser")
                if soup.title and soup.title.string:
                    title = title or soup.title.string.strip()
                for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
            except Exception as e:
                logger.warning(f"BeautifulSoup fallback failed for {url}: {e}")
                return None

        if not text:
            return None

        if len(text) > limit:
            text = text[:limit]

        result = {"url": url, "title": title, "text": text}
        await cache_set(cache_key, result, expire_seconds=86400)
        logger.info(f"Fetched {len(text)} chars from {url}")
        return result

    async def fetch_urls(self, urls: List[str], max_chars: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently, skipping failures."""
        results = await asyncio.gather(*[self.fetch_url(u, max_chars=max_chars) for u in urls])
        return [r for r in results if r]


content_fetcher = ContentFetcher()
