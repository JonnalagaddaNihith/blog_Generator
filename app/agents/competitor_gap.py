from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


class CompetitorGapAgent:
    """
    Competitor Gap Agent - Analyze competitor content and identify missing topics.
    """

    async def execute(self, topic: str, research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze competitor content and identify gaps.
        Returns competitor analysis and missing topics.
        """
        try:
            logger.info(f"Starting competitor gap analysis for topic: {topic}")

            # Build context from research results
            context = "\n".join([
                f"- {r.get('title', '')} ({r.get('url', '')}): {r.get('snippet', '')}"
                for r in research_results[:10]
            ])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Based on the following research results for the topic \"{topic}\", analyze competitor content:\n\nResearch Context:\n{context}",
                multiplier=5
            )
            
            prompt = f"""
Based on the following research results for the topic "{topic}", analyze competitor content:

Research Context:
{context}

Identify:
1. Top competitors (5-7 main sources based on URLs/titles)
2. What topics they are covering
3. Gaps - what topics are missing or could be better covered
4. Opportunities for differentiation

Character limit: approximately {char_limit} characters. Be thorough but concise.

Return the result as a JSON object with this structure:
{{
    "competitors": [
        {{"name": "Competitor Name", "url": "URL", "topics_covered": ["topic1", "topic2"]}}
    ],
    "gaps": ["gap1", "gap2", ...],
    "opportunities": ["opportunity1", "opportunity2", ...]
}}
"""

            response, _ = await openrouter_service.generate_text(
                prompt=prompt,
                temperature=0.6,
                multiplier=5,
            )

            if response is None:
                raise ValueError("LLM response is None")
            
            logger.info(f"LLM response length: {len(response)}")
            logger.info(f"LLM response preview: {response[:500]}")

            json_str = extract_json_from_llm_response(response)
            logger.info(f"Extracted JSON string length: {len(json_str)}")
            
            if not json_str:
                raise ValueError("Extracted JSON string is empty")
            
            analysis_data = json.loads(json_str)

            logger.info(f"Competitor gap analysis completed: {len(analysis_data.get('competitors', []))} competitors identified")

            return {
                "agent": "competitor_gap",
                "competitors": analysis_data.get("competitors", []),
                "gaps": analysis_data.get("gaps", []),
                "opportunities": analysis_data.get("opportunities", []),
            }

        except Exception as e:
            logger.error(f"Error in Competitor Gap Agent: {e}")
            raise


competitor_gap_agent = CompetitorGapAgent()
