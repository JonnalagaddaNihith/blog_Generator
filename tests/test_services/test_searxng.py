import pytest
from unittest.mock import AsyncMock, patch
from app.services.searxng import searxng_service


@pytest.mark.asyncio
async def test_searxng_search():
    """Test SearXNG search functionality."""
    mock_response = {
        "results": [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "content": "Test content 1",
                "engine": "google",
                "category": "general"
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/2",
                "content": "Test content 2",
                "engine": "bing",
                "category": "general"
            }
        ]
    }

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.raise_for_status = lambda: None
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_response_obj

        results = await searxng_service.search("test query", num_results=2)

        assert len(results) == 2
        assert results[0]["title"] == "Test Result 1"
        assert results[1]["title"] == "Test Result 2"


@pytest.mark.asyncio
async def test_searxng_extract_content():
    """Test SearXNG content extraction."""
    mock_response = {
        "content": "Extracted content from the webpage"
    }

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.raise_for_status = lambda: None
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_response_obj

        content = await searxng_service.extract_content("https://example.com")

        assert content == "Extracted content from the webpage"
