from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.services.excel.models import StructuredInvoiceData


class WorkflowStatus(str, Enum):
    CREATED = "created"
    TEMPLATE_READY = "template_ready"
    PROMPT_READY = "prompt_ready"
    LLM_PROCESSING = "llm_processing"
    JSON_VALIDATED = "json_validated"
    EXCEL_GENERATING = "excel_generating"
    AUDIT_PERSISTED = "audit_persisted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowRequest:
    task_id: str
    input_file_path: str
    template_id: str
    template_version: Optional[str] = None
    selected_optional_field_ids: List[str] = field(default_factory=list)
    extra_instructions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowAuditRecord:
    task_id: str
    input_file_path: str
    template_snapshot: Dict[str, Any]
    target_fields: List[str]
    prompt_context: Dict[str, Any]
    llm_raw_text: str
    llm_cleaned_json: Dict[str, Any]
    excel_output_path: str
    document_manifest: Dict[str, Any]
    status_history: List[str]
    error_info: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowResult:
    task_id: str
    status: WorkflowStatus
    structured_data: StructuredInvoiceData
    excel_output_path: str
    audit_file_path: str
