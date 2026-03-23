import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import httpx
from PIL import Image

from src.core.config import QWEN3_VL_8B_SSPU_MODEL


ImagePath = Union[str, Path]


class Qwen3VL8BSSPULLM:
    def __init__(self) -> None:
        self.api_url = QWEN3_VL_8B_SSPU_MODEL["API_URL"]
        self.model_name = QWEN3_VL_8B_SSPU_MODEL["MODEL_NAME"]
        self.temperature = QWEN3_VL_8B_SSPU_MODEL["TEMPERATURE"]
        self.max_tokens = QWEN3_VL_8B_SSPU_MODEL["MAX_TOKENS"]
        self.timeout = QWEN3_VL_8B_SSPU_MODEL["TIMEOUT"]
        self.max_image_size = QWEN3_VL_8B_SSPU_MODEL["MAX_IMAGE_SIZE"]
        self.image_quality = QWEN3_VL_8B_SSPU_MODEL["IMAGE_QUALITY"]

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

    def _build_user_content(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
    ) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = []
        for raw_path in image_paths:
            image_path = Path(raw_path)
            if not image_path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            base64_image = self._resize_and_encode(image_path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                }
            )

        content.append({"type": "text", "text": user_prompt})
        return content

    def _build_messages(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append(
            {
                "role": "user",
                "content": self._build_user_content(image_paths, user_prompt),
            }
        )
        return messages

    async def chat(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not image_paths:
            raise ValueError("image_paths must not be empty.")

        payload = {
            "model": self.model_name,
            "messages": self._build_messages(
                image_paths=image_paths,
                user_prompt=user_prompt,
                system_prompt=system_prompt,
            ),
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
            "temperature": self.temperature if temperature is None else temperature,
        }
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def invoke(
        self,
        image_paths: Sequence[ImagePath],
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        response = await self.chat(
            image_paths=image_paths,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import asyncio

    from src.core.config import TESTS_DIR

    async def main() -> None:
        client = Qwen3VL8BSSPULLM()
        image_path = TESTS_DIR / "发票文件" / "tmp.png"
        system_prompt = "你是一个发票字段提取助手。请严格输出 JSON。"
        user_prompt = "请根据发票图片提取字段，并只返回 JSON。"
        result = await client.invoke(
            image_paths=[image_path],
            user_prompt=user_prompt,
            system_prompt=system_prompt,
        )
        print(result)

    asyncio.run(main())
