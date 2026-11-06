import httpx
from typing import List
from app.cache import cache_get, cache_set
from app.utils.logger import logger


class GoogleSuggestionsService:
    """
    Fetches Google autocomplete suggestions (free, no API key).
    Used to ground keyword research in real search behavior.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.url = "https://suggestqueries.google.com/complete/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def get_suggestions(self, query: str, max_results: int = 10) -> List[str]:
        """Return autocomplete suggestions for a query."""
        if not query:
            return []

        cache_key = f"gsuggest:{query}:{max_results}"
        cached = await cache_get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(
                    self.url,
                    params={"client": "firefox", "q": query, "hl": "en"},
                )
                response.raise_for_status()
                data = response.json()

            suggestions = [s for s in (data[1] if isinstance(data, list) and len(data) > 1 else []) if s]
            suggestions = suggestions[:max_results]

            await cache_set(cache_key, suggestions, expire_seconds=86400)
            logger.info(f"Got {len(suggestions)} Google suggestions for: {query}")
            return suggestions

        except Exception as e:
            logger.warning(f"Failed to get Google suggestions for '{query}': {e}")
            return []

    async def get_suggestions_for_queries(self, queries: List[str], max_results: int = 10) -> List[str]:
        """Get suggestions for multiple seed queries, deduplicated."""
        import asyncio

        results = await asyncio.gather(*[self.get_suggestions(q, max_results=max_results) for q in queries])
        seen = set()
        merged = []
        for group in results:
            for s in group:
                key = s.lower()
                if key not in seen:
                    seen.add(key)
                    merged.append(s)
        return merged


google_suggestions_service = GoogleSuggestionsService()
