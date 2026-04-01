from typing import List

from pydantic import BaseModel


class StandardFieldsResponse(BaseModel):
    version: str
    default_missing_value: str
    fields: List[str]
