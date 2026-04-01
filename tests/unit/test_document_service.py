from pathlib import Path

import pytest

from src.services.document import DocumentProcessingError, DocumentService


FIXTURES = Path("tests/fixtures/invoices")
PDF_FIXTURE = next(FIXTURES.glob("*.pdf"))


def test_parse_image_returns_manifest() -> None:
    service = DocumentService()

    result = service.parse(FIXTURES / "tmp.png", task_id="image-case")

    assert result.file_type == "image"
    assert result.page_indices == [1]
    assert result.manifest.page_images[0].source_type == "image"


def test_parse_pdf_without_backend_raises_clear_error() -> None:
    service = DocumentService()
    service._resolve_pdf_renderer = lambda: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        DocumentProcessingError("PDF processing requires PyMuPDF or pypdfium2 to be installed.")
    )

    with pytest.raises(DocumentProcessingError, match="PyMuPDF or pypdfium2"):
        service.parse(PDF_FIXTURE, task_id="pdf-case")


def test_parse_pdf_enhances_rendered_images_in_place(tmp_path: Path) -> None:
    service = DocumentService(output_dir=tmp_path)
    rendered_page = tmp_path / "page_001.png"
    rendered_page.write_bytes((FIXTURES / "tmp.png").read_bytes())
    service._resolve_pdf_renderer = lambda: (  # type: ignore[attr-defined]
        lambda _path, _output_dir: [rendered_page]
    )

    result = service.parse(PDF_FIXTURE, task_id="pdf-enhanced-case")

    assert result.file_type == "pdf"
    assert result.image_paths[0].endswith("page_001.png")
    assert Path(result.image_paths[0]).is_file()
    assert result.manifest.page_images[0].image_path.endswith("page_001.png")
