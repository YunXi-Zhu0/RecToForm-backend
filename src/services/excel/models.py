from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from src.services.template.models import ExcelFieldMapping


@dataclass(frozen=True)
class StructuredInvoiceData:
    data: Dict[str, str]
    missing_fields: List[str] = field(default_factory=list)
    extra_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExcelWriteRequest:
    template_id: str
    template_version: str
    mapping_version: str
    excel_template_path: Path
    structured_data: StructuredInvoiceData
    target_fields: List[str]
    excel_mappings: Dict[str, ExcelFieldMapping]
    output_dir: Path
    output_filename: str = ""


@dataclass(frozen=True)
class ExcelWriteResult:
    output_file_path: Path
    written_fields: List[str]
    skipped_fields: List[str]
    missing_mappings: List[str]
