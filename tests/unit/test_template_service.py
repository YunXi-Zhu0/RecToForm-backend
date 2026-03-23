from src.services.template import TemplateService


def test_list_templates_contains_defaults() -> None:
    service = TemplateService()

    templates = service.list_templates()

    assert len(templates) == 2
    assert {item.template_id for item in templates} == {"finance_invoice", "asset_import"}


def test_get_template_bundle_merges_optional_fields_in_order() -> None:
    service = TemplateService()

    bundle = service.get_template_bundle(
        template_id="finance_invoice",
        selected_optional_field_ids=["invoice_date", "seller_name", "invoice_date"],
    )

    assert bundle.default_fields == [
        "serial_no",
        "invoice_number",
        "invoice_code",
        "invoice_amount",
        "remark",
    ]
    assert bundle.optional_fields == ["invoice_date", "seller_name"]
    assert bundle.target_fields == [
        "serial_no",
        "invoice_number",
        "invoice_code",
        "invoice_amount",
        "remark",
        "invoice_date",
        "seller_name",
    ]
    assert bundle.excel_mappings["invoice_number"].cell == "B2"
