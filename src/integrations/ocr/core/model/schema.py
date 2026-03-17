from dataclasses import dataclass
from typing import Dict

@dataclass
class OCRPageResult:
    markdown: str
    images: Dict[str, str] # name -> url
