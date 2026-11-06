import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger


class FactCheckService:
    """
    Google Fact Check Tools API - searches claims verified by fact-checking
    organizations (Snopes, PolitiFact, FactCheck.org, etc.).

    Requires a Google Cloud API key with the Fact Check Tools API enabled.
    Get one at https://console.cloud.google.com/apis/credentials
    """

    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(settings.google_api_key)

    async def search_claims(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search fact-checked claims matching a query string.
        Returns a list of {claim, rating, publisher, url, review_date}.
        Returns [] when no API key is configured or on failure.
        """
        if not self.enabled or not query:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "query": query,
                        "languageCode": "en",
                        "pageSize": max_results,
                        "key": settings.google_api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for claim in data.get("claims", []):
                reviews = claim.get("claimReview", [])
                if not reviews:
                    continue
                review = reviews[0]
                publisher = review.get("publisher", {})
                results.append({
                    "claim": claim.get("text", ""),
                    "rating": review.get("textualScore", ""),
                    "publisher": publisher.get("name", ""),
                    "url": review.get("url", ""),
                    "review_date": review.get("reviewDate", ""),
                })

            logger.info(f"Fact Check API: {len(results)} results for '{query[:60]}'")
            return results

        except Exception as e:
            logger.warning(f"Fact Check API search failed for '{query[:60]}': {e}")
            return []

    async def search_claims_batch(self, queries: List[str], max_results: int = 2) -> List[Dict[str, Any]]:
        """Search multiple claims concurrently, deduplicated by review URL."""
        import asyncio

        results_groups = await asyncio.gather(
            *[self.search_claims(q, max_results=max_results) for q in queries]
        )
        seen = set()
        merged = []
        for group in results_groups:
            for r in group:
                key = r.get("url") or r.get("claim", "").lower()
                if key not in seen:
                    seen.add(key)
                    merged.append(r)
        return merged


fact_check_service = FactCheckService()
