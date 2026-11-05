from typing import Dict, Any, List
from app.services.searxng import searxng_service
from app.utils.logger import logger


class WebResearchAgent:
    """
    Web Research Agent - Search and extract top 5 relevant results using SearXNG.
    """

    async def execute(self, topic: str, company_description: str = "") -> Dict[str, Any]:
        """
        Execute web research for the given topic.
        Returns search results with titles, URLs, and snippets.
        """
        try:
            logger.info(f"Starting web research for topic: {topic}")

            # Build search query
            search_query = topic

            # Perform search
            results = await searxng_service.search(
                query=search_query,
                num_results=5,
                categories=["general"],
                language="en",
            )

            logger.info(f"Web research completed: {len(results)} results found")

            return {
                "agent": "web_research",
                "query": search_query,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            logger.error(f"Error in Web Research Agent: {e}")
            raise


web_research_agent = WebResearchAgent()
