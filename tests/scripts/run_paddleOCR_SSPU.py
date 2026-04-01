import base64
import os
from pathlib import Path

import requests

from src.core.config import TESTS_DIR
from src.core.config import PaddleOCR_VL_1P5_SSPU


def get_response(input_path: Path):
    url = PaddleOCR_VL_1P5_SSPU["API_URL"]
    files = [("files", open(input_path, "rb"))]
    res = requests.post(url, files=files)
    return res


def decode_base64(image_bytes: str, output_dir: Path):
    img_data = base64.b64decode(image_bytes)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_dir / "result.jpg", "wb") as f:
        f.write(img_data)


if __name__ == "__main__":
    from pprint import pprint
    from typing import List

    invoice_dir = TESTS_DIR / "fixtures" / "invoices"
    input_path = invoice_dir / "姹芥补250808.pdf"
    output_dir = TESTS_DIR / "scripts" / "outputs" / "paddleocr_sspu"

    response = get_response(input_path)

    results: List = response.json().get("results")

    texts: List = results[0].get("pages")[0].get("texts")
    image_base64: str = results[0].get("pages")[0].get("image_base64")

    decode_base64(image_base64, output_dir)

    pprint(texts, indent=4)
