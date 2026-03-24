import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from src.core.config import DEFAULT_AUDIT_DIR, DEFAULT_OUTPUT_DIR
from src.services.document import DocumentService
from src.services.excel import ExcelService, ExcelWriteRequest, StructuredInvoiceData
from src.services.llm import LLMService, PromptContext, PromptFieldSet
from src.services.template import TemplateService
from src.services.workflow.models import (
    WorkflowAuditRecord,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
)


class WorkflowService:
    def __init__(
        self,
        template_service: Optional[TemplateService] = None,
        excel_service: Optional[ExcelService] = None,
        document_service: Optional[DocumentService] = None,
        llm_service: Optional[LLMService] = None,
        output_dir: Optional[Path] = None,
        audit_dir: Optional[Path] = None,
    ) -> None:
        self.template_service = template_service or TemplateService()
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
        prompt_context = None
        document_result = None

        try:
            document_result = self.document_service.parse(
                input_file_path=Path(request.input_file_path),
                task_id=request.task_id,
            )
            template_bundle = self.template_service.get_template_bundle(
                template_id=request.template_id,
                template_version=request.template_version,
                selected_optional_field_ids=request.selected_optional_field_ids,
            )
            status_history.append(WorkflowStatus.TEMPLATE_READY.value)

            prompt_context = PromptContext(
                template_id=template_bundle.template_id,
                template_name=template_bundle.template_name,
                file_type=document_result.file_type.upper(),
                page_indices=document_result.page_indices,
                fields=PromptFieldSet(
                    default_fields=template_bundle.default_fields,
                    optional_fields=template_bundle.optional_fields,
                ),
                extra_instructions=request.extra_instructions,
                json_example={field_id: "" for field_id in template_bundle.target_fields},
            )
            status_history.append(WorkflowStatus.PROMPT_READY.value)
            status_history.append(WorkflowStatus.LLM_PROCESSING.value)

            llm_result = await self.llm_service.extract_structured_data(
                image_paths=document_result.image_paths,
                context=prompt_context,
            )
            structured_data = self.excel_service.build_structured_invoice_data(
                result=llm_result,
                target_fields=template_bundle.target_fields,
            )
            status_history.append(WorkflowStatus.JSON_VALIDATED.value)
            status_history.append(WorkflowStatus.EXCEL_GENERATING.value)

            excel_result = self.excel_service.write(
                ExcelWriteRequest(
                    template_id=template_bundle.template_id,
                    template_version=template_bundle.template_version,
                    mapping_version=template_bundle.mapping_version,
                    excel_template_path=template_bundle.excel_template_path,
                    structured_data=structured_data,
                    target_fields=template_bundle.target_fields,
                    default_fields=template_bundle.default_fields,
                    optional_fields=template_bundle.optional_fields,
                    field_definitions=template_bundle.field_definitions,
                    excel_mappings=template_bundle.excel_mappings,
                    all_excel_mappings=template_bundle.all_excel_mappings,
                    output_dir=self.output_dir / "excel",
                    output_filename="%s_%s.xlsx" % (request.task_id, template_bundle.template_id),
                )
            )
            excel_output_path = str(excel_result.output_file_path)

            self._persist_audit(
                audit_file_path=audit_file_path,
                record=WorkflowAuditRecord(
                    task_id=request.task_id,
                    input_file_path=request.input_file_path,
                    template_snapshot={
                        "template_id": template_bundle.template_id,
                        "template_name": template_bundle.template_name,
                        "template_version": template_bundle.template_version,
                        "mapping_version": template_bundle.mapping_version,
                        "excel_template_path": str(template_bundle.excel_template_path),
                    },
                    target_fields=template_bundle.target_fields,
                    prompt_context=asdict(prompt_context),
                    llm_raw_text=llm_result.raw_text,
                    llm_cleaned_json=structured_data.data,
                    excel_output_path=excel_output_path,
                    document_manifest=document_result.manifest.to_dict(),
                    status_history=status_history + [WorkflowStatus.AUDIT_PERSISTED.value, WorkflowStatus.SUCCEEDED.value],
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
                        "template_id": template_bundle.template_id if template_bundle else request.template_id,
                        "template_version": template_bundle.template_version if template_bundle else request.template_version or "",
                    },
                    target_fields=template_bundle.target_fields if template_bundle else [],
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
