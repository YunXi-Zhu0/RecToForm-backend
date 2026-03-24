from pathlib import Path

from openpyxl import load_workbook

from src.services.excel import ExcelService, ExcelWriteRequest, StructuredInvoiceData
from src.services.template import TemplateService


def test_write_populates_template_cells(tmp_path: Path) -> None:
    template_bundle = TemplateService().get_template_bundle("finance_invoice")
    excel_service = ExcelService()
    structured_data = StructuredInvoiceData(
        data={
            "serial_no": "1",
            "invoice_number": "INV-001",
            "invoice_code": "CODE-001",
            "invoice_amount": "199.00",
            "remark": "invoice.png",
        },
        missing_fields=[],
        extra_fields=[],
    )

    result = excel_service.write(
        ExcelWriteRequest(
            template_id=template_bundle.template_id,
            template_version=template_bundle.template_version,
            mapping_version=template_bundle.mapping_version,
            excel_template_path=template_bundle.excel_template_path,
            structured_data=structured_data,
            target_fields=template_bundle.target_fields,
            default_fields=template_bundle.default_fields,
            optional_fields=template_bundle.optional_fields,
            field_definitions=template_bundle.field_definitions,
            excel_mappings=template_bundle.excel_mappings,
            all_excel_mappings=template_bundle.all_excel_mappings,
            output_dir=tmp_path,
            output_filename="filled.xlsx",
        )
    )

    workbook = load_workbook(result.output_file_path)
    sheet = workbook["Sheet1"]
    assert sheet["A2"].value == "1"
    assert sheet["B2"].value == "INV-001"
    assert sheet["E2"].value == "invoice.png"
    assert sheet["F1"].value in (None, "")
    assert sheet["G1"].value in (None, "")
    assert sheet["H1"].value in (None, "")
    assert result.missing_mappings == []


def test_selected_optional_fields_render_headers(tmp_path: Path) -> None:
    template_bundle = TemplateService().get_template_bundle(
        "finance_invoice",
        selected_optional_field_ids=["invoice_date", "seller_name"],
    )
    excel_service = ExcelService()
    structured_data = StructuredInvoiceData(
        data={field_id: "" for field_id in template_bundle.target_fields},
        missing_fields=list(template_bundle.target_fields),
        extra_fields=[],
    )

    result = excel_service.write(
        ExcelWriteRequest(
            template_id=template_bundle.template_id,
            template_version=template_bundle.template_version,
            mapping_version=template_bundle.mapping_version,
            excel_template_path=template_bundle.excel_template_path,
            structured_data=structured_data,
            target_fields=template_bundle.target_fields,
            default_fields=template_bundle.default_fields,
            optional_fields=template_bundle.optional_fields,
            field_definitions=template_bundle.field_definitions,
            excel_mappings=template_bundle.excel_mappings,
            all_excel_mappings=template_bundle.all_excel_mappings,
            output_dir=tmp_path,
            output_filename="filled_optional.xlsx",
        )
    )

    workbook = load_workbook(result.output_file_path)
    sheet = workbook["Sheet1"]
    assert sheet["F1"].value == "开票日期"
    assert sheet["G1"].value == "销售方"
    assert sheet["H1"].value in (None, "")
