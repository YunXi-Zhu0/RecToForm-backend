import os
from pathlib import Path
from typing import List

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


def _get_list_env(key: str, default: List[str]) -> List[str]:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TESTS_DIR = ROOT_DIR / "tests"
TEMPLATE_DIR = ROOT_DIR / "template"
STANDARD_FIELDS_CONFIG_PATH = TEMPLATE_DIR / "standard_fields.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs"
DEFAULT_AUDIT_DIR = DEFAULT_OUTPUT_DIR / "audits"
DEFAULT_DOCUMENT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "documents"
API_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "api"
API_UPLOAD_DIR = API_OUTPUT_DIR / "uploads"
API_TASK_DIR = API_OUTPUT_DIR / "tasks"
API_EXPORT_DIR = API_OUTPUT_DIR / "exports"
DEFAULT_MISSING_VALUE = ""

API_TITLE = os.getenv("API_TITLE", "RecToForm API")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = _get_int_env("API_PORT", 8080)
API_CORS_ORIGINS = _get_list_env("API_CORS_ORIGINS", ["*"])

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
EXPORT_FILE_MAPPING_TTL = _get_int_env("EXPORT_FILE_MAPPING_TTL", 86400)
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "invoice_tasks")
RQ_JOB_TIMEOUT = _get_int_env("RQ_JOB_TIMEOUT", 1800)
RQ_RESULT_TTL = _get_int_env("RQ_RESULT_TTL", 86400)
RQ_WORKER_PROCESSES = _get_int_env("RQ_WORKER_PROCESSES", 4)

WORKFLOW_ASYNC_CONCURRENCY = _get_int_env("WORKFLOW_ASYNC_CONCURRENCY", 15)
MAX_UPLOAD_FILES = _get_int_env("MAX_UPLOAD_FILES", 50)
MAX_FILE_SIZE_MB = _get_int_env("MAX_FILE_SIZE_MB", 10)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen_official")

QWEN3_VL_PLUS_MODEL = {
    "MODEL_NAME": "qwen-vl-ocr",
    "API_KEY": os.getenv("QWEN3_VL_PLUS_API_KEY"),
    "BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "TEMPERATURE": _get_float_env("QWEN3_VL_PLUS_TEMPERATURE", 0.5),
    "MAX_TOKENS": _get_int_env("QWEN3_VL_PLUS_MAX_TOKENS", 1000),
}

QWEN3_VL_8B_SSPU_MODEL = {
    "API_URL": os.getenv("QWEN3_VL_8B_SSPU_API_URL", ""),
    "MODEL_NAME": os.getenv("QWEN3_VL_8B_SSPU_MODEL_NAME", "/model/Qwen3-VL-8B"),
    "TEMPERATURE": _get_float_env("QWEN3_VL_8B_SSPU_TEMPERATURE", 0.7),
    "MAX_TOKENS": _get_int_env("QWEN3_VL_8B_SSPU_MAX_TOKENS", 500),
    "TIMEOUT": _get_float_env("QWEN3_VL_8B_SSPU_TIMEOUT", 120.0),
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
