import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
from app.cache import cache_get, cache_set
from app.utils.logger import logger


class SearXNGService:
    def __init__(self):
        self.base_url = settings.searxng_url
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
        }

    async def search(
        self,
        query: str,
        num_results: int = 5,
        categories: Optional[List[str]] = None,
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Search using SearXNG instance.
        Returns a list of search results with title, url, snippet, etc.
        """
        cache_key = f"search:{query}:{num_results}:{language}"
        cached = await cache_get(cache_key)
        if cached:
            logger.info(f"Cache hit for search query: {query}")
            return cached

        try:
            params = {
                "q": query,
                "format": "json",
                "language": language,
            }

            if categories:
                params["categories"] = ",".join(categories)

            # Retry logic for SearXNG requests
            max_retries = 5
            data = None
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(
                            f"{self.base_url}/search",
                            params=params,
                            headers=self.headers,
                        )
                        response.raise_for_status()
                        data = response.json()
                        break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 403 and attempt < max_retries - 1:
                        logger.warning(f"Got 403 from SearXNG, retrying (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                        continue
                    raise
                except httpx.ConnectError as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection error to SearXNG, retrying (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                        continue
                    raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Error from SearXNG: {e}, retrying (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                        continue
                    raise

            if data is None:
                raise Exception("Failed to get response from SearXNG after retries")

            results = []
            for item in data.get("results", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "snippet": item.get("content", ""),
                    "engine": item.get("engine", ""),
                    "category": item.get("category", ""),
                })

            await cache_set(cache_key, results, expire_seconds=3600)
            logger.info(f"Successfully retrieved {len(results)} results for query: {query}")
            return results

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during SearXNG search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during SearXNG search: {e}")
            raise

    async def extract_content(self, url: str) -> Optional[str]:
        """
        Extract main content from a URL using SearXNG's extract endpoint.
        """
        cache_key = f"extract:{url}"
        cached = await cache_get(cache_key)
        if cached:
            logger.info(f"Cache hit for URL extraction: {url}")
            return cached

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/extract",
                    params={"url": url},
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("content", "")

                await cache_set(cache_key, content, expire_seconds=86400)
                logger.info(f"Successfully extracted content from URL: {url}")
                return content

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during content extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during content extraction: {e}")
            return None


searxng_service = SearXNGService()
