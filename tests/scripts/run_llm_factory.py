from pathlib import Path

from src.integrations.llm.factory.llm_factory import LLMFactory
from src.integrations.llm.capabilities.llm_capabilities import LLMCapabilities
from src.integrations.llm.schema.request import LLMRequest


async def run_llm_factory(
        path: Path,
        provider_name: str
):
    provider = LLMFactory.create(
        provider_name=provider_name,
        required_capabilities=LLMCapabilities(
            supports_vision=True,
            supports_system_prompt=True,
            supports_json_output=True,
        ),
    )

    request = LLMRequest.from_prompts(
        user_prompt="请提取发票字段，返回 JSON",
        system_prompt="你是发票信息抽取助手，只返回合法JSON。",
        image_paths = [path],
        response_format = {"type": "json_object"},
    )

    response = await provider.invoke(request)
    print(response.parsed_text)


if __name__ == "__main__":
    import asyncio
    from src.core.config import LLM_PROVIDERS
    from src.core.config import TESTS_DIR
    path = TESTS_DIR / "fixtures" / "invoices" / "tmp.png"
    provider_name = LLM_PROVIDERS.get("qwen_official").get("provider")

    asyncio.run(run_llm_factory(path, provider_name))
