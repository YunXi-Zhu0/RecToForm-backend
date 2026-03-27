from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.core.config import EXPORT_FILE_MAPPING_TTL, REDIS_URL


class ExportRegistryError(RuntimeError):
    pass


class ExportFileRegistry:
    def register_standard_fields_export(self, filename: str) -> str:
        raise NotImplementedError

    def resolve_standard_fields_export(self, export_id: str) -> Optional[str]:
        raise NotImplementedError


class RedisExportFileRegistry(ExportFileRegistry):
    STANDARD_FIELDS_KEY_PREFIX = "exports:standard_fields"

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        mapping_ttl: int = EXPORT_FILE_MAPPING_TTL,
    ) -> None:
        self.redis_url = redis_url
        self.mapping_ttl = mapping_ttl
        self._client = None

    def register_standard_fields_export(self, filename: str) -> str:
        export_id = str(uuid4())
        normalized_filename = Path(filename).name
        try:
            client = self._get_client()
            client.set(
                self._build_standard_fields_key(export_id),
                normalized_filename,
                ex=self.mapping_ttl,
            )
        except Exception as exc:  # pragma: no cover - depends on Redis runtime state
            raise ExportRegistryError("Failed to persist export file mapping.") from exc
        return export_id

    def resolve_standard_fields_export(self, export_id: str) -> Optional[str]:
        try:
            client = self._get_client()
            filename = client.get(self._build_standard_fields_key(export_id))
        except Exception as exc:  # pragma: no cover - depends on Redis runtime state
            raise ExportRegistryError("Failed to load export file mapping.") from exc
        if not filename:
            return None
        normalized_filename = Path(str(filename)).name
        if normalized_filename != filename:
            return None
        return normalized_filename

    def _build_standard_fields_key(self, export_id: str) -> str:
        return "%s:%s" % (self.STANDARD_FIELDS_KEY_PREFIX, export_id)

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from redis import Redis
        except ImportError as exc:  # pragma: no cover - fallback for partial envs
            raise ExportRegistryError("Redis dependency is not installed.") from exc
        self._client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._client
