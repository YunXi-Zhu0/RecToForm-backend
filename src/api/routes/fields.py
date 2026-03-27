from fastapi import APIRouter, Depends

from src.api.dependencies import get_standard_schema_service
from src.api.schemas import StandardFieldsResponse
from src.services.standard import StandardSchemaService


router = APIRouter(tags=["standard-fields"])


@router.get("/standard-fields", response_model=StandardFieldsResponse)
def get_standard_fields(
    standard_schema_service: StandardSchemaService = Depends(get_standard_schema_service),
) -> StandardFieldsResponse:
    schema = standard_schema_service.load_schema()
    return StandardFieldsResponse(
        version=schema.version,
        default_missing_value=schema.default_missing_value,
        fields=list(schema.keys),
    )
