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
            user_prompt="请结合上传的全部发票图片提取发票信息，并输出完整标准 JSON。",
            system_prompt="你是发票字段提取助手。你的任务是根据提供的发票图片提取标准字段，并严格输出 JSON。\n\n"
            "要求：\n"
            "1. 只能根据输入图片提取字段，禁止猜测或补造不存在的信息。\n"
            "2. 若字段无法确认，返回空值。\n"
            "3. 多张图片或多页 PDF 时，请综合全部图片内容后输出一个 JSON 结果。\n"
            "4. 输出字段名及其顺序必须与系统给定的固定中文键列表完全一致。\n"
            "5. 最终只输出合法 JSON，不要输出解释、分析过程或额外文本。\n"
            "6. 缺失字段统一返回 `%s`。\n"
            "7. 必须输出完整标准 JSON，即使字段缺失也要保留对应 key。\n",
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
    provider_name = LLM_PROVIDERS["qwen_official"]["provider"]
    asyncio.run(run_llm_service(invoice_dir, provider_name))
