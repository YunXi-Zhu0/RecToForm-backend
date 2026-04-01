from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from src.integrations.llm.schema.message import LLMImageInput, LLMMessage


ImagePath = Union[str, Path]


@dataclass
class LLMRequest:
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    messages: List[LLMMessage] = field(default_factory=list)
    image_inputs: List[LLMImageInput] = field(default_factory=list)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    response_format: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_prompts(
        cls,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[Sequence[ImagePath]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "LLMRequest":
        images = [LLMImageInput.from_path(Path(path)) for path in (image_paths or [])]
        return cls(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_inputs=images,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            metadata=metadata or {},
        )
