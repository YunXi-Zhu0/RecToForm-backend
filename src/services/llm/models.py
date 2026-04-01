from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PromptContext:
    template_id: str
    template_name: str
    file_type: str
    page_indices: List[int] = field(default_factory=list)
    standard_fields: List[str] = field(default_factory=list)
    schema_version: str = "v1"
    recommended_output_fields: List[str] = field(default_factory=list)
    missing_value: str = ""
    extra_instructions: List[str] = field(default_factory=list)
    json_example: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class StructuredExtractionResult:
    data: Dict[str, Any]
    raw_text: str
    cleaned_text: str
    extra_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
