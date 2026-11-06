from typing import Dict, Any, List
import json
import textstat
from app.services.openrouter import openrouter_service
from app.services.languagetool import languagetool_service
from app.utils.logger import logger, extract_json_from_llm_response


def compute_readability_metrics(content: str) -> Dict[str, Any]:
    """Deterministic readability metrics via textstat."""
    try:
        return {
            "word_count": textstat.lexicon_count(content, removepunct=True),
            "sentence_count": textstat.sentence_count(content),
            "avg_sentence_length": round(textstat.avg_sentence_length(content), 2),
            "flesch_reading_ease": round(textstat.flesch_reading_ease(content), 2),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(content), 2),
            "smog_index": round(textstat.smog_index(content), 2),
        }
    except Exception:
        return {}


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

            # Deterministic checks: textstat readability metrics + LanguageTool
            # grammar/style issues (real proofreading engine, not LLM guesswork)
            readability_metrics = compute_readability_metrics(content)
            lt_result = await languagetool_service.check(content)

            logger.info(f"Quality validation completed: grammar={quality_data.get('grammar_score')}, readability={quality_data.get('readability_score')}, languagetool_issues={lt_result.get('issue_count')}")

            return {
                "agent": "quality",
                "grammar_score": quality_data.get("grammar_score", 0),
                "readability_score": quality_data.get("readability_score", 0),
                "issues": quality_data.get("issues", []),
                "overall_assessment": quality_data.get("overall_assessment", ""),
                "readability_metrics": readability_metrics,
                "grammar_issue_count": lt_result.get("issue_count", 0),
                "grammar_issues": lt_result.get("issues", []),
            }

        except Exception as e:
            logger.error(f"Error in Quality Agent: {e}")
            raise


quality_agent = QualityAgent()
