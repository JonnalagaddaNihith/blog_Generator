import json

from app.utils.logger import extract_json_from_llm_response, safe_json_loads


def test_extract_json_from_llm_response_repairs_invalid_escapes():
    response = "{\"suggestion\":\"siblings\\' AI interactions\",\"note\":\"line one\\nline two\",\"path\":\"C:\\\\temp\"}"

    parsed = safe_json_loads(extract_json_from_llm_response(response))

    assert parsed["suggestion"] == "siblings' AI interactions"
    assert parsed["note"] == "line one\nline two"
    assert parsed["path"] == "C:\\temp"


def test_extract_json_from_llm_response_handles_unescaped_quotes():
    """Test that unescaped quotes inside string values are handled."""
    response = '''{
        "competitors": [
            {
                "name": "Test",
                "topics_covered": [
                    "Nutrient-dense "superfood" highlights (hemp seeds, kefir, kale)",
                    "Regular topic without quotes"
                ]
            }
        ],
        "gaps": ["gap1", "gap2"],
        "opportunities": ["opp1", "opp2"]
    }'''

    parsed = safe_json_loads(extract_json_from_llm_response(response))

    assert len(parsed["competitors"]) == 1
    assert len(parsed["competitors"][0]["topics_covered"]) == 2
    assert parsed["competitors"][0]["topics_covered"][0] == 'Nutrient-dense "superfood" highlights (hemp seeds, kefir, kale)'
    assert parsed["competitors"][0]["topics_covered"][1] == "Regular topic without quotes"
    assert parsed["gaps"] == ["gap1", "gap2"]
    assert parsed["opportunities"] == ["opp1", "opp2"]


def test_safe_json_loads_direct_parsing():
    """Test that valid JSON is parsed directly."""
    json_str = '{"key": "value", "array": [1, 2, 3]}'
    parsed = safe_json_loads(json_str)
    assert parsed["key"] == "value"
    assert parsed["array"] == [1, 2, 3]


def test_safe_json_loads_fallback_to_escaped_quotes():
    """Test fallback to escaping unescaped quotes when direct parsing fails."""
    json_str = '{"text": "This has "quotes" inside"}'
    parsed = safe_json_loads(json_str)
    assert parsed["text"] == 'This has "quotes" inside'


def test_safe_json_loads_raises_on_invalid_json():
    """Test that invalid JSON raises ValueError."""
    import pytest
    with pytest.raises(ValueError):
        safe_json_loads('{"invalid": json}')
