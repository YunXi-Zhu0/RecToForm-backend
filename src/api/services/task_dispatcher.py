import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.core.config import API_UPLOAD_DIR, MAX_FILE_SIZE_MB, MAX_UPLOAD_FILES
from src.services.document import DocumentService
from src.services.workflow import (
    BatchWorkflowFileInput,
    BatchWorkflowService,
    BatchWorkflowRequest,
    WorkflowStatus,
)

from src.api.services.queue import QueueDispatchError, QueueGateway, create_default_queue
from src.api.services.result_builder import ResultBuilder
from src.api.services.task_repository import TaskFileRecord, TaskRecord, TaskRepository


class TaskValidationError(ValueError):
    pass


class DuplicateUploadError(TaskValidationError):
    def __init__(self, duplicate_files: List[str]) -> None:
        self.duplicate_files = list(duplicate_files)
        super().__init__(
            "Duplicate files are not allowed: %s" % ", ".join(self.duplicate_files)
        )


@dataclass(frozen=True)
class TaskCreateConfig:
    mode: str
    template_id: str = ""
    template_version: str = ""
    extra_instructions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PreparedUploadFile:
    file_name: str
    file_bytes: bytes
    size: int
    content_hash: str


class TaskDispatcher:
    def __init__(
        self,
        repository: Optional[TaskRepository] = None,
        queue_gateway: Optional[QueueGateway] = None,
        batch_workflow_service: Optional[BatchWorkflowService] = None,
        result_builder: Optional[ResultBuilder] = None,
        upload_dir: Optional[Path] = None,
    ) -> None:
        self.repository = repository or TaskRepository()
        self.queue_gateway = queue_gateway or create_default_queue()
        self.batch_workflow_service = batch_workflow_service or BatchWorkflowService()
        self.result_builder = result_builder or ResultBuilder()
        self.upload_dir = Path(upload_dir or API_UPLOAD_DIR)
        self.document_service = DocumentService()

    async def create_task(self, config: TaskCreateConfig, uploaded_files: List[object]) -> TaskRecord:
        self._validate_task_config(config)
        self._validate_uploaded_files(uploaded_files)
        prepared_files = await self._prepare_uploaded_files(uploaded_files)

        task_id = uuid.uuid4().hex
        file_records = self._persist_uploaded_files(task_id=task_id, prepared_files=prepared_files)
        record = self.repository.create_task(
            task_id=task_id,
            mode=config.mode,
            input_files=file_records,
            template_id=config.template_id,
            template_version=config.template_version,
            extra_instructions=config.extra_instructions,
        )

        try:
            self.queue_gateway.enqueue(task_id)
        except Exception as exc:
            self.repository.update_task(
                task_id,
                status=WorkflowStatus.FAILED.value,
                stage=WorkflowStatus.FAILED.value,
                error_message=str(exc),
            )
            if isinstance(exc, QueueDispatchError):
                raise
            raise QueueDispatchError(str(exc))
        return self.repository.get_task(task_id)

    def process_task(self, task_id: str) -> TaskRecord:
        task = self.repository.get_task(task_id)
        self.repository.update_task(
            task_id,
            status=WorkflowStatus.RUNNING.value,
            stage=WorkflowStatus.RUNNING.value,
            error_message="",
        )

        batch_request = BatchWorkflowRequest(
            task_id=task.task_id,
            mode=task.mode,
            template_id=task.template_id or None,
            template_version=task.template_version or None,
            extra_instructions=list(task.extra_instructions),
            files=[
                BatchWorkflowFileInput(
                    file_id=item.file_id,
                    file_name=item.file_name,
                    input_file_path=item.file_path,
                )
                for item in task.input_files
            ],
        )

        async def _progress_callback(
            stage: WorkflowStatus,
            processed_files: int,
            succeeded_files: int,
            failed_files: int,
        ) -> None:
            self.repository.update_task(
                task_id,
                status=WorkflowStatus.RUNNING.value,
                stage=stage.value,
                processed_files=processed_files,
                succeeded_files=succeeded_files,
                failed_files=failed_files,
                progress_percent=self._calculate_progress(task.total_files, processed_files),
            )

        async def _file_result_callback(file_result) -> None:
            current = self.repository.get_task(task_id)
            current_file = next(
                item for item in current.input_files if item.file_id == file_result.file_id
            )
            self.repository.replace_file_record(
                task_id,
                TaskFileRecord(
                    file_id=current_file.file_id,
                    file_name=current_file.file_name,
                    file_path=current_file.file_path,
                    size=current_file.size,
                    status=file_result.status.value,
                    structured_data=dict(file_result.structured_data),
                    audit_file_path=file_result.audit_file_path,
                    excel_output_path=file_result.excel_output_path,
                    error_message=file_result.error_message,
                ),
            )

        try:
            batch_result = asyncio.run(
                self.batch_workflow_service.run(
                    request=batch_request,
                    progress_callback=_progress_callback,
                    file_result_callback=_file_result_callback,
                )
            )
            latest_task = self.repository.get_task(task_id)
            if task.mode == "template" and batch_result.succeeded_files > 0:
                self.repository.update_task(
                    task_id,
                    status=WorkflowStatus.RUNNING.value,
                    stage=WorkflowStatus.EXCEL_GENERATING.value,
                    progress_percent=100,
                )
                latest_task = self.repository.get_task(task_id)

            result_payload = self.result_builder.build_task_result(latest_task)
            result_payload_path = self.repository.save_result_payload(task_id, result_payload)
            final_status = batch_result.status.value
            final_stage = final_status
            updated = self.repository.update_task(
                task_id,
                status=final_status,
                stage=final_stage,
                processed_files=batch_result.processed_files,
                succeeded_files=batch_result.succeeded_files,
                failed_files=batch_result.failed_files,
                progress_percent=100,
                result_payload_path=result_payload_path,
                excel_output_path=str(result_payload.get("excel_output_path", "")),
                error_message="",
            )
            return updated
        except Exception as exc:
            latest_task = self.repository.get_task(task_id)
            fallback_payload = {
                "task_id": latest_task.task_id,
                "mode": latest_task.mode,
                "status": WorkflowStatus.FAILED.value,
                "failed_items": [
                    {
                        "file_id": item.file_id,
                        "file_name": item.file_name,
                        "error_message": item.error_message or str(exc),
                    }
                    for item in latest_task.input_files
                ],
            }
            result_payload_path = self.repository.save_result_payload(task_id, fallback_payload)
            return self.repository.update_task(
                task_id,
                status=WorkflowStatus.FAILED.value,
                stage=WorkflowStatus.FAILED.value,
                processed_files=latest_task.processed_files,
                succeeded_files=latest_task.succeeded_files,
                failed_files=latest_task.failed_files or latest_task.total_files,
                progress_percent=100,
                result_payload_path=result_payload_path,
                error_message=str(exc),
            )

    async def _prepare_uploaded_files(
        self,
        uploaded_files: List[object],
    ) -> List[PreparedUploadFile]:
        prepared_files: List[PreparedUploadFile] = []

        for uploaded_file in uploaded_files:
            file_name = self._normalize_filename(getattr(uploaded_file, "filename", "") or "")
            file_bytes = await uploaded_file.read()
            size = len(file_bytes)
            self._validate_file_size(size=size, file_name=file_name)
            self._validate_file_type(file_name=file_name)
            prepared_files.append(
                PreparedUploadFile(
                    file_name=file_name,
                    file_bytes=file_bytes,
                    size=size,
                    content_hash=hashlib.sha256(file_bytes).hexdigest(),
                )
            )

        duplicate_files = self._collect_duplicate_files(prepared_files)
        if duplicate_files:
            raise DuplicateUploadError(duplicate_files)

        return prepared_files

    def _persist_uploaded_files(
        self,
        task_id: str,
        prepared_files: List[PreparedUploadFile],
    ) -> List[TaskFileRecord]:
        target_dir = self.upload_dir / task_id
        target_dir.mkdir(parents=True, exist_ok=True)
        records: List[TaskFileRecord] = []

        for index, prepared_file in enumerate(prepared_files, start=1):
            output_path = target_dir / ("%02d_%s" % (index, prepared_file.file_name))
            output_path.write_bytes(prepared_file.file_bytes)
            records.append(
                TaskFileRecord(
                    file_id="file-%03d" % index,
                    file_name=prepared_file.file_name,
                    file_path=str(output_path),
                    size=prepared_file.size,
                )
            )
        return records

    def _validate_task_config(self, config: TaskCreateConfig) -> None:
        if config.mode not in {"template", "standard_edit"}:
            raise TaskValidationError("Unsupported mode: %s" % config.mode)
        if config.mode == "template" and not config.template_id:
            raise TaskValidationError("template mode requires template_id.")
        if config.mode == "standard_edit" and config.template_id:
            raise TaskValidationError("standard_edit mode does not accept template_id.")

    def _validate_uploaded_files(self, uploaded_files: List[object]) -> None:
        if not uploaded_files:
            raise TaskValidationError("At least one file is required.")
        if len(uploaded_files) > MAX_UPLOAD_FILES:
            raise TaskValidationError(
                "Too many files. Maximum allowed: %s" % MAX_UPLOAD_FILES
            )
        for item in uploaded_files:
            if not getattr(item, "filename", ""):
                raise TaskValidationError("Uploaded file must include a filename.")

    def _validate_file_type(self, file_name: str) -> None:
        file_type = self.document_service.detect_file_type(Path(file_name))
        if file_type == "unknown":
            raise TaskValidationError("Unsupported file type: %s" % file_name)

    def _validate_file_size(self, size: int, file_name: str) -> None:
        if size <= 0:
            raise TaskValidationError("Uploaded file is empty: %s" % file_name)
        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise TaskValidationError(
                "Uploaded file exceeds %sMB: %s" % (MAX_FILE_SIZE_MB, file_name)
            )

    def _normalize_filename(self, file_name: str) -> str:
        normalized = Path(file_name).name.strip()
        if not normalized:
            raise TaskValidationError("Uploaded file must include a filename.")
        return normalized

    def _collect_duplicate_files(
        self,
        prepared_files: List[PreparedUploadFile],
    ) -> List[str]:
        duplicates_by_hash = {}
        for item in prepared_files:
            duplicates_by_hash.setdefault(item.content_hash, []).append(item.file_name)

        duplicate_files: List[str] = []
        seen_names = set()
        for file_names in duplicates_by_hash.values():
            if len(file_names) < 2:
                continue
            for file_name in file_names:
                if file_name in seen_names:
                    continue
                duplicate_files.append(file_name)
                seen_names.add(file_name)
        return duplicate_files

    def _calculate_progress(self, total_files: int, processed_files: int) -> int:
        if total_files <= 0:
            return 0
        return int((processed_files / total_files) * 100)


def parse_task_config(raw_config: str) -> TaskCreateConfig:
    try:
        payload = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise TaskValidationError("config must be valid JSON.") from exc

    raw_extra_instructions = payload.get("extra_instructions", [])
    if not isinstance(raw_extra_instructions, list):
        raise TaskValidationError("extra_instructions must be a list.")

    return TaskCreateConfig(
        mode=str(payload.get("mode", "")),
        template_id=str(payload.get("template_id", "")),
        template_version=str(payload.get("template_version", "")),
        extra_instructions=[
            str(item) for item in raw_extra_instructions if str(item).strip()
        ],
    )


def process_task_job(task_id: str) -> None:
    dispatcher = TaskDispatcher()
    dispatcher.process_task(task_id)
