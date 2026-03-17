import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 测试文件目录
TESTS_DIR = ROOT_DIR / "tests"


# DeepseekSSPU 模型配置
DEEPSEEK_SSPU_MODEL = {
    "BASE_URL": os.getenv("DEEPSEEKSSPU_MODEL_BASE_URL"),
    "MODEL_NAME": os.getenv("DEEPSEEKSSPU_MODEL_NAME"),
    "TEMPERATURE": os.getenv("DEEPSEEKSSPU_MODEL_TEMPERATURE"),
    "MAX_TOKENS": os.getenv("DEEPSEEKSSPU_MODEL_MAX_TOKENS"),
}

# qwen3-max 模型配置
QWEN3_MAX_MODEL = {
    "MODEL_NAME": "qwen3-max",
    "API_KEY": os.getenv("QWEN3_MAX_API_KEY"),
    "BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}


# PaddleOCR-VL-1.5_API
PaddleOCR_VL_1P5 = {
    "API_URL": os.getenv("PADDLEOCR_VL_1P5_API_URL"),
    "TOKEN": os.getenv("PADDLEOCR_VL_1P5_TOKEN")
}
