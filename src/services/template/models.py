from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class TemplateFieldDefinition:
    field_id: str
    field_label: str
    description: str = ""
    required: bool = False
    example_value: str = ""
    value_type: str = "string"
    source_hint: str = ""
    default_value: str = ""


@dataclass(frozen=True)
class TemplateDefinition:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
    excel_template_path: Path
    default_field_ids: List[str] = field(default_factory=list)
    optional_field_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExcelFieldMapping:
    template_id: str
    template_version: str
    mapping_version: str
    field_id: str
    sheet_name: str
    cell: str
    write_mode: str = "overwrite"


@dataclass(frozen=True)
class TemplateBundle:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
    excel_template_path: Path
    field_definitions: Dict[str, TemplateFieldDefinition]
    default_fields: List[str]
    optional_fields: List[str]
    target_fields: List[str]
    excel_mappings: Dict[str, ExcelFieldMapping]


@dataclass(frozen=True)
class TemplateSummary:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
