from pathlib import Path

from src.api.services.result_builder import ResultBuilder
from src.api.services.task_repository import TaskFileRecord, TaskRecord
from src.services.excel import ExcelService
from src.services.standard import StandardSchemaService
from src.services.template import TemplateService


def test_result_builder_builds_template_preview_and_excel(tmp_path: Path) -> None:
    builder = ResultBuilder(
        template_service=TemplateService(),
        standard_schema_service=StandardSchemaService(),
        excel_service=ExcelService(output_dir=tmp_path / "outputs"),
        export_dir=tmp_path / "exports",
    )
    task = TaskRecord(
        task_id="task-template",
        mode="template",
        status="succeeded",
        stage="succeeded",
        total_files=2,
        processed_files=2,
        succeeded_files=2,
        failed_files=0,
        progress_percent=100,
        template_id="finance_invoice",
        template_version="v1",
        input_files=[
            TaskFileRecord(
                file_id="file-001",
                file_name="a.png",
                file_path="/tmp/a.png",
                size=1,
                status="succeeded",
                structured_data={
                    "发票号码": "INV-001",
                    "发票代码": "CODE-001",
                    "合计": "88.00",
                    "备注": "A",
                },
            ),
            TaskFileRecord(
                file_id="file-002",
                file_name="b.png",
                file_path="/tmp/b.png",
                size=1,
                status="succeeded",
                structured_data={
                    "发票号码": "INV-002",
                    "发票代码": "CODE-002",
                    "合计": "99.00",
                    "备注": "B",
                },
            ),
        ],
    )

    payload = builder.build_task_result(task)

    assert payload["preview_headers"] == ["序号", "发票号码", "发票代码", "发票金额", "备注"]
    assert payload["preview_rows"][0] == ["1", "INV-001", "CODE-001", "88.00", "A"]
    assert payload["preview_rows"][1] == ["2", "INV-002", "CODE-002", "99.00", "B"]
    assert Path(payload["excel_output_path"]).is_file()


def test_result_builder_builds_standard_edit_rows(tmp_path: Path) -> None:
    builder = ResultBuilder(export_dir=tmp_path / "exports")
    task = TaskRecord(
        task_id="task-standard",
        mode="standard_edit",
        status="partially_succeeded",
        stage="partially_succeeded",
        total_files=2,
        processed_files=2,
        succeeded_files=1,
        failed_files=1,
        progress_percent=100,
        input_files=[
            TaskFileRecord(
                file_id="file-001",
                file_name="a.png",
                file_path="/tmp/a.png",
                size=1,
                status="succeeded",
                structured_data={
                    "发票代码": "CODE-001",
                    "发票号码": "INV-001",
                },
            ),
            TaskFileRecord(
                file_id="file-002",
                file_name="b.png",
                file_path="/tmp/b.png",
                size=1,
                status="failed",
                error_message="parse failed",
            ),
        ],
    )

    payload = builder.build_task_result(task)

    assert payload["status"] == "partially_succeeded"
    assert payload["standard_fields"][0] == "发票代码"
    assert payload["rows"][0][0] == "CODE-001"
    assert payload["rows"][0][1] == "INV-001"
    assert payload["failed_items"][0]["file_name"] == "b.png"
