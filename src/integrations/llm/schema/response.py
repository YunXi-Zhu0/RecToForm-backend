from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LLMUsage:
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class LLMResponse:
    provider_name: str
    model_name: str
    raw_response: Any
    parsed_text: str
    finish_reason: Optional[str] = None
    usage: LLMUsage = field(default_factory=LLMUsage)
    metadata: Dict[str, Any] = field(default_factory=dict)
