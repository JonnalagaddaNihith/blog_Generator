from typing import Dict, Any, List
import json
import re
from app.services.openrouter import openrouter_service
from app.services.rich_results import rich_results_service
from app.utils.logger import logger, extract_json_from_llm_response


def compute_keyword_density(content: str, keywords: List[str]) -> Dict[str, float]:
    """
    Deterministically compute keyword density (% of total words) for each keyword.
    Multi-word keywords count their full phrase length.
    """
    words = re.findall(r"\b\w+\b", content.lower())
    total_words = len(words)
    if total_words == 0:
        return {kw: 0.0 for kw in keywords}

    content_lower = content.lower()
    density = {}
    for kw in keywords:
        if not kw:
            continue
        count = content_lower.count(kw.lower())
        kw_word_count = len(kw.split())
        density[kw] = round((count * kw_word_count / total_words) * 100, 2)
    return density


class SEOAgent:
    """
    SEO Agent - Optimize title, metadata, keywords, and headings.
    """

    async def execute(
        self,
        topic: str,
        content: str,
        keywords: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Optimize blog content for SEO.
        Returns SEO metadata including title, meta description, and headings analysis.
        """
        try:
            logger.info(f"Starting SEO optimization for topic: {topic}")

            primary_keywords = keywords.get("primary_keywords", [])
            secondary_keywords = keywords.get("secondary_keywords", [])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Optimize the following blog content for SEO:\n\nTopic: {topic}\n\nPrimary Keywords: {', '.join(primary_keywords)}\nSecondary Keywords: {', '.join(secondary_keywords[:10])}\n\nBlog Content (first 2000 characters):\n{content[:2000]}",
                multiplier=3
            )
            
            prompt = f"""
Optimize the following blog content for SEO:

Topic: {topic}

Primary Keywords: {", ".join(primary_keywords)}
Secondary Keywords: {", ".join(secondary_keywords[:10])}

Blog Content (first 2000 characters):
{content[:2000]}

Generate:
1. An SEO-optimized title (50-60 characters, includes primary keyword)
2. A meta description (150-160 characters, compelling, includes keywords)

Character limit: approximately {char_limit} characters. Be precise and actionable.

Return the result as a JSON object with this structure:
{{
    "title": "SEO-optimized title",
    "meta_description": "Compelling meta description"
}}
"""

            response, _ = await openrouter_service.generate_text(
                prompt=prompt,
                temperature=0.5,
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
            
            seo_data = json.loads(json_str)

            # Keyword density is computed deterministically — the LLM's
            # estimate is unreliable. Prefer the computed values.
            all_keywords = list(dict.fromkeys(primary_keywords + secondary_keywords[:10]))
            keyword_density = compute_keyword_density(content, all_keywords)

            # Build and validate schema.org Article structured data (JSON-LD)
            # for rich results eligibility.
            title = seo_data.get("title", "")
            meta_description = seo_data.get("meta_description", "")
            jsonld = rich_results_service.build_article_jsonld(
                title=title,
                description=meta_description,
                keywords=primary_keywords,
                content=content,
            )
            rich_results_validation = rich_results_service.validate_jsonld(jsonld)

            # Validate against Google's Schema Markup Validator (validator.schema.org)
            # — accepts raw markup, works on unpublished content. Rate-limited;
            # failures degrade gracefully.
            schema_org_validation = await rich_results_service.validate_with_schema_org(jsonld)
            if schema_org_validation.get("success"):
                rich_results_validation["schema_org"] = schema_org_validation
                if not schema_org_validation.get("valid"):
                    rich_results_validation["errors"].extend(
                        f"schema.org: {e}" for e in schema_org_validation.get("errors", [])
                    )
                    rich_results_validation["valid"] = False

            logger.info(
                f"SEO optimization completed: title generated, "
                f"jsonld valid={rich_results_validation['valid']}"
            )

            return {
                "agent": "seo",
                "title": title,
                "meta_description": meta_description,
                "keyword_density": keyword_density,
                "structured_data": jsonld,
                "rich_results": rich_results_validation,
            }

        except Exception as e:
            logger.error(f"Error in SEO Agent: {e}")
            raise


seo_agent = SEOAgent()
