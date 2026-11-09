from typing import Dict, Any, List
import json
import re
from urllib.parse import urlparse
from app.services.openrouter import openrouter_service
from app.services.content_fetcher import content_fetcher
from app.services.fact_check import fact_check_service
from app.utils.logger import logger, extract_json_from_llm_response


def _extract_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    match = re.search(r"https?://\S+", value)
    if not match:
        return ""
    return re.sub(r"[.,;:!?)\]}>\"']+$", "", match.group(0))


def _candidate_labels(candidate: Dict[str, Any]) -> List[str]:
    url = candidate.get("url", "")
    labels = [candidate.get("title", ""), candidate.get("publisher", "")]
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if domain:
        labels.append(domain)
    return [label for label in labels if label]


def _resolve_claim_source_url(claim: Dict[str, Any], candidates: List[Dict[str, Any]]) -> str:
    for field in ("source_url", "url", "source", "publisher"):
        url = _extract_url(claim.get(field))
        if url:
            return url

    hint = " ".join(
        str(claim.get(field, ""))
        for field in ("source", "publisher", "source_name", "source_title")
    ).lower()
    if not hint.strip():
        return ""

    for candidate in candidates:
        for label in _candidate_labels(candidate):
            if label.lower() in hint:
                return candidate.get("url", "")
    return ""


def _normalize_claims(claims: List[Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for claim in claims:
        if not isinstance(claim, dict):
            claim = {"claim": str(claim), "supported": False}
        claim["source_url"] = _resolve_claim_source_url(claim, candidates)
        normalized.append(claim)
    return normalized


class FactVerificationAgent:
    """
    Fact Verification Agent - Verify factual claims against research sources.
    """

    async def execute(
        self,
        content: str,
        research_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify factual claims in the blog content against research sources.
        Returns verification report with confidence score.
        """
        try:
            logger.info("Starting fact verification")

            # Fetch full page content for the top research sources so claims
            # are verified against article text, not just search snippets.
            source_urls = [r.get("url") for r in research_results if r.get("url")][:3]
            fetched_sources = await content_fetcher.fetch_urls(source_urls, max_chars=5000)

            # Build research context: prefer fetched page text, fall back to snippets
            fetched_by_url = {f["url"]: f for f in fetched_sources}
            context_parts = []
            for r in research_results[:10]:
                url = r.get("url", "")
                fetched = fetched_by_url.get(url)
                if fetched:
                    context_parts.append(
                        f"- {fetched.get('title') or r.get('title', '')} ({url}):\n{fetched['text'][:2500]}"
                    )
                else:
                    context_parts.append(
                        f"- {r.get('title', '')} ({url}): {r.get('snippet', '')}"
                    )
            research_context = "\n".join(context_parts)

            # Pass 1: extract key factual claims so they can be checked against
            # the Google Fact Check Tools API before the full verification pass.
            claims_prompt = f"""
Extract up to 8 key factual claims from the following blog content that could be verified against external sources (statistics, studies, health effects, dates, named entities).

Blog Content:
{content[:6000]}

Return ONLY a JSON object:
{{"claims": ["claim 1", "claim 2", ...]}}
"""
            claims_response, _ = await openrouter_service.generate_text(
                prompt=claims_prompt,
                temperature=0.0,
                multiplier=1,
            )
            extracted_claims = []
            if claims_response:
                try:
                    claims_json = extract_json_from_llm_response(claims_response)
                    extracted_claims = json.loads(claims_json).get("claims", [])[:8]
                except Exception as e:
                    logger.warning(f"Claim extraction failed: {e}")

            # Query Google Fact Check Tools API for the extracted claims
            fact_check_context = ""
            fact_checks = []
            if fact_check_service.enabled and extracted_claims:
                fact_checks = await fact_check_service.search_claims_batch(
                    extracted_claims[:5], max_results=2
                )
                if fact_checks:
                    fact_check_context = "\n".join([
                        f"- Claim: {f['claim']}\n  Rating: {f['rating']} | Source: {f['publisher']} ({f['url']})"
                        for f in fact_checks
                    ])
                    logger.info(f"Fact Check API returned {len(fact_checks)} verified claims")

            fact_check_section = ""
            if fact_check_context:
                fact_check_section = (
                    "\nPublished Fact-Checks (Google Fact Check Tools API):\n"
                    f"{fact_check_context}\n"
                )

            source_candidates = [
                {"url": r.get("url", ""), "title": r.get("title", ""), "publisher": ""}
                for r in research_results
                if r.get("url")
            ] + [
                {"url": f.get("url", ""), "title": f.get("claim", ""), "publisher": f.get("publisher", "")}
                for f in fact_checks
                if f.get("url")
            ]

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Verify factual claims in the following blog content against the provided research sources:\n\nBlog Content:\n{content}\n\nResearch Sources:\n{research_context}",
                multiplier=3
            )

            prompt = f"""
Verify factual claims in the following blog content against the provided research sources:

Blog Content:
{content}

Research Sources:
{research_context}
{fact_check_section}
Identify EVERY key factual claim in the content and check each one against the research sources and published fact-checks.

Return the result as a JSON object with this structure:
{{
    "claims": [
        {{"claim": "...", "supported": true, "source": "...", "source_url": "https://..."}},
        {{"claim": "...", "supported": false, "source": "none found", "source_url": "", "issue": "..."}}
    ],
    "confidence_score": 85,
    "recommendations": ["..."]
}}

Rules:
- List every factual claim you check, including unsupported/questionable ones (supported: false).
- Do not omit claims; the counts are computed from this list.
- source_url must be copied exactly from a URL in Research Sources or Published Fact-Checks.
- Do not invent source URLs; use an empty string when no source URL is available.
- Character limit: approximately {char_limit} characters. Be thorough but concise.
"""

            response, _ = await openrouter_service.generate_text(
                prompt=prompt,
                temperature=0.3,
                multiplier=3,
            )

            if response is None:
                raise ValueError("LLM response is None")

            logger.info(f"LLM response length: {len(response)}")
            logger.info(f"LLM response preview: {response[:500]}")

            json_str = extract_json_from_llm_response(response)
            logger.info(f"Extracted JSON string length: {len(json_str)}")

            if not json_str:
                raise ValueError("Extracted JSON string is empty")

            verification_data = json.loads(json_str)

            # Normalize claims list (accept legacy "sources" key too)
            claims = verification_data.get("claims") or verification_data.get("sources", [])
            claims = _normalize_claims(claims, source_candidates)
            claims_verified = sum(1 for c in claims if c.get("supported"))
            total_claims = len(claims)

            logger.info(
                f"Fact verification completed: {claims_verified}/{total_claims} claims supported, "
                f"confidence={verification_data.get('confidence_score')}"
            )

            return {
                "agent": "fact_verification",
                "claims_verified": claims_verified,
                "total_claims": total_claims,
                "sources": claims,
                "confidence_score": verification_data.get("confidence_score", 0),
                "recommendations": verification_data.get("recommendations", []),
            }

        except Exception as e:
            logger.error(f"Error in Fact Verification Agent: {e}")
            raise


fact_verification_agent = FactVerificationAgent()
