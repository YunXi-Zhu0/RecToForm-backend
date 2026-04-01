import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.core.config import STANDARD_FIELDS_CONFIG_PATH
from src.services.standard.models import StandardJsonSchema


EXPECTED_STANDARD_KEYS = [
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


class StandardSchemaConfigError(ValueError):
    pass


class StandardSchemaService:
    def __init__(self, schema_path: Optional[Path] = None) -> None:
        self.schema_path = Path(schema_path or STANDARD_FIELDS_CONFIG_PATH)

    def load_schema(self) -> StandardJsonSchema:
        payload = self._load_json(self.schema_path)
        schema = self._build_schema(payload)
        self._validate_schema(payload=payload, schema=schema)
        return schema

    def get_standard_keys(self) -> List[str]:
        return list(self.load_schema().keys)

    def ensure_known_fields(self, field_names: Iterable[str]) -> None:
        schema = self.load_schema()
        unknown = [field_name for field_name in field_names if field_name not in schema.keys]
        if unknown:
            raise StandardSchemaConfigError(
                "Unknown standard field keys: %s" % ", ".join(dict.fromkeys(unknown))
            )

    def _build_schema(self, payload: Dict[str, object]) -> StandardJsonSchema:
        return StandardJsonSchema(
            keys=list(payload.get("keys", [])),
            required_keys=list(payload.get("required_keys", payload.get("keys", []))),
            default_missing_value=str(payload.get("default_missing_value", "")),
            version=str(payload.get("version", "v1")),
        )

    def _validate_schema(
        self,
        payload: Dict[str, object],
        schema: StandardJsonSchema,
    ) -> None:
        raw_keys = payload.get("keys")
        if not isinstance(raw_keys, list) or not raw_keys:
            raise StandardSchemaConfigError("Standard schema must define a non-empty keys list.")

        duplicated_keys = [
            key for key, count in Counter(str(item) for item in raw_keys).items() if count > 1
        ]
        if duplicated_keys:
            raise StandardSchemaConfigError(
                "Standard schema contains duplicated keys: %s" % ", ".join(duplicated_keys)
            )

        invalid_keys = [
            item
            for item in raw_keys
            if not isinstance(item, str) or not item.strip()
        ]
        if invalid_keys:
            raise StandardSchemaConfigError("Standard schema contains blank or non-string keys.")

        missing_keys = [key for key in EXPECTED_STANDARD_KEYS if key not in schema.keys]
        if missing_keys:
            raise StandardSchemaConfigError(
                "Standard schema is missing required keys: %s" % ", ".join(missing_keys)
            )

        illegal_keys = [key for key in schema.keys if key not in EXPECTED_STANDARD_KEYS]
        if illegal_keys:
            raise StandardSchemaConfigError(
                "Standard schema contains illegal keys: %s" % ", ".join(illegal_keys)
            )

        raw_required_keys = payload.get("required_keys", schema.keys)
        if not isinstance(raw_required_keys, list):
            raise StandardSchemaConfigError("Standard schema required_keys must be a list.")

        unknown_required = [key for key in schema.required_keys if key not in schema.keys]
        if unknown_required:
            raise StandardSchemaConfigError(
                "Standard schema required_keys contain unknown keys: %s"
                % ", ".join(unknown_required)
            )

    def _load_json(self, path: Path) -> Dict[str, object]:
        if not path.is_file():
            raise StandardSchemaConfigError("Standard schema file not found: %s" % path)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
