import json
import re
from typing import Any, Dict, List, Optional, Tuple

from src.services.llm.models import StructuredExtractionResult


def parse_structured_output(
    raw_text: str,
    standard_fields: List[str],
    missing_value: str = "",
) -> StructuredExtractionResult:
    cleaned_text = extract_json_object(raw_text)
    parsed = json.loads(cleaned_text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output must be a JSON object.")

    normalized, extra_fields, missing_fields = normalize_fields(
        parsed,
        standard_fields=standard_fields,
        missing_value=missing_value,
    )
    return StructuredExtractionResult(
        data=normalized,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        extra_fields=extra_fields,
        missing_fields=missing_fields,
    )


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    candidates = [text]
    if fenced_match:
        candidates.insert(0, fenced_match.group(1).strip())

    for candidate in candidates:
        extracted = _extract_first_json_object(candidate)
        if extracted is not None:
            return extracted

    raise ValueError("No JSON object found in LLM output.")


def _extract_first_json_object(text: str) -> Optional[str]:
    decoder = json.JSONDecoder()

    for start_index, char in enumerate(text):
        if char != "{":
            continue

        try:
            parsed, end_index = decoder.raw_decode(text[start_index:])
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            return text[start_index : start_index + end_index].strip()

    return None


def normalize_fields(
    parsed: Dict[str, Any],
    standard_fields: List[str],
    missing_value: str = "",
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    normalized: Dict[str, Any] = {}
    extra_fields = [field_name for field_name in parsed.keys() if field_name not in standard_fields]
    missing_fields: List[str] = []

    for field_name in standard_fields:
        value = parsed.get(field_name, missing_value)
        normalized[field_name] = normalize_value(value, missing_value=missing_value)
        if field_name not in parsed:
            missing_fields.append(field_name)

    return normalized, extra_fields, missing_fields


def normalize_value(value: Any, missing_value: str = "") -> Any:
    if value is None:
        return missing_value
    if isinstance(value, str):
        return value.strip()
    return value
