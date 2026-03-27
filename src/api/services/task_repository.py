import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config import API_TASK_DIR


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TaskFileRecord:
    file_id: str
    file_name: str
    file_path: str
    size: int
    status: str = "queued"
    structured_data: Dict[str, str] = field(default_factory=dict)
    audit_file_path: str = ""
    excel_output_path: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskFileRecord":
        return cls(
            file_id=str(payload["file_id"]),
            file_name=str(payload["file_name"]),
            file_path=str(payload["file_path"]),
            size=int(payload["size"]),
            status=str(payload.get("status", "queued")),
            structured_data=dict(payload.get("structured_data", {})),
            audit_file_path=str(payload.get("audit_file_path", "")),
            excel_output_path=str(payload.get("excel_output_path", "")),
            error_message=str(payload.get("error_message", "")),
        )


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    mode: str
    status: str
    stage: str
    total_files: int
    processed_files: int
    succeeded_files: int
    failed_files: int
    progress_percent: int
    template_id: str = ""
    template_version: str = ""
    extra_instructions: List[str] = field(default_factory=list)
    input_files: List[TaskFileRecord] = field(default_factory=list)
    result_payload_path: str = ""
    excel_output_path: str = ""
    error_message: str = ""
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["input_files"] = [item.to_dict() for item in self.input_files]
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskRecord":
        return cls(
            task_id=str(payload["task_id"]),
            mode=str(payload["mode"]),
            status=str(payload["status"]),
            stage=str(payload["stage"]),
            total_files=int(payload["total_files"]),
            processed_files=int(payload.get("processed_files", 0)),
            succeeded_files=int(payload.get("succeeded_files", 0)),
            failed_files=int(payload.get("failed_files", 0)),
            progress_percent=int(payload.get("progress_percent", 0)),
            template_id=str(payload.get("template_id", "")),
            template_version=str(payload.get("template_version", "")),
            extra_instructions=list(payload.get("extra_instructions", [])),
            input_files=[
                TaskFileRecord.from_dict(item) for item in payload.get("input_files", [])
            ],
            result_payload_path=str(payload.get("result_payload_path", "")),
            excel_output_path=str(payload.get("excel_output_path", "")),
            error_message=str(payload.get("error_message", "")),
            created_at=str(payload.get("created_at", _utc_now())),
            updated_at=str(payload.get("updated_at", _utc_now())),
        )


class TaskNotFoundError(FileNotFoundError):
    pass


class TaskRepository:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = Path(storage_dir or API_TASK_DIR)

    def create_task(
        self,
        task_id: str,
        mode: str,
        input_files: List[TaskFileRecord],
        template_id: str = "",
        template_version: str = "",
        extra_instructions: Optional[List[str]] = None,
    ) -> TaskRecord:
        record = TaskRecord(
            task_id=task_id,
            mode=mode,
            status="queued",
            stage="queued",
            total_files=len(input_files),
            processed_files=0,
            succeeded_files=0,
            failed_files=0,
            progress_percent=0,
            template_id=template_id,
            template_version=template_version,
            extra_instructions=list(extra_instructions or []),
            input_files=list(input_files),
        )
        self.save_task(record)
        return record

    def get_task(self, task_id: str) -> TaskRecord:
        path = self._resolve_task_path(task_id)
        if not path.is_file():
            raise TaskNotFoundError("Task not found: %s" % task_id)
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return TaskRecord.from_dict(payload)

    def save_task(self, record: TaskRecord) -> TaskRecord:
        path = self._resolve_task_path(record.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.to_dict()
        payload["updated_at"] = _utc_now()
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return TaskRecord.from_dict(payload)

    def update_task(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        processed_files: Optional[int] = None,
        succeeded_files: Optional[int] = None,
        failed_files: Optional[int] = None,
        progress_percent: Optional[int] = None,
        result_payload_path: Optional[str] = None,
        excel_output_path: Optional[str] = None,
        error_message: Optional[str] = None,
        input_files: Optional[List[TaskFileRecord]] = None,
    ) -> TaskRecord:
        current = self.get_task(task_id)
        updated = TaskRecord(
            task_id=current.task_id,
            mode=current.mode,
            status=status or current.status,
            stage=stage or current.stage,
            total_files=current.total_files,
            processed_files=processed_files
            if processed_files is not None
            else current.processed_files,
            succeeded_files=succeeded_files
            if succeeded_files is not None
            else current.succeeded_files,
            failed_files=failed_files if failed_files is not None else current.failed_files,
            progress_percent=progress_percent
            if progress_percent is not None
            else current.progress_percent,
            template_id=current.template_id,
            template_version=current.template_version,
            extra_instructions=list(current.extra_instructions),
            input_files=list(input_files or current.input_files),
            result_payload_path=result_payload_path
            if result_payload_path is not None
            else current.result_payload_path,
            excel_output_path=excel_output_path
            if excel_output_path is not None
            else current.excel_output_path,
            error_message=error_message if error_message is not None else current.error_message,
            created_at=current.created_at,
            updated_at=_utc_now(),
        )
        return self.save_task(updated)

    def replace_file_record(self, task_id: str, file_record: TaskFileRecord) -> TaskRecord:
        current = self.get_task(task_id)
        updated_files = [
            file_record if item.file_id == file_record.file_id else item for item in current.input_files
        ]
        return self.update_task(task_id, input_files=updated_files)

    def save_result_payload(self, task_id: str, payload: Dict[str, Any]) -> str:
        task_dir = self.storage_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        payload_path = task_dir / "result.json"
        with payload_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        self.update_task(task_id, result_payload_path=str(payload_path))
        return str(payload_path)

    def load_result_payload(self, task_id: str) -> Dict[str, Any]:
        task = self.get_task(task_id)
        if not task.result_payload_path:
            raise TaskNotFoundError("Task result payload not found: %s" % task_id)
        path = Path(task.result_payload_path)
        if not path.is_file():
            raise TaskNotFoundError("Task result payload not found: %s" % task.result_payload_path)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _resolve_task_path(self, task_id: str) -> Path:
        return self.storage_dir / ("%s.json" % task_id)
