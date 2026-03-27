from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies import get_export_file_registry, get_result_builder
from src.api.services import ExportFileRegistry, ResultBuilder


class FakeExportFileRegistry(ExportFileRegistry):
    def __init__(self) -> None:
        self._mappings = {}
        self._counter = 0

    def register_standard_fields_export(self, filename: str) -> str:
        self._counter += 1
        export_id = "export-%s" % self._counter
        self._mappings[export_id] = filename
        return export_id

    def resolve_standard_fields_export(self, export_id: str):
        return self._mappings.get(export_id)


def test_export_standard_fields_returns_uuid_download_url(tmp_path: Path) -> None:
    app = create_app()
    registry = FakeExportFileRegistry()
    builder = ResultBuilder(export_dir=tmp_path / "exports")
    app.dependency_overrides[get_result_builder] = lambda: builder
    app.dependency_overrides[get_export_file_registry] = lambda: registry

    client = TestClient(app)
    response = client.post(
        "/api/v1/exports/standard-fields",
        json={
            "headers": ["发票代码", "发票号码"],
            "rows": [["CODE-001", "INV-001"]],
            "filename": "custom_export.xlsx",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["export_id"] == "export-1"
    assert payload["filename"] == "custom_export.xlsx"
    assert payload["download_url"].endswith("/api/v1/exports/standard-fields/export-1")
    assert "custom_export.xlsx" not in payload["download_url"]


def test_download_standard_fields_export_resolves_file_by_uuid(tmp_path: Path) -> None:
    app = create_app()
    registry = FakeExportFileRegistry()
    builder = ResultBuilder(export_dir=tmp_path / "exports")
    export_dir = builder.export_dir / "standard_fields"
    export_dir.mkdir(parents=True, exist_ok=True)
    file_path = export_dir / "custom_export.xlsx"
    file_path.write_bytes(b"excel-binary")
    export_id = registry.register_standard_fields_export(file_path.name)
    app.dependency_overrides[get_result_builder] = lambda: builder
    app.dependency_overrides[get_export_file_registry] = lambda: registry

    client = TestClient(app)
    response = client.get("/api/v1/exports/standard-fields/%s" % export_id)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.content == b"excel-binary"
    assert "custom_export.xlsx" in response.headers["content-disposition"]


def test_download_standard_fields_export_returns_404_when_uuid_missing(tmp_path: Path) -> None:
    app = create_app()
    registry = FakeExportFileRegistry()
    builder = ResultBuilder(export_dir=tmp_path / "exports")
    app.dependency_overrides[get_result_builder] = lambda: builder
    app.dependency_overrides[get_export_file_registry] = lambda: registry

    client = TestClient(app)
    response = client.get("/api/v1/exports/standard-fields/export-missing")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Export file not found."
