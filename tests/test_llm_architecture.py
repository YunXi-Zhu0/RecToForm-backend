import unittest
from pathlib import Path

from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.factory.llm_factory import LLMFactory
from src.integrations.llm.providers.qwen.local_openai_compatible import (
    QwenLocalOpenAICompatibleProvider,
)
from src.integrations.llm.schema.request import LLMRequest


class LLMArchitectureTests(unittest.TestCase):
    def test_request_from_prompts_builds_image_inputs(self) -> None:
        request = LLMRequest.from_prompts(
            user_prompt="extract invoice fields",
            system_prompt="return json only",
            image_paths=["tests/发票文件/tmp.png"],
            response_format={"type": "json_object"},
        )

        self.assertEqual(request.user_prompt, "extract invoice fields")
        self.assertEqual(request.system_prompt, "return json only")
        self.assertEqual(request.image_inputs[0].path, Path("tests/发票文件/tmp.png"))
        self.assertEqual(request.response_format, {"type": "json_object"})

    def test_factory_creates_local_provider(self) -> None:
        provider = LLMFactory.create("qwen_local_openai_compatible")
        self.assertIsInstance(provider, QwenLocalOpenAICompatibleProvider)

    def test_factory_validates_capabilities(self) -> None:
        with self.assertRaises(ValueError):
            LLMFactory.create(
                "qwen_local_openai_compatible",
                required_capabilities=LLMCapabilities(supports_tools=True),
            )


if __name__ == "__main__":
    unittest.main()
