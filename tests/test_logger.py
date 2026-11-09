import json

from app.utils.logger import extract_json_from_llm_response


def test_extract_json_from_llm_response_repairs_invalid_escapes():
    response = "{\"suggestion\":\"siblings\\' AI interactions\",\"note\":\"line one\\nline two\",\"path\":\"C:\\\\temp\"}"

    parsed = json.loads(extract_json_from_llm_response(response))

    assert parsed["suggestion"] == "siblings' AI interactions"
    assert parsed["note"] == "line one\nline two"
    assert parsed["path"] == "C:\\temp"
