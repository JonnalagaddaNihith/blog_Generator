import json
from unittest.mock import AsyncMock

import pytest

from app.agents.fact_verification import fact_verification_agent
from app.services.content_fetcher import content_fetcher
from app.services.fact_check import fact_check_service
from app.services.openrouter import openrouter_service


@pytest.mark.asyncio
async def test_fact_verification_adds_source_url(monkeypatch):
    research_results = [
        {
            "title": "Example Health Study",
            "url": "https://example.com/study",
            "snippet": "Study snippet",
        }
    ]
    captured_prompt = {}

    async def fake_generate_text(prompt, **kwargs):
        if "Extract up to 8" in prompt:
            return json.dumps({"claims": ["Example claim"]}), 100

        captured_prompt["value"] = prompt
        return json.dumps({
            "claims": [
                {
                    "claim": "Example claim",
                    "supported": True,
                    "source": "Example Health Study",
                }
            ],
            "confidence_score": 90,
            "recommendations": [],
        }), 100

    monkeypatch.setattr(
        content_fetcher,
        "fetch_urls",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        fact_check_service,
        "search_claims_batch",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(openrouter_service, "generate_text", fake_generate_text)

    result = await fact_verification_agent.execute(
        content="Example claim.",
        research_results=research_results,
    )

    assert "source_url" in captured_prompt["value"]
    assert result["sources"][0]["source_url"] == "https://example.com/study"
