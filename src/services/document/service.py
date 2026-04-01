import mimetypes
from pathlib import Path
from typing import List, Optional

from src.core.config import (
    DEFAULT_DOCUMENT_OUTPUT_DIR,
    DOCUMENT_IMAGE_AUTOCONTRAST_CUTOFF,
    DOCUMENT_IMAGE_BRIGHTNESS,
    DOCUMENT_IMAGE_CONTRAST,
    DOCUMENT_IMAGE_ENHANCE_ENABLED,
    DOCUMENT_IMAGE_SHARPEN_PERCENT,
    DOCUMENT_IMAGE_SHARPEN_RADIUS,
    DOCUMENT_IMAGE_SHARPEN_THRESHOLD,
)
from src.services.document.models import (
    DocumentManifest,
    DocumentParseResult,
    PageImageItem,
    UploadedFileMeta,
)


class DocumentProcessingError(ValueError):
    pass


class DocumentService:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = Path(output_dir or DEFAULT_DOCUMENT_OUTPUT_DIR)
        self.enhance_images = DOCUMENT_IMAGE_ENHANCE_ENABLED

    def parse(self, input_file_path: Path, task_id: Optional[str] = None) -> DocumentParseResult:
        path = Path(input_file_path)
        if not path.is_file():
            raise FileNotFoundError("Input file not found: %s" % path)

        file_type = self.detect_file_type(path)
        uploaded = UploadedFileMeta(
            file_name=path.name,
            file_path=str(path),
            content_type=mimetypes.guess_type(str(path))[0] or "application/octet-stream",
            size=path.stat().st_size,
        )

        if file_type == "image":
            return self._parse_image(path, uploaded)
        if file_type == "pdf":
            return self._parse_pdf(path, uploaded, task_id=task_id)
        raise DocumentProcessingError("Unsupported file type: %s" % path.suffix)

    def detect_file_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in self.IMAGE_EXTENSIONS:
            return "image"
        if suffix == ".pdf":
            return "pdf"
        return "unknown"

    def _parse_image(self, path: Path, uploaded: UploadedFileMeta) -> DocumentParseResult:
        page_images = [PageImageItem(page_index=1, image_path=str(path), source_type="image")]
        manifest = DocumentManifest(
            source_file_path=str(path),
            file_type="image",
            page_images=page_images,
        )
        return DocumentParseResult(
            file_type="image",
            image_paths=[str(path)],
            page_indices=[1],
            manifest=manifest,
            uploaded_file=uploaded,
        )

    def _parse_pdf(
        self,
        path: Path,
        uploaded: UploadedFileMeta,
        task_id: Optional[str] = None,
    ) -> DocumentParseResult:
        renderer = self._resolve_pdf_renderer()
        output_dir = self.output_dir / (task_id or path.stem)
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered_paths = renderer(path, output_dir)
        self._enhance_rendered_images(rendered_paths)
        page_images = [
            PageImageItem(page_index=index + 1, image_path=str(image_path), source_type="pdf_page")
            for index, image_path in enumerate(rendered_paths)
        ]
        manifest = DocumentManifest(
            source_file_path=str(path),
            file_type="pdf",
            page_images=page_images,
        )
        return DocumentParseResult(
            file_type="pdf",
            image_paths=[item.image_path for item in page_images],
            page_indices=[item.page_index for item in page_images],
            manifest=manifest,
            uploaded_file=uploaded,
        )

    def _enhance_rendered_images(self, rendered_paths: List[Path]) -> None:
        if not self.enhance_images:
            return

        for path in rendered_paths:
            self._enhance_image(path)

    def _enhance_image(self, path: Path) -> Path:
        try:
            from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        except ImportError as exc:  # pragma: no cover - pillow is a project dependency
            raise DocumentProcessingError(
                "Image enhancement requires Pillow to be installed."
            ) from exc

        with Image.open(path) as image:
            processed = image.convert("RGB") if image.mode not in {"RGB", "L"} else image.copy()
            processed = ImageOps.autocontrast(
                processed,
                cutoff=DOCUMENT_IMAGE_AUTOCONTRAST_CUTOFF,
            )
            processed = ImageEnhance.Contrast(processed).enhance(DOCUMENT_IMAGE_CONTRAST)
            processed = ImageEnhance.Brightness(processed).enhance(DOCUMENT_IMAGE_BRIGHTNESS)
            processed = processed.filter(
                ImageFilter.UnsharpMask(
                    radius=DOCUMENT_IMAGE_SHARPEN_RADIUS,
                    percent=DOCUMENT_IMAGE_SHARPEN_PERCENT,
                    threshold=DOCUMENT_IMAGE_SHARPEN_THRESHOLD,
                )
            )
            processed.save(path)
        return path

    def _resolve_pdf_renderer(self):
        try:
            import fitz  # type: ignore

            def _render_with_pymupdf(path: Path, output_dir: Path) -> List[Path]:
                document = fitz.open(path)
                output_paths: List[Path] = []
                try:
                    for index, page in enumerate(document):
                        pixmap = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                        output_path = output_dir / ("page_%03d.png" % (index + 1))
                        pixmap.save(output_path)
                        output_paths.append(output_path)
                finally:
                    document.close()
                return output_paths

            return _render_with_pymupdf
        except ImportError:
            pass

        try:
            import pypdfium2 as pdfium  # type: ignore

            def _render_with_pdfium(path: Path, output_dir: Path) -> List[Path]:
                pdf = pdfium.PdfDocument(str(path))
                output_paths: List[Path] = []
                for index in range(len(pdf)):
                    page = pdf[index]
                    bitmap = page.render(scale=3)
                    image = bitmap.to_pil()
                    output_path = output_dir / ("page_%03d.png" % (index + 1))
                    image.save(output_path)
                    output_paths.append(output_path)
                return output_paths

            return _render_with_pdfium
        except ImportError:
            pass

        raise DocumentProcessingError(
            "PDF processing requires PyMuPDF or pypdfium2 to be installed."
        )
