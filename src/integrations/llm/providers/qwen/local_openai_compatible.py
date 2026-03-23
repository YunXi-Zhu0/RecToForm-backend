import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import httpx
from PIL import Image

from src.core.config import QWEN3_VL_8B_SSPU_MODEL
from src.integrations.llm.base.llm import BaseLLMProvider
from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.schema.request import ImagePath, LLMRequest
from src.integrations.llm.schema.response import LLMResponse, LLMUsage


class QwenLocalOpenAICompatibleProvider(BaseLLMProvider):
    provider_name = "qwen_local_openai_compatible"

    def __init__(self) -> None:
        self.api_url = QWEN3_VL_8B_SSPU_MODEL["API_URL"]
        self.model_name = QWEN3_VL_8B_SSPU_MODEL["MODEL_NAME"]
        self.temperature = QWEN3_VL_8B_SSPU_MODEL["TEMPERATURE"]
        self.max_tokens = QWEN3_VL_8B_SSPU_MODEL["MAX_TOKENS"]
        self.timeout = QWEN3_VL_8B_SSPU_MODEL["TIMEOUT"]
        self.max_image_size = QWEN3_VL_8B_SSPU_MODEL["MAX_IMAGE_SIZE"]
        self.image_quality = QWEN3_VL_8B_SSPU_MODEL["IMAGE_QUALITY"]

    def get_capabilities(self) -> LLMCapabilities:
        return LLMCapabilities(
            supports_vision=True,
            supports_system_prompt=True,
            supports_json_output=True,
            max_image_count=None,
            max_output_tokens=self.max_tokens,
        )

    def _resize_and_encode(self, image_path: Path) -> str:
        with Image.open(image_path) as image:
            image.thumbnail(
                (self.max_image_size, self.max_image_size),
                Image.Resampling.LANCZOS,
            )

            if image.mode != "RGB":
                image = image.convert("RGB")

            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.image_quality)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _build_user_content(self, request: LLMRequest) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []

        for image_input in request.image_inputs:
            if not image_input.path.is_file():
                raise FileNotFoundError("Image file not found: %s" % image_input.path)

            base64_image = self._resize_and_encode(image_input.path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,%s" % base64_image,
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
        else:
            messages.append(
                {
                    "role": "user",
                    "content": self._build_user_content(request),
                }
            )

        return messages

    def _build_payload(self, request: LLMRequest) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(request),
            "max_tokens": self.max_tokens if request.max_tokens is None else request.max_tokens,
            "temperature": self.temperature if request.temperature is None else request.temperature,
        }

        if request.response_format:
            payload["response_format"] = request.response_format

        return payload

    async def invoke(self, request: LLMRequest) -> LLMResponse:
        if not request.image_inputs and not request.messages:
            raise ValueError(
                "Qwen local provider requires image_inputs or pre-built messages."
            )

        headers = {"Content-Type": "application/json"}
        payload = self._build_payload(request)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            raw_response = response.json()

        choice = raw_response["choices"][0]
        usage = raw_response.get("usage", {})
        return LLMResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            raw_response=raw_response,
            parsed_text=choice["message"]["content"],
            finish_reason=choice.get("finish_reason"),
            usage=LLMUsage(
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
        )


class Qwen3VL8BSSPULLM:
    def __init__(self) -> None:
        self.provider = QwenLocalOpenAICompatibleProvider()

    async def chat(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        request = LLMRequest.from_prompts(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            image_paths=image_paths,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = await self.provider.invoke(request)
        return response.raw_response

    async def invoke(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        request = LLMRequest.from_prompts(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            image_paths=image_paths,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = await self.provider.invoke(request)
        return response.parsed_text
