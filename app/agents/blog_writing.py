from typing import Dict, Any, List
from app.services.openrouter import openrouter_service
from app.utils.logger import logger


class BlogWritingAgent:
    """
    Blog Writing Agent - Write the complete blog content.
    """

    async def execute(
        self,
        topic: str,
        outline: List[Dict[str, Any]],
        keywords: Dict[str, List[str]],
        tone: str,
        audience: str,
        target_word_count: int,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Write the complete blog content based on outline.
        Returns the blog content.
        """
        try:
            logger.info(f"Starting blog writing for topic: {topic}")

            # Build outline text
            outline_text = "\n".join([
                f"{i+1}. {section.get('section', '')} ({section.get('word_count', 0)} words): {section.get('description', '')}"
                for i, section in enumerate(outline)
            ])

            primary_keywords = keywords.get("primary_keywords", [])
            secondary_keywords = keywords.get("secondary_keywords", [])

            # Calculate char limit first
            char_limit = openrouter_service._calculate_char_limit(
                f"Write a complete blog post based on the following outline:\n\nTopic: {topic}\nTone: {tone}\nTarget Audience: {audience}\nTotal Target Word Count: {target_word_count}\n\nPrimary Keywords to include: {', '.join(primary_keywords)}\nSecondary Keywords to include: {', '.join(secondary_keywords[:10])}\n\nOutline:\n{outline_text}",
                multiplier=8
            )
            
            prompt = f"""
Write a complete blog post based on the following outline:

Topic: {topic}
Tone: {tone}
Target Audience: {audience}
Total Target Word Count: {target_word_count} words

Primary Keywords to include: {", ".join(primary_keywords)}
Secondary Keywords to include: {", ".join(secondary_keywords[:10])}

Outline:
{outline_text}

Requirements:
- Aim for approximately {target_word_count} words in the complete article body, excluding Markdown formatting symbols
- Follow the outline section word counts so their total matches the target word count
- Write engaging, high-quality content for each section
- Naturally incorporate the keywords
- Match the specified tone and audience
- Use proper formatting with markdown headings (## for main sections, ### for subsections)
- Ensure smooth transitions between sections
- Make it informative and valuable to the reader

Write the complete blog post:
"""

            content, _ = await openrouter_service.generate_text(
                prompt=prompt,
                max_tokens=1000000,  # Blog writing needs maximum tokens for full content
                temperature=0.7,
                multiplier=8,
                use_cache=use_cache,
            )

            if content is None:
                raise ValueError("LLM response is None")
            
            logger.info(f"Blog writing completed: {len(content)} characters")

            return {
                "agent": "blog_writing",
                "content": content,
            }

        except Exception as e:
            logger.error(f"Error in Blog Writing Agent: {e}")
            raise


blog_writing_agent = BlogWritingAgent()
