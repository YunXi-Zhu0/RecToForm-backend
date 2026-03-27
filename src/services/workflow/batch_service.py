import asyncio
from typing import Awaitable, Callable, List, Optional

from src.core.config import WORKFLOW_ASYNC_CONCURRENCY
from src.services.workflow.models import (
    BatchWorkflowFileInput,
    BatchWorkflowFileResult,
    BatchWorkflowRequest,
    BatchWorkflowResult,
    WorkflowRequest,
    WorkflowStatus,
)
from src.services.workflow.service import WorkflowService


ProgressCallback = Callable[[WorkflowStatus, int, int, int], Awaitable[None]]
FileResultCallback = Callable[[BatchWorkflowFileResult], Awaitable[None]]


class BatchWorkflowService:
    def __init__(
        self,
        workflow_service: Optional[WorkflowService] = None,
        concurrency: int = WORKFLOW_ASYNC_CONCURRENCY,
    ) -> None:
        self.workflow_service = workflow_service or WorkflowService()
        self.concurrency = max(1, int(concurrency))

    async def run(
        self,
        request: BatchWorkflowRequest,
        progress_callback: Optional[ProgressCallback] = None,
        file_result_callback: Optional[FileResultCallback] = None,
    ) -> BatchWorkflowResult:
        semaphore = asyncio.Semaphore(self.concurrency)
        file_results: List[BatchWorkflowFileResult] = []
        processed_files = 0
        succeeded_files = 0
        failed_files = 0

        if progress_callback is not None:
            await progress_callback(WorkflowStatus.FILE_PREPROCESSING, 0, 0, 0)

        async def _run_single(file_input: BatchWorkflowFileInput) -> BatchWorkflowFileResult:
            async with semaphore:
                workflow_request = WorkflowRequest(
                    task_id="%s_%s" % (request.task_id, file_input.file_id),
                    input_file_path=file_input.input_file_path,
                    template_id=request.template_id if request.mode == "template" else None,
                    template_version=request.template_version if request.mode == "template" else None,
                    extra_instructions=list(request.extra_instructions),
                )
                try:
                    workflow_result = await self.workflow_service.run(workflow_request)
                    return self._build_success_file_result(
                        file_input=file_input,
                        structured_data=dict(workflow_result.structured_data.data),
                        excel_output_path=workflow_result.excel_output_path,
                        audit_file_path=workflow_result.audit_file_path,
                        status=workflow_result.status,
                    )
                except Exception as exc:
                    return BatchWorkflowFileResult(
                        file_id=file_input.file_id,
                        file_name=file_input.file_name,
                        status=WorkflowStatus.FAILED,
                        error_message=str(exc),
                    )

        tasks = [asyncio.create_task(_run_single(file_input)) for file_input in request.files]

        if progress_callback is not None and tasks:
            await progress_callback(WorkflowStatus.LLM_PROCESSING, 0, 0, 0)

        for task in asyncio.as_completed(tasks):
            file_result = await task
            file_results.append(file_result)
            processed_files += 1
            if file_result.status == WorkflowStatus.SUCCEEDED:
                succeeded_files += 1
            else:
                failed_files += 1

            if file_result_callback is not None:
                await file_result_callback(file_result)
            if progress_callback is not None:
                await progress_callback(
                    WorkflowStatus.LLM_PROCESSING,
                    processed_files,
                    succeeded_files,
                    failed_files,
                )

        if progress_callback is not None:
            await progress_callback(
                WorkflowStatus.ASSEMBLING_RESULTS,
                processed_files,
                succeeded_files,
                failed_files,
            )

        final_status = self._resolve_final_status(
            total_files=len(request.files),
            succeeded_files=succeeded_files,
            failed_files=failed_files,
        )
        final_stage = WorkflowStatus.ASSEMBLING_RESULTS
        if final_status in (WorkflowStatus.SUCCEEDED, WorkflowStatus.PARTIALLY_SUCCEEDED):
            final_stage = WorkflowStatus.SUCCEEDED
        if final_status == WorkflowStatus.FAILED:
            final_stage = WorkflowStatus.FAILED

        return BatchWorkflowResult(
            task_id=request.task_id,
            mode=request.mode,
            status=final_status,
            stage=final_stage,
            total_files=len(request.files),
            processed_files=processed_files,
            succeeded_files=succeeded_files,
            failed_files=failed_files,
            file_results=sorted(file_results, key=lambda item: item.file_name),
        )

    def _build_success_file_result(
        self,
        file_input: BatchWorkflowFileInput,
        structured_data: dict,
        excel_output_path: str,
        audit_file_path: str,
        status: WorkflowStatus,
    ) -> BatchWorkflowFileResult:
        return BatchWorkflowFileResult(
            file_id=file_input.file_id,
            file_name=file_input.file_name,
            status=status,
            structured_data=structured_data,
            excel_output_path=excel_output_path,
            audit_file_path=audit_file_path,
        )

    def _resolve_final_status(
        self,
        total_files: int,
        succeeded_files: int,
        failed_files: int,
    ) -> WorkflowStatus:
        if total_files == 0 or failed_files == total_files:
            return WorkflowStatus.FAILED
        if succeeded_files == total_files:
            return WorkflowStatus.SUCCEEDED
        return WorkflowStatus.PARTIALLY_SUCCEEDED
