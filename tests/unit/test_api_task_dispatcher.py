import asyncio
from pathlib import Path

from src.api.services import InlineQueueGateway
from src.api.services.task_dispatcher import TaskCreateConfig, TaskDispatcher, parse_task_config
from src.api.services.task_repository import TaskRepository
from src.services.workflow import (
    BatchWorkflowFileResult,
    BatchWorkflowResult,
    WorkflowStatus,
)


class FakeUploadFile:
    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


class StubBatchWorkflowService:
    async def run(self, request, progress_callback=None, file_result_callback=None):
        await progress_callback(WorkflowStatus.FILE_PREPROCESSING, 0, 0, 0)
        success_result = BatchWorkflowFileResult(
            file_id=request.files[0].file_id,
            file_name=request.files[0].file_name,
            status=WorkflowStatus.SUCCEEDED,
            structured_data={"发票代码": "CODE-001", "发票号码": "INV-001"},
            excel_output_path="/tmp/file.xlsx",
            audit_file_path="/tmp/file.json",
        )
        failed_result = BatchWorkflowFileResult(
            file_id=request.files[1].file_id,
            file_name=request.files[1].file_name,
            status=WorkflowStatus.FAILED,
            error_message="parse failed",
        )
        await file_result_callback(success_result)
        await progress_callback(WorkflowStatus.LLM_PROCESSING, 1, 1, 0)
        await file_result_callback(failed_result)
        await progress_callback(WorkflowStatus.LLM_PROCESSING, 2, 1, 1)
        await progress_callback(WorkflowStatus.ASSEMBLING_RESULTS, 2, 1, 1)
        return BatchWorkflowResult(
            task_id=request.task_id,
            mode=request.mode,
            status=WorkflowStatus.PARTIALLY_SUCCEEDED,
            stage=WorkflowStatus.ASSEMBLING_RESULTS,
            total_files=2,
            processed_files=2,
            succeeded_files=1,
            failed_files=1,
            file_results=[success_result, failed_result],
        )


class StubResultBuilder:
    def build_task_result(self, task):
        return {
            "task_id": task.task_id,
            "mode": task.mode,
            "status": "partially_succeeded",
            "standard_fields": ["发票代码", "发票号码"],
            "rows": [["CODE-001", "INV-001"]],
            "failed_items": [{"file_id": "file-002", "file_name": "b.png", "error_message": "parse failed"}],
            "excel_output_path": "",
        }


def test_parse_task_config_accepts_standard_edit() -> None:
    config = parse_task_config('{"mode":"standard_edit","extra_instructions":["keep table order"]}')

    assert config.mode == "standard_edit"
    assert config.extra_instructions == ["keep table order"]


def test_task_dispatcher_creates_and_processes_task(tmp_path: Path) -> None:
    repository = TaskRepository(storage_dir=tmp_path / "tasks")
    dispatcher = TaskDispatcher(
        repository=repository,
        queue_gateway=InlineQueueGateway(lambda task_id: None),
        batch_workflow_service=StubBatchWorkflowService(),
        result_builder=StubResultBuilder(),
        upload_dir=tmp_path / "uploads",
    )

    created = asyncio.run(
        dispatcher.create_task(
            TaskCreateConfig(mode="standard_edit"),
            [
                FakeUploadFile("a.png", b"image-a"),
                FakeUploadFile("b.png", b"image-b"),
            ],
        )
    )
    finished = dispatcher.process_task(created.task_id)

    assert finished.status == "partially_succeeded"
    assert finished.processed_files == 2
    assert finished.succeeded_files == 1
    assert finished.failed_files == 1
    payload = repository.load_result_payload(created.task_id)
    assert payload["rows"] == [["CODE-001", "INV-001"]]
    task = repository.get_task(created.task_id)
    assert task.input_files[0].structured_data["发票号码"] == "INV-001"
    assert task.input_files[1].error_message == "parse failed"
