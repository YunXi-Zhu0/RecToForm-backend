from pathlib import Path
from typing import Optional

from src.services.workflow import WorkflowRequest, WorkflowService


async def run_workflow_service(
    path: Path,
    template_id: Optional[str],
    template_version: Optional[str],
    extra_instructions: list[str],
    task_id: str = "real-run-001",
):
    from src.services.llm import LLMService

    provider_name = "qwen_local_openai_compatible"
    llm_service = LLMService(provider_name=provider_name)


    service = WorkflowService(llm_service=llm_service)

    result = await service.run(
        WorkflowRequest(
            task_id=task_id,
            input_file_path=str(path),
            template_id=template_id,
            template_version=template_version,
            extra_instructions=extra_instructions,
        )
    )

    from pprint import pprint
    pprint(f"task_id: {result.task_id}", indent=4)
    pprint(f"status: {result.status.value}", indent=4)
    pprint(f"excel_output_path: {result.excel_output_path}", indent=4)
    pprint(f"audit_file_path: {result.audit_file_path}", indent=4)
    pprint(f"structured_data: {result.structured_data.data}", indent=4)


if __name__ == "__main__":
    import asyncio

    from src.core.config import TESTS_DIR

    path = TESTS_DIR / "fixtures" / "invoices" / "page_001.png"
    template_id = "finance_invoice"
    template_version = "v1"
    extra_instructions = []

    asyncio.run(
        run_workflow_service(
            path=path,
            template_id=template_id,
            template_version=template_version,
            extra_instructions=extra_instructions,
        )
    )
