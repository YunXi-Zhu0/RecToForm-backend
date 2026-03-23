from abc import ABC, abstractmethod

from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.schema.request import LLMRequest
from src.integrations.llm.schema.response import LLMResponse


class BaseLLMProvider(ABC):
    provider_name = "unknown"
    model_name = "unknown"

    @abstractmethod
    async def invoke(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def get_capabilities(self) -> LLMCapabilities:
        raise NotImplementedError
