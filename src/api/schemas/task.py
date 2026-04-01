from typing import List

from pydantic import BaseModel

from src.api.schemas.common import FailedItemResponse


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    mode: str
    total_files: int
    duplicate_files: List[str] = []


class TaskStatusResponse(BaseModel):
    task_id: str
    mode: str
    status: str
    stage: str
    total_files: int
    processed_files: int
    succeeded_files: int
    failed_files: int
    progress_percent: int
    error_message: str = ""


class TemplateTaskResultResponse(BaseModel):
    task_id: str
    mode: str
    status: str
    preview_headers: List[str]
    preview_rows: List[List[str]]
    excel_download_url: str = ""
    failed_items: List[FailedItemResponse]


class StandardEditTaskResultResponse(BaseModel):
    task_id: str
    mode: str
    status: str
    standard_fields: List[str]
    rows: List[List[str]]
    failed_items: List[FailedItemResponse]
