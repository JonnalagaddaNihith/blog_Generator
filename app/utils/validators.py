from pydantic import validator
from typing import Optional


def validate_word_count(value: Optional[int]) -> Optional[int]:
    if value is not None and (value < 100 or value > 10000):
        raise ValueError("Word count must be between 100 and 10000")
    return value


def validate_url(value: Optional[str]) -> Optional[str]:
    if value:
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
    return value
