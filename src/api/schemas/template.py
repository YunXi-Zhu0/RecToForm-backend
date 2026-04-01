from typing import Dict, List

from pydantic import BaseModel


class TemplateSummaryResponse(BaseModel):
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str


class TemplateDetailResponse(BaseModel):
    template_id: str
    template_name: str
    template_version: str
    mapping_version: str
    recommended_field_ids: List[str]
    default_header_labels: Dict[str, str]
