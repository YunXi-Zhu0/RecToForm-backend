import asyncio
import json
from pathlib import Path
from unittest.mock import patch

from src.services.excel.models import StructuredInvoiceData
from src.services.llm.models import StructuredExtractionResult
from src.services.workflow import WorkflowRequest, WorkflowService, WorkflowStatus


class StubLLMService:
    def __init__(self) -> None:
        self.last_context = None

    async def extract_structured_data(self, image_paths, context):
        self.last_context = context
        return StructuredExtractionResult(
            data={
                "发票代码": "CODE-20260323",
                "发票号码": "INV-20260323",
                "开票日期": "2026-03-23",
                "购买方名称": "",
                "购买方纳税人识别号": "",
                "购买方地址电话": "",
                "购买方开户行及账号": "",
                "货物或应税劳务、服务名称": "",
                "规格型号": "",
                "单位": "",
                "数量": "",
                "单价": "",
                "金额": "",
                "税率": "",
                "税额": "",
                "合计": "88.00",
                "价税合计(大写)": "",
                "销售方名称": "",
                "销售方纳税人识别号": "",
                "销售方地址电话": "",
                "销售方开户行及账号": "",
                "收款人": "",
                "复核": "",
                "开票人": "",
                "销售方": "",
                "备注": "tmp.png",
            },
            raw_text='{"发票号码":"INV-20260323"}',
            cleaned_text='{"发票号码":"INV-20260323"}',
            missing_fields=[],
            extra_fields=[],
        )


class StubExcelService:
    def build_structured_invoice_data(self, result, standard_fields):
        normalized = {field_name: str(result.data.get(field_name, "")) for field_name in standard_fields}
        return StructuredInvoiceData(
            data=normalized,
            missing_fields=[],
            extra_fields=list(result.extra_fields),
        )

    def write(self, request):
        output_path = request.output_dir / request.output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("template", encoding="utf-8")
        return type("WriteResult", (), {"output_file_path": output_path})()

    def write_standard_fields(self, request):
        output_path = request.output_dir / request.output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("standard_fields", encoding="utf-8")
        return type("WriteResult", (), {"output_file_path": output_path})()


def _create_input_image(tmp_path: Path) -> Path:
    input_path = tmp_path / "input.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake-image")
    return input_path


def test_workflow_run_generates_excel_and_audit(tmp_path: Path) -> None:
    llm_service = StubLLMService()
    service = WorkflowService(
        llm_service=llm_service,
        excel_service=StubExcelService(),
        output_dir=tmp_path / "outputs",
        audit_dir=tmp_path / "audits",
    )

    result = asyncio.run(
        service.run(
            WorkflowRequest(
                task_id="task-001",
                input_file_path=str(_create_input_image(tmp_path)),
                template_id="finance_invoice",
            )
        )
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert Path(result.excel_output_path).is_file()
    assert Path(result.audit_file_path).is_file()
    assert result.structured_data.data["发票号码"] == "INV-20260323"
    assert llm_service.last_context.extra_instructions == [
        "金额字段保留票面原始格式。",
        "备注字段保留票面原始内容，不要补充解释。",
    ]

    audit_payload = json.loads(Path(result.audit_file_path).read_text(encoding="utf-8"))
    assert audit_payload["llm_cleaned_json"]["发票号码"] == "INV-20260323"
    assert audit_payload["standard_fields"][0] == "发票代码"
    assert "json_validated" in audit_payload["status_history"]


def test_workflow_run_without_template_exports_standard_fields(tmp_path: Path) -> None:
    llm_service = StubLLMService()
    service = WorkflowService(
        llm_service=llm_service,
        excel_service=StubExcelService(),
        output_dir=tmp_path / "outputs",
        audit_dir=tmp_path / "audits",
    )

    result = asyncio.run(
        service.run(
            WorkflowRequest(
                task_id="task-002",
                input_file_path=str(_create_input_image(tmp_path)),
            )
        )
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert Path(result.excel_output_path).is_file()
    audit_payload = json.loads(Path(result.audit_file_path).read_text(encoding="utf-8"))
    assert audit_payload["template_snapshot"]["export_mode"] == "standard_fields"
    assert audit_payload["export_fields"][0] == "发票代码"
    assert audit_payload["prompt_context"]["template_id"] == "standard_fields_default"
    assert llm_service.last_context.extra_instructions == []


def test_workflow_prefers_request_extra_instructions_over_template_defaults(tmp_path: Path) -> None:
    llm_service = StubLLMService()
    service = WorkflowService(
        llm_service=llm_service,
        excel_service=StubExcelService(),
        output_dir=tmp_path / "outputs",
        audit_dir=tmp_path / "audits",
    )

    asyncio.run(
        service.run(
            WorkflowRequest(
                task_id="task-003",
                input_file_path=str(_create_input_image(tmp_path)),
                template_id="finance_invoice",
                extra_instructions=["优先使用用户自定义附加要求。"],
            )
        )
    )

    assert llm_service.last_context.extra_instructions == ["优先使用用户自定义附加要求。"]


def test_workflow_uses_system_default_extra_instructions_when_no_request_or_template(tmp_path: Path) -> None:
    llm_service = StubLLMService()
    service = WorkflowService(
        llm_service=llm_service,
        excel_service=StubExcelService(),
        output_dir=tmp_path / "outputs",
        audit_dir=tmp_path / "audits",
    )

    with patch(
        "src.services.workflow.service.DEFAULT_EXTRA_INSTRUCTIONS",
        ["保留原票面日期格式。", "缺失字段返回空字符串。"],
    ):
        asyncio.run(
            service.run(
                WorkflowRequest(
                    task_id="task-004",
                    input_file_path=str(_create_input_image(tmp_path)),
                )
            )
        )

    assert llm_service.last_context.extra_instructions == [
        "保留原票面日期格式。",
        "缺失字段返回空字符串。",
    ]
