import asyncio
from pathlib import Path

from src.services.llm.models import StructuredExtractionResult
from src.services.workflow import WorkflowRequest, WorkflowService, WorkflowStatus


class StubLLMService:
    async def extract_structured_data(self, image_paths, context):
        return StructuredExtractionResult(
            data={
                "serial_no": "1",
                "invoice_number": "INV-20260323",
                "invoice_code": "INV-20260323",
                "invoice_amount": "88.00",
                "remark": "tmp.png",
                "invoice_date": "2026-03-23",
            },
            raw_text='{"serial_no":"1"}',
            cleaned_text='{"serial_no":"1"}',
            missing_fields=[],
            extra_fields=[],
        )


def test_workflow_run_generates_excel_and_audit(tmp_path: Path) -> None:
    service = WorkflowService(
        llm_service=StubLLMService(),
        output_dir=tmp_path / "outputs",
        audit_dir=tmp_path / "audits",
    )

    result = asyncio.run(
        service.run(
            WorkflowRequest(
                task_id="task-001",
                input_file_path="tests/fixtures/invoices/tmp.png",
                template_id="finance_invoice",
                selected_optional_field_ids=["invoice_date"],
            )
        )
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert Path(result.excel_output_path).is_file()
    assert Path(result.audit_file_path).is_file()
    assert result.structured_data.data["invoice_number"] == "INV-20260323"
