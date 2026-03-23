from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PromptFieldSet:
    default_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    @property
    def target_fields(self) -> List[str]:
        ordered_fields: List[str] = []
        for field_name in self.default_fields + self.optional_fields:
            if field_name not in ordered_fields:
                ordered_fields.append(field_name)
        return ordered_fields


@dataclass(frozen=True)
class PromptContext:
    template_id: str
    template_name: str
    file_type: str
    page_indices: List[int] = field(default_factory=list)
    fields: PromptFieldSet = field(default_factory=PromptFieldSet)
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
