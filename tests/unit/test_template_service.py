from src.services.template import TemplateService


def test_list_templates_contains_defaults() -> None:
    service = TemplateService()

    templates = service.list_templates()

    assert len(templates) == 2
    assert {item.template_id for item in templates} == {"finance_invoice", "asset_import"}


def test_get_template_bundle_reads_recommended_export_fields() -> None:
    service = TemplateService()

    bundle = service.get_template_bundle(template_id="finance_invoice")

    assert bundle.recommended_field_ids == [
        "序号",
        "发票号码",
        "发票代码",
        "发票金额",
        "备注",
    ]
    assert bundle.default_header_labels["发票金额"] == "发票金额"
    assert bundle.excel_mappings["发票号码"].cell == "B2"
    assert bundle.excel_mappings["发票金额"].source_key == "合计"
    assert bundle.referenced_standard_fields == ["发票号码", "发票代码", "合计", "备注"]
