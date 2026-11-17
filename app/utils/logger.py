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


def _escape_unescaped_quotes_in_strings(json_str: str) -> str:
    """
    Escape unescaped quotes that appear inside JSON string values.
    This handles cases like: "Nutrient-dense "superfood" highlights"
    """
    result = []
    in_string = False
    i = 0

    while i < len(json_str):
        char = json_str[i]

        if char == '"':
            if not in_string:
                # Starting a string
                in_string = True
                result.append(char)
            else:
                # Check if this is an escaped quote
                if i > 0 and json_str[i-1] == '\\':
                    # Already escaped, keep as is
                    result.append(char)
                else:
                    # Check if this quote is followed by valid JSON structure
                    # (comma, closing brace, closing bracket, colon, or whitespace then these)
                    next_idx = i + 1
                    # Skip whitespace
                    while next_idx < len(json_str) and json_str[next_idx] in ' \t\n\r':
                        next_idx += 1

                    if next_idx < len(json_str) and json_str[next_idx] in ',}]:':
                        # This is likely a closing quote
                        in_string = False
                        result.append(char)
                    else:
                        # This is an unescaped quote inside a string, escape it
                        result.append('\\"')
            i += 1
            continue

        if char == '\\' and in_string:
            # Keep escape sequences as is
            result.append(char)
            if i + 1 < len(json_str):
                result.append(json_str[i + 1])
                i += 2
            else:
                i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def _try_parse_json(json_str: str) -> dict:
    """Try to parse JSON, returning None on failure."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None


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

    # First, try to repair invalid escape sequences
    repaired = _repair_invalid_json_escapes(json_str)

    # Try parsing directly
    parsed = _try_parse_json(repaired)
    if parsed is not None:
        return repaired

    # If direct parsing fails, try escaping unescaped quotes
    escaped = _escape_unescaped_quotes_in_strings(repaired)

    # Try parsing the escaped version
    parsed = _try_parse_json(escaped)
    if parsed is not None:
        return escaped

    # Return the escaped version as last resort (might work with more aggressive repair)
    return escaped


def safe_json_loads(json_str: str) -> dict:
    """
    Safely parse JSON with multiple fallback strategies for malformed LLM output.
    Returns parsed dict or raises ValueError with helpful error message.
    """
    if not json_str:
        raise ValueError("JSON string is empty")

    # Try direct parsing first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Try with unescaped quote escaping
    repaired = _repair_invalid_json_escapes(json_str)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Try escaping unescaped quotes in strings
    escaped = _escape_unescaped_quotes_in_strings(repaired)
    try:
        return json.loads(escaped)
    except json.JSONDecodeError:
        pass

    # If all else fails, raise with the most repaired version for debugging
    raise ValueError(f"Failed to parse JSON. First 200 chars: {escaped[:200]}")


# Alias for backward compatibility
def extract_json_from_llm_response_old(response: str) -> str:
    """Original function for reference."""
    json_str = response.strip()

    # Remove markdown code blocks with various formats
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    elif json_str.startswith("```"):
        json_str = json_str[3:]

    if json_str.endswith("```"):
        json_str = json_str[:-3]

    json_str = json_str.strip()

    start_idx = json_str.find("{")
    end_idx = json_str.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = json_str[start_idx:end_idx + 1]

    return _repair_invalid_json_escapes(json_str)
