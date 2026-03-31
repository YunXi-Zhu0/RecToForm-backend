import base64
import io

import requests
from PIL import Image


def resize_and_encode(image_path, max_size=2048):
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    if img.mode != "RGB":
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def analyze_image(image_path, system_prompt, user_prompt):
    url = "http://10.100.1.93:12368/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    base64_img = resize_and_encode(image_path)

    payload = {
        "model": "/model/Qwen3-VL-8B",
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
        "max_pixels": 500000,
        "max_tokens": 512,
        "temperature": 0.5,
        "top_p": 0.8,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    from src.core.config import TESTS_DIR

    path = TESTS_DIR / "fixtures" / "invoices" / "page_001.png"

    fields = [
        "发票代码",
        "发票号码",
        "开票日期",
        "购买方名称",
        "购买方纳税人识别号",
        "购买方地址电话",
        "购买方开户行及账号",
        "货物或应税劳务、服务名称",
        "规格型号",
        "单位",
        "数量",
        "单价",
        "金额",
        "税率",
        "税额",
        "合计",
        "价税合计(大写)",
        "销售方名称",
        "销售方纳税人识别号",
        "销售方地址电话",
        "销售方开户行及账号",
        "收款人",
        "复核",
        "开票人",
        "销售方",
        "备注",
    ]
    missing_value = ""

    system_prompt = (
        "你是发票字段提取助手。你的任务是根据提供的发票图片提取标准字段。\n\n"
        "要求：\n"
        "1. 只能根据输入图片提取字段，禁止猜测或补造不存在的信息。\n"
        "2. 若字段无法确认，返回空值。\n"
        "3. 输出字段名必须与系统给定的固定中文键列表完全一致。\n"
        "4. 最终只输出合法 JSON，不要输出解释、分析过程或额外文本。\n"
        f"5. 缺失字段统一返回空字符 。\n"
        "6. 必须输出完整标准 JSON，即使字段缺失也要保留对应 key。\n"
        f"7. 本次仅允许输出以下字段：{fields}。"
    )

    user_prompt = (
        "当前任务：请结合上传的发票图片提取发票信息，并输出完整标准 JSON。\n"
        "返回 json 示例如下：\n"
        "{\n"
        '  "发票号码": "25317000002264951341",\n'
        '  "发票代码": "",\n'
        '  "发票金额": "123.45"\n'
        "}\n"
        f"注意：缺失字段统一返回 `{missing_value}`。"
    )

    result = analyze_image(path, system_prompt, user_prompt)
    print(result["choices"][0]["message"]["content"])
