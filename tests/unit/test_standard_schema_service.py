import json

import pytest

from src.services.standard import (
    EXPECTED_STANDARD_KEYS,
    StandardSchemaConfigError,
    StandardSchemaService,
)


def test_load_schema_returns_expected_standard_keys() -> None:
    schema = StandardSchemaService().load_schema()

    assert schema.keys == EXPECTED_STANDARD_KEYS
    assert schema.required_keys == EXPECTED_STANDARD_KEYS
    assert schema.default_missing_value == ""


def test_load_schema_rejects_missing_keys(tmp_path) -> None:
    schema_path = tmp_path / "standard_fields.json"
    schema_path.write_text(
        json.dumps(
            {
                "version": "v1",
                "default_missing_value": "",
                "keys": EXPECTED_STANDARD_KEYS[:-1],
                "required_keys": EXPECTED_STANDARD_KEYS[:-1],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(StandardSchemaConfigError, match="missing required keys"):
        StandardSchemaService(schema_path=schema_path).load_schema()


def test_load_schema_rejects_duplicated_keys(tmp_path) -> None:
    schema_path = tmp_path / "standard_fields.json"
    duplicated_keys = EXPECTED_STANDARD_KEYS[:-1] + [EXPECTED_STANDARD_KEYS[-1], EXPECTED_STANDARD_KEYS[-1]]
    schema_path.write_text(
        json.dumps(
            {
                "version": "v1",
                "default_missing_value": "",
                "keys": duplicated_keys,
                "required_keys": EXPECTED_STANDARD_KEYS,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(StandardSchemaConfigError, match="duplicated keys"):
        StandardSchemaService(schema_path=schema_path).load_schema()
