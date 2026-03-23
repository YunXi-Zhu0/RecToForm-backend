from typing import Optional, Sequence

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - defer hard failure to runtime construction
    AsyncOpenAI = None

from src.core.config import QWEN3_MAX_MODEL
from src.integrations.llm.base.llm import BaseLLMProvider
from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.schema.request import ImagePath, LLMRequest
from src.integrations.llm.schema.response import LLMResponse, LLMUsage


class QwenOfficialProvider(BaseLLMProvider):
    provider_name = "qwen_official"

    def __init__(self) -> None:
        if AsyncOpenAI is None:
            raise ImportError("openai package is required for qwen_official provider.")
        self.model_name = QWEN3_MAX_MODEL["MODEL_NAME"]
        self.temperature = QWEN3_MAX_MODEL["TEMPERATURE"]
        self.max_tokens = QWEN3_MAX_MODEL["MAX_TOKENS"]
        self.client = AsyncOpenAI(
            api_key=QWEN3_MAX_MODEL["API_KEY"],
            base_url=QWEN3_MAX_MODEL["BASE_URL"],
        )

    def get_capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_vision=False,
            supports_system_prompt=True,
            supports_json_output=True,
        )

    async def invoke(self, request: LLMRequest) -> LLMResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        if request.messages:
            messages.extend(
                {"role": item.role, "content": item.content} for item in request.messages
            )
        elif request.user_prompt:
            messages.append({"role": "user", "content": request.user_prompt})
        else:
            raise ValueError("Qwen official provider requires user prompt or messages.")

        completion = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature if request.temperature is None else request.temperature,
            max_tokens=self.max_tokens if request.max_tokens is None else request.max_tokens,
        )

        usage = completion.usage
        parsed_text = completion.choices[0].message.content or ""
        return LLMResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            raw_response=completion.model_dump(),
            parsed_text=parsed_text,
            finish_reason=completion.choices[0].finish_reason,
            usage=LLMUsage(
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                total_tokens=usage.total_tokens if usage else None,
            ),
        )


class Qwen3MaxLLM:
    def __init__(self) -> None:
        self.provider = QwenOfficialProvider()

    async def invoke(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        request = LLMRequest.from_prompts(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )
        response = await self.provider.invoke(request)
        return response.parsed_text
