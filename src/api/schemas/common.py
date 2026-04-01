from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class TaskMode(str, Enum):
    TEMPLATE = "template"
    STANDARD_EDIT = "standard_edit"


class HealthResponse(BaseModel):
    status: str = "ok"


class FailedItemResponse(BaseModel):
    file_id: str
    file_name: str
    error_message: str = ""


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")


class FileProgressResponse(BaseModel):
    file_id: str
    file_name: str
    status: str


class RowsPreviewResponse(BaseModel):
    headers: List[str]
    rows: List[List[str]]
