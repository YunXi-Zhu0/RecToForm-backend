import asyncio
import json

import pytest
from fastapi import HTTPException

from src.api.routes.tasks import create_task
from src.api.services.task_dispatcher import DuplicateUploadError
from src.api.services.task_repository import TaskRecord


class FakeUploadFile:
    def __init__(self, filename: str) -> None:
        self.filename = filename


class StubTaskDispatcher:
    def __init__(self, result=None, error: Exception = None) -> None:
        self.result = result
        self.error = error

    async def create_task(self, config, uploaded_files):
        if self.error is not None:
            raise self.error
        return self.result


def test_create_task_route_returns_duplicate_file_names() -> None:
    dispatcher = StubTaskDispatcher(error=DuplicateUploadError(["a.png", "copied.png"]))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            create_task(
                config=json.dumps({"mode": "standard_edit"}),
                files=[FakeUploadFile("a.png"), FakeUploadFile("copied.png")],
                dispatcher=dispatcher,
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "message": "Duplicate files are not allowed.",
        "duplicate_files": ["a.png", "copied.png"],
    }


def test_create_task_route_success_response_contains_empty_duplicate_file_list() -> None:
    dispatcher = StubTaskDispatcher(
        result=TaskRecord(
            task_id="task-001",
            mode="standard_edit",
            status="queued",
            stage="queued",
            total_files=2,
            processed_files=0,
            succeeded_files=0,
            failed_files=0,
            progress_percent=0,
        )
    )

    response = asyncio.run(
        create_task(
            config=json.dumps({"mode": "standard_edit"}),
            files=[FakeUploadFile("a.png"), FakeUploadFile("b.png")],
            dispatcher=dispatcher,
        )
    )

    assert response.task_id == "task-001"
    assert response.total_files == 2
    assert response.duplicate_files == []
