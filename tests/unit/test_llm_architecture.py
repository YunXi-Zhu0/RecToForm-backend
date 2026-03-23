import unittest
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory

from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.factory.llm_factory import LLMFactory
from src.integrations.llm.providers.qwen.local_openai_compatible import (
    QwenLocalOpenAICompatibleProvider,
)
from src.integrations.llm.providers.qwen.official import QwenOfficialProvider
from src.integrations.llm.schema.request import LLMRequest


class LLMArchitectureTests(unittest.TestCase):
    def test_request_from_prompts_builds_image_inputs(self) -> None:
        request = LLMRequest.from_prompts(
            user_prompt="extract invoice fields",
            system_prompt="return json only",
            image_paths=["tests/fixtures/invoices/tmp.png"],
            response_format={"type": "json_object"},
        )

        self.assertEqual(request.user_prompt, "extract invoice fields")
        self.assertEqual(request.system_prompt, "return json only")
        self.assertEqual(
            request.image_inputs[0].path,
            Path("tests/fixtures/invoices/tmp.png"),
        )
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

    def test_official_provider_declares_vision_capability(self) -> None:
        provider = object.__new__(QwenOfficialProvider)
        provider.max_tokens = 2048

        capabilities = provider.get_capabilities()

        self.assertTrue(capabilities.supports_vision)
        self.assertEqual(capabilities.max_output_tokens, 2048)

    def test_official_provider_builds_multimodal_messages(self) -> None:
        provider = object.__new__(QwenOfficialProvider)
        provider.model_name = "qwen3-vl-plus"

        with TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "invoice.png"
            image_bytes = b"fake-image-content"
            image_path.write_bytes(image_bytes)

            request = LLMRequest.from_prompts(
                user_prompt="extract invoice fields",
                system_prompt="return json only",
                image_paths=[image_path],
                response_format={"type": "json_object"},
            )

            messages = provider._build_messages(request)

        self.assertEqual(messages[0], {"role": "system", "content": "return json only"})
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"][0]["type"], "image_url")
        self.assertEqual(
            messages[1]["content"][0]["image_url"]["url"],
            "data:image/png;base64,%s" % b64encode(image_bytes).decode("utf-8"),
        )
        self.assertEqual(
            messages[1]["content"][1],
            {"type": "text", "text": "extract invoice fields"},
        )

if __name__ == "__main__":
    unittest.main()
