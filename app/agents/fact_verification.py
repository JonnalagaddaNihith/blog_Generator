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
                f"Verify factual claims in the following blog content against the provided research sources:\n\nBlog Content:\n{content}\n\nResearch Sources:\n{research_context}",
                multiplier=3
            )

            prompt = f"""
Verify factual claims in the following blog content against the provided research sources:

Blog Content:
{content}

Research Sources:
{research_context}

Identify EVERY key factual claim in the content and check each one against the research sources.

Return the result as a JSON object with this structure:
{{
    "claims": [
        {{"claim": "...", "supported": true, "source": "..."}},
        {{"claim": "...", "supported": false, "source": "none found", "issue": "..."}}
    ],
    "confidence_score": 85,
    "recommendations": ["..."]
}}

Rules:
- List every factual claim you check, including unsupported/questionable ones (supported: false).
- Do not omit claims; the counts are computed from this list.
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
