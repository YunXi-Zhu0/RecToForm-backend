import json
from pathlib import Path
from typing import Dict, List, Optional

from src.core.config import TEMPLATE_DIR
from src.services.standard import StandardSchemaService
from src.services.template.models import (
    ExcelFieldMapping,
    TemplateBundle,
    TemplateDefinition,
    TemplateSummary,
)


class TemplateNotFoundError(ValueError):
    pass


class TemplateConfigError(ValueError):
    pass


class TemplateService:
    def __init__(
        self,
        template_dir: Optional[Path] = None,
        standard_schema_service: Optional[StandardSchemaService] = None,
    ) -> None:
        self.template_dir = Path(template_dir or TEMPLATE_DIR)
        self.index_path = self.template_dir / "index.json"
        self.standard_schema_service = standard_schema_service or StandardSchemaService()

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
    ) -> TemplateBundle:
        payload = self._load_json(
            self._resolve_template_file(
                template_id=template_id,
                template_version=template_version,
            )
        )
        definition = self._build_definition(payload)
        all_excel_mappings = self._build_all_mappings(payload=payload, definition=definition)
        self._validate_definition(definition, all_excel_mappings)
        return TemplateBundle(
            template_id=definition.template_id,
            template_name=definition.template_name,
            template_version=definition.template_version,
            mapping_version=definition.mapping_version,
            excel_template_path=definition.excel_template_path,
            recommended_field_ids=list(definition.recommended_field_ids),
            default_header_labels=dict(definition.default_header_labels),
            excel_mappings=self._select_target_mappings(
                mappings=all_excel_mappings,
                target_fields=definition.recommended_field_ids,
            ),
            referenced_standard_fields=self._collect_referenced_standard_fields(all_excel_mappings),
        )

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
            recommended_field_ids=list(payload.get("recommended_field_ids", [])),
            default_header_labels=dict(payload.get("default_header_labels", {})),
        )

    def _build_all_mappings(
        self,
        payload: Dict[str, object],
        definition: TemplateDefinition,
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
                value_source=str(item.get("value_source", "standard")),
                source_key=str(item.get("source_key", "")),
                default_value=str(item.get("default_value", "")),
            )
            if mapping.field_id in mappings:
                raise TemplateConfigError("Duplicated template field id: %s" % mapping.field_id)
            mappings[mapping.field_id] = mapping
        return mappings

    def _select_target_mappings(
        self,
        mappings: Dict[str, ExcelFieldMapping],
        target_fields: List[str],
    ) -> Dict[str, ExcelFieldMapping]:
        missing_fields = [field_id for field_id in target_fields if field_id not in mappings]
        if missing_fields:
            raise TemplateConfigError(
                "Template mappings are missing field ids: %s" % ", ".join(missing_fields)
            )
        return {field_id: mappings[field_id] for field_id in target_fields}

    def _validate_definition(
        self,
        definition: TemplateDefinition,
        mappings: Dict[str, ExcelFieldMapping],
    ) -> None:
        if not definition.excel_template_path.is_file():
            raise TemplateConfigError(
                "Excel template file not found: %s" % definition.excel_template_path
            )

        missing_labels = [
            field_id
            for field_id in definition.recommended_field_ids
            if field_id not in definition.default_header_labels
        ]
        if missing_labels:
            raise TemplateConfigError(
                "Template default header labels are missing field ids: %s"
                % ", ".join(missing_labels)
            )

        missing_mappings = [
            field_id for field_id in definition.recommended_field_ids if field_id not in mappings
        ]
        if missing_mappings:
            raise TemplateConfigError(
                "Template mappings are missing recommended field ids: %s"
                % ", ".join(missing_mappings)
            )

        supported_sources = {"standard", "system", "user", "rule", "literal"}
        for mapping in mappings.values():
            if mapping.value_source not in supported_sources:
                raise TemplateConfigError(
                    "Unsupported mapping source type for field %s: %s"
                    % (mapping.field_id, mapping.value_source)
                )
            if mapping.value_source == "standard" and not mapping.source_key:
                raise TemplateConfigError(
                    "Template standard mapping must define source_key: %s" % mapping.field_id
                )

        self.standard_schema_service.ensure_known_fields(
            mapping.source_key
            for mapping in mappings.values()
            if mapping.value_source == "standard"
        )

    def _collect_referenced_standard_fields(
        self,
        mappings: Dict[str, ExcelFieldMapping],
    ) -> List[str]:
        referenced_fields: List[str] = []
        for mapping in mappings.values():
            if mapping.value_source != "standard" or mapping.source_key in referenced_fields:
                continue
            referenced_fields.append(mapping.source_key)
        return referenced_fields

    def _load_json(self, path: Path) -> Dict[str, object]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
