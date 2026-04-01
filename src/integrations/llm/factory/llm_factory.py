from typing import Optional

from src.core.config import LLM_PROVIDER
from src.integrations.llm.base.llm import BaseLLMProvider
from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.providers.qwen.local_openai_compatible import (
    QwenLocalOpenAICompatibleProvider,
)
from src.integrations.llm.providers.qwen.official import QwenOfficialProvider


class LLMFactory:
    _providers = {
        "qwen_official": QwenOfficialProvider,
        "qwen_local_openai_compatible": QwenLocalOpenAICompatibleProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: Optional[str] = None,
        required_capabilities: Optional[LLMCapabilities] = None,
    ) -> BaseLLMProvider:
        target_name = provider_name or LLM_PROVIDER
        provider_class = cls._providers.get(target_name)
        if provider_class is None:
            raise ValueError("Unsupported LLM provider: %s" % target_name)

        provider = provider_class()
        if required_capabilities is not None:
            cls._validate_capabilities(
                provider.get_capabilities(),
                required_capabilities,
            )
        return provider

    @staticmethod
    def _validate_capabilities(
        capabilities: LLMCapabilities,
        required: LLMCapabilities,
    ) -> None:
        capability_checks = (
            ("supports_vision", required.supports_vision),
            ("supports_system_prompt", required.supports_system_prompt),
            ("supports_json_output", required.supports_json_output),
            ("supports_stream", required.supports_stream),
            ("supports_tools", required.supports_tools),
        )

        for field_name, expected in capability_checks:
            if expected and not getattr(capabilities, field_name):
                raise ValueError("Provider does not satisfy capability: %s" % field_name)


def get_llm_provider(
    provider_name: Optional[str] = None,
    required_capabilities: Optional[LLMCapabilities] = None,
) -> BaseLLMProvider:
    return LLMFactory.create(
        provider_name=provider_name,
        required_capabilities=required_capabilities,
    )
