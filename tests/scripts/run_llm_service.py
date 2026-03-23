from pathlib import Path
from src.services.llm.service import LLMService


async def run_llm_service(
        path: Path,
        provider_name: str
):
    service = LLMService(provider_name=provider_name)

    response = await service.analyze_images(
        image_paths=[path],
        user_prompt="请提取发票字段并返回 JSON",
        system_prompt="你是发票识别助手，只返回合法JSON。",
        response_format={"type": "json_object"},
    )

    print(response.parsed_text)


if __name__ == "__main__":
    import asyncio
    from src.core.config import LLM_PROVIDERS
    from src.core.config import TESTS_DIR
    path = TESTS_DIR / "fixtures" / "invoices" / "tmp.png"
    provider_name = LLM_PROVIDERS.get("qwen_local_openai_compatible").get("provider")

    asyncio.run(run_llm_service(path, provider_name))
