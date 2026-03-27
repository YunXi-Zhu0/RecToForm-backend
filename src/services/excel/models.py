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
    export_field_ids: List[str]
    default_header_labels: Dict[str, str]
    excel_mappings: Dict[str, ExcelFieldMapping]
    output_dir: Path
    output_filename: str = ""


@dataclass(frozen=True)
class StandardExcelWriteRequest:
    structured_data: StructuredInvoiceData
    standard_fields: List[str]
    output_dir: Path
    output_filename: str = ""
    sheet_name: str = "Sheet1"


@dataclass(frozen=True)
class TableExcelWriteRequest:
    headers: List[str]
    rows: List[List[str]]
    output_dir: Path
    output_filename: str = ""
    sheet_name: str = "Sheet1"


@dataclass(frozen=True)
class ExcelWriteResult:
    output_file_path: Path
    written_fields: List[str]
    skipped_fields: List[str]
    missing_mappings: List[str]
