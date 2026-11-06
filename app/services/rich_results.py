import httpx
import json
from typing import Dict, Any, List, Optional
from app.config import settings
from app.utils.logger import logger


# Schema.org types relevant to blog articles and their required properties
REQUIRED_PROPERTIES = {
    "Article": ["headline"],
    "NewsArticle": ["headline"],
    "BlogPosting": ["headline"],
    "FAQPage": ["mainEntity"],
}

RECOMMENDED_PROPERTIES = {
    "Article": ["description", "author", "datePublished", "image"],
    "BlogPosting": ["description", "author", "datePublished", "image"],
    "FAQPage": [],
}


class RichResultsService:
    """
    Structured data (JSON-LD) generation and validation for SEO.

    Two modes:
    - build_article_jsonld(): deterministic Article schema from SEO output
    - validate_jsonld(): local schema.org sanity checks (no network needed)
    - test_url(): Google Rich Results Test API — only works on live URLs
      and requires GOOGLE_API_KEY with the Search Console API enabled.
    """

    RICH_RESULTS_URL = "https://searchconsole.googleapis.com/v1/urlTestingTools/richResultsTest:run"
    SCHEMA_ORG_VALIDATOR_URL = "https://validator.schema.org/validate"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def build_article_jsonld(
        self,
        title: str,
        description: str,
        keywords: List[str],
        content: str,
        author: str = "",
        image_url: str = "",
    ) -> Dict[str, Any]:
        """Build a schema.org Article JSON-LD document."""
        doc: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "keywords": ", ".join(keywords) if keywords else "",
            "wordCount": len(content.split()) if content else 0,
        }
        if author:
            doc["author"] = {"@type": "Organization", "name": author}
        if image_url:
            doc["image"] = image_url
        return doc

    def validate_jsonld(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a JSON-LD document against schema.org expectations.
        Deterministic, no network calls.
        Returns {"valid": bool, "errors": [...], "warnings": [...]}.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(doc, dict):
            return {"valid": False, "errors": ["JSON-LD must be an object"], "warnings": []}

        context = doc.get("@context")
        if context != "https://schema.org" and context != "http://schema.org":
            errors.append(f"Invalid or missing @context: {context!r}")

        schema_type = doc.get("@type")
        if not schema_type:
            errors.append("Missing @type")
        elif schema_type not in REQUIRED_PROPERTIES:
            warnings.append(f"Uncommon @type '{schema_type}' — rich results may not apply")

        for prop in REQUIRED_PROPERTIES.get(schema_type, []):
            if not doc.get(prop):
                errors.append(f"Missing required property '{prop}' for {schema_type}")

        for prop in RECOMMENDED_PROPERTIES.get(schema_type, []):
            if not doc.get(prop):
                warnings.append(f"Missing recommended property '{prop}' for {schema_type}")

        # headline should be <= 110 chars for rich results display
        headline = doc.get("headline", "")
        if headline and len(headline) > 110:
            warnings.append(f"headline is {len(headline)} chars — may be truncated in rich results")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    async def validate_with_schema_org(self, jsonld: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate JSON-LD via validator.schema.org (Google's Schema Markup
        Validator backend). Accepts raw markup — works on unpublished content.

        Unofficial endpoint, rate-limited (~50 requests/hour per IP).
        Returns {"success", "valid", "errors", "warnings", "num_objects"}
        or {"success": False, "error": ...} on failure — never raises.
        """
        html = (
            "<html><head>"
            f'<script type="application/ld+json">{json.dumps(jsonld)}</script>'
            "</head><body></body></html>"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.SCHEMA_ORG_VALIDATOR_URL,
                    params={"output": "json"},
                    data={"html": html},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; BlogGenerator/1.0)",
                        "Accept": "application/json",
                    },
                )

            if response.status_code == 429:
                logger.warning("schema.org validator rate limited (429)")
                return {"success": False, "error": "rate_limited"}
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}

            # Response may carry an XSSI prefix like ")]}'"
            text = response.text.lstrip()
            if text.startswith(")]}'"):
                text = text[4:].lstrip()
            data = json.loads(text)

            def extract_messages(items):
                msgs = []
                for item in items or []:
                    if isinstance(item, dict):
                        msgs.append(item.get("message") or item.get("messageArgs") or str(item))
                    else:
                        msgs.append(str(item))
                return msgs

            errors = extract_messages(data.get("errors"))
            warnings = extract_messages(data.get("warnings"))

            logger.info(
                f"schema.org validation: {data.get('numObjects', 0)} objects, "
                f"{len(errors)} errors, {len(warnings)} warnings"
            )
            return {
                "success": True,
                "valid": data.get("totalNumErrors", len(errors)) == 0,
                "num_objects": data.get("numObjects", 0),
                "errors": errors,
                "warnings": warnings,
            }

        except Exception as e:
            logger.warning(f"schema.org validator failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_url(self, url: str, user_agent: str = "MOBILE") -> Dict[str, Any]:
        """
        Run Google's Rich Results Test API against a LIVE URL.
        Requires GOOGLE_API_KEY with Search Console API enabled.
        Does not work for unpublished/generated content.
        """
        if not settings.google_api_key:
            return {"success": False, "error": "GOOGLE_API_KEY not configured"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.RICH_RESULTS_URL,
                    params={"key": settings.google_api_key},
                    json={"url": url, "userAgent": user_agent},
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for r in data.get("testResultsPerRichResultType", []):
                results.append({
                    "type": r.get("richResultType", ""),
                    "status": r.get("richResultStatus", ""),
                })
            return {"success": True, "url": url, "results": results}

        except Exception as e:
            logger.warning(f"Rich Results Test API failed for {url}: {e}")
            return {"success": False, "url": url, "error": str(e)}


rich_results_service = RichResultsService()
