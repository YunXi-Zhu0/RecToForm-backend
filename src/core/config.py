import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for partially provisioned envs
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False

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
TEMPLATE_DIR = ROOT_DIR / "template"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs"
DEFAULT_AUDIT_DIR = DEFAULT_OUTPUT_DIR / "audits"
DEFAULT_DOCUMENT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "documents"
DEFAULT_MISSING_VALUE = ""

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen_local_openai_compatible")

QWEN3_VL_PLUS_MODEL = {
    "MODEL_NAME": "qwen3-vl-plus",
    "API_KEY": os.getenv("QWEN3_VL_PLUS_API_KEY"),
    "BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "TEMPERATURE": _get_float_env("QWEN3_VL_PLUS_TEMPERATURE", 0.7),
    "MAX_TOKENS": _get_int_env("QWEN3_VL_PLUS_MAX_TOKENS", 500),
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

LLM_PROVIDERS = {
    "qwen_official": {
        "provider": "qwen_official",
        "model_name": QWEN3_VL_PLUS_MODEL["MODEL_NAME"],
    },
    "qwen_local_openai_compatible": {
        "provider": "qwen_local_openai_compatible",
        "model_name": QWEN3_VL_8B_SSPU_MODEL["MODEL_NAME"],
    },
}
