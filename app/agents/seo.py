from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


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
3. Keyword density analysis

Character limit: approximately {char_limit} characters. Be precise and actionable.

Return the result as a JSON object with this structure:
{{
    "title": "SEO-optimized title",
    "meta_description": "Compelling meta description",
    "keyword_density": {{"keyword": "percentage"}}
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

            logger.info(f"SEO optimization completed: title generated")

            return {
                "agent": "seo",
                "title": seo_data.get("title", ""),
                "meta_description": seo_data.get("meta_description", ""),
                "keyword_density": seo_data.get("keyword_density", {}),
            }

        except Exception as e:
            logger.error(f"Error in SEO Agent: {e}")
            raise


seo_agent = SEOAgent()
