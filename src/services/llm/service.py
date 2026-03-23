from typing import Any, Dict, Optional, Sequence

from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.factory.llm_factory import get_llm_provider
from src.integrations.llm.schema.request import ImagePath, LLMRequest
from src.integrations.llm.schema.response import LLMResponse
from src.services.llm.json_parser import parse_structured_output
from src.services.llm.models import PromptContext, StructuredExtractionResult
from src.services.llm.prompt_builder import build_system_prompt, build_user_prompt


class LLMService:
    def __init__(self, provider_name: Optional[str] = None) -> None:
        self.provider_name = provider_name

    def build_prompts(self, context: PromptContext) -> Dict[str, str]:
        return {
            "system_prompt": build_system_prompt(context),
            "user_prompt": build_user_prompt(context),
        }

    def parse_json_result(
        self,
        raw_text: str,
        context: PromptContext,
    ) -> StructuredExtractionResult:
        return parse_structured_output(
            raw_text=raw_text,
            target_fields=context.fields.target_fields,
            missing_value=context.missing_value,
        )

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

    async def extract_structured_data(
        self,
        image_paths: Sequence[ImagePath],
        context: PromptContext,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> StructuredExtractionResult:
        prompts = self.build_prompts(context)
        llm_response = await self.analyze_images(
            image_paths=image_paths,
            user_prompt=prompts["user_prompt"],
            system_prompt=prompts["system_prompt"],
            response_format=response_format or {"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self.parse_json_result(
            raw_text=llm_response.parsed_text,
            context=context,
        )
