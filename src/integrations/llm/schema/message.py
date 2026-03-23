from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class LLMImageInput:
    path: Path
    mime_type: str = "image/jpeg"

    @classmethod
    def from_path(cls, value: Path) -> "LLMImageInput":
        return cls(path=Path(value))


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str
    name: Optional[str] = None
