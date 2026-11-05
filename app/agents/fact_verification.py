from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


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

            # Build research context
            research_context = "\n".join([
                f"- {r.get('title', '')}: {r.get('snippet', '')}"
                for r in research_results[:10]
            ])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Verify factual claims in the following blog content against the provided research sources:\n\nBlog Content (first 2000 characters):\n{content[:2000]}\n\nResearch Sources:\n{research_context}",
                multiplier=3
            )
            
            prompt = f"""
Verify factual claims in the following blog content against the provided research sources:

Blog Content (first 2000 characters):
{content[:2000]}

Research Sources:
{research_context}

Identify:
1. Key factual claims in the content
2. Which claims are supported by the research sources
3. Which claims need verification or are questionable
4. Overall confidence score (0-100)

Character limit: approximately {char_limit} characters. Be thorough but concise.

Return the result as a JSON object with this structure:
{{
    "claims_verified": 10,
    "total_claims": 12,
    "sources": [
        {{"claim": "...", "supported": true, "source": "..."}}
    ],
    "confidence_score": 85,
    "recommendations": ["..."]
}}
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

            logger.info(f"Fact verification completed: confidence={verification_data.get('confidence_score')}")

            return {
                "agent": "fact_verification",
                "claims_verified": verification_data.get("claims_verified", 0),
                "total_claims": verification_data.get("total_claims", 0),
                "sources": verification_data.get("sources", []),
                "confidence_score": verification_data.get("confidence_score", 0),
                "recommendations": verification_data.get("recommendations", []),
            }

        except Exception as e:
            logger.error(f"Error in Fact Verification Agent: {e}")
            raise


fact_verification_agent = FactVerificationAgent()
