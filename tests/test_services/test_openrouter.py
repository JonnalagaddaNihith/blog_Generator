import pytest
from unittest.mock import AsyncMock, patch
from app.services.openrouter import openrouter_service


@pytest.mark.asyncio
async def test_openrouter_text_generation():
    """Test OpenRouter text generation."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "Generated text response"
                }
            }
        ]
    }

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.raise_for_status = lambda: None
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value = mock_response_obj

        result = await openrouter_service.generate_text(
            prompt="Test prompt",
            max_tokens=100
        )

        assert result == "Generated text response"


@pytest.mark.asyncio
async def test_openrouter_image_generation():
    """Test OpenRouter image generation."""
    mock_response = {
        "data": [
            {
                "url": "https://example.com/generated-image.png"
            }
        ]
    }

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.raise_for_status = lambda: None
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value = mock_response_obj

        result = await openrouter_service.generate_image(
            prompt="Test image prompt"
        )

        assert "image_url" in result
        assert result["image_url"] == "https://example.com/generated-image.png"
