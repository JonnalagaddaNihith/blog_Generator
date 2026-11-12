from typing import Dict, Any
from app.services.openrouter import openrouter_service
from app.storage.file_manager import file_manager
from app.utils.logger import logger


class ImageAgent:
    """
    Image Agent - Generate exactly one relevant featured image.
    """

    async def execute(
        self,
        topic: str,
        content: str,
        tone: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a featured image for the blog.
        Returns image details including path.
        """
        try:
            logger.info(f"Starting image generation for topic: {topic}")

            # Generate image prompt based on topic and content
            prompt = f"""
Create a professional, high-quality featured image for a blog post about: {topic}
Tone: {tone}
The image should be visually appealing, relevant to the topic, and suitable for a professional blog.
"""

            # Generate image using OpenRouter
            image_result = await openrouter_service.generate_image(
                prompt=prompt,
                size="1024x1024",
                use_cache=use_cache,
            )

            # Download the image
            image_url = image_result.get("image_url")
            if image_url:
                image_data = await openrouter_service.download_image(image_url)

                # Save to local storage
                image_path = file_manager.save_image(image_data, prefix="blog")

                logger.info(f"Image generation completed: {image_path}")

                return {
                    "agent": "image",
                    "prompt": prompt,
                    "image_path": image_path,
                    "image_url": image_url,
                    "model_used": image_result.get("model_used"),
                }
            else:
                raise ValueError("No image URL returned from OpenRouter")

        except Exception as e:
            logger.error(f"Error in Image Agent: {e}")
            raise


image_agent = ImageAgent()
