from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.services.excel.models import StructuredInvoiceData


class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    FILE_PREPROCESSING = "file_preprocessing"
    TEMPLATE_READY = "template_ready"
    PROMPT_READY = "prompt_ready"
    LLM_PROCESSING = "llm_processing"
    JSON_VALIDATED = "json_validated"
    ASSEMBLING_RESULTS = "assembling_results"
    EXCEL_GENERATING = "excel_generating"
    AUDIT_PERSISTED = "audit_persisted"
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowRequest:
    task_id: str
    input_file_path: str
    source_file_name: str = ""
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    extra_instructions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowAuditRecord:
    task_id: str
    input_file_path: str
    template_snapshot: Dict[str, Any]
    standard_fields: List[str]
    export_fields: List[str]
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


@dataclass(frozen=True)
class BatchWorkflowFileInput:
    file_id: str
    file_name: str
    input_file_path: str


@dataclass(frozen=True)
class BatchWorkflowRequest:
    task_id: str
    mode: str
    files: List[BatchWorkflowFileInput]
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    extra_instructions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatchWorkflowFileResult:
    file_id: str
    file_name: str
    status: WorkflowStatus
    structured_data: Dict[str, str] = field(default_factory=dict)
    excel_output_path: str = ""
    audit_file_path: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BatchWorkflowResult:
    task_id: str
    mode: str
    status: WorkflowStatus
    stage: WorkflowStatus
    total_files: int
    processed_files: int
    succeeded_files: int
    failed_files: int
    file_results: List[BatchWorkflowFileResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
