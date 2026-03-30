import base64
import io

import requests
from PIL import Image


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def resize_and_encode(image_path, max_size=1024):
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    if img.mode != "RGB":
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def analyze_image(image_path, prompt):
    url = "http://10.100.1.93:12368/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    base64_img = resize_and_encode(image_path)

    payload = {
        "model": "/model/Qwen3-VL-8B",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    from src.core.config import TESTS_DIR

    path = TESTS_DIR / "fixtures" / "invoices" / "page_001.png"

    prompt = """
        "你是发票字段提取助手。你的任务是根据提供的发票图片提取标准字段。\n\n"
        "要求：\n"
        "1. 只能根据输入图片提取字段，禁止猜测或补造不存在的信息。\n"
        "2. 若字段无法确认，返回空值。\n"
        "3. 输出字段名必须与系统给定的固定中文键列表完全一致。\n"
        "4. 最终只输出合法 JSON，不要输出解释、分析过程或额外文本。\n"
        "5. 缺失字段统一返回 `%s`。\n"
        "6. 必须输出完整标准 JSON，即使字段缺失也要保留对应 key。\n"
    """

    result = analyze_image(path, prompt)
    print(result["choices"][0]["message"]["content"])
