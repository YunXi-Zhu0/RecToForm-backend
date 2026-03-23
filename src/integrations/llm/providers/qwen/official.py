import base64
import mimetypes
from typing import Any, Dict, List, Optional, Sequence

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - defer hard failure to runtime construction
    AsyncOpenAI = None

from src.core.config import QWEN3_VL_PLUS_MODEL
from src.integrations.llm.base.llm import BaseLLMProvider
from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.schema.request import ImagePath, LLMRequest
from src.integrations.llm.schema.response import LLMResponse, LLMUsage


class QwenOfficialProvider(BaseLLMProvider):
    provider_name = "qwen_official"

    def __init__(self) -> None:
        if AsyncOpenAI is None:
            raise ImportError("openai package is required for qwen_official provider.")
        self.model_name = QWEN3_VL_PLUS_MODEL["MODEL_NAME"]
        self.temperature = QWEN3_VL_PLUS_MODEL["TEMPERATURE"]
        self.max_tokens = QWEN3_VL_PLUS_MODEL["MAX_TOKENS"]
        self.client = AsyncOpenAI(
            api_key=QWEN3_VL_PLUS_MODEL["API_KEY"],
            base_url=QWEN3_VL_PLUS_MODEL["BASE_URL"],
        )

    def get_capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_vision=True,
            supports_system_prompt=True,
            supports_json_output=True,
            max_output_tokens=self.max_tokens,
        )

    def _encode_image_to_data_url(self, image_path: ImagePath) -> str:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        resolved_mime_type = mime_type or "image/jpeg"
        base64_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return "data:%s;base64,%s" % (resolved_mime_type, base64_image)

    def _build_multimodal_user_content(self, request: LLMRequest) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []

        for image_input in request.image_inputs:
            if not image_input.path.is_file():
                raise FileNotFoundError("Image file not found: %s" % image_input.path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": self._encode_image_to_data_url(image_input.path),
                    },
                }
            )

        if request.user_prompt:
            content.append({"type": "text", "text": request.user_prompt})

        return content

    def _build_messages(self, request: LLMRequest) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        if request.messages:
            messages.extend(
                {"role": item.role, "content": item.content} for item in request.messages
            )

        if request.image_inputs:
            messages.append(
                {
                    "role": "user",
                    "content": self._build_multimodal_user_content(request),
                }
            )
        elif request.user_prompt and not request.messages:
            messages.append({"role": "user", "content": request.user_prompt})

        if not messages or (
            len(messages) == 1 and messages[0]["role"] == "system"
        ):
            raise ValueError("Qwen official provider requires user prompt, messages, or image inputs.")

        return messages

    async def invoke(self, request: LLMRequest) -> LLMResponse:
        completion = await self.client.chat.completions.create(
            model=self.model_name,
            messages=self._build_messages(request),
            temperature=self.temperature if request.temperature is None else request.temperature,
            max_tokens=self.max_tokens if request.max_tokens is None else request.max_tokens,
            response_format=request.response_format,
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

    async def invoke(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[Sequence[ImagePath]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        request = LLMRequest.from_prompts(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            image_paths=image_paths,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )
        response = await self.provider.invoke(request)
        return response.parsed_text
