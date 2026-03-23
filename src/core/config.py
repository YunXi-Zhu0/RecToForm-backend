import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_float_env(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return float(value)


def _get_int_env(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return int(value)


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = ROOT_DIR / "tests"

QWEN3_MAX_MODEL = {
    "MODEL_NAME": "qwen3-max",
    "API_KEY": os.getenv("QWEN3_MAX_API_KEY"),
    "BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

QWEN3_VL_8B_SSPU_MODEL = {
    "API_URL": os.getenv("QWEN3_VL_8B_SSPU_API_URL", ""),
    "MODEL_NAME": os.getenv("QWEN3_VL_8B_SSPU_MODEL_NAME", "/model/Qwen3-VL-8B"),
    "TEMPERATURE": _get_float_env("QWEN3_VL_8B_SSPU_TEMPERATURE", 0.7),
    "MAX_TOKENS": _get_int_env("QWEN3_VL_8B_SSPU_MAX_TOKENS", 500),
    "TIMEOUT": _get_float_env("QWEN3_VL_8B_SSPU_TIMEOUT", 30.0),
    "MAX_IMAGE_SIZE": _get_int_env("QWEN3_VL_8B_SSPU_MAX_IMAGE_SIZE", 1024),
    "IMAGE_QUALITY": _get_int_env("QWEN3_VL_8B_SSPU_IMAGE_QUALITY", 85),
}
