import logging
import json
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


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
    
    return json_str

