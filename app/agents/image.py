from typing import Dict, Any
from app.services.image_generation import image_generation_service
from app.storage.file_manager import file_manager
from app.utils.logger import logger


class ImageAgent:
    """
    Image Agent - Generate exactly one relevant featured image using Qwen/FLUX.
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
            # Focus on visual elements only - AI models cannot reliably generate text
            prompt = f"""
Create a purely abstract, geometric featured image for a blog post about: {topic}
Tone: {tone}
Use only shapes, colors, gradients, lines, and geometric patterns.
No icons, no graphics, no symbols, no text, no letters, no numbers.
Pure abstract art suitable for a professional blog header.
"""

            # Generate image using Qwen/FLUX service
            image_result = await image_generation_service.generate_image(
                prompt=prompt,
                backend="qwen-space",
                seed=42,
                image_format="webp",
                quality=85,
            )

            # Get image bytes
            image_bytes = image_result.get("image_bytes")
            if image_bytes:
                # Save to local storage
                image_format = image_result.get("image_format", "webp")
                image_path = file_manager.save_image(image_bytes, prefix="blog", image_format=image_format)

                logger.info(f"Image generation completed: {image_path}")

                return {
                    "agent": "image",
                    "prompt": prompt,
                    "image_path": image_path,
                    "model_used": image_result.get("model_used"),
                    "backend": image_result.get("backend"),
                }
            else:
                raise ValueError("No image bytes returned from image generation service")

        except Exception as e:
            logger.error(f"Error in Image Agent: {e}")
            raise


image_agent = ImageAgent()
