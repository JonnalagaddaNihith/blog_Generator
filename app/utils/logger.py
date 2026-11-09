import logging
import json
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def _repair_invalid_json_escapes(json_str: str) -> str:
    repaired = []
    in_string = False
    i = 0

    while i < len(json_str):
        char = json_str[i]

        if not in_string:
            repaired.append(char)
            if char == '"':
                in_string = True
            i += 1
            continue

        if char == '"':
            in_string = False
            repaired.append(char)
            i += 1
            continue

        if char != "\\":
            repaired.append(char)
            i += 1
            continue

        if i + 1 >= len(json_str):
            repaired.append(char)
            i += 1
            continue

        next_char = json_str[i + 1]
        if next_char in {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}:
            repaired.append(char)
            repaired.append(next_char)
            i += 2
            continue

        i += 1

    return "".join(repaired)


def extract_json_from_llm_response(response: str) -> str:
    """Extract JSON from LLM response, removing markdown code blocks if present."""
    json_str = response.strip()
    
    # Remove markdown code blocks with various formats
    if json_str.startswith("```json"):
        json_str = json_str[7:]  # Remove ```json
    elif json_str.startswith("```"):
        json_str = json_str[3:]  # Remove ```
    
    if json_str.endswith("```"):
        json_str = json_str[:-3]  # Remove trailing ```
    
    json_str = json_str.strip()
    
    # Find the first { and last } to extract just the JSON object
    start_idx = json_str.find("{")
    end_idx = json_str.rfind("}")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = json_str[start_idx:end_idx + 1]
    
    return _repair_invalid_json_escapes(json_str)

