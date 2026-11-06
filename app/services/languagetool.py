import httpx
import hashlib
from typing import Dict, Any, List
from app.cache import cache_get, cache_set
from app.utils.logger import logger


class LanguageToolService:
    """
    LanguageTool public HTTP API - grammar, spelling and style checking.

    Free endpoint, no API key required. Limits: ~20 requests/min per IP,
    20KB text per request. Text is truncated to stay under the limit.
    Docs: https://dev.languagetool.org/public-http-api.html
    """

    CHECK_URL = "https://api.languagetool.org/v2/check"
    MAX_TEXT_CHARS = 19000  # stay under the 20KB per-request limit
    MAX_ISSUES_RETURNED = 25

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def check(self, text: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Check text for grammar/style issues.
        Returns {"issue_count", "issues": [{message, rule, offset, suggestions}]}.
        Returns an empty result on failure — never raises.
        """
        if not text or not text.strip():
            return {"issue_count": 0, "issues": []}

        text = text[: self.MAX_TEXT_CHARS]
        cache_key = f"languagetool:{language}:{hashlib.md5(text.encode()).hexdigest()}"
        cached = await cache_get(cache_key)
        if cached:
            logger.info("Cache hit for LanguageTool check")
            return cached

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.CHECK_URL,
                    data={"text": text, "language": language},
                )
                response.raise_for_status()
                data = response.json()

            matches = data.get("matches", [])
            issues: List[Dict[str, Any]] = []
            for m in matches[: self.MAX_ISSUES_RETURNED]:
                replacements = m.get("replacements", [])
                suggestions = [r.get("value", "") for r in replacements[:3] if r.get("value")]
                context = m.get("context", {})
                issues.append({
                    "message": m.get("message", ""),
                    "rule": m.get("rule", {}).get("id", ""),
                    "short_message": m.get("rule", {}).get("shortMessage", ""),
                    "offset": m.get("offset", 0),
                    "length": m.get("length", 0),
                    "context": context.get("text", ""),
                    "suggestions": suggestions,
                })

            result = {"issue_count": len(matches), "issues": issues}
            await cache_set(cache_key, result, expire_seconds=86400)
            logger.info(f"LanguageTool check completed: {len(matches)} issues found")
            return result

        except Exception as e:
            logger.warning(f"LanguageTool check failed: {e}")
            return {"issue_count": 0, "issues": [], "error": str(e)}


languagetool_service = LanguageToolService()
