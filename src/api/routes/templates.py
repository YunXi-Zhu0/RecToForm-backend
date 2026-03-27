from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_template_service
from src.api.schemas import TemplateDetailResponse, TemplateSummaryResponse
from src.services.template import TemplateNotFoundError, TemplateService


router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=List[TemplateSummaryResponse])
def list_templates(
    template_service: TemplateService = Depends(get_template_service),
) -> List[TemplateSummaryResponse]:
    return [
        TemplateSummaryResponse(
            template_id=item.template_id,
            template_name=item.template_name,
            template_version=item.template_version,
            mapping_version=item.mapping_version,
        )
        for item in template_service.list_templates()
    ]


@router.get("/{template_id}", response_model=TemplateDetailResponse)
def get_template_detail(
    template_id: str,
    template_service: TemplateService = Depends(get_template_service),
) -> TemplateDetailResponse:
    try:
        bundle = template_service.get_template_bundle(template_id=template_id)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return TemplateDetailResponse(
        template_id=bundle.template_id,
        template_name=bundle.template_name,
        template_version=bundle.template_version,
        mapping_version=bundle.mapping_version,
        recommended_field_ids=list(bundle.recommended_field_ids),
        default_header_labels=dict(bundle.default_header_labels),
    )
