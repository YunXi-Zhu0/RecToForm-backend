from pathlib import Path

from src.services.workflow import WorkflowRequest, WorkflowService


async def run_workflow_service(
        path: Path,
        template_id: str,
        template_version: str,
        selected_optional_field_ids: list[str],
        extra_instructions: list[str],
        task_id: str = "real-run-001",
):
    service = WorkflowService()

    result = await service.run(
        WorkflowRequest(
            task_id=task_id,
            input_file_path=str(path),
            template_id=template_id,
            template_version=template_version,
            selected_optional_field_ids=selected_optional_field_ids,
            extra_instructions=extra_instructions,
        )
    )

    print("task_id:", result.task_id)
    print("status:", result.status.value)
    print("excel_output_path:", result.excel_output_path)
    print("audit_file_path:", result.audit_file_path)
    print("structured_data:", result.structured_data.data)


if __name__ == "__main__":
    import asyncio
    from src.core.config import TESTS_DIR

    path = TESTS_DIR / "fixtures" / "invoices" / "汽油25.pdf"
    template_id = "finance_invoice"
    template_version = "v1"
    selected_optional_field_ids = [
        "invoice_date",
        "seller_name",
        "buyer_name",
    ]
    extra_instructions = [
        "Return valid JSON only.",
        "Keep the original amount format from the invoice.",
        "Use an empty string for missing fields.",
    ]

    asyncio.run(
        run_workflow_service(
            path=path,
            template_id=template_id,
            template_version=template_version,
            selected_optional_field_ids=selected_optional_field_ids,
            extra_instructions=extra_instructions,
        )
    )
