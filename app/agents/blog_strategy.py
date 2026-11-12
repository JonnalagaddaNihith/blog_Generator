from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.utils.logger import logger, extract_json_from_llm_response


class BlogStrategyAgent:
    """
    Blog Strategy Agent - Generate differentiated strategy and structured outline.
    """

    async def execute(
        self,
        topic: str,
        target_word_count: int,
        audience: str,
        tone: str,
        keywords: Dict[str, List[str]],
        competitor_analysis: Dict[str, Any],
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate blog strategy and structured outline.
        Returns strategy and outline structure.
        """
        try:
            logger.info(f"Starting blog strategy for topic: {topic}")

            # Build context
            primary_keywords = keywords.get("primary_keywords", [])
            gaps = competitor_analysis.get("gaps", [])
            opportunities = competitor_analysis.get("opportunities", [])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Generate a blog strategy and structured outline for the following:\n\nTopic: {topic}\nTarget Word Count: {target_word_count}\nTarget Audience: {audience}\nTone: {tone}\n\nPrimary Keywords: {', '.join(primary_keywords)}\n\nCompetitor Gaps: {', '.join(gaps[:5])}\nOpportunities: {', '.join(opportunities[:5])}",
                multiplier=4
            )
            
            prompt = f"""
Generate a blog strategy and structured outline for the following:

Topic: {topic}
Target Word Count: {target_word_count}
Target Audience: {audience}
Tone: {tone}

Primary Keywords: {", ".join(primary_keywords)}

Competitor Gaps: {", ".join(gaps[:5])}
Opportunities: {", ".join(opportunities[:5])}

Create:
1. A differentiated strategy that addresses gaps and opportunities
2. A structured outline with headings, subheadings, and brief descriptions for each section

The word_count values across all outline sections must add up to the target word count of {target_word_count}. Allocate words across sections based on their importance and scope.

Character limit: approximately {char_limit} characters. Be detailed but efficient.

Return the result as a JSON object with this structure:
{{
    "strategy": "Strategy description...",
    "outline": [
        {{"section": "Introduction", "word_count": 150, "description": "..."}},
        {{"section": "Main Section 1", "word_count": 300, "description": "..."}},
        ...
    ]
}}
"""

            response, _ = await openrouter_service.generate_text(
                prompt=prompt,
                temperature=0.7,
                multiplier=4,
                use_cache=use_cache,
            )

            if response is None:
                raise ValueError("LLM response is None")
            
            logger.info(f"LLM response length: {len(response)}")
            logger.info(f"LLM response preview: {response[:500]}")

            json_str = extract_json_from_llm_response(response)
            logger.info(f"Extracted JSON string length: {len(json_str)}")
            
            if not json_str:
                raise ValueError("Extracted JSON string is empty")
            
            strategy_data = json.loads(json_str)

            logger.info(f"Blog strategy completed: {len(strategy_data.get('outline', []))} sections in outline")

            return {
                "agent": "blog_strategy",
                "strategy": strategy_data.get("strategy", ""),
                "outline": strategy_data.get("outline", []),
            }

        except Exception as e:
            logger.error(f"Error in Blog Strategy Agent: {e}")
            raise


blog_strategy_agent = BlogStrategyAgent()
