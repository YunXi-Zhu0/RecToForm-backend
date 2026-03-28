import asyncio
from pathlib import Path
from typing import List

from src.core.config import LLM_PROVIDERS, TESTS_DIR
from src.services.document import DocumentService
from src.services.llm.service import LLMService


async def analyze_invoice(
    path: Path,
    provider_name: str,
    semaphore: asyncio.Semaphore,
) -> None:
    async with semaphore:
        document_service = DocumentService()
        llm_service = LLMService(provider_name=provider_name)

        document_result = await asyncio.to_thread(
            document_service.parse,
            path,
            path.stem,
        )
        response = await llm_service.analyze_images(
            image_paths=document_result.image_paths,
            user_prompt="请提取发票字段并返回 JSON",
            system_prompt="你是发票识别助手，只返回合法JSON。",
            response_format={"type": "json_object"},
        )

        print("=" * 80)
        print("file:", path.name)
        print("file_type:", document_result.file_type)
        print("image_count:", len(document_result.image_paths))
        print(response.parsed_text)


def collect_invoice_files(invoice_dir: Path) -> List[Path]:
    supported_suffixes = DocumentService.IMAGE_EXTENSIONS | {".pdf"}
    return sorted(
        path
        for path in invoice_dir.iterdir()
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


async def run_llm_service(
    invoice_dir: Path,
    provider_name: str,
    max_concurrency: int = 3,
) -> None:
    invoice_paths = collect_invoice_files(invoice_dir)
    if not invoice_paths:
        raise FileNotFoundError("No supported invoice files found in: %s" % invoice_dir)

    semaphore = asyncio.Semaphore(max_concurrency)
    tasks = [
        asyncio.create_task(analyze_invoice(path, provider_name, semaphore))
        for path in invoice_paths
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    failed_paths: List[Path] = []
    for path, result in zip(invoice_paths, results):
        if isinstance(result, Exception):
            failed_paths.append(path)
            print("=" * 80)
            print("file:", path.name)
            print("status: failed")
            print("error:", repr(result))

    print("=" * 80)
    print("total:", len(invoice_paths))
    print("failed:", len(failed_paths))


if __name__ == "__main__":
    invoice_dir = TESTS_DIR / "fixtures" / "invoices"
    provider_name = LLM_PROVIDERS["qwen_local_openai_compatible"]["provider"]
    asyncio.run(run_llm_service(invoice_dir, provider_name))
