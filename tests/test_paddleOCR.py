# Please make sure the requests library is installed
# pip install requests
import base64
import os
import requests
from src.core.config import TESTS_DIR
from src.core.config import PaddleOCR_VL_1P5


# API_URL 及 TOKEN 请访问 [PaddleOCR 官网](https://aistudio.baidu.com/paddleocr/task) 在 API 调用示例中获取。
API_URL = PaddleOCR_VL_1P5["API_URL"]
TOKEN = PaddleOCR_VL_1P5["TOKEN"]

invoice_dir = TESTS_DIR / "发票文件"
file_path = invoice_dir / "汽油25.pdf"

with open(file_path, "rb") as file:
    file_bytes = file.read()
    file_data = base64.b64encode(file_bytes).decode("ascii")

headers = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}

required_payload = {
    "file": file_data,
    "fileType": 0,  # For PDF documents, set `fileType` to 0; for images, set `fileType` to 1
}

optional_payload = {
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useChartRecognition": False,
}

payload = {**required_payload, **optional_payload}

response = requests.post(API_URL, json=payload, headers=headers)
print(response.status_code)
assert response.status_code == 200
result = response.json()["result"]

output_dir = TESTS_DIR / "paddleOCR_output"
os.makedirs(output_dir, exist_ok=True)

for i, res in enumerate(result["layoutParsingResults"]):
    md_filename = os.path.join(output_dir, f"doc_{i}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(res["markdown"]["text"])
    print(f"Markdown document saved at {md_filename}")

    for img_name, img in res["outputImages"].items():
        img_response = requests.get(img)
        if img_response.status_code == 200:
            # Save image to local
            filename = os.path.join(output_dir, f"{img_name}_{i}.jpg")
            with open(filename, "wb") as f:
                f.write(img_response.content)
            print(f"Image saved to: {filename}")
        else:
            print(f"Failed to download image, status code: {img_response.status_code}")
