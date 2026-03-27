from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config import API_EXPORT_DIR, DEFAULT_MISSING_VALUE
from src.services.excel import ExcelService, TableExcelWriteRequest
from src.services.standard import StandardSchemaService
from src.services.template import TemplateService
from src.services.template.models import ExcelFieldMapping, TemplateBundle

from src.api.services.task_repository import TaskFileRecord, TaskRecord


class ResultBuilder:
    def __init__(
        self,
        template_service: Optional[TemplateService] = None,
        standard_schema_service: Optional[StandardSchemaService] = None,
        excel_service: Optional[ExcelService] = None,
        export_dir: Optional[Path] = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
        self.standard_schema_service = standard_schema_service or StandardSchemaService()
        self.excel_service = excel_service or ExcelService()
        self.export_dir = Path(export_dir or API_EXPORT_DIR)

    def build_task_result(self, task: TaskRecord) -> Dict[str, Any]:
        if task.mode == "template":
            return self._build_template_result(task)
        return self._build_standard_edit_result(task)

    def export_custom_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        filename: str,
    ) -> str:
        normalized_filename = self._normalize_filename(filename or "standard_fields_export.xlsx")
        result = self.excel_service.write_table(
            TableExcelWriteRequest(
                headers=list(headers),
                rows=[list(row) for row in rows],
                output_dir=self.export_dir / "standard_fields",
                output_filename=normalized_filename,
            )
        )
        return str(result.output_file_path)

    def _build_standard_edit_result(self, task: TaskRecord) -> Dict[str, Any]:
        schema = self.standard_schema_service.load_schema()
        succeeded_items = self._select_succeeded_files(task.input_files)
        return {
            "task_id": task.task_id,
            "mode": task.mode,
            "status": task.status,
            "standard_fields": list(schema.keys),
            "rows": [
                [item.structured_data.get(field_name, DEFAULT_MISSING_VALUE) for field_name in schema.keys]
                for item in succeeded_items
            ],
            "failed_items": self._build_failed_items(task.input_files),
        }

    def _build_template_result(self, task: TaskRecord) -> Dict[str, Any]:
        bundle = self.template_service.get_template_bundle(
            template_id=task.template_id,
            template_version=task.template_version or None,
        )
        succeeded_items = self._select_succeeded_files(task.input_files)
        preview_headers = [
            bundle.default_header_labels.get(field_id, field_id)
            for field_id in bundle.recommended_field_ids
        ]
        preview_rows = [
            self._build_template_row(
                bundle=bundle,
                structured_data=item.structured_data,
                row_index=index,
            )
            for index, item in enumerate(succeeded_items, start=1)
        ]
        excel_output_path = ""
        if preview_rows:
            excel_result = self.excel_service.write_table(
                TableExcelWriteRequest(
                    headers=preview_headers,
                    rows=preview_rows,
                    output_dir=self.export_dir / task.task_id,
                    output_filename="%s_%s.xlsx" % (task.task_id, task.template_id),
                )
            )
            excel_output_path = str(excel_result.output_file_path)

        return {
            "task_id": task.task_id,
            "mode": task.mode,
            "status": task.status,
            "preview_headers": preview_headers,
            "preview_rows": preview_rows,
            "excel_output_path": excel_output_path,
            "failed_items": self._build_failed_items(task.input_files),
        }

    def _build_template_row(
        self,
        bundle: TemplateBundle,
        structured_data: Dict[str, str],
        row_index: int,
    ) -> List[str]:
        row: List[str] = []
        for field_id in bundle.recommended_field_ids:
            mapping = bundle.excel_mappings[field_id]
            row.append(self._resolve_mapping_value(mapping, structured_data, row_index))
        return row

    def _resolve_mapping_value(
        self,
        mapping: ExcelFieldMapping,
        structured_data: Dict[str, str],
        row_index: int,
    ) -> str:
        if mapping.value_source == "standard":
            return str(
                structured_data.get(mapping.source_key, mapping.default_value)
                or mapping.default_value
                or DEFAULT_MISSING_VALUE
            )
        if mapping.field_id == "序号" and mapping.value_source == "literal":
            return str(row_index)
        return str(mapping.default_value or DEFAULT_MISSING_VALUE)

    def _select_succeeded_files(self, files: List[TaskFileRecord]) -> List[TaskFileRecord]:
        return [item for item in files if item.status == "succeeded"]

    def _build_failed_items(self, files: List[TaskFileRecord]) -> List[Dict[str, str]]:
        return [
            {
                "file_id": item.file_id,
                "file_name": item.file_name,
                "error_message": item.error_message,
            }
            for item in files
            if item.status != "succeeded"
        ]

    def _normalize_filename(self, filename: str) -> str:
        name = filename.strip() or "export.xlsx"
        if not name.lower().endswith(".xlsx"):
            return "%s.xlsx" % name
        return name
