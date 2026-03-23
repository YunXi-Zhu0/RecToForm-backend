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

    with pytest.raises(DocumentProcessingError, match="PyMuPDF or pypdfium2"):
        service.parse(PDF_FIXTURE, task_id="pdf-case")
