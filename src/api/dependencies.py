from functools import lru_cache

from src.api.services import (
    RedisExportFileRegistry,
    ResultBuilder,
    TaskDispatcher,
    TaskRepository,
)
from src.services.standard import StandardSchemaService
from src.services.template import TemplateService


@lru_cache(maxsize=1)
def get_template_service() -> TemplateService:
    return TemplateService()


@lru_cache(maxsize=1)
def get_standard_schema_service() -> StandardSchemaService:
    return StandardSchemaService()


@lru_cache(maxsize=1)
def get_task_repository() -> TaskRepository:
    return TaskRepository()


@lru_cache(maxsize=1)
def get_result_builder() -> ResultBuilder:
    return ResultBuilder()


@lru_cache(maxsize=1)
def get_export_file_registry() -> RedisExportFileRegistry:
    return RedisExportFileRegistry()


@lru_cache(maxsize=1)
def get_task_dispatcher() -> TaskDispatcher:
    return TaskDispatcher(
        repository=get_task_repository(),
        result_builder=get_result_builder(),
    )
