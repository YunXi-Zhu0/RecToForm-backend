import asyncio

from src.services.excel.models import StructuredInvoiceData
from src.services.workflow import (
    BatchWorkflowFileInput,
    BatchWorkflowRequest,
    BatchWorkflowService,
    WorkflowResult,
    WorkflowStatus,
)


class StubWorkflowService:
    def __init__(self) -> None:
        self.requests = []

    async def run(self, request):
        self.requests.append(request)
        if request.input_file_path.endswith("bad.png"):
            raise ValueError("llm failed")
        return WorkflowResult(
            task_id=request.task_id,
            status=WorkflowStatus.SUCCEEDED,
            structured_data=StructuredInvoiceData(
                data={
                    "发票号码": "INV-%s" % request.task_id,
                    "备注": request.input_file_path,
                }
            ),
            excel_output_path="/tmp/%s.xlsx" % request.task_id,
            audit_file_path="/tmp/%s.json" % request.task_id,
        )


def test_batch_workflow_service_returns_partial_success() -> None:
    stages = []
    workflow_service = StubWorkflowService()

    async def progress_callback(stage, processed_files, succeeded_files, failed_files):
        stages.append((stage.value, processed_files, succeeded_files, failed_files))

    service = BatchWorkflowService(workflow_service=workflow_service, concurrency=2)
    result = asyncio.run(
        service.run(
            BatchWorkflowRequest(
                task_id="task-001",
                mode="standard_edit",
                files=[
                    BatchWorkflowFileInput(
                        file_id="file-001",
                        file_name="ok.png",
                        input_file_path="ok.png",
                    ),
                    BatchWorkflowFileInput(
                        file_id="file-002",
                        file_name="bad.png",
                        input_file_path="bad.png",
                    ),
                ],
            ),
            progress_callback=progress_callback,
        )
    )

    assert result.status == WorkflowStatus.PARTIALLY_SUCCEEDED
    assert result.processed_files == 2
    assert result.succeeded_files == 1
    assert result.failed_files == 1
    assert result.file_results[0].file_name == "bad.png"
    assert result.file_results[1].structured_data["发票号码"].startswith("INV-task-001")
    assert stages[0][0] == "file_preprocessing"
    assert stages[-1][0] == "assembling_results"
    assert sorted(request.source_file_name for request in workflow_service.requests) == ["bad.png", "ok.png"]
