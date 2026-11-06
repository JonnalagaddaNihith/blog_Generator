from typing import Dict, Any, List
import json
from app.services.openrouter import openrouter_service
from app.services.google_suggestions import google_suggestions_service
from app.utils.logger import logger, extract_json_from_llm_response


class KeywordIntelligenceAgent:
    """
    Keyword Intelligence Agent - Extract primary, secondary, and long-tail keywords.
    """

    @staticmethod
    def _to_search_phrase(topic: str) -> str:
        """
        Convert a question-style topic into a shorter search phrase that
        Google autocomplete responds to (e.g. drop trailing '?').
        """
        phrase = topic.strip().rstrip("?").strip()
        # If still long, keep first 6 words as the seed
        words = phrase.split()
        if len(words) > 6:
            phrase = " ".join(words[:6])
        return phrase

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

            # Ground keyword extraction in real Google search suggestions.
            # Autocomplete returns empty for long question-style queries, so
            # normalize the topic into a shorter search phrase first.
            topic_seed = self._to_search_phrase(topic)
            google_suggestions = await google_suggestions_service.get_suggestions(topic_seed, max_results=10)
            suggestions_context = "\n".join(f"- {s}" for s in google_suggestions) or "(none)"

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Based on the following research results for the topic \"{topic}\", extract keywords:\n\nResearch Context:\n{context}",
                multiplier=2
            )
            
            prompt = f"""
Based on the following research results for the topic "{topic}", extract keywords:

Research Context:
{context}

Google Autocomplete Suggestions (real search queries users type):
{suggestions_context}

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

            # Query autocomplete again using the extracted primary keywords as
            # seeds — natural phrases return far more suggestions than the raw
            # topic. Merge everything into long-tail keywords.
            primary = keywords_data.get("primary_keywords", [])
            keyword_seeds = [topic_seed] + [k for k in primary if k][:5]
            keyword_suggestions = await google_suggestions_service.get_suggestions_for_queries(
                keyword_seeds, max_results=8
            )
            all_suggestions = list(dict.fromkeys(google_suggestions + keyword_suggestions))

            long_tail = list(keywords_data.get("long_tail_keywords", []))
            existing = {k.lower() for k in long_tail}
            for s in all_suggestions:
                if s.lower() not in existing:
                    long_tail.append(s)
                    existing.add(s.lower())

            logger.info(f"Keyword intelligence completed: {len(primary)} primary keywords, {len(all_suggestions)} google suggestions")

            return {
                "agent": "keyword_intelligence",
                "primary_keywords": primary,
                "secondary_keywords": keywords_data.get("secondary_keywords", []),
                "long_tail_keywords": long_tail,
                "google_suggestions": all_suggestions,
            }

        except Exception as e:
            logger.error(f"Error in Keyword Intelligence Agent: {e}")
            raise


keyword_intelligence_agent = KeywordIntelligenceAgent()
