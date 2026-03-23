from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class UploadedFileMeta:
    file_name: str
    file_path: str
    content_type: str
    size: int


@dataclass(frozen=True)
class PageImageItem:
    page_index: int
    image_path: str
    source_type: str


@dataclass(frozen=True)
class DocumentManifest:
    source_file_path: str
    file_type: str
    page_images: List[PageImageItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentParseResult:
    file_type: str
    image_paths: List[str]
    page_indices: List[int]
    manifest: DocumentManifest
    uploaded_file: UploadedFileMeta
