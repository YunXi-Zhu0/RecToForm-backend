import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.core.config import TEMPLATE_DIR
from src.services.template.models import (
    ExcelFieldMapping,
    TemplateBundle,
    TemplateDefinition,
    TemplateFieldDefinition,
    TemplateSummary,
)


class TemplateNotFoundError(ValueError):
    pass


class TemplateConfigError(ValueError):
    pass


class TemplateService:
    def __init__(self, template_dir: Optional[Path] = None) -> None:
        self.template_dir = Path(template_dir or TEMPLATE_DIR)
        self.index_path = self.template_dir / "index.json"

    def list_templates(self) -> List[TemplateSummary]:
        return [
            TemplateSummary(
                template_id=item["template_id"],
                template_name=item["template_name"],
                template_version=item["template_version"],
                mapping_version=item["mapping_version"],
            )
            for item in self._load_index()
        ]

    def get_template_bundle(
        self,
        template_id: str,
        template_version: Optional[str] = None,
        selected_optional_field_ids: Optional[Iterable[str]] = None,
    ) -> TemplateBundle:
        payload = self._load_json(
            self._resolve_template_file(
                template_id=template_id,
                template_version=template_version,
            )
        )
        definition = self._build_definition(payload)
        field_definitions = self._build_field_definitions(payload)
        self._validate_definition(definition, field_definitions)

        selected_optional_ids = self.merge_fields(
            default_field_ids=[],
            optional_field_ids=list(selected_optional_field_ids or []),
            allowed_optional_ids=definition.optional_field_ids,
        )
        target_fields = self.merge_fields(
            default_field_ids=definition.default_field_ids,
            optional_field_ids=selected_optional_ids,
        )
        excel_mappings = self._build_mappings(
            payload=payload,
            definition=definition,
            target_fields=target_fields,
        )
        return TemplateBundle(
            template_id=definition.template_id,
            template_name=definition.template_name,
            template_version=definition.template_version,
            mapping_version=definition.mapping_version,
            excel_template_path=definition.excel_template_path,
            field_definitions=field_definitions,
            default_fields=list(definition.default_field_ids),
            optional_fields=selected_optional_ids,
            target_fields=target_fields,
            excel_mappings=excel_mappings,
        )

    def merge_fields(
        self,
        default_field_ids: Iterable[str],
        optional_field_ids: Iterable[str],
        allowed_optional_ids: Optional[Iterable[str]] = None,
    ) -> List[str]:
        defaults = list(default_field_ids)
        allowed = set(allowed_optional_ids or [])
        should_validate_optional = allowed_optional_ids is not None
        merged: List[str] = []

        for field_id in defaults + list(optional_field_ids):
            if should_validate_optional and field_id not in allowed and field_id not in defaults:
                raise TemplateConfigError("Unknown optional field id: %s" % field_id)
            if field_id not in merged:
                merged.append(field_id)
        return merged

    def _load_index(self) -> List[Dict[str, str]]:
        if not self.index_path.is_file():
            raise TemplateConfigError("Template index not found: %s" % self.index_path)
        payload = self._load_json(self.index_path)
        items = payload.get("templates", [])
        if not isinstance(items, list):
            raise TemplateConfigError("Template index must contain a templates list.")
        return items

    def _resolve_template_file(self, template_id: str, template_version: Optional[str]) -> Path:
        matches = [
            item
            for item in self._load_index()
            if item["template_id"] == template_id
            and (template_version is None or item["template_version"] == template_version)
        ]
        if not matches:
            raise TemplateNotFoundError(
                "Template not found: template_id=%s template_version=%s"
                % (template_id, template_version or "latest")
            )
        return self.template_dir / matches[0]["file"]

    def _build_definition(self, payload: Dict[str, object]) -> TemplateDefinition:
        return TemplateDefinition(
            template_id=str(payload["template_id"]),
            template_name=str(payload["template_name"]),
            template_version=str(payload["template_version"]),
            mapping_version=str(payload["mapping_version"]),
            excel_template_path=self.template_dir / str(payload["excel_template_path"]),
            default_field_ids=list(payload.get("default_field_ids", [])),
            optional_field_ids=list(payload.get("optional_field_ids", [])),
        )

    def _build_field_definitions(
        self,
        payload: Dict[str, object],
    ) -> Dict[str, TemplateFieldDefinition]:
        definitions: Dict[str, TemplateFieldDefinition] = {}
        for item in payload.get("field_definitions", []):
            field = TemplateFieldDefinition(
                field_id=str(item["field_id"]),
                field_label=str(item["field_label"]),
                description=str(item.get("description", "")),
                required=bool(item.get("required", False)),
                example_value=str(item.get("example_value", "")),
                value_type=str(item.get("value_type", "string")),
                source_hint=str(item.get("source_hint", "")),
                default_value=str(item.get("default_value", "")),
            )
            definitions[field.field_id] = field
        return definitions

    def _build_mappings(
        self,
        payload: Dict[str, object],
        definition: TemplateDefinition,
        target_fields: Iterable[str],
    ) -> Dict[str, ExcelFieldMapping]:
        mappings: Dict[str, ExcelFieldMapping] = {}
        for item in payload.get("excel_mappings", []):
            mapping = ExcelFieldMapping(
                template_id=definition.template_id,
                template_version=definition.template_version,
                mapping_version=definition.mapping_version,
                field_id=str(item["field_id"]),
                sheet_name=str(item["sheet_name"]),
                cell=str(item["cell"]),
                write_mode=str(item.get("write_mode", "overwrite")),
            )
            mappings[mapping.field_id] = mapping

        missing_fields = [field_id for field_id in target_fields if field_id not in mappings]
        if missing_fields:
            raise TemplateConfigError(
                "Template mappings are missing field ids: %s" % ", ".join(missing_fields)
            )
        return {field_id: mappings[field_id] for field_id in target_fields}

    def _validate_definition(
        self,
        definition: TemplateDefinition,
        field_definitions: Dict[str, TemplateFieldDefinition],
    ) -> None:
        if not definition.excel_template_path.is_file():
            raise TemplateConfigError(
                "Excel template file not found: %s" % definition.excel_template_path
            )
        expected_fields = definition.default_field_ids + definition.optional_field_ids
        missing = [field_id for field_id in expected_fields if field_id not in field_definitions]
        if missing:
            raise TemplateConfigError(
                "Template field definitions are missing field ids: %s" % ", ".join(missing)
            )

    def _load_json(self, path: Path) -> Dict[str, object]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
