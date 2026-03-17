import base64
import aiofiles
import httpx
from pathlib import Path
from typing import List

from src.core.config import PaddleOCR_VL_1P5
from src.integrations.ocr.core.model.schema import OCRPageResult

class PaddleOCRClient:
    def __init__(self):
        self.api_url = PaddleOCR_VL_1P5["API_URL"]
        self.token = PaddleOCR_VL_1P5["TOKEN"]

        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

    async def _encode_file(self, file_path: Path) -> str:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        return base64.b64encode(content).decode("ascii")

    async def _get_file_type(self, file_path: Path) -> int:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            file_type = 0
        elif ext in {".jpg", ".jpeg", ".png", ".bmp"}:
            file_type = 1
        else:
            raise ValueError(f"无法识别的文件类型: {ext}")

        return file_type


    async def parse_file(
            self,
            file_path: Path,
            file_type: int | None = None,
            use_doc_orientation_classify: bool = False,
            use_doc_unwarping: bool = False,
            use_chart_recognition: bool = False,
    ) -> List[OCRPageResult]:
        payload = {
            "file": await self._encode_file(file_path),
            "fileType": await self._get_file_type(file_path) if file_type is None else file_type,
            "useDocOrientationClassify": use_doc_orientation_classify,
            "useDocUnwarping": use_doc_unwarping,
            "useChartRecognition": use_chart_recognition,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()

        try:
            raw = response.json()["result"]["layoutParsingResults"]
        except Exception as e:
            raise RuntimeError(f"OCR 响应解析失败: {response.text}") from e

        pages: List[OCRPageResult] = []
        for item in raw:
            pages.append(
                OCRPageResult(
                    markdown=item["markdown"]["text"],
                    images=item.get("outputImages", {})
                )
            )

        return pages


if __name__ == "__main__":
    import asyncio
    from pprint import pprint
    from src.core.config import TESTS_DIR

    test_file_path = TESTS_DIR / "发票文件" / "汽油25.pdf"

    async def ocr():
        ocr_client = PaddleOCRClient()
        page = await ocr_client.parse_file(test_file_path)
        pprint(page, indent=4)

    asyncio.run(ocr())
