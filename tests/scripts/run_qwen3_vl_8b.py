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

    path = TESTS_DIR / "fixtures" / "invoices" / "tmp.png"

    prompt = """
    鐜板湪浣犳槸涓€鍚嶄笓涓氱殑鍙戠エ瀹℃煡鍛? 璇锋牴鎹笅闈㈢粰鍑虹殑淇℃伅, 鎻愬彇鍙戠エ鍥剧墖涓搴旂殑瀛楁鍙婂叾瀵瑰簲鐨勬暟鎹? 浠son褰㈠紡杩斿洖
    """

    result = analyze_image(path, prompt)
    print(result["choices"][0]["message"]["content"])
