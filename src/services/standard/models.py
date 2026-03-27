from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class StandardJsonSchema:
    keys: List[str] = field(default_factory=list)
    required_keys: List[str] = field(default_factory=list)
    default_missing_value: str = ""
    version: str = "v1"

    def is_known_key(self, key: str) -> bool:
        return key in self.keys
