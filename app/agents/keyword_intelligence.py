from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


class KeywordIntelligenceAgent:
    """
    Keyword Intelligence Agent - Extract primary, secondary, and long-tail keywords.
    """

    async def execute(self, topic: str, research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract keywords from research results.
        Returns primary, secondary, and long-tail keywords.
        """
        try:
            logger.info(f"Starting keyword intelligence for topic: {topic}")

            # Build context from research results
            context = "\n".join([
                f"- {r.get('title', '')}: {r.get('snippet', '')}"
                for r in research_results[:10]
            ])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Based on the following research results for the topic \"{topic}\", extract keywords:\n\nResearch Context:\n{context}",
                multiplier=2
            )
            
            prompt = f"""
Based on the following research results for the topic "{topic}", extract keywords:

Research Context:
{context}

Extract and categorize keywords into:
1. Primary keywords (5-7 most important, high-volume keywords)
2. Secondary keywords (10-15 related, medium-volume keywords)
3. Long-tail keywords (10-15 specific, lower-volume but targeted phrases)

Character limit: approximately {char_limit} characters. Keep your response concise.

Return the result as a JSON object with this structure:
{{
    "primary_keywords": ["keyword1", "keyword2", ...],
    "secondary_keywords": ["keyword1", "keyword2", ...],
    "long_tail_keywords": ["phrase1", "phrase2", ...]
}}
"""

            response, _ = await openrouter_service.generate_text(
                prompt=prompt,
                temperature=0.5,
                multiplier=2,
            )

            if response is None:
                raise ValueError("LLM response is None")
            
            logger.info(f"LLM response length: {len(response)}")
            logger.info(f"LLM response preview: {response[:500]}")

            json_str = extract_json_from_llm_response(response)
            logger.info(f"Extracted JSON string length: {len(json_str)}")
            
            if not json_str:
                raise ValueError("Extracted JSON string is empty")
            
            keywords_data = json.loads(json_str)

            logger.info(f"Keyword intelligence completed: {len(keywords_data.get('primary_keywords', []))} primary keywords")

            return {
                "agent": "keyword_intelligence",
                "primary_keywords": keywords_data.get("primary_keywords", []),
                "secondary_keywords": keywords_data.get("secondary_keywords", []),
                "long_tail_keywords": keywords_data.get("long_tail_keywords", []),
            }

        except Exception as e:
            logger.error(f"Error in Keyword Intelligence Agent: {e}")
            raise


keyword_intelligence_agent = KeywordIntelligenceAgent()
