from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


class QualityAgent:
    """
    Quality Agent - Validate grammar, readability, and structure.
    """

    async def execute(self, content: str) -> Dict[str, Any]:
        """
        Validate blog content quality.
        Returns quality scores and issues.
        """
        try:
            logger.info("Starting quality validation")

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Analyze the following blog content for quality:\n\nBlog Content:\n{content[:3000]}",
                multiplier=3
            )
            
            prompt = f"""
Analyze the following blog content for quality:

Blog Content:
{content[:3000]}

Evaluate:
1. Grammar and spelling (score 0-100)
2. Readability (score 0-100, based on sentence structure, complexity, etc.)
3. Structure and flow
4. Any issues or improvements needed

Character limit: approximately {char_limit} characters. Be specific and constructive.

Return the result as a JSON object with this structure:
{{
    "grammar_score": 85,
    "readability_score": 90,
    "issues": [
        {{"type": "grammar", "location": "...", "suggestion": "..."}},
        {{"type": "style", "location": "...", "suggestion": "..."}}
    ],
    "overall_assessment": "..."
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
            
            quality_data = json.loads(json_str)

            logger.info(f"Quality validation completed: grammar={quality_data.get('grammar_score')}, readability={quality_data.get('readability_score')}")

            return {
                "agent": "quality",
                "grammar_score": quality_data.get("grammar_score", 0),
                "readability_score": quality_data.get("readability_score", 0),
                "issues": quality_data.get("issues", []),
                "overall_assessment": quality_data.get("overall_assessment", ""),
            }

        except Exception as e:
            logger.error(f"Error in Quality Agent: {e}")
            raise


quality_agent = QualityAgent()
