from pathlib import Path
from shutil import copyfile
from typing import Iterable, Optional

from openpyxl import load_workbook

from src.core.config import DEFAULT_MISSING_VALUE, DEFAULT_OUTPUT_DIR
from src.services.excel.models import ExcelWriteRequest, ExcelWriteResult, StructuredInvoiceData
from src.services.llm.models import StructuredExtractionResult


class ExcelWriteError(ValueError):
    pass


class ExcelService:
    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)

    def write(self, request: ExcelWriteRequest) -> ExcelWriteResult:
        self._validate_request(request)
        request.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = request.output_dir / self._resolve_output_filename(request)
        copyfile(request.excel_template_path, output_path)

        workbook = load_workbook(output_path)
        written_fields = []
        for field_id in request.target_fields:
            mapping = request.excel_mappings.get(field_id)
            if mapping is None:
                continue
            value = request.structured_data.data.get(field_id, DEFAULT_MISSING_VALUE)
            workbook[mapping.sheet_name][mapping.cell] = value
            written_fields.append(field_id)

        workbook.save(output_path)
        missing_mappings = [
            field_id for field_id in request.target_fields if field_id not in request.excel_mappings
        ]
        skipped_fields = [field_id for field_id in request.target_fields if field_id not in written_fields]
        return ExcelWriteResult(
            output_file_path=output_path,
            written_fields=written_fields,
            skipped_fields=skipped_fields,
            missing_mappings=missing_mappings,
        )

    def build_structured_invoice_data(
        self,
        result: StructuredExtractionResult,
        target_fields: Iterable[str],
    ) -> StructuredInvoiceData:
        normalized = {
            field_id: str(result.data.get(field_id, DEFAULT_MISSING_VALUE) or DEFAULT_MISSING_VALUE)
            for field_id in target_fields
        }
        missing_fields = [
            field_id for field_id in target_fields if normalized[field_id] == DEFAULT_MISSING_VALUE
        ]
        return StructuredInvoiceData(
            data=normalized,
            missing_fields=missing_fields,
            extra_fields=list(result.extra_fields),
        )

    def _validate_request(self, request: ExcelWriteRequest) -> None:
        if not request.excel_template_path.is_file():
            raise ExcelWriteError("Excel template file not found: %s" % request.excel_template_path)
        workbook = load_workbook(request.excel_template_path, read_only=True)
        sheet_names = set(workbook.sheetnames)
        workbook.close()
        for field_id in request.target_fields:
            mapping = request.excel_mappings.get(field_id)
            if mapping is None:
                continue
            if mapping.sheet_name not in sheet_names:
                raise ExcelWriteError(
                    "Worksheet not found for field %s: %s" % (field_id, mapping.sheet_name)
                )

    def _resolve_output_filename(self, request: ExcelWriteRequest) -> str:
        if request.output_filename:
            return request.output_filename
        stem = request.excel_template_path.stem
        suffix = request.excel_template_path.suffix or ".xlsx"
        return "%s_%s%s" % (stem, request.template_id, suffix)
