from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class TemplateDefinition:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
    excel_template_path: Path
    recommended_field_ids: List[str] = field(default_factory=list)
    default_header_labels: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExcelFieldMapping:
    template_id: str
    template_version: str
    mapping_version: str
    field_id: str
    sheet_name: str
    cell: str
    write_mode: str = "overwrite"
    value_source: str = "standard"
    source_key: str = ""
    default_value: str = ""


@dataclass(frozen=True)
class TemplateBundle:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
    excel_template_path: Path
    recommended_field_ids: List[str]
    default_header_labels: Dict[str, str]
    excel_mappings: Dict[str, ExcelFieldMapping]
    referenced_standard_fields: List[str]


@dataclass(frozen=True)
class TemplateSummary:
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
