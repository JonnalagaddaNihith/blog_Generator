"""Image generation service using Hugging Face Qwen/FLUX models.

This service provides GPU-free Python clients for hosted text-to-image generation.
The default backend calls the actual Qwen-Image-2.1 model through its official
Gradio demo Space. The alternative is FLUX.1-schnell through HF Inference Providers.
"""
from __future__ import annotations

import asyncio
import io
import os
from pathlib import Path
from typing import Any, Literal

from gradio_client import Client
from huggingface_hub import InferenceClient
from PIL import Image

from app.utils.logger import logger

ImageFormat = Literal["webp", "png"]


class GenerationError(RuntimeError):
    pass


def _token() -> str:
    token = os.getenv("HF_TOKEN")
    if not token or token.startswith("hf_replace"):
        raise GenerationError("Set a valid HF_TOKEN in your .env file.")
    return token


def _encode_image(image: Image.Image, image_format: ImageFormat = "webp", quality: int = 85) -> bytes:
    """Encode a Pillow image in the requested format, preserving alpha if present."""
    if image_format not in ("webp", "png"):
        raise ValueError("image_format must be 'webp' or 'png'")
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    buffer = io.BytesIO()
    if image_format == "webp":
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        image = image.convert("RGBA" if has_alpha else "RGB")
        image.save(buffer, format="WEBP", quality=quality, method=6)
    else:
        image.save(buffer, format="PNG")
    return buffer.getvalue()


def _downloaded_image_to_bytes(
    result: Any,
    image_format: ImageFormat = "webp",
    quality: int = 85,
) -> bytes:
    """Convert the file path returned by Gradio into PNG or WebP bytes."""
    if isinstance(result, (tuple, list)):
        if not result:
            raise GenerationError("The remote Space returned no image.")
        return _downloaded_image_to_bytes(result[0], image_format, quality)
    if isinstance(result, dict):
        if "path" in result:
            return _downloaded_image_to_bytes(result["path"], image_format, quality)
        if "name" in result:
            return _downloaded_image_to_bytes(result["name"], image_format, quality)
    if not isinstance(result, (str, os.PathLike)):
        raise GenerationError(f"Unexpected Space output type: {type(result).__name__}")

    path = Path(result)
    if not path.is_file():
        raise GenerationError("Space returned an image reference, but no local file was downloaded.")

    try:
        with Image.open(path) as image:
            image.load()
            return _encode_image(image, image_format, quality)
    except (OSError, ValueError) as exc:
        raise GenerationError("Could not decode or convert the Space image.") from exc


def _generate_qwen_sync(
    prompt: str,
    seed: int = 42,
    image_format: ImageFormat = "webp",
    quality: int = 85,
) -> bytes:
    """Synchronous implementation of Qwen generation."""
    client = Client(
        os.getenv("QWEN_SPACE_ID", "Qwen/Qwen-Image-2.1"),
        token=_token(),
        verbose=False,
        httpx_kwargs={"timeout": 120.0},
    )
    try:
        prepared = client.predict(
            [], prompt, False, True, "speed", seed, False,
            api_name="/prepare_request",
        )
        if not isinstance(prepared, (tuple, list)) or len(prepared) < 2:
            raise GenerationError("Unexpected response from /prepare_request")
        used_seed = int(prepared[1])

        generated = client.predict(
            prompt, False, True, "", used_seed, 576, 1024, " ",
            api_name="/generate_request",
        )
        return _downloaded_image_to_bytes(generated, image_format, quality)
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(
            "Qwen Space request failed. Check your HF token, ZeroGPU quota, "
            f"and the Space API. Original error: {exc}"
        ) from exc
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


async def generate_qwen(
    prompt: str,
    seed: int = 42,
    image_format: ImageFormat = "webp",
    quality: int = 85,
) -> bytes:
    """Call Qwen's two-stage hosted Space; then return WebP or PNG bytes.

    Source structure checked 2026-11-18. The public API may change without
    notice.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _generate_qwen_sync,
        prompt,
        seed,
        image_format,
        quality,
    )


def _generate_flux_sync(
    prompt: str,
    image_format: ImageFormat = "webp",
    quality: int = 85,
) -> bytes:
    """Synchronous implementation of FLUX generation."""
    model = os.getenv("HF_FALLBACK_MODEL", "black-forest-labs/FLUX.1-schnell")
    try:
        client = InferenceClient(provider="auto", api_key=_token())
        image = client.text_to_image(prompt=prompt, model=model)
        return _encode_image(image, image_format, quality)
    except GenerationError:
        raise
    except Exception as exc:
        raise GenerationError(
            "Hugging Face Inference Provider request failed. Confirm that your "
            "account has access to the model, accepted its terms, and has "
            f"available inference credits. Original error: {exc}"
        ) from exc


async def generate_flux(
    prompt: str,
    image_format: ImageFormat = "webp",
    quality: int = 85,
) -> bytes:
    """Optional independent image backend; this does NOT run Qwen."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _generate_flux_sync,
        prompt,
        image_format,
        quality,
    )


class ImageGenerationService:
    """Service for generating images using Qwen/FLUX backends."""

    def __init__(self):
        self.default_backend = os.getenv("IMAGE_BACKEND", "qwen-space")

    async def generate_image(
        self,
        prompt: str,
        backend: Literal["qwen-space", "flux-provider"] = "qwen-space",
        seed: int = 42,
        image_format: ImageFormat = "webp",
        quality: int = 85,
    ) -> dict:
        """
        Generate an image using the specified backend.

        Returns:
            dict: Contains image_bytes, model_used, and metadata
        """
        try:
            logger.info(f"Generating image with backend: {backend}")

            if backend == "qwen-space":
                image_bytes = await generate_qwen(prompt, seed, image_format, quality)
                actual_model = "Qwen/Qwen-Image-2.1"
            else:
                image_bytes = await generate_flux(prompt, image_format, quality)
                actual_model = os.getenv("HF_FALLBACK_MODEL", "black-forest-labs/FLUX.1-schnell")

            logger.info(f"Image generated successfully using model: {actual_model}")

            return {
                "image_bytes": image_bytes,
                "model_used": actual_model,
                "backend": backend,
                "image_format": image_format,
                "prompt": prompt,
            }

        except GenerationError as exc:
            logger.error(f"Image generation failed: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error during image generation: {exc}")
            raise GenerationError(f"Unexpected error: {exc}") from exc


image_generation_service = ImageGenerationService()
