from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.factory.llm_factory import get_llm_provider
from src.integrations.llm.schema.request import ImagePath, LLMRequest
from src.integrations.llm.schema.response import LLMResponse


class LLMService:
    def __init__(self, provider_name: Optional[str] = None) -> None:
        self.provider_name = provider_name

    async def analyze_images(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        provider = get_llm_provider(
            provider_name=self.provider_name,
            required_capabilities=LLMCapabilities(
                supports_vision=True,
                supports_system_prompt=bool(system_prompt),
                supports_json_output=bool(response_format),
            ),
        )
        request = LLMRequest.from_prompts(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            image_paths=image_paths,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return await provider.invoke(request)
