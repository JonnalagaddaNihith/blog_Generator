import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.cache import cache_get, cache_set
from app.utils.logger import logger


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.text_model = settings.openrouter_text_model
        self.image_model = settings.openrouter_image_model
        self.timeout = 300.0

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Blog Generator",
        }

    def _calculate_max_tokens(self, prompt: str, requested_max: int = None, multiplier: int = 3) -> int:
        """
        Calculate dynamic max_tokens based on prompt length.
        """
        # Estimate prompt tokens (rough approximation: 1 token ≈ 4 characters)
        prompt_tokens = len(prompt) // 4
        
        # Calculate dynamic max: prompt length * multiplier, with minimum and maximum bounds
        # Multiplier ensures output is proportional to input complexity
        calculated_max = prompt_tokens * multiplier
        
        # Apply minimum and maximum bounds
        min_tokens = 1000
        max_tokens_cap = 1000000  # Very high cap to prevent truncation
        
        # If user specified a max, use it but ensure it's within bounds
        if requested_max:
            calculated_max = max(min_tokens, min(requested_max, max_tokens_cap))
        else:
            calculated_max = max(min_tokens, min(calculated_max, max_tokens_cap))
        
        logger.info(f"Dynamic max_tokens calculated: {calculated_max} (prompt tokens: {prompt_tokens}, multiplier: {multiplier})")
        return calculated_max

    def _calculate_char_limit(self, prompt: str, multiplier: int = 3) -> int:
        """
        Calculate dynamic character limit based on prompt length and multiplier.
        """
        prompt_tokens = len(prompt) // 4
        max_tokens = prompt_tokens * multiplier
        # Apply bounds
        min_tokens = 1000
        max_tokens_cap = 1000000
        max_tokens = max(min_tokens, min(max_tokens, max_tokens_cap))
        return max_tokens * 4  # Convert to characters

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        model: Optional[str] = None,
        multiplier: int = 3,
        use_cache: bool = True,
    ) -> tuple[str, int]:
        """
        Generate text using OpenRouter API.
        Returns (content, char_limit).
        """
        # Calculate dynamic max_tokens and char limit
        dynamic_max = self._calculate_max_tokens(prompt, max_tokens, multiplier)
        char_limit = self._calculate_char_limit(prompt, multiplier)

        cache_key = f"text:{model or self.text_model}:{hash(prompt)}:{dynamic_max}:{temperature}"
        if use_cache:
            cached = await cache_get(cache_key)
            if cached:
                logger.info(f"Cache hit for text generation")
                return cached, char_limit

        try:
            payload = {
                "model": model or self.text_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": dynamic_max,
                "temperature": temperature,
                # Reasoning models (e.g. Nemotron) return content=None and put
                # output in `reasoning`, often truncated. Disable reasoning so
                # the answer lands in `content`.
                "reasoning": {"enabled": False},
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"OpenRouter response data keys: {data.keys()}")
                logger.info(f"OpenRouter choices length: {len(data.get('choices', []))}")
                logger.info(f"OpenRouter full response structure: {data}")
                
                if not data.get("choices") or len(data["choices"]) == 0:
                    logger.error(f"No choices in response: {data}")
                    raise ValueError("No choices in OpenRouter response")
                
                message = data["choices"][0].get("message", {})
                content = message.get("content")
                
                if content is None:
                    logger.error(f"Content is None. Message: {message}")
                    logger.error(f"Full choice: {data['choices'][0]}")
                    logger.error(f"Full response data: {data}")
                    
                    # Try multiple fallback fields
                    possible_fields = ["reasoning", "text", "delta", "content"]
                    extracted_content = None
                    
                    for field in possible_fields:
                        field_value = message.get(field, "")
                        if field_value:
                            logger.warning(f"Content is None, attempting to extract from {field} field")
                            # Try to find JSON in the field
                            import re
                            json_match = re.search(r'\{[\s\S]*\}', field_value)
                            if json_match:
                                extracted_content = json_match.group(0)
                                logger.info(f"Extracted JSON from {field}, length: {len(extracted_content)}")
                                break
                            # If no JSON, use the field value directly
                            extracted_content = field_value
                            logger.info(f"Using {field} field directly, length: {len(extracted_content)}")
                            break
                    
                    # If still no content, try checking for other response structures
                    if not extracted_content:
                        # Some models return text directly in a different structure
                        if "text" in data:
                            extracted_content = data.get("text", "")
                            logger.info(f"Extracted from data.text, length: {len(extracted_content)}")
                        elif "output" in data:
                            extracted_content = data.get("output", "")
                            logger.info(f"Extracted from data.output, length: {len(extracted_content)}")
                    
                    if extracted_content:
                        if use_cache:
                            await cache_set(cache_key, extracted_content, expire_seconds=3600)
                        return extracted_content, char_limit
                    
                    raise ValueError("Content is None in OpenRouter response and no fallback content found")

                if use_cache:
                    await cache_set(cache_key, content, expire_seconds=3600)
                logger.info(f"Successfully generated text using model: {model or self.text_model}")
                return content, char_limit

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during text generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text generation: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate image using OpenRouter API.
        Returns dictionary with image_url, model_used, etc.
        """
        cache_key = f"image:{model or self.image_model}:{hash(prompt)}:{size}"
        if use_cache:
            cached = await cache_get(cache_key)
            if cached:
                logger.info(f"Cache hit for image generation")
                return cached

        try:
            payload = {
                "model": model or self.image_model,
                "prompt": prompt,
                "size": size,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                result = {
                    "image_url": data["data"][0]["url"],
                    "model_used": model or self.image_model,
                    "prompt": prompt,
                    "size": size,
                }

                if use_cache:
                    await cache_set(cache_key, result, expire_seconds=86400)
                logger.info(f"Successfully generated image using model: {model or self.image_model}")
                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during image generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image generation: {e}")
            raise

    async def download_image(self, image_url: str) -> bytes:
        """
        Download image from URL.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during image download: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image download: {e}")
            raise


openrouter_service = OpenRouterService()
