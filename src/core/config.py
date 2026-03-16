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