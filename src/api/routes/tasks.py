from pathlib import Path
from typing import List, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from src.api.dependencies import get_task_dispatcher, get_task_repository
from src.api.schemas import (
    StandardEditTaskResultResponse,
    TaskCreateResponse,
    TaskStatusResponse,
    TemplateTaskResultResponse,
)
from src.api.services import (
    QueueDispatchError,
    TaskDispatcher,
    TaskNotFoundError,
    TaskRepository,
    TaskValidationError,
    parse_task_config,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    config: str = Form(...),
    files: List[UploadFile] = File(...),
    dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
) -> TaskCreateResponse:
    try:
        task_config = parse_task_config(config)
        task = await dispatcher.create_task(task_config, list(files))
    except TaskValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except QueueDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return TaskCreateResponse(
        task_id=task.task_id,
        status=task.status,
        mode=task.mode,
        total_files=task.total_files,
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    repository: TaskRepository = Depends(get_task_repository),
) -> TaskStatusResponse:
    try:
        task = repository.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return TaskStatusResponse(
        task_id=task.task_id,
        mode=task.mode,
        status=task.status,
        stage=task.stage,
        total_files=task.total_files,
        processed_files=task.processed_files,
        succeeded_files=task.succeeded_files,
        failed_files=task.failed_files,
        progress_percent=task.progress_percent,
        error_message=task.error_message,
    )


@router.get(
    "/{task_id}/result",
    response_model=Union[TemplateTaskResultResponse, StandardEditTaskResultResponse],
)
def get_task_result(
    task_id: str,
    request: Request,
    repository: TaskRepository = Depends(get_task_repository),
) -> Union[TemplateTaskResultResponse, StandardEditTaskResultResponse]:
    try:
        task = repository.get_task(task_id)
        payload = repository.load_result_payload(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if task.status not in {"succeeded", "partially_succeeded", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task result is not ready yet.",
        )

    if task.mode == "template":
        excel_download_url = ""
        if payload.get("excel_output_path"):
            excel_download_url = str(request.url_for("download_task_excel", task_id=task_id))
        return TemplateTaskResultResponse(
            task_id=str(payload["task_id"]),
            mode=str(payload["mode"]),
            status=str(payload["status"]),
            preview_headers=list(payload.get("preview_headers", [])),
            preview_rows=[list(row) for row in payload.get("preview_rows", [])],
            excel_download_url=excel_download_url,
            failed_items=list(payload.get("failed_items", [])),
        )

    return StandardEditTaskResultResponse(
        task_id=str(payload["task_id"]),
        mode=str(payload["mode"]),
        status=str(payload["status"]),
        standard_fields=list(payload.get("standard_fields", [])),
        rows=[list(row) for row in payload.get("rows", [])],
        failed_items=list(payload.get("failed_items", [])),
    )


@router.get("/{task_id}/excel", name="download_task_excel")
def download_task_excel(
    task_id: str,
    repository: TaskRepository = Depends(get_task_repository),
) -> FileResponse:
    try:
        task = repository.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if task.mode != "template" or not task.excel_output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excel export is not available for this task.",
        )

    excel_path = Path(task.excel_output_path)
    if not excel_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Excel file not found.")

    return FileResponse(
        path=excel_path,
        filename=excel_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
