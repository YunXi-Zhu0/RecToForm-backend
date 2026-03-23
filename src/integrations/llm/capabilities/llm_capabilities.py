from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMCapabilities:
    supports_vision: bool = False
    supports_system_prompt: bool = True
    supports_json_output: bool = False
    supports_stream: bool = False
    supports_tools: bool = False
    max_image_count: Optional[int] = None
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
