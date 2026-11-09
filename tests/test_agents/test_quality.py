import json
from unittest.mock import AsyncMock

import pytest

from app.agents.quality import quality_agent
from app.services.languagetool import languagetool_service
from app.services.openrouter import openrouter_service


@pytest.mark.asyncio
async def test_quality_agent_evaluates_entire_content(monkeypatch):
    content = "Introduction. " + ("Detailed analysis. " * 400) + "Final conclusion."
    captured_prompt = {}

    async def fake_generate_text(prompt, **kwargs):
        captured_prompt["value"] = prompt
        return json.dumps({
            "grammar_score": 90,
            "readability_score": 85,
            "issues": [],
            "overall_assessment": "Good",
        }), 1000

    monkeypatch.setattr(openrouter_service, "generate_text", fake_generate_text)
    monkeypatch.setattr(
        languagetool_service,
        "check",
        AsyncMock(return_value={"issue_count": 0, "issues": []}),
    )

    await quality_agent.execute(content)

    assert len(content) > 3000
    assert content in captured_prompt["value"]
