import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from src.core.config import DEFAULT_AUDIT_DIR, DEFAULT_OUTPUT_DIR
from src.services.document import DocumentService
from src.services.excel import (
    ExcelService,
    ExcelWriteRequest,
    StandardExcelWriteRequest,
    StructuredInvoiceData,
)
from src.services.llm import LLMService, PromptContext
from src.services.standard import StandardSchemaService
from src.services.template import TemplateService
from src.services.workflow.models import (
    WorkflowAuditRecord,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
)

DEFAULT_EXTRA_INSTRUCTIONS: List[str] = []


class WorkflowService:
    DEFAULT_STANDARD_EXPORT_TEMPLATE_ID = "standard_fields_default"
    DEFAULT_STANDARD_EXPORT_TEMPLATE_NAME = "标准字段直出"

    def __init__(
        self,
        template_service: Optional[TemplateService] = None,
        excel_service: Optional[ExcelService] = None,
        document_service: Optional[DocumentService] = None,
        llm_service: Optional[LLMService] = None,
        standard_schema_service: Optional[StandardSchemaService] = None,
        output_dir: Optional[Path] = None,
        audit_dir: Optional[Path] = None,
    ) -> None:
        self.standard_schema_service = standard_schema_service or StandardSchemaService()
        self.template_service = template_service or TemplateService(
            standard_schema_service=self.standard_schema_service
        )
        self.excel_service = excel_service or ExcelService()
        self.document_service = document_service or DocumentService()
        self.llm_service = llm_service or LLMService()
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        self.audit_dir = Path(audit_dir or DEFAULT_AUDIT_DIR)

    async def run(self, request: WorkflowRequest) -> WorkflowResult:
        status_history: List[str] = [WorkflowStatus.CREATED.value]
        llm_result = None
        structured_data = StructuredInvoiceData(data={})
        excel_output_path = ""
        audit_file_path = self.audit_dir / ("%s.json" % request.task_id)
        template_bundle = None
        standard_schema = None
        prompt_context = None
        document_result = None

        try:
            status_history.append(WorkflowStatus.RUNNING.value)
            status_history.append(WorkflowStatus.FILE_PREPROCESSING.value)
            document_result = self.document_service.parse(
                input_file_path=Path(request.input_file_path),
                task_id=request.task_id,
            )
            standard_schema = self.standard_schema_service.load_schema()
            if request.template_id:
                template_bundle = self.template_service.get_template_bundle(
                    template_id=request.template_id,
                    template_version=request.template_version,
                )
                status_history.append(WorkflowStatus.TEMPLATE_READY.value)

            prompt_context = PromptContext(
                template_id=(
                    template_bundle.template_id
                    if template_bundle
                    else self.DEFAULT_STANDARD_EXPORT_TEMPLATE_ID
                ),
                template_name=(
                    template_bundle.template_name
                    if template_bundle
                    else self.DEFAULT_STANDARD_EXPORT_TEMPLATE_NAME
                ),
                file_type=document_result.file_type.upper(),
                page_indices=document_result.page_indices,
                standard_fields=list(standard_schema.keys),
                schema_version=standard_schema.version,
                recommended_output_fields=(
                    template_bundle.recommended_field_ids
                    if template_bundle
                    else list(standard_schema.keys)
                ),
                missing_value=standard_schema.default_missing_value,
                extra_instructions=self._resolve_extra_instructions(
                    request_extra_instructions=request.extra_instructions,
                    template_extra_instructions=(
                        template_bundle.default_extra_instructions if template_bundle else []
                    ),
                ),
                json_example={
                    field_id: standard_schema.default_missing_value
                    for field_id in standard_schema.keys
                },
            )
            status_history.append(WorkflowStatus.PROMPT_READY.value)
            status_history.append(WorkflowStatus.LLM_PROCESSING.value)

            llm_result = await self.llm_service.extract_structured_data(
                image_paths=document_result.image_paths,
                context=prompt_context,
            )
            structured_data = self.excel_service.build_structured_invoice_data(
                result=llm_result,
                standard_fields=standard_schema.keys,
            )
            status_history.append(WorkflowStatus.JSON_VALIDATED.value)
            status_history.append(WorkflowStatus.EXCEL_GENERATING.value)

            if template_bundle:
                excel_result = self.excel_service.write(
                    ExcelWriteRequest(
                        template_id=template_bundle.template_id,
                        template_version=template_bundle.template_version,
                        mapping_version=template_bundle.mapping_version,
                        excel_template_path=template_bundle.excel_template_path,
                        structured_data=structured_data,
                        export_field_ids=template_bundle.recommended_field_ids,
                        default_header_labels=template_bundle.default_header_labels,
                        excel_mappings=template_bundle.excel_mappings,
                        output_dir=self.output_dir / "excel",
                        output_filename="%s_%s.xlsx" % (request.task_id, template_bundle.template_id),
                    )
                )
            else:
                excel_result = self.excel_service.write_standard_fields(
                    StandardExcelWriteRequest(
                        structured_data=structured_data,
                        standard_fields=list(standard_schema.keys),
                        output_dir=self.output_dir / "excel",
                        output_filename="%s_standard_fields.xlsx" % request.task_id,
                        source_file_name=request.source_file_name or Path(request.input_file_path).name,
                    )
                )
            excel_output_path = str(excel_result.output_file_path)

            self._persist_audit(
                audit_file_path=audit_file_path,
                record=WorkflowAuditRecord(
                    task_id=request.task_id,
                    input_file_path=request.input_file_path,
                    template_snapshot={
                        "template_id": (
                            template_bundle.template_id
                            if template_bundle
                            else self.DEFAULT_STANDARD_EXPORT_TEMPLATE_ID
                        ),
                        "template_name": (
                            template_bundle.template_name
                            if template_bundle
                            else self.DEFAULT_STANDARD_EXPORT_TEMPLATE_NAME
                        ),
                        "template_version": template_bundle.template_version if template_bundle else "",
                        "mapping_version": template_bundle.mapping_version if template_bundle else "",
                        "excel_template_path": (
                            str(template_bundle.excel_template_path) if template_bundle else ""
                        ),
                        "export_mode": "template" if template_bundle else "standard_fields",
                        "recommended_field_ids": (
                            template_bundle.recommended_field_ids
                            if template_bundle
                            else list(standard_schema.keys)
                        ),
                        "referenced_standard_fields": (
                            template_bundle.referenced_standard_fields
                            if template_bundle
                            else list(standard_schema.keys)
                        ),
                    },
                    standard_fields=list(standard_schema.keys),
                    export_fields=(
                        template_bundle.recommended_field_ids
                        if template_bundle
                        else list(standard_schema.keys)
                    ),
                    prompt_context=asdict(prompt_context),
                    llm_raw_text=llm_result.raw_text,
                    llm_cleaned_json=structured_data.data,
                    excel_output_path=excel_output_path,
                    document_manifest=document_result.manifest.to_dict(),
                    status_history=status_history
                    + [WorkflowStatus.AUDIT_PERSISTED.value, WorkflowStatus.SUCCEEDED.value],
                ),
            )
            return WorkflowResult(
                task_id=request.task_id,
                status=WorkflowStatus.SUCCEEDED,
                structured_data=structured_data,
                excel_output_path=excel_output_path,
                audit_file_path=str(audit_file_path),
            )
        except Exception as exc:
            status_history.append(WorkflowStatus.FAILED.value)
            self._persist_audit(
                audit_file_path=audit_file_path,
                record=WorkflowAuditRecord(
                    task_id=request.task_id,
                    input_file_path=request.input_file_path,
                    template_snapshot={
                        "template_id": (
                            template_bundle.template_id
                            if template_bundle
                            else request.template_id or self.DEFAULT_STANDARD_EXPORT_TEMPLATE_ID
                        ),
                        "template_version": template_bundle.template_version if template_bundle else request.template_version or "",
                        "export_mode": "template" if template_bundle else "standard_fields",
                    },
                    standard_fields=list(standard_schema.keys) if standard_schema else [],
                    export_fields=(
                        template_bundle.recommended_field_ids
                        if template_bundle
                        else list(standard_schema.keys) if standard_schema else []
                    ),
                    prompt_context=asdict(prompt_context) if prompt_context else {},
                    llm_raw_text=llm_result.raw_text if llm_result else "",
                    llm_cleaned_json=structured_data.data,
                    excel_output_path=excel_output_path,
                    document_manifest=document_result.manifest.to_dict() if document_result else {},
                    status_history=status_history,
                    error_info={
                        "message": str(exc),
                        "type": exc.__class__.__name__,
                        "traceback": traceback.format_exc(),
                    },
                ),
            )
            raise

    def _persist_audit(self, audit_file_path: Path, record: WorkflowAuditRecord) -> None:
        audit_file_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_file_path.open("w", encoding="utf-8") as file:
            json.dump(record.to_dict(), file, ensure_ascii=False, indent=2)

    def _resolve_extra_instructions(
        self,
        request_extra_instructions: List[str],
        template_extra_instructions: List[str],
    ) -> List[str]:
        if request_extra_instructions:
            return list(request_extra_instructions)
        if template_extra_instructions:
            return list(template_extra_instructions)
        return list(DEFAULT_EXTRA_INSTRUCTIONS)
